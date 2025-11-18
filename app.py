#!/usr/bin/env python3
"""
Telegram API Microservice usando Telethon
Servicio REST para enviar mensajes de Telegram a números de teléfono
"""

import os
import asyncio
from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.errors import PhoneNumberInvalidError, UserPrivacyRestrictedError
from dotenv import load_dotenv
import logging

# Cargar variables de entorno
load_dotenv()

# Configuración
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Cliente de Telegram (se inicializará en el primer uso)
telegram_client = None


async def get_telegram_client():
    """Obtiene o crea el cliente de Telegram"""
    global telegram_client

    if telegram_client is None:
        telegram_client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await telegram_client.connect()

        # Verificar si está autorizado
        if not await telegram_client.is_user_authorized():
            logger.error("Cliente no autorizado. Ejecute first_login.py primero.")
            raise Exception("Cliente no autorizado")

    return telegram_client


async def send_telegram_message(phone_number, message):
    """
    Envía un mensaje de Telegram a un número de teléfono

    Args:
        phone_number: Número de teléfono en formato internacional (+12345678900)
        message: Mensaje a enviar

    Returns:
        dict: Resultado del envío
    """
    try:
        client = await get_telegram_client()

        # Asegurar formato de número (agregar + si no lo tiene)
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        # Enviar mensaje
        result = await client.send_message(phone_number, message)

        logger.info(f"Mensaje enviado exitosamente a {phone_number}")

        return {
            'success': True,
            'phone_number': phone_number,
            'message_id': result.id,
            'date': result.date.isoformat()
        }

    except PhoneNumberInvalidError:
        logger.error(f"Número de teléfono inválido: {phone_number}")
        return {
            'success': False,
            'error': 'invalid_phone',
            'message': f'Número de teléfono inválido: {phone_number}'
        }

    except UserPrivacyRestrictedError:
        logger.error(f"Usuario tiene restricciones de privacidad: {phone_number}")
        return {
            'success': False,
            'error': 'privacy_restricted',
            'message': f'El usuario no permite mensajes de desconocidos: {phone_number}'
        }

    except Exception as e:
        logger.error(f"Error al enviar mensaje a {phone_number}: {str(e)}")
        return {
            'success': False,
            'error': 'send_failed',
            'message': str(e)
        }


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        'status': 'ok',
        'service': 'telegram-api-service',
        'version': '1.0.0'
    })


@app.route('/send-message', methods=['POST'])
def send_message():
    """
    Endpoint para enviar mensajes de Telegram

    Body JSON:
    {
        "phone_number": "+1234567890",
        "message": "Hola, este es un mensaje de prueba"
    }
    """
    try:
        data = request.get_json()

        # Validar datos
        if not data:
            return jsonify({
                'success': False,
                'error': 'missing_data',
                'message': 'Se requiere body JSON'
            }), 400

        phone_number = data.get('phone_number')
        message = data.get('message')

        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'missing_phone',
                'message': 'Se requiere el campo phone_number'
            }), 400

        if not message:
            return jsonify({
                'success': False,
                'error': 'missing_message',
                'message': 'Se requiere el campo message'
            }), 400

        # Enviar mensaje de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_telegram_message(phone_number, message))
        loop.close()

        # Retornar resultado
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"Error en endpoint send-message: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': str(e)
        }), 500


@app.route('/send-batch', methods=['POST'])
def send_batch():
    """
    Endpoint para enviar mensajes en lote

    Body JSON:
    {
        "messages": [
            {"phone_number": "+1234567890", "message": "Mensaje 1"},
            {"phone_number": "+9876543210", "message": "Mensaje 2"}
        ]
    }
    """
    try:
        data = request.get_json()

        if not data or 'messages' not in data:
            return jsonify({
                'success': False,
                'error': 'missing_data',
                'message': 'Se requiere el campo messages'
            }), 400

        messages = data['messages']

        if not isinstance(messages, list):
            return jsonify({
                'success': False,
                'error': 'invalid_format',
                'message': 'messages debe ser un array'
            }), 400

        # Enviar mensajes
        results = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        for msg in messages:
            phone_number = msg.get('phone_number')
            message = msg.get('message')

            if phone_number and message:
                result = loop.run_until_complete(
                    send_telegram_message(phone_number, message)
                )
                results.append(result)
            else:
                results.append({
                    'success': False,
                    'error': 'invalid_message',
                    'message': 'Faltan campos en el mensaje'
                })

        loop.close()

        # Contar éxitos y fallos
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count

        return jsonify({
            'success': True,
            'total': len(results),
            'sent': success_count,
            'failed': failed_count,
            'results': results
        })

    except Exception as e:
        logger.error(f"Error en endpoint send-batch: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Verificar variables de entorno
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        logger.error("Faltan variables de entorno requeridas")
        logger.error("Asegúrate de configurar: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER")
        exit(1)

    # Iniciar servidor
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Iniciando servidor en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
