# Guía de Despliegue con Docker

## Despliegue Local con Docker

### 1. Preparación Inicial

Antes de construir la imagen Docker, **debes autenticarte con Telegram**:

```bash
# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus credenciales

# Autenticación inicial (IMPORTANTE: hacer esto ANTES de Docker)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python first_login.py
```

Esto creará el archivo `telegram_session.session` que es **crítico** para el funcionamiento del servicio.

### 2. Construir y Ejecutar con Docker

#### Opción A: Docker Compose (Recomendado)

```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

#### Opción B: Docker directamente

```bash
# Construir imagen
docker build -t telegram-api-service .

# Ejecutar contenedor
docker run -d \
  --name telegram-api \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/telegram_session.session:/app/telegram_session.session:ro \
  telegram-api-service

# Ver logs
docker logs -f telegram-api

# Detener y eliminar
docker stop telegram-api
docker rm telegram-api
```

### 3. Verificar que Funciona

```bash
# Health check
curl http://localhost:5000/health

# Enviar mensaje de prueba
curl -X POST http://localhost:5000/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+5491112345678",
    "message": "Mensaje de prueba desde Docker"
  }'
```

## Despliegue en Producción

### Render.com

1. **Preparación del Repositorio**:
   ```bash
   # Asegúrate de que .gitignore excluye:
   # - .env
   # - *.session

   git add Dockerfile .dockerignore docker-compose.yml
   git commit -m "Add Docker support"
   git push
   ```

2. **Crear Web Service en Render**:
   - Tipo: Web Service
   - Runtime: Docker
   - Docker Command: (dejar vacío, usa CMD del Dockerfile)
   - Port: 5000

3. **Configurar Variables de Entorno**:
   En Render Dashboard → Environment:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_PHONE_NUMBER`
   - `SESSION_NAME`
   - `PORT=5000`

4. **Subir Archivo de Sesión**:
   ```bash
   # Opción 1: Usar Render Shell
   # En el dashboard de Render, abre Shell y ejecuta:
   cat > telegram_session.session
   # Pega el contenido del archivo local y presiona Ctrl+D

   # Opción 2: Usar base64 (más seguro)
   # Local:
   base64 telegram_session.session > session.b64

   # En Render Shell:
   echo "CONTENIDO_BASE64_AQUI" | base64 -d > telegram_session.session
   ```

### Railway.app

1. **Conectar Repositorio**:
   - New Project → Deploy from GitHub
   - Seleccionar repositorio

2. **Railway detectará automáticamente el Dockerfile**

3. **Configurar Variables de Entorno**:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELEGRAM_PHONE_NUMBER`
   - `SESSION_NAME`
   - `PORT` (Railway lo detecta automáticamente)

4. **Subir Archivo de Sesión**:
   ```bash
   # Instalar Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # Seleccionar proyecto
   railway link

   # Subir archivo de sesión al volumen
   railway run bash
   # Luego subir el archivo manualmente
   ```

### Fly.io

1. **Instalar Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Inicializar App**:
   ```bash
   fly launch --no-deploy
   # Configurar nombre y región
   ```

3. **Configurar Secretos**:
   ```bash
   fly secrets set \
     TELEGRAM_API_ID=tu_api_id \
     TELEGRAM_API_HASH=tu_api_hash \
     TELEGRAM_PHONE_NUMBER=+tu_numero \
     SESSION_NAME=telegram_session
   ```

4. **Crear Volumen para Sesión**:
   ```bash
   # Crear volumen
   fly volumes create telegram_data --size 1

   # Editar fly.toml para montar volumen
   ```

5. **Subir Archivo de Sesión y Desplegar**:
   ```bash
   # Desplegar
   fly deploy

   # SSH a la instancia
   fly ssh console

   # Copiar archivo de sesión (desde otra terminal)
   fly ssh sftp shell
   put telegram_session.session /app/
   ```

### DigitalOcean App Platform

1. **Crear App**:
   - Source: GitHub
   - Detecta Dockerfile automáticamente

2. **Configurar**:
   - HTTP Port: 5000
   - Variables de entorno en App Settings

3. **Archivo de Sesión**:
   - Usar volúmenes persistentes
   - O incluir en variables de entorno como base64

### VPS (Ubuntu/Debian)

```bash
# Conectar al servidor
ssh user@tu-servidor

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clonar repositorio
git clone tu-repositorio.git
cd python-telegram-api-service

# Copiar archivo de sesión (desde local)
# En tu máquina local:
scp telegram_session.session user@tu-servidor:~/python-telegram-api-service/

# En el servidor, configurar .env
nano .env

# Ejecutar con Docker Compose
docker-compose up -d

# Configurar Nginx como reverse proxy (opcional)
sudo apt install nginx
sudo nano /etc/nginx/sites-available/telegram-api
```

Configuración de Nginx:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Activar sitio
sudo ln -s /etc/nginx/sites-available/telegram-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL con Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

## Consideraciones de Seguridad

1. **Archivo de Sesión**: Es extremadamente sensible. Manéjalo con el mismo cuidado que una contraseña.

2. **Variables de Entorno**: Nunca las commitees al repositorio.

3. **HTTPS**: Siempre usa HTTPS en producción (configura con Nginx + Let's Encrypt o usa el SSL del hosting).

4. **API Key**: Considera agregar autenticación con API keys para proteger los endpoints.

5. **Rate Limiting**: Implementa rate limiting para evitar abusos y respetar los límites de Telegram.

## Troubleshooting

### Container no inicia
```bash
# Ver logs detallados
docker logs telegram-api

# Verificar que el archivo de sesión existe
docker exec telegram-api ls -la telegram_session.session
```

### "Cliente no autorizado"
```bash
# El archivo .session no está montado correctamente
# Verifica que existe en el host y está montado en el contenedor
```

### Puerto ya en uso
```bash
# Cambiar el puerto en docker-compose.yml
ports:
  - "8000:5000"  # Host:Container
```
