import logging
import sys
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from plexapi.server import PlexServer
from config import TELEGRAM_BOT_TOKEN, PLEX_SERVERS, GLANCES_SERVERS
import os

# Configuración de logging
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
    """Verifica si el usuario está autorizado para usar el bot."""
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
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error al enviar imagen: {str(e)}")
        return context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )

def edit_message_with_image(update: Update, context: CallbackContext, text: str, reply_markup: InlineKeyboardMarkup) -> None:
    try:
        context.bot.edit_message_caption(
            chat_id=update.effective_chat.id,
            message_id=update.effective_message.message_id,
            caption=text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error al editar mensaje: {str(e)}")
        send_message_with_image(update, context, text, reply_markup)

def start(update: Update, context: CallbackContext) -> None:
    logger.info("Comando /start recibido")
    if not is_authorized(update):
        update.message.reply_text("Lo siento, no estás autorizado para usar este bot.")
        return
    show_main_menu(update, context)

def show_main_menu(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando menú principal")
    if not is_authorized(update):
        return
    keyboard = [
        [InlineKeyboardButton("🖥️ Ver servidores", callback_data='view_servers')],
        [InlineKeyboardButton("🎬 Streams actuales", callback_data='current_streams')],
        [InlineKeyboardButton("🔄 Usuarios transcodificando", callback_data='transcoding_users')],
        [InlineKeyboardButton("ℹ️ Obtener Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = ('¡Bienvenido a Dual Plex Control! 🎉\n'
                   '¿Listo para dominar tus servidores? 😎\n'
                   '¿Qué tareas quieres realizar hoy?')
    
    edit_message_with_image(update, context, welcome_text, reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    logger.info("Botón presionado")
    if not is_authorized(update):
        update.callback_query.answer("No estás autorizado para usar este bot, ponte en contacto con @SinCracK")
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
        keyboard = [[InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        edit_message_with_image(update, context, error_message, reply_markup)

def show_servers(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando servidores")
    if not is_authorized(update):
        return
    keyboard = [[InlineKeyboardButton(f"🏙️ Servidor {server['name']}", callback_data=f"server_{i}")] for i, server in enumerate(PLEX_SERVERS)]
    keyboard.append([InlineKeyboardButton("🔙 Volver al Menú Principal", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, "¡Elige tu el servidor a administrar! 👑", reply_markup)

def show_server_options(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando opciones para el servidor: {server['name']}")
    if not is_authorized(update):
        return
    keyboard = [
        [InlineKeyboardButton("🔄 Actualizar bibliotecas", callback_data=f"update_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("👀 Ver reproducciones", callback_data=f"playing_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("📊 Ver estado del servidor", callback_data=f"status_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("📚 Ver bibliotecas del servidor", callback_data=f"stats_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("🔙 Volver a Servidores", callback_data="view_servers")],
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, f"¿Qué magia quieres hacer en {server['name']}? ✨", reply_markup)

def update_libraries(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Actualizando bibliotecas en el servidor: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        for section in plex.library.sections():
            section.update()
        success_message = f"¡Boom! 💥 Bibliotecas actualizadas en {server['name']}. ¡Tu contenido está más fresco que nunca! 🌟"
        keyboard = [
            [InlineKeyboardButton("🔙 Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
            [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        edit_message_with_image(update, context, success_message, reply_markup)
    except Exception as e:
        logger.error(f"Error al actualizar bibliotecas: {str(e)}")
        error_message = f"Error al actualizar bibliotecas en {server['name']}: {str(e)}"
        keyboard = [[InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]]
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
            message = f"🎬 ¡Acción en {server['name']}! Esto es lo que está pasando:\n\n"
            for session in sessions:
                message += f"👤 Usuario: {session.usernames[0]}\n"
                message += f"🎥 Título: {session.title}\n"
                if session.type == 'movie':
                    session_type = 'Película'
                elif session.type == 'episode':
                    session_type = 'Episodio'
                else:
                    session_type = session.type.capitalize()
                message += f"📺 Tipo: {session_type}\n"
                message += f"⏳ Progreso: {session.viewOffset // 60000} minutos\n\n"
        else:
            message = f"😴 Parece que {server['name']} está ocioso. ¡No hay reproducciones en curso!"
    except Exception as e:
        logger.error(f"Error al obtener reproducciones: {str(e)}")
        message = f"Error al obtener reproducciones de {server['name']}: {str(e)}"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_current_streams(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando streams actuales")
    if not is_authorized(update):
        return
    
    total_users = 0
    total_transcoding = 0
    message = "🎬 Reproducciones actuales en los servidores:\n\n"
    
    for server in PLEX_SERVERS:
        try:
            plex = PlexServer(server['url'], server['token'])
            sessions = plex.sessions()
            
            server_users = len(sessions)
            server_transcoding = 0
            total_users += server_users
            
            message += f"Servidor {server['name']} ({server_users} usuarios activos):\n"
            if sessions:
                for session in sessions:
                    message += f"👤 Usuario: {session.usernames[0]}\n"
                    message += f"🎥 Título: {session.title}\n"
                    if session.type == 'movie':
                        session_type = 'Película'
                    elif session.type == 'episode':
                        session_type = 'Episodio'
                    else:
                        session_type = session.type.capitalize()
                    message += f"📺 Tipo: {session_type}\n"
                    message += f"⏳ Progreso: {session.viewOffset // 60000} minutos\n"
                    
                    # Verificar si se está realizando transcodificación
                    if session.transcodeSessions:
                        message += "🔄 Transcodificando: Sí\n"
                        server_transcoding += 1
                    else:
                        message += "🔄 Transcodificando: No\n"
                    
                    message += "\n"
                
                total_transcoding += server_transcoding
            else:
                message += "No hay reproducciones activas.\n\n"
        except Exception as e:
            logger.error(f"Error al conectar con {server['name']}: {str(e)}")
            message += f"Error al conectar con {server['name']}: {str(e)}\n\n"
    
    message = (f"Total de usuarios activos: {total_users}\n"
               f"Usuarios realizando transcodificación: {total_transcoding}\n\n") + message
    
    keyboard = [[InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]]
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
            
            return f"Uso de CPU: {cpu_usage:.1f}%\nUso de RAM: {mem_usage:.1f}%\nIP Pública: {public_ip}\nIP Privada: {private_ip}\nTiempo de actividad: {uptime}"
        else:
            return f"Error al obtener datos. Códigos de estado - CPU: {cpu_response.status_code}, RAM: {mem_response.status_code}, IP: {ip_response.status_code}, Uptime: {uptime_response.status_code}"
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
        status = "🟢 En línea"
        
        message = f"📊 Estado del servidor {server['name']}:\n\n"
        message += f"Estado: {status}\n"
        message += f"Versión: {plex.version}\n"
        message += f"Plataforma: {plex.platform}\n"
        message += f"Identificador: {plex.machineIdentifier}\n\n"
        
        if hasattr(plex, 'myPlexAccount'):
            account = plex.myPlexAccount()
            if account:
                message += f"Nombre de la cuenta: {account.username}\n"
                message += f"Email de la cuenta: {account.email}\n"
        if hasattr(plex, 'friendlyName'):
            message += f"Nombre amigable: {plex.friendlyName}\n"
        
        # Obtener información de Glances
        glances_server = next((s for s in GLANCES_SERVERS if s['name'].lower() == server['name'].lower()), None)
        if glances_server:
            glances_data = get_glances_data(glances_server['url'])
            if not glances_data.startswith("Error"):
                cpu_usage, ram_usage, public_ip, private_ip, uptime = glances_data.split('\n')
                message += f"\n💻 {cpu_usage}\n"
                message += f"🧠 {ram_usage}\n"
                message += f"🌐 {public_ip}\n"
                message += f"🏠 {private_ip}\n"
                message += f"⏱️ {uptime}\n"
            else:
                message += f"\n⚠️ {glances_data}\n"
        else:
            message += f"\n⚠️ No se encontró configuración de Glances para el servidor {server['name']}\n"

        sessions = plex.sessions()
        active_streams = len(sessions)
        message += f"\nStreams activos: {active_streams}\n"
        
        libraries = plex.library.sections()
        library_info = "\nBibliotecas:\n"
        for lib in libraries:
            library_info += f"- {lib.title}\n"
        message += library_info

    except Exception as e:
        logger.error(f"Error al obtener el estado del servidor: {str(e)}")
        status = "🔴 Fuera de línea"
        message = f"📊 Estado del servidor {server['name']}:\n\n"
        message += f"Estado: {status}\n"
        message += f"Error: No se pudo conectar al servidor o obtener información. Detalles: {str(e)}\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_library_stats(update: Update, context: CallbackContext, server: dict) -> None:
    logger.info(f"Mostrando estadísticas de la biblioteca: {server['name']}")
    if not is_authorized(update):
        return
    try:
        plex = PlexServer(server['url'], server['token'])
        message = f"📚 Bibliotecas de {server['name']}:\n\n"
        
        for section in plex.library.sections():
            message += f"📁 {section.title}:\n"
            if section.type == 'movie':
                section_type = 'Película'
            elif section.type == 'show':
                section_type = 'Serie'
            else:
                section_type = section.type.capitalize()
            message += f"   - Tipo: {section_type}\n"
            message += f"   - Total de elementos: {section.totalSize}\n\n"
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de la biblioteca: {str(e)}")
        message = f"Error al obtener estadísticas de la biblioteca {server['name']}: {str(e)}"
    
    keyboard = [
        [InlineKeyboardButton("🔙 Volver a Opciones del Servidor", callback_data=f"server_{PLEX_SERVERS.index(server)}")],
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, message, reply_markup)

def show_help(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando ayuda")
    if not is_authorized(update):
        return
    help_text = (
        "🦸‍♂️ ¡Bienvenido al Centro de Ayuda del Bot de Control Plex! 🦸‍♀️\n\n"
        "Aquí tienes una guía rápida de lo que puedo hacer:\n\n"
        "🖥️ Ver servidores: Te muestra una lista de tus servidores Plex.\n"
        "🔄 Actualizar bibliotecas: Actualiza todas las bibliotecas en un servidor específico.\n"
        "👀 Ver reproducciones: Muestra qué se está reproduciendo actualmente en un servidor.\n"
        "📊 Estado del servidor: Muestra información sobre el estado y la versión del servidor.\n"
        "📚 Ver bibliotecas del servidor: Muestra las bibliotecas del servidor.\n"
        "🎬 Streams actuales: Muestra todos los streams activos en tus servidores Plex.\n"
        "🔄 Usuarios transcodificando: Muestra los usuarios que están realizando transcodificación.\n\n"
        "¡No dudes en contacter conmigo si necesitas ayuda @SinCracK ! 🎉"
    )
    keyboard = [[InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    edit_message_with_image(update, context, help_text, reply_markup)

def show_transcoding_users(update: Update, context: CallbackContext) -> None:
    logger.info("Mostrando usuarios transcodificando")
    if not is_authorized(update):
        return
    
    message = "🔄 Usuarios haciendo transcode:\n\n"
    total_transcoding_video = 0
    total_transcoding_audio = 0
    
    for server in PLEX_SERVERS:
        try:
            plex = PlexServer(server['url'], server['token'])
            sessions = plex.sessions()
            
            server_transcoding_video = 0
            server_transcoding_audio = 0
            server_message = f"Servidor {server['name']}:\n"
            
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
                    
                    server_message += f"👤 Usuario: {session.usernames[0]}\n"
                    server_message += f"🎥 Título: {session.title}\n"
                    if session.type == 'movie':
                        session_type = 'Película'
                    elif session.type == 'episode':
                        session_type = 'Episodio'
                    else:
                        session_type = session.type.capitalize()
                    server_message += f"📺 Tipo: {session_type}\n"
                    server_message += f"⏳ Progreso: {session.viewOffset // 60000} minutos\n"
                    
                    if transcode_type:
                        server_message += f"🔄 Transcodificando: {' y '.join(transcode_type)}\n"
                    else:
                        server_message += "🔄 Transcodificando: Desconocido\n"
                    
                    server_message += "\n"
            
            if server_transcoding_video > 0 or server_transcoding_audio > 0:
                message += server_message
                total_transcoding_video += server_transcoding_video
                total_transcoding_audio += server_transcoding_audio
            else:
                message += f"Servidor {server['name']}: No hay usuarios transcodificando.\n\n"
        
        except Exception as e:
            logger.error(f"Error al conectar con {server['name']}: {str(e)}")
            message += f"Error al conectar con {server['name']}: {str(e)}\n\n"
    
    if total_transcoding_video == 0 and total_transcoding_audio == 0:
        message = "😴 No hay usuarios realizando transcodificación en este momento."
    else:
        message = (f"Transcodificando Video: {total_transcoding_video} usuarios\n"
                   f"Transcodificando Audio: {total_transcoding_audio} usuarios\n\n") + message
    
    keyboard = [[InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="main_menu")]]
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
    logger.info("Bot iniciado y en ejecución")
    updater.idle()

if __name__ == '__main__':
    main()

