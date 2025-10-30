# Usa una imagen base de Python
FROM python:3.11-slim

# Actualiza e instala LibreOffice y dependencias
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-common \
    default-jre-headless \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verifica la instalación de LibreOffice
RUN which libreoffice && \
    which soffice && \
    libreoffice --version && \
    echo "LibreOffice instalado correctamente"

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de requisitos
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del proyecto
COPY . .

# Colecta archivos estáticos
RUN python manage.py collectstatic --noinput

# Expone el puerto
EXPOSE 8000

# Script de entrada
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]