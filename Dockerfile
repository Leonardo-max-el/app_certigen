# Usa una imagen base de Python
FROM python:3.11-slim

# Instala LibreOffice y dependencias
RUN apt-get update && apt-get install -y \
    libreoffice \
    libreoffice-writer \
    libreoffice-common \
    default-jre-headless \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

# Comando de inicio
CMD python manage.py migrate && \
    python manage.py create_admin && \
    gunicorn Admin_Upla.wsgi:application --bind 0.0.0.0:$PORT --timeout 120