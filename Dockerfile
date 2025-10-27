# Usar Python 3.11 como imagen base
FROM python:3.11-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para cryptography
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    flask \
    pymysql \
    cryptography

# Crear directorios necesarios
RUN mkdir -p /app/src /app/templates

# Copiar archivos
COPY . .

# Exponer puerto para la interfaz web
EXPOSE 8080

# Comando por defecto - ejecutar la aplicación Flask
CMD ["python", "app.py"]