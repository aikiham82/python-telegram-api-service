#!/usr/bin/env python3
"""
Script de autenticación inicial para Telegram
Ejecutar SOLO la primera vez para crear la sesión
"""

import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')


async def main():
    """Proceso de autenticación inicial"""
    print("=== Autenticación Inicial de Telegram ===\n")

    # Verificar variables
    if not API_ID or not API_HASH or not PHONE_NUMBER:
        print("ERROR: Faltan variables de entorno")
        print("Asegúrate de configurar:")
        print("  - TELEGRAM_API_ID")
        print("  - TELEGRAM_API_HASH")
        print("  - TELEGRAM_PHONE_NUMBER")
        return

    print(f"API ID: {API_ID}")
    print(f"Teléfono: {PHONE_NUMBER}")
    print(f"Sesión: {SESSION_NAME}\n")

    # Crear cliente
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    print("Conectando a Telegram...")
    await client.connect()

    # Verificar si ya está autorizado
    if await client.is_user_authorized():
        print("\n✓ Ya estás autorizado!")
        me = await client.get_me()
        print(f"  Usuario: {me.first_name} {me.last_name or ''}")
        print(f"  Username: @{me.username or 'N/A'}")
        print(f"  ID: {me.id}")
    else:
        print("Iniciando proceso de autenticación...")

        # Solicitar código
        await client.send_code_request(PHONE_NUMBER)
        print(f"\nSe ha enviado un código de verificación a {PHONE_NUMBER}")
        code = input("Ingresa el código que recibiste: ")

        try:
            # Iniciar sesión
            await client.sign_in(PHONE_NUMBER, code)
            print("\n✓ Autenticación exitosa!")

            # Obtener información del usuario
            me = await client.get_me()
            print(f"  Usuario: {me.first_name} {me.last_name or ''}")
            print(f"  Username: @{me.username or 'N/A'}")
            print(f"  ID: {me.id}")

        except Exception as e:
            print(f"\n✗ Error en la autenticación: {e}")

            # Si requiere contraseña de dos pasos
            if "password" in str(e).lower():
                print("\nTu cuenta tiene verificación en dos pasos habilitada")
                password = input("Ingresa tu contraseña de Telegram: ")
                try:
                    await client.sign_in(password=password)
                    print("\n✓ Autenticación exitosa!")

                    me = await client.get_me()
                    print(f"  Usuario: {me.first_name} {me.last_name or ''}")
                    print(f"  Username: @{me.username or 'N/A'}")
                    print(f"  ID: {me.id}")
                except Exception as e2:
                    print(f"\n✗ Error: {e2}")
                    return

    print("\n" + "="*50)
    print("Sesión creada exitosamente!")
    print(f"Archivo de sesión: {SESSION_NAME}.session")
    print("\nAhora puedes ejecutar el servidor con:")
    print("  python app.py")
    print("="*50)

    await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
