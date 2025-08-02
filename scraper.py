import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json

# Configuración de fuentes
FUENTES = {
    "sevilla_fc": "https://www.sevillafc.es/calendario",
    "lnfs": "https://lnfs.es/calendario/",
    "rfaf": "https://rfaf.es/directos",
    "f1": "https://www.formula1.com/en/racing-calendar.html",
    "motogp": "https://www.motogp.com/en/calendar"
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def limpiar_texto(texto):
    """Elimina espacios extra y caracteres no deseados"""
    return re.sub(r'\s+', ' ', texto).strip() if texto else ""

def obtener_soup(url, headers=None):
    """Obtiene el BeautifulSoup de una URL"""
    headers = headers or {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error al obtener {url}: {e}")
        return None

def extraer_sevilla_fc():
    eventos = []
    soup = obtener_soup(FUENTES['sevilla_fc'])
    if not soup:
        return eventos
    
    # Buscar eventos en la página (ajustar selectores según la estructura real)
    for evento in soup.select('.event-item'):  # Selector a ajustar
        # Extraer fecha, hora, equipos y canal
        fecha_element = evento.select_one('.event-date')  # Ajustar
        if fecha_element:
            fecha_str = limpiar_texto(fecha_element.text)
            try:
                fecha_evento = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            except:
                continue
            
            if fecha_evento == datetime.now().date():
                titulo = limpiar_texto(evento.select_one('.event-title').text)  # Ajustar
                hora_element = evento.select_one('.event-time')  # Ajustar
                hora = limpiar_texto(hora_element.text) if hora_element else "Hora no disponible"
                canal_element = evento.select_one('.event-channel')  # Ajustar
                canal = limpiar_texto(canal_element.text) if canal_element else "Por confirmar"
                
                eventos.append({
                    'deporte': 'Fútbol',
                    'titulo': titulo,
                    'fecha': fecha_evento,
                    'hora': hora,
                    'canal': canal
                })
    return eventos

def extraer_lnfs():
    eventos = []
    soup = obtener_soup(FUENTES['lnfs'])
    if not soup:
        return eventos
    
    # Buscar partidos de hoy en el calendario de la LNFS
    for partido in soup.select('.partido'):  # Selector a ajustar
        fecha_element = partido.select_one('.fecha')  # Ajustar
        if fecha_element:
            fecha_str = limpiar_texto(fecha_element.text)
            try:
                fecha_evento = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            except:
                continue
            
            if fecha_evento == datetime.now().date():
                local = limpiar_texto(partido.select_one('.equipo-local').text)  # Ajustar
                visitante = limpiar_texto(partido.select_one('.equipo-visitante').text)  # Ajustar
                hora = limpiar_texto(partido.select_one('.hora').text) if partido.select_one('.hora') else "Hora no disponible"
                canal = limpiar_texto(partido.select_one('.canal').text) if partido.select_one('.canal') else "Por confirmar"
                
                eventos.append({
                    'deporte': 'Fútbol Sala (LNFS)',
                    'titulo': f"{local} vs {visitante}",
                    'fecha': fecha_evento,
                    'hora': hora,
                    'canal': canal
                })
    return eventos

def extraer_rfaf():
    eventos = []
    soup = obtener_soup(FUENTES['rfaf'])
    if not soup:
        return eventos
    
    # RFAF TV: extraer los directos de hoy
    for directo in soup.select('.directo'):  # Selector a ajustar
        fecha_element = directo.select_one('.fecha')  # Ajustar
        if fecha_element:
            fecha_str = limpiar_texto(fecha_element.text)
            try:
                fecha_evento = datetime.strptime(fecha_str, '%d/%m/%Y').date()
            except:
                continue
            
            if fecha_evento == datetime.now().date():
                titulo = limpiar_texto(directo.select_one('.titulo').text)  # Ajustar
                hora = limpiar_texto(directo.select_one('.hora').text) if directo.select_one('.hora') else "Hora no disponible"
                # En RFAF, el canal es RFAF TV
                eventos.append({
                    'deporte': 'Fútbol Sala (RFAF TV)',
                    'titulo': titulo,
                    'fecha': fecha_evento,
                    'hora': hora,
                    'canal': "RFAF TV"
                })
    return eventos

def extraer_f1():
    eventos = []
    soup = obtener_soup(FUENTES['f1'])
    if not soup:
        return eventos
    
    # Solo eventos del fin de semana (viernes, sábado, domingo)
    hoy = datetime.now().date()
    if hoy.weekday() not in [4,5,6]:  # 4: viernes, 5: sábado, 6: domingo
        return eventos
    
    # Buscar el evento de este fin de semana
    for evento in soup.select('.event-item'):  # Selector a ajustar
        # El evento tiene un rango de fechas. Si hoy está en ese rango, mostramos todas las sesiones
        fecha_inicio_element = evento.select_one('.fecha-inicio')  # Ajustar
        fecha_fin_element = evento.select_one('.fecha-fin')  # Ajustar
        if not fecha_inicio_element or not fecha_fin_element:
            continue
        
        try:
            fecha_inicio = datetime.strptime(limpiar_texto(fecha_inicio_element.text), '%d %b %Y').date()
            fecha_fin = datetime.strptime(limpiar_texto(fecha_fin_element.text), '%d %b %Y').date()
        except:
            continue
        
        if fecha_inicio <= hoy <= fecha_fin:
            # Extraer todas las sesiones del evento (prácticas, clasificación, carrera)
            nombre_gp = limpiar_texto(evento.select_one('.nombre-gp').text)  # Ajustar
            for sesion in evento.select('.sesion'):  # Selector a ajustar
                nombre_sesion = limpiar_texto(sesion.select_one('.nombre-sesion').text)  # Ajustar
                fecha_sesion = hoy  # Pero realmente debería extraer la fecha de la sesión
                hora_sesion = limpiar_texto(sesion.select_one('.hora-sesion').text)  # Ajustar
                canal = limpiar_texto(sesion.select_one('.canal').text) if sesion.select_one('.canal') else "Por confirmar"
                
                eventos.append({
                    'deporte': 'Fórmula 1',
                    'titulo': f"{nombre_gp} - {nombre_sesion}",
                    'fecha': fecha_sesion,
                    'hora': hora_sesion,
                    'canal': canal
                })
    return eventos

def extraer_motogp():
    eventos = []
    soup = obtener_soup(FUENTES['motogp'])
    if not soup:
        return eventos
    
    # Igual que F1: eventos del fin de semana
    hoy = datetime.now().date()
    if hoy.weekday() not in [4,5,6]:
        return eventos
    
    for evento in soup.select('.event-item'):  # Selector a ajustar
        fecha_inicio_element = evento.select_one('.fecha-inicio')  # Ajustar
        fecha_fin_element = evento.select_one('.fecha-fin')  # Ajustar
        if not fecha_inicio_element or not fecha_fin_element:
            continue
        
        try:
            fecha_inicio = datetime.strptime(limpiar_texto(fecha_inicio_element.text), '%d %b %Y').date()
            fecha_fin = datetime.strptime(limpiar_texto(fecha_fin_element.text), '%d %b %Y').date()
        except:
            continue
        
        if fecha_inicio <= hoy <= fecha_fin:
            nombre_gp = limpiar_texto(evento.select_one('.nombre-gp').text)  # Ajustar
            for sesion in evento.select('.sesion'):  # Ajustar
                nombre_sesion = limpiar_texto(sesion.select_one('.nombre-sesion').text)  # Ajustar
                fecha_sesion = hoy  # Debería extraer la fecha específica de la sesión
                hora_sesion = limpiar_texto(sesion.select_one('.hora-sesion').text)  # Ajustar
                canal = limpiar_texto(sesion.select_one('.canal').text) if sesion.select_one('.canal') else "Por confirmar"
                
                eventos.append({
                    'deporte': 'MotoGP',
                    'titulo': f"{nombre_gp} - {nombre_sesion}",
                    'fecha': fecha_sesion,
                    'hora': hora_sesion,
                    'canal': canal
                })
    return eventos

def generar_html(eventos):
    """Genera el archivo HTML con los eventos"""
    # Ordenar eventos por hora (si la hora está disponible)
    eventos_ordenados = sorted(eventos, key=lambda x: x.get('hora', '00:00'))
    
    # Generar HTML para cada evento
    eventos_html = []
    for evento in eventos_ordenados:
        eventos_html.append(f"""
        <div class="evento">
            <div class="deporte">{evento['deporte']}</div>
            <div class="titulo">{evento['titulo']}</div>
            <div>
                <span class="hora">⏱️ {evento['hora']}</span> | 
                <span class="canal">📺 {evento['canal']}</span>
            </div>
        </div>
        """)
    
    if not eventos_html:
        eventos_html.append("""
        <div class="evento">
            <div class="deporte">😴 No hay eventos programados para hoy</div>
            <div>Revisa mañana para nueva información deportiva</div>
        </div>
        """)
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agenda Deportiva Diaria</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px; 
            background-color: #f5f5f5;
        }}
        header {{ 
            background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{ margin: 0; }}
        .fecha {{ font-size: 1.2em; margin-top: 5px; }}
        .evento {{ 
            background-color: white; 
            border-left: 4px solid #1a2a6c; 
            padding: 15px; 
            margin-bottom: 15px; 
            border-radius: 0 8px 8px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .deporte {{ 
            font-weight: bold; 
            color: #1a2a6c; 
            font-size: 1.1em;
            margin-bottom: 5px;
        }}
        .titulo {{
            font-size: 1.05em;
            margin-bottom: 8px;
        }}
        .hora {{ 
            background-color: #e74c3c; 
            color: white; 
            padding: 3px 8px; 
            border-radius: 4px; 
            font-size: 0.9em;
            display: inline-block;
            margin-right: 10px;
        }}
        .canal {{ 
            color: #2980b9; 
            font-weight: bold;
            font-size: 0.95em;
        }}
        .error {{ 
            background-color: #ffecec; 
            border-left: 4px solid #e74c3c; 
            color: #e74c3c;
        }}
        footer {{ 
            text-align: center; 
            margin-top: 30px; 
            color: #7f8c8d; 
            font-size: 0.9em;
        }}
        .actualizacion {{ font-style: italic; }}
    </style>
</head>
<body>
    <header>
        <h1>🗓️ Agenda Deportiva</h1>
        <div class="fecha">{datetime.now().strftime('%A, %d de %B de %Y')}</div>
    </header>
    
    {"".join(eventos_html)}
    
    <footer>
        <p>Actualizado automáticamente todos los días a las 06:00 AM UTC</p>
        <p class="actualizacion">Última actualización: {datetime.now().strftime('%H:%M')}</p>
    </footer>
</body>
</html>"""
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    eventos = []
    
    # Extraer eventos de todas las fuentes
    eventos.extend(extraer_sevilla_fc())
    eventos.extend(extraer_lnfs())
    eventos.extend(extraer_rfaf())
    eventos.extend(extraer_f1())
    eventos.extend(extraer_motogp())
    
    generar_html(eventos)

if __name__ == "__main__":
    main()