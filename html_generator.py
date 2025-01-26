import base64
import requests
from datetime import datetime

def get_image_as_base64(url):
    response = requests.get(url)
    if response.status_code == 200:
        return base64.b64encode(response.content).decode('utf-8')
    return None

def generate_streams_html(streams_data):
    # Obtener la imagen como base64
    image_url = "https://sincrack.com/loguito.png"
    image_base64 = get_image_as_base64(image_url)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Streams en los servidores</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.4;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f0f8ff;
            }}
            .header {{
                text-align: center;
                margin-bottom: 20px;
            }}
            .header img {{
                max-width: 200px;
                height: auto;
            }}
            .stats-container {{
                display: flex;
                justify-content: center;
                gap: 20px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            .stat-box {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                min-width: 200px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            .stat-box h3 {{
                margin: 0;
                color: #0056b3;
                font-size: 0.9em;
                text-transform: uppercase;
            }}
            .stat-box p {{
                margin: 10px 0 0 0;
                font-size: 1.5em;
                font-weight: bold;
                color: #003366;
            }}
            .server-stats {{
                display: flex;
                gap: 10px;
                margin-top: 5px;
                font-size: 0.8em;
                justify-content: center;
            }}
            h1 {{
                color: #0056b3;
                text-align: center;
                margin: 10px 0;
            }}
            .server {{
                background-color: #ffffff;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .server h2 {{
                color: #0056b3;
                margin: 0 0 10px 0;
                border-bottom: 2px solid #0056b3;
                padding-bottom: 5px;
            }}
            .stream {{
                background-color: #e6f2ff;
                border: 1px solid #b3d9ff;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }}
            .stream h3 {{
                color: #003366;
                margin: 0 0 5px 0;
            }}
            .stream p {{
                margin: 3px 0;
            }}
            .transcoding-details {{
                margin-top: 20px;
                background-color: #003366;
                color: white;
                padding: 15px;
                border-radius: 5px;
            }}
            .transcoding-stream {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }}
            .transcoding-stream p {{
                margin: 3px 0;
            }}
            .timestamp {{
                text-align: center;
                font-style: italic;
                margin: 10px 0;
                color: #666;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                background-color: #003366;
                color: white;
                border-radius: 5px;
                font-size: 0.9em;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            @media (max-width: 600px) {{
                body {{
                    padding: 10px;
                }}
                .server {{
                    padding: 10px;
                }}
                .stat-box {{
                    min-width: 150px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/png;base64,{image_base64}" alt="SinCracK Cloud Logo">
        </div>
    """

    # Calcular estadísticas por servidor
    total_users = 0
    total_transcoding = 0
    server_stats = {}

    for server_name, server_data in streams_data.items():
        server_users = len(server_data['sessions'])
        server_transcoding = sum(1 for session in server_data['sessions'] if session['transcoding'])
        server_stats[server_name] = {
            'users': server_users,
            'transcoding': server_transcoding
        }
        total_users += server_users
        total_transcoding += server_transcoding

    # Añadir cajas de estadísticas
    html_content += """
        <div class="stats-container">
    """
    
    # Caja de total de streams
    html_content += f"""
            <div class="stat-box">
                <h3>Usuarios</h3>
                <p>{total_users}</p>
                <div class="server-stats">
    """
    for server_name, stats in server_stats.items():
        html_content += f"<span>{server_name}: {stats['users']}</span>"
    html_content += """
                </div>
            </div>
    """

    # Caja de transcodificación
    html_content += f"""
            <div class="stat-box">
                <h3>Transcodes</h3>
                <p>{total_transcoding}</p>
                <div class="server-stats">
    """
    for server_name, stats in server_stats.items():
        html_content += f"<span>{server_name}: {stats['transcoding']}</span>"
    html_content += """
                </div>
            </div>
        </div>
    """

    html_content += """
        <h1>DETALLES</h1>
        <div class="timestamp">Generado el: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</div>
    """

    transcoding_streams = []

    for server_name, server_data in streams_data.items():
        html_content += f"""
        <div class="server">
            <h2>Servidor: {server_name}</h2>
        """

        if server_data['sessions']:
            for session in server_data['sessions']:
                html_content += f"""
                <div class="stream">
                    <h3>{session['title']}</h3>
                    <p><strong>Usuario:</strong> {session['username']}</p>
                    <p><strong>Tipo:</strong> {session['type']}</p>
                    <p><strong>Progreso:</strong> {session['progress']} minutos</p>
                    <p><strong>Reproductor:</strong> {session['player']}</p>
                    <p><strong>Transcodificando:</strong> {'Sí' if session['transcoding'] else 'No'}</p>
                </div>
                """
                if session['transcoding']:
                    transcoding_streams.append({
                        'server': server_name,
                        'session': session
                    })
        else:
            html_content += "<p>No hay reproducciones activas.</p>"

        html_content += "</div>"


    if transcoding_streams:
        html_content += """
        <div class="transcoding-details">
            <h2 style="color: white; margin: 0 0 10px 0;">Usuarios Transcodificando</h2>
        """
        for stream in transcoding_streams:
            html_content += f"""
            <div class="transcoding-stream">
                <h3 style="color: white; margin: 0 0 5px 0;">{stream['session']['title']}</h3>
                <p><strong>Servidor:</strong> {stream['server']}</p>
                <p><strong>Usuario:</strong> {stream['session']['username']}</p>
                <p><strong>Tipo:</strong> {stream['session']['type']}</p>
                <p><strong>Progreso:</strong> {stream['session']['progress']} minutos</p>
                <p><strong>Reproductor:</strong> {stream['session']['player']}</p>
            </div>
            """
        html_content += "</div>"

    # Añadir el pie de página con el mensaje de copyright
    html_content += """
        <div class="footer">
            <p>Desarrollado por SinCracK</p>
            <p>© 2025 SinCracK. Todos los derechos reservados.</p>
        </div>
    </body>
    </html>
    """

    return html_content

