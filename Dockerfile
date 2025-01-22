# Usar una imagen base de Python ligera
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar las dependencias necesarias para psutil
RUN apt-get update && apt-get install -y gcc python3-dev

# Copiar el archivo de requisitos
COPY requirements.txt ./

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los archivos del proyecto
COPY bot.py config.py ./

# Copiar la imagen del bot
COPY telegrambot.png ./

# Configurar las variables de entorno para el logging
ENV PYTHONUNBUFFERED=1

# Comando para ejecutar el bot
CMD ["python", "-u", "bot.py"]