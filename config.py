import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

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

GLANCES_SERVERS = [
    {
        'name': 'Arkham',
        'url': os.getenv('GLANCES_SERVER_1_URL', 'http://192.168.1.100:61208'),
    },
    {
        'name': 'Gotham',
        'url': os.getenv('GLANCES_SERVER_2_URL', 'http://192.168.1.101:61208'),
    }
]

