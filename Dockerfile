# Usar imagen oficial de Python slim
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY app.py .
COPY first_login.py .

# Crear directorio para la sesión
RUN mkdir -p /app/sessions

# Exponer el puerto
EXPOSE 5000

# Variables de entorno por defecto (se pueden sobrescribir)
ENV PORT=5000
ENV SESSION_NAME=telegram_session

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando para ejecutar la aplicación
# NOTA: Usar solo 1 worker porque Telethon usa SQLite para sesiones
# SQLite no soporta acceso concurrente de múltiples procesos
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "--timeout", "120", "--worker-class", "sync", "app:app"]
