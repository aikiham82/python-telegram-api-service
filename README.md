# Telegram API Microservice

Microservicio REST para enviar mensajes de Telegram a números de teléfono usando Telethon (Telegram Client API).

## Características

- Envío de mensajes a números de teléfono (no requiere que sean contactos)
- API REST simple y fácil de integrar
- Soporte para envío individual y en lote
- Manejo de errores y logs detallados
- Compatible con n8n y otras herramientas de automatización

## Requisitos

- Python 3.8 o superior
- Cuenta de Telegram activa
- Credenciales de aplicación de Telegram (API ID y API Hash)

## Instalación

### 1. Obtener Credenciales de Telegram

1. Visita https://my.telegram.org/apps
2. Inicia sesión con tu número de teléfono
3. Crea una nueva aplicación
4. Guarda tu `api_id` y `api_hash`

### 2. Instalar Dependencias

```bash
cd python-telegram-api-service

# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

Configura las siguientes variables:

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE_NUMBER=+5491112345678
SESSION_NAME=telegram_session
PORT=5000
```

### 4. Autenticación Inicial

**IMPORTANTE:** Ejecuta este paso solo la primera vez:

```bash
python first_login.py
```

Este script:
1. Te enviará un código de verificación a tu teléfono
2. Te pedirá que ingreses el código
3. Creará un archivo de sesión (`telegram_session.session`)
4. Si tienes verificación en dos pasos, te pedirá tu contraseña

**Guarda el archivo `.session` en un lugar seguro.** Este archivo contiene tu sesión autenticada.

### 5. Iniciar el Servidor

```bash
# Modo desarrollo
python app.py

# Modo producción (con gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

El servidor estará disponible en `http://localhost:5000`

## API Endpoints

### 1. Health Check

Verifica que el servicio esté funcionando.

```bash
GET /health
```

**Respuesta:**
```json
{
  "status": "ok",
  "service": "python-telegram-api-service",
  "version": "1.0.0"
}
```

### 2. Enviar Mensaje Individual

Envía un mensaje a un número de teléfono.

```bash
POST /send-message
Content-Type: application/json

{
  "phone_number": "+5491112345678",
  "message": "Hola, este es un mensaje de prueba"
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "phone_number": "+5491112345678",
  "message_id": 12345,
  "date": "2025-11-17T14:30:00"
}
```

**Respuesta con error:**
```json
{
  "success": false,
  "error": "invalid_phone",
  "message": "Número de teléfono inválido: +123"
}
```

### 3. Enviar Mensajes en Lote

Envía múltiples mensajes en una sola petición.

```bash
POST /send-batch
Content-Type: application/json

{
  "messages": [
    {
      "phone_number": "+5491112345678",
      "message": "Mensaje para el usuario 1"
    },
    {
      "phone_number": "+5491187654321",
      "message": "Mensaje para el usuario 2"
    }
  ]
}
```

**Respuesta:**
```json
{
  "success": true,
  "total": 2,
  "sent": 2,
  "failed": 0,
  "results": [
    {
      "success": true,
      "phone_number": "+5491112345678",
      "message_id": 12345,
      "date": "2025-11-17T14:30:00"
    },
    {
      "success": true,
      "phone_number": "+5491187654321",
      "message_id": 12346,
      "date": "2025-11-17T14:30:01"
    }
  ]
}
```

## Tipos de Errores

| Código de Error | Descripción |
|----------------|-------------|
| `invalid_phone` | Número de teléfono inválido o no existe en Telegram |
| `privacy_restricted` | El usuario no permite mensajes de desconocidos |
| `send_failed` | Error general al enviar el mensaje |
| `missing_data` | Faltan datos en la petición |
| `internal_error` | Error interno del servidor |

## Integración con n8n

### Configurar el nodo HTTP Request

1. En tu workflow de n8n, reemplaza el nodo "Telegram" con "HTTP Request"
2. Configura el nodo así:
   - **Method:** POST
   - **URL:** `http://localhost:5000/send-message` (o la URL de tu servidor)
   - **Body Content Type:** JSON
   - **Body:**
     ```json
     {
       "phone_number": "={{ $json.telefono }}",
       "message": "Hola, este es un mensaje automático desde nuestro sistema."
     }
     ```

## Despliegue en Producción

### Opción 1: Servidor Linux (Systemd)

Crea un servicio systemd:

```bash
sudo nano /etc/systemd/system/telegram-api.service
```

Contenido:

```ini
[Unit]
Description=Telegram API Microservice
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/a/python-telegram-api-service
Environment="PATH=/ruta/a/python-telegram-api-service/venv/bin"
ExecStart=/ruta/a/python-telegram-api-service/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Iniciar el servicio:

```bash
sudo systemctl enable telegram-api
sudo systemctl start telegram-api
sudo systemctl status telegram-api
```

### Opción 2: Docker (Recomendado)

Este proyecto incluye configuración completa de Docker. Ver **[DEPLOYMENT.md](DEPLOYMENT.md)** para instrucciones detalladas.

Inicio rápido:

```bash
# 1. Autenticarse primero (genera telegram_session.session)
python first_login.py

# 2. Configurar variables de entorno
cp .env.example .env
nano .env

# 3. Ejecutar con Docker Compose
docker-compose up -d
```

**Importante**: El archivo `.session` debe generarse ANTES de usar Docker.

### Opción 3: Render.com

1. Sube el código a un repositorio Git
2. Conecta el repositorio a Render
3. Configura las variables de entorno en Render
4. **IMPORTANTE:** Sube el archivo `.session` manualmente al servidor de Render

## Seguridad

### Recomendaciones:

1. **Protege tu archivo .session**: Este archivo contiene tu sesión autenticada. No lo compartas ni lo subas a repositorios públicos.

2. **Usa HTTPS en producción**: Nunca expongas el servicio en HTTP en producción.

3. **Implementa autenticación**: Agrega autenticación con API Keys:

   ```python
   API_KEY = os.getenv('API_KEY')

   @app.before_request
   def check_api_key():
       if request.endpoint != 'health_check':
           api_key = request.headers.get('X-API-Key')
           if api_key != API_KEY:
               return jsonify({'error': 'Unauthorized'}), 401
   ```

4. **Rate limiting**: Implementa límites de tasa para evitar abuso.

5. **Firewall**: Restringe el acceso al puerto 5000 solo a IPs autorizadas.

## Troubleshooting

### Error: "Cliente no autorizado"

- Ejecuta `python first_login.py` nuevamente
- Verifica que el archivo `.session` exista y tenga permisos correctos

### Error: "FloodWaitError"

- Telegram tiene límites de envío de mensajes
- Espera el tiempo indicado antes de enviar más mensajes
- Considera implementar colas y throttling

### Error: "PhoneNumberInvalidError"

- Verifica que el número esté en formato internacional (+código_país + número)
- Asegúrate de que el número tenga Telegram instalado

### El usuario no recibe mensajes

- Verifica la configuración de privacidad del usuario
- Algunos usuarios solo aceptan mensajes de contactos

## Licencia

MIT

## Soporte

Para problemas o preguntas, abre un issue en el repositorio.
