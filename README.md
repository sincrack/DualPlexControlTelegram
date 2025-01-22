# 🤖 DualPlexControlTelegram

¡Bienvenido al DualPlexControlTelegram! Este bot de Telegram te permite gestionar y monitorear 2 servidores Plex de manera fácil y divertida. 🎉

## 🌟 Características

- 📊 Muestra estadísticas de tus servidores Plex.
- 🔄 Actualiza bibliotecas de Plex.
- 👀 Visualiza reproducciones actuales.
- 📈 Monitorea el estado del servidor (CPU, RAM, IP, tiempo de actividad).
- 🎬 Muestra todos los streams activos.
- 🔍 Identifica usuarios que están transcodificando.

## 🚀 Despliegue

### Requisitos previos

- Docker y Docker Compose instalados en tu sistema.
- Servidores Plex configurados.
- Glances instalado en los servidores donde corren Plex.

### Pasos para el despliegue

1. **Clonar el repositorio**

    ```bash
    git clone https://github.com/sincrack/DualPlexControlTelegram.git
    cd DualPlexControlTelegram
    ```

2. **Configurar el archivo `docker-compose.yml`**

    Edita las siguientes variables de entorno en el archivo `docker-compose.yml`:

    - `TELEGRAM_BOT_TOKEN`: Tu token de bot de Telegram.
    - `PLEX_SERVER_X_URL`: URL de tu servidor Plex (reemplaza X con el número de servidor).
    - `PLEX_SERVER_X_TOKEN`: Token de tu servidor Plex.
    - `GLANCES_SERVER_X_URL`: URL de Glances en tu servidor Plex.
    - `TELEGRAM_API_ID`: TU API DE TELEGRAM  (Podeis obtenerlo aqui: https://my.telegram.org/apps)
    - `TELEGRAM_API_HASH`: TU API HASH DE TELEGRAM

    Ejemplo:

    ```yaml
    environment:
      - TELEGRAM_BOT_TOKEN=tu_token_aqui
      - PLEX_SERVER_1_URL=http://192.168.1.100:32400
      - PLEX_SERVER_1_TOKEN=tu_token_plex_aqui
      - GLANCES_SERVER_1_URL=http://192.168.1.100:61208
    ```

3. **Configurar el archivo `bot.py`**

    Agrega los IDs de grupos autorizados donde incluiras el bot en `AUTHORIZED_CHAT_IDS`.
    Define el nombre de usuario de telegram que tendra permiso sobre el bot en `AUTHORIZED_USERNAME`.

    Ejemplo:

    ```python
    AUTHORIZED_CHAT_IDS = [-1234567890, -9876543210]
    AUTHORIZED_USERNAME = "TuNombreDeUsuario"
    ```

4. **Personalizar nombres de servidores**

    Modifica los nombres de los servidores Plex en `config.py`:

    ```python
    PLEX_SERVERS = [
        {
            'name': 'MiServidor1',
            'url': os.getenv('PLEX_SERVER_1_URL'),
            'token': os.getenv('PLEX_SERVER_1_TOKEN')
        },
        {
            'name': 'MiServidor2',
            'url': os.getenv('PLEX_SERVER_2_URL'),
            'token': os.getenv('PLEX_SERVER_2_TOKEN')
        }
    ]
    ```

5. **Instalar Glances en los servidores Plex**

    En cada servidor Plex, instala Glances y configúralo como servicio web:

    ```bash
    sudo apt-get update
    sudo apt-get install glances
    glances -w &
    ```

6. **Iniciar el bot**

    Desde el directorio del proyecto, ejecuta:

    ```bash
    docker-compose up -d --build
    ```

    ¡Y listo! El Bot DualPlexControlTelegram estará funcionando.

## 🛠 Uso

Inicia una conversación con el bot en Telegram y usa el comando `/start` para comenzar. El bot incluye botones interactivos para facilitar el uso.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si tienes ideas para mejorar este bot, abre un issue o envía un pull request.

## 📜 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) por facilitar la creación de bots de Telegram.
- [PlexAPI](https://github.com/pkkid/python-plexapi) por la interacción con Plex.
- [Glances](https://github.com/nicolargo/glances) por el monitoreo del sistema.

Creado con ❤️ por @SinCracK.
