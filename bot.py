import logging
import sys
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from plexapi.server import PlexServer
from config import TELEGRAM_BOT_TOKEN, PLEX_SERVERS, GLANCES_SERVERS
import os

# FunciÃ³n de utilidad para escapar caracteres especiales de Markdown
def escape_markdown(text):
    """
    Escapa los caracteres especiales de Markdown en el texto.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

# ConfiguraciÃ³n de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración de seguridad
AUTHORIZED_CHAT_IDS = [-1234567890, -9876543210]
AUTHORIZED_USERNAME = "TuNombreDeUsuario"

def is_authorized(update: Update) -> bool:
    """Verifica si el usuario estÃ¡ autorizado para usar el bot."""
    if update.effective_chat.id in AUTHORIZED_CHAT_IDS:
        return True
    if update.effective_user and update.effective_user.username == AUTHORIZED_USERNAME:
        return True
    return False

def send_message_with_image(update: Update, context: CallbackContext, text: str, reply_markup: InlineKeyboardMarkup) -> Message:
    image_path = 'telegrambot.png'
    try:
        with open(image_path, 'rb') as photo:
            return context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error al enviar imagen: {str(e)}")
        return context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

def edit_message_with_image(update: Update, context: CallbackContext, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    try:
        context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error al editar mensaje: {str(e)}")
        send_message_with_image(update, context, text, reply_markup)

def start(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /start recibido")
    if not is_authorized(update):
        update.message.reply_text("Lo siento, no estÃ¡s autorizado para usar este bot.")
        return
    show_main_menu(update, context)

def show_main_menu(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando menÃº principal")
    if not is_authorized(update):
        return
    keyboard = [
        [InlineKeyboardButton("ðŸ–¥ï¸ Ver servidores", callback_data='view_servers')],
        [InlineKeyboardButton("ðŸŽ¬ Streams actuales", callback_data='current_streams')],
        [InlineKeyboardButton("ðŸ”„ Usuarios transcodificando", callback_data='transcoding_users')],
        [InlineKeyboardButton("â„¹ï¸ Obtener Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = ('Â¡Hola! ðŸŽ¬âœ¨\n\n'
                   'Bienvenido a Dual Plex Control, tu centro de mando para gestionar Plex de manera sencilla y eficiente.\n\n'
                   'Â¿Preparado para tomar el control total de tu experiencia multimedia? ðŸš€\n\n'
                   'Dime, Â¿quÃ© te gustarÃ­a hacer hoy?')
    
    edit_message_with_image(update, context, welcome_text, reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    logger.info("BotÃ³n presionado")
    if not is_authorized(update):
        update.callback_query.answer("No estÃ¡s autorizado para usar este bot, ponte en contacto con @SinCracK")
        return
    query = update.callback_query
    query.answer()

    try:
        if query.data == 'view_servers':
            show_servers(update, context)
        elif query.data == 'current_streams':
            show_current_streams(update, context)
        elif query.data.startswith('server_'):
            server_index = int(query.data.split('_')[1])
            show_server_options(update, context, PLEX_SERVERS[server_index])
        elif query.data.startswith('update_'):
            server_index = int(query.data.split('_')[1])
            update_libraries(update, context, PLEX_SERVERS[server_index])
        elif query.data.startswith('playing_'):
            server_index = int(query.data.split('_')[1])
            view_playing(update, context, PLEX_SERVERS[server_index])
        elif query.data.startswith('status_'):
            server_index = int(query.data.split('_')[1])
            show_server_status(update, context, PLEX_SERVERS[server_index])
        elif query.data.startswith('stats_'):
            server_index = int(query.data.split('_')[1])
            show_library_stats(update, context, PLEX_SERVERS[server_index])
        elif query.data == 'help':
            show_help(update, context)
        elif query.data == 'main_menu':
            show_main_menu(update, context)
        elif query.data == 'transcoding_users':
            show_transcoding_users(update, context)
    except Exception as e:
        logger.error(f"Error en el manejo de botones: {str(e)}")
        error_message = f"Lo siento, ha ocurrido un error: {str(e)}"
        keyboard = [[InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        edit_message_with_image(update, context, error_message, reply_markup)

def show_servers(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando servidores")
    if not is_authorized(update):
        return
    keyboard = [[InlineKeyboardButton(f"ðŸ™ï¸ {server['name']}", callback_data=f"server_{i}")] for i, server in enumerate(PLEX_SERVERS)]
    keyboard.append([InlineKeyboardButton("ðŸ”™ Volver al MenÃº Principal", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, "Â¡Elige el servidor! ðŸ‘‘", reply_markup)

def show_server_options(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando opciones para el servidor: {server['name']}")
    if not is_authorized(update):
        return
    keyboard = [
        [InlineKeyboardButton("ðŸ”„ Actualizar bibliotecas", callback_data=f"update_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ‘€ Ver reproducciones", callback_data=f"playing_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ“Š Ver estado del servidor", callback_data=f"status_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ“š Bibliotecas", callback_data=f"stats_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ”™ Volver a Servidores", callback_data="view_servers")],
        [InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, f"Â¿QuÃ© quieres hacer en {server['name']}? âœ¨", reply_markup)

def update_libraries(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Actualizando bibliotecas en el servidor: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        for section in plex.library.sections():
            section.update()
        success_message = f"Â¡Boom! ðŸ’¥ Bibliotecas actualizadas en {server['name']}. Â¡Tu contenido estÃ¡ mÃ¡s fresco que nunca! ðŸŒŸ"
        keyboard = [
            [InlineKeyboardButton("ðŸ”™ Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
            [InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        edit_message_with_image(update, context, success_message, reply_markup)
    except Exception as e:
        logger.error(f"Error al actualizar bibliotecas: {str(e)}")
        error_message = f"Error al actualizar bibliotecas en {server['name']}: {str(e)}"
        keyboard = [[InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        edit_message_with_image(update, context, error_message, reply_markup)

def view_playing(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando reproducciones en el servidor: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        sessions = plex.sessions()
        if sessions:
            message = f"ðŸŽ¬ Â¡AcciÃ³n en *{server['name']}*! Esto es lo que estÃ¡ pasando:\n\n"
            for session in sessions:
                message += f"ðŸ‘¤ *Usuario:* {escape_markdown(session.usernames[0])}\n"
                if session.type == 'episode':
                    message += f"ðŸŽ¥ *Serie:* {escape_markdown(session.grandparentTitle)}\n"
                    message += f"ðŸ“º *Episodio:* {escape_markdown(session.title)}\n"
                else:
                    message += f"ðŸŽ¥ *TÃ­tulo:* {escape_markdown(session.title)}\n"
                if session.type == 'movie':
                    session_type = 'PelÃ­cula'
                elif session.type == 'episode':
                    session_type = 'Episodio'
                else:
                    session_type = session.type.capitalize()
                message += f"ðŸ“º *Tipo:* {escape_markdown(session_type)}\n"
                message += f"â³ *Progreso:* {session.viewOffset // 60000} minutos\n"
                message += f"ðŸ–¥ï¸ *Reproductor:* {escape_markdown(session.player.title)}\n"
                message += f"\n"
        else:
            message = f"ðŸ˜´ Parece que {server['name']} estÃ¡ tomando una siesta. Â¡No hay reproducciones en curso!"
    except Exception as e:
        logger.error(f"Error al obtener reproducciones: {str(e)}")
        message = f"Error al obtener reproducciones de {server['name']}: {str(e)}"
    
    keyboard = [
        [InlineKeyboardButton("ðŸ”™ Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_current_streams(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando streams actuales")
    if not is_authorized(update):
        return
    
    total_users = 0
    total_transcoding = 0
    message = "ðŸŽ¬ *Streams actuales en todos los servidores:*\n\n"
    
    for server in PLEX_SERVERS:
        try:
            plex = PlexServer(server['url'], server['token'])
            sessions = plex.sessions()
            
            server_users = len(sessions)
            server_transcoding = 0
            total_users += server_users
            
            message += f"*Servidor {escape_markdown(server['name'])}* ({server_users} usuarios activos):\n"
            if sessions:
                for session in sessions:
                    message += f"ðŸ‘¤ *Usuario:* {escape_markdown(session.usernames[0])}\n"
                    if session.type == 'episode':
                        message += f"ðŸŽ¥ *Serie:* {escape_markdown(session.grandparentTitle)}\n"
                        message += f"ðŸ“º *Episodio:* {escape_markdown(session.title)}\n"
                    else:
                        message += f"ðŸŽ¥ *TÃ­tulo:* {escape_markdown(session.title)}\n"
                    if session.type == 'movie':
                        session_type = 'PelÃ­cula'
                    elif session.type == 'episode':
                        session_type = 'Episodio'
                    else:
                        session_type = session.type.capitalize()
                    message += f"ðŸ“º *Tipo:* {escape_markdown(session_type)}\n"
                    message += f"â³ *Progreso:* {session.viewOffset // 60000} minutos\n"

                    # Verificar si se estÃ¡ realizando transcodificaciÃ³n
                    if session.transcodeSessions:
                        message += "ðŸ”„ *Transcodificando:* SÃ­\n"
                        server_transcoding += 1
                    else:
                        message += "ðŸ”„ *Transcodificando:* No\n"
                    message += f"ðŸ–¥ï¸ *Reproductor:* {escape_markdown(session.player.title)}\n"
                    message += "\n"
                
                total_transcoding += server_transcoding
            else:
                message += "No hay reproducciones activas.\n\n"
        except Exception as e:
            logger.error(f"Error al conectar con {escape_markdown(server['name'])}: {str(e)}")
            message += f"Error al conectar con {escape_markdown(server['name'])}: {str(e)}\n\n"
    
    message = (f"*Total de usuarios activos:* {total_users}\n"
               f"*Usuarios realizando transcodificaciÃ³n:* {total_transcoding}\n\n") + message
    
    keyboard = [[InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def get_glances_data(url):
    try:
        # Intenta primero con la API v3
        cpu_url = f"{url}/api/3/cpu"
        mem_url = f"{url}/api/3/mem"
        ip_url = f"{url}/api/3/ip"
        uptime_url = f"{url}/api/3/uptime"
        
        cpu_response = requests.get(cpu_url, timeout=5)
        mem_response = requests.get(mem_url, timeout=5)
        ip_response = requests.get(ip_url, timeout=5)
        uptime_response = requests.get(uptime_url, timeout=5)
        
        if cpu_response.status_code == 404 or mem_response.status_code == 404 or ip_response.status_code == 404 or uptime_response.status_code == 404:
            # Si obtenemos un 404, intentamos con la API v4
            cpu_url = f"{url}/api/4/cpu"
            mem_url = f"{url}/api/4/mem"
            ip_url = f"{url}/api/4/ip"
            uptime_url = f"{url}/api/4/uptime"
            
            cpu_response = requests.get(cpu_url, timeout=5)
            mem_response = requests.get(mem_url, timeout=5)
            ip_response = requests.get(ip_url, timeout=5)
            uptime_response = requests.get(uptime_url, timeout=5)
        
        if cpu_response.status_code == 200 and mem_response.status_code == 200 and ip_response.status_code == 200 and uptime_response.status_code == 200:
            cpu_data = cpu_response.json()
            mem_data = mem_response.json()
            ip_data = ip_response.json()
            uptime_data = uptime_response.json()
            
            # Manejo de diferentes estructuras de datos para CPU
            if 'total' in cpu_data:
                cpu_usage = cpu_data['total']
            elif isinstance(cpu_data, list) and len(cpu_data) > 0 and 'total' in cpu_data[0]:
                cpu_usage = cpu_data[0]['total']
            else:
                raise ValueError("Estructura de datos de CPU no reconocida")
            
            # Manejo de diferentes estructuras de datos para memoria
            if 'used' in mem_data and 'total' in mem_data:
                mem_usage = (mem_data['used'] / mem_data['total']) * 100
            elif isinstance(mem_data, list) and len(mem_data) > 0 and 'used' in mem_data[0] and 'total' in mem_data[0]:
                mem_usage = (mem_data[0]['used'] / mem_data[0]['total']) * 100
            else:
                raise ValueError("Estructura de datos de memoria no reconocida")
            
            # Manejo de diferentes estructuras de datos para IP
            public_ip = ip_data.get('public_address', 'No disponible')
            private_ip = ip_data.get('address', 'No disponible')
            
            # Manejo de diferentes estructuras de datos para uptime
            if isinstance(uptime_data, str):
                uptime = uptime_data
            elif isinstance(uptime_data, dict) and 'uptime' in uptime_data:
                uptime = uptime_data['uptime']
            elif isinstance(uptime_data, list) and len(uptime_data) > 0:
                uptime = uptime_data[0] if isinstance(uptime_data[0], str) else uptime_data[0].get('uptime', 'No disponible')
            else:
                uptime = 'No disponible'
            
            return f"Uso de CPU: {cpu_usage:.1f}%\nUso de RAM: {mem_usage:.1f}%\nIP PÃºblica: {public_ip}\nIP Privada: {private_ip}\nTiempo de actividad: {uptime}"
        else:
            return f"Error al obtener datos. CÃ³digos de estado - CPU: {cpu_response.status_code}, RAM: {mem_response.status_code}, IP: {ip_response.status_code}, Uptime: {uptime_response.status_code}"
    except requests.RequestException as e:
        return f"Error al conectar con Glances: {str(e)}"
    except ValueError as e:
        return f"Error al procesar datos de Glances: {str(e)}"

def show_server_status(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando estado del servidor: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        status = "ðŸŸ¢ En lÃ­nea"
        
        message = f"ðŸ“Š *Estado del servidor {escape_markdown(server['name'])}:*\n\n"
        message += f"*Estado:* {status}\n"
        message += f"*VersiÃ³n:* {escape_markdown(plex.version)}\n"
        message += f"*Plataforma:* {escape_markdown(plex.platform)}\n"
        message += f"*Identificador:* {escape_markdown(plex.machineIdentifier)}\n\n"
        
        if hasattr(plex, 'myPlexAccount'):
            account = plex.myPlexAccount()
            if account:
                message += f"*Nombre de la cuenta:* {escape_markdown(account.username)}\n"
                message += f"*Email de la cuenta:* {escape_markdown(account.email)}\n"
        if hasattr(plex, 'friendlyName'):
            message += f"*Nombre amigable:* {escape_markdown(plex.friendlyName)}\n"
        
        # Obtener informaciÃ³n de Glances
        glances_server = next((s for s in GLANCES_SERVERS if s['name'].lower() == server['name'].lower()), None)
        if glances_server:
            glances_data = get_glances_data(glances_server['url'])
            if not glances_data.startswith("Error"):
                cpu_usage, ram_usage, public_ip, private_ip, uptime = glances_data.split('\n')
                message += f"\nðŸ’» *{cpu_usage}*\n"
                message += f"ðŸ§  *{ram_usage}*\n"
                message += f"ðŸŒ *{public_ip}*\n"
                message += f"ðŸ  *{private_ip}*\n"
                message += f"â±ï¸ *{uptime}*\n"
            else:
                message += f"\nâš ï¸ {glances_data}\n"
        else:
            message += f"\nâš ï¸ No se encontrÃ³ configuraciÃ³n de Glances para el servidor {escape_markdown(server['name'])}\n"

        sessions = plex.sessions()
        active_streams = len(sessions)
        message += f"\n*Streams activos:* {active_streams}\n"
        
        libraries = plex.library.sections()
        library_info = "\n*Bibliotecas:*\n"
        for lib in libraries:
            library_info += f"- *{escape_markdown(lib.title)}*\n"
        message += library_info

    except Exception as e:
        logger.error(f"Error al obtener el estado del servidor: {str(e)}")
        status = "ðŸ”´ Fuera de lÃ­nea"
        message = f"ðŸ“Š *Estado del servidor {escape_markdown(server['name'])}:*\n\n"
        message += f"*Estado:* {status}\n"
        message += f"Error: No se pudo conectar al servidor o obtener informaciÃ³n. Detalles: {str(e)}\n"
    
    keyboard = [
        [InlineKeyboardButton("ðŸ”™ Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_library_stats(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando estadÃ­sticas de la biblioteca: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        message = f"ðŸ“š *Bibliotecas de {escape_markdown(server['name'])}:*\n\n"
        
        for section in plex.library.sections():
            message += f"ðŸ“ *{escape_markdown(section.title)}:*\n"
            if section.type == 'movie':
                section_type = 'PelÃ­cula'
            elif section.type == 'show':
                section_type = 'Serie'
            else:
                section_type = section.type.capitalize()
            message += f"   - *Tipo:* {escape_markdown(section_type)}\n"
            message += f"   - *Total de elementos:* {section.totalSize}\n\n"
    except Exception as e:
        logger.error(f"Error al obtener estadÃ­sticas de la biblioteca: {str(e)}")
        message = f"Error al obtener estadÃ­sticas de la biblioteca {escape_markdown(server['name'])}: {str(e)}"
    
    keyboard = [
        [InlineKeyboardButton("ðŸ”™ Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_help(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando ayuda")
    if not is_authorized(update):
        return
    help_text = (
        "ðŸ¦¸â€â™‚ï¸ Â¡Bienvenido al Centro de Ayuda del Bot! ðŸ¦¸â€â™€ï¸\n\n"
        "AquÃ­ tienes una guÃ­a rÃ¡pida de lo que puedo hacer:\n\n"
        "ðŸ–¥ï¸ *Ver servidores:* Te muestra una lista de tus servidores Plex.\n"
        "ðŸ”„ *Actualizar bibliotecas:* Actualiza todas las bibliotecas en un servidor especÃ­fico.\n"
        "ðŸ‘€ *Ver reproducciones:* Muestra quÃ© se estÃ¡ reproduciendo actualmente en un servidor.\n"
        "ðŸ“Š *Estado del servidor:* Muestra informaciÃ³n sobre el estado y la versiÃ³n del servidor.\n"
        "ðŸ“š *Bibliotecas:* Muestra las bibliotecas del servidor.\n"
        "ðŸŽ¬ *Streams actuales:* Muestra todos los streams activos en tus servidores Plex.\n"
        "ðŸ”„ *Usuarios transcodificando:* Muestra los usuarios que estÃ¡n realizando transcodificaciÃ³n.\n\n"
        "Â¡No dudes en contactar conmigo si tienes dudas @SinCracK ! ðŸŽ‰"
    )
    keyboard = [[InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, help_text, reply_markup)

def show_transcoding_users(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando usuarios transcodificando")
    if not is_authorized(update):
        return
    
    message = "ðŸ”„ *Usuarios realizando transcodificaciÃ³n:*\n\n"
    total_transcoding_video = 0
    total_transcoding_audio = 0
    
    for server in PLEX_SERVERS:
        try:
            plex = PlexServer(server['url'], server['token'])
            sessions = plex.sessions()
            
            server_transcoding_video = 0
            server_transcoding_audio = 0
            server_message = f"*Servidor {escape_markdown(server['name'])}:*\n"
            
            for session in sessions:
                if session.transcodeSessions:
                    transcode_type = []
                    for transcode_session in session.transcodeSessions:
                        if transcode_session.videoDecision == 'transcode':
                            transcode_type.append('Video')
                            server_transcoding_video += 1
                        if transcode_session.audioDecision == 'transcode':
                            transcode_type.append('Audio')
                            server_transcoding_audio += 1
                    
                    server_message += f"ðŸ‘¤ *Usuario:* {escape_markdown(session.usernames[0])}\n"
                    if session.type == 'episode':
                        server_message += f"ðŸŽ¥ *Serie:* {escape_markdown(session.grandparentTitle)}\n"
                        server_message += f"ðŸ“º *Episodio:* {escape_markdown(session.title)}\n"
                    else:
                        server_message += f"ðŸŽ¥ *TÃ­tulo:* {escape_markdown(session.title)}\n"
                    if session.type == 'movie':
                        session_type = 'PelÃ­cula'
                    elif session.type == 'episode':
                        session_type = 'Episodio'
                    else:
                        session_type = session.type.capitalize()
                    server_message += f"ðŸ“º *Tipo:* {escape_markdown(session_type)}\n"
                    server_message += f"â³ *Progreso:* {session.viewOffset // 60000} minutos\n"
                    server_message += f"ðŸ–¥ï¸ *Reproductor:* {escape_markdown(session.player.title)}\n"
                    
                    if transcode_type:
                        server_message += f"ðŸ”„ *Transcodificando:* {' y '.join(transcode_type)}\n"
                    else:
                        server_message += "ðŸ”„ *Transcodificando:* Desconocido\n"
                    server_message += "\n"  # Agregar una lÃ­nea en blanco entre usuarios
            
            if server_transcoding_video > 0 or server_transcoding_audio > 0:
                message += server_message
                total_transcoding_video += server_transcoding_video
                total_transcoding_audio += server_transcoding_audio
            else:
                message += f"Servidor {escape_markdown(server['name'])}: No hay usuarios transcodificando.\n\n"
        
        except Exception as e:
            logger.error(f"Error al conectar con {escape_markdown(server['name'])}: {str(e)}")
            message += f"Error al conectar con {escape_markdown(server['name'])}: {str(e)}\n\n"
    
    if total_transcoding_video == 0 and total_transcoding_audio == 0:
        message = "ðŸ˜´ *No hay usuarios realizando transcodificaciÃ³n en este momento.*"
    else:
        message = (f"*Transcodificando Video:* {total_transcoding_video} usuarios\n"
                   f"*Transcodificando Audio:* {total_transcoding_audio} usuarios\n\n") + message
    
    keyboard = [[InlineKeyboardButton("ðŸ  Volver al MenÃº Principal", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def main() -> None:
    logger.info("Iniciando el bot")
    from config import PLEX_SERVERS, GLANCES_SERVERS
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    logger.info("Comenzando el polling")
    updater.start_polling()
    logger.info("Bot iniciado y en ejecuciÃ³n")
    updater.idle()

if __name__ == '__main__':
    main()

