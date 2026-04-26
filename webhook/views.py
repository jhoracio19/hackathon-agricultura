from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from google import genai
from thefuzz import process
from core.models import Agricultor, Cosecha, Cultivo, Municipio, PrecioMercado, Consulta, EstadoConversacion, ProgramaApoyo

MENU = (
    "👋 ¡Hola! Soy *CampoAmigo*, tu asistente cafetalero de Sierra Norte 🏔️\n\n"
    "¿En qué te puedo ayudar hoy?\n"
    "_(Escribe el número o la palabra)_\n\n"
    "1️⃣ *FOTO* → Detecta plagas en tu cafetal\n\n"
    "2️⃣ *PRECIO* → Precios del café hoy en Sierra Norte\n\n"
    "3️⃣ *VENDER* → Publica tu café sin intermediarios\n\n"
    "4️⃣ *EVENTOS* → Eventos para cafetaleros\n\n"
    "5️⃣ *CLIMA* → Pronóstico y alertas para tu cafetal\n\n"
    "6️⃣ *MIS COSECHAS* → Ver y gestionar tu café publicado\n\n"
    "7️⃣ *PLANEAR* → ¿Cuándo sembrar o cosechar tu café?\n\n"
    "━━━━━━━━━━━━━━━\n"
    "💡 En cualquier momento escribe *MENU* para ver estas opciones"
)

# LISTA ACTUALIZADA: Genética de Puebla y Subproductos
CULTIVOS_CAFE = [
    'Café Arábica', 'Café Garnica', 'Café Typica', 'Café Bourbon',
    'Cáscara de Café (Cascara Tea)', 'Pulpa para Abono Orgánico',
    'Miel de Flor de Café', 'Madera de Cafeto (Ahumado)'
]

MUNICIPIOS_SIERRA_NORTE = 'Cuetzalan, Xicotepec, Hueytamalco, Zacatlán, Huauchinango, Jonotla, Tlatlauquitepec'

# MAPA PARA PROCESOS
MAPA_PROCESOS = {
    '1': 'sin_procesar', 'sin procesar': 'sin_procesar', 'crudo': 'sin_procesar',
    '2': 'lavado', 'lavado': 'lavado',
    '3': 'natural', 'natural': 'natural',
    '4': 'honey', 'honey': 'honey',
    '5': 'anerobic', 'anaerobica': 'anerobic', 'fermentacion': 'anerobic'
}

def buscar_cultivo(texto):
    cultivos = list(Cultivo.objects.all())
    nombres = [c.nombre.lower() for c in cultivos]
    resultado = process.extractOne(texto.lower(), nombres, score_cutoff=60)
    if resultado:
        nombre_encontrado = resultado[0]
        return next((c for c in cultivos if c.nombre.lower() == nombre_encontrado), None)
    return None

def buscar_municipio(texto):
    municipios = list(Municipio.objects.all())
    nombres = [m.nombre.lower() for m in municipios]
    resultado = process.extractOne(texto.lower(), nombres, score_cutoff=60)
    if resultado:
        nombre_encontrado = resultado[0]
        return next((m for m in municipios if m.nombre.lower() == nombre_encontrado), None)
    return None

def enviar_whatsapp(telefono, mensaje):
    url = f'https://graph.facebook.com/v25.0/{settings.PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    body = {
        'messaging_product': 'whatsapp',
        'to': telefono,
        'type': 'text',
        'text': {'body': mensaje}
    }
    respuesta = requests.post(url, headers=headers, json=body)
    print(f"WhatsApp API response: {respuesta.status_code} - {respuesta.text}")

def obtener_url_imagen(image_id):
    url = f'https://graph.facebook.com/v25.0/{image_id}'
    headers = {'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}'}
    response = requests.get(url, headers=headers)
    return response.json().get('url')

def analizar_imagen_gemini(image_url):
    headers = {'Authorization': f'Bearer {settings.WHATSAPP_TOKEN}'}
    response = requests.get(image_url, headers=headers)
    image_data = response.content

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    prompt = """
    Eres un agrónomo experto en café de la Sierra Norte de Puebla, México.

    PASO 1 - VALIDACIÓN: Determina si la imagen muestra una planta de café, hoja de café, grano, fruto (cereza), tallo o cualquier parte de la planta de café u otro cultivo agrícola.

    Si la imagen NO es un cultivo o planta responde exactamente así:
    {
      "es_cultivo": false,
      "tiene_plaga": false,
      "nombre_plaga": null,
      "severidad": "ninguna",
      "recomendacion": "La imagen no parece ser un cultivo. Por favor toma una foto de tu planta de café.",
      "confianza": "alta"
    }

    Si SÍ es un cultivo, analiza con especial atención las siguientes plagas y enfermedades comunes del café en Sierra Norte de Puebla:
    - Roya del café (Hemileia vastatrix) — manchas amarillas en hojas
    - Broca del café (Hypothenemus hampei) — perforaciones en el grano
    - Ojo de gallo (Mycena citricolor) — manchas circulares en hojas
    - Antracnosis — manchas oscuras en frutos
    - Phoma — manchas en hojas jóvenes
    - Nematodos — raíces dañadas

    Responde:
    {
      "es_cultivo": true,
      "tiene_plaga": true o false,
      "nombre_plaga": "nombre de la plaga o null",
      "severidad": "leve/moderada/grave/ninguna",
      "recomendacion": "acción concreta en máximo 2 oraciones, específica para Sierra Norte",
      "confianza": "alta/media/baja"
    }

    Si la imagen es borrosa o lejana, pide foto más cerca a 20-30cm.
    Responde SOLO en formato JSON sin markdown.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            prompt,
            genai.types.Part.from_bytes(
                data=image_data,
                mime_type='image/jpeg'
            )
        ]
    )

    texto = response.text.strip()
    texto = texto.replace('```json', '').replace('```', '').strip()

    if not texto:
        return {
            "es_cultivo": False,
            "tiene_plaga": False,
            "nombre_plaga": None,
            "severidad": "ninguna",
            "recomendacion": "No pude analizar la imagen. Por favor toma la foto más cerca, a 20-30cm de la planta.",
            "confianza": "baja"
        }

    return json.loads(texto)

COORDENADAS_MUNICIPIOS = {
    'cuetzalan del progreso': (20.0167, -97.5167),
    'cuetzalan': (20.0167, -97.5167),
    'xicotepec de juárez': (20.2833, -97.9667),
    'xicotepec': (20.2833, -97.9667),
    'zihuateutla': (20.1500, -97.9000),
    'hueytamalco': (20.0833, -97.6500),
    'tlatlauquitepec': (19.9833, -97.4833),
    'tetela de ocampo': (19.8167, -97.8167),
    'jonotla': (20.0000, -97.5500),
    'zapotitlán de méndez': (20.0333, -97.6833),
    'naupan': (20.2167, -98.0833),
    'honey': (20.2833, -98.0667),
    'jalpan': (20.4833, -98.0833),
    'tlaola': (20.3167, -97.9833),
    'huauchinango': (20.1833, -98.0500),
    'zacatlán': (19.9292, -97.9614),
    'huitzilan de serdán': (20.0333, -97.6167),
    'zongozotla': (19.9833, -97.6833),
    'san felipe tepatlán': (20.1167, -97.8333),
    'cuautempan': (19.9167, -97.7833),
}

def obtener_alerta_clima(municipio_nombre, cultivos_lista):
    try:
        municipio_key = municipio_nombre.lower().strip()
        coords = COORDENADAS_MUNICIPIOS.get(municipio_key)

        if coords:
            params = {
                'lat': coords[0],
                'lon': coords[1],
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es',
                'cnt': 8
            }
        else:
            params = {
                'q': f'{municipio_nombre},Puebla,MX',
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es',
                'cnt': 8
            }

        url = "https://api.openweathermap.org/data/2.5/forecast"
        response = requests.get(url, params=params, timeout=10)
        clima_data = response.json()

        if clima_data.get('cod') != '200':
            params = {
                'q': f'{municipio_nombre},MX',
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es',
                'cnt': 8
            }
            response = requests.get(url, params=params, timeout=10)
            clima_data = response.json()
            if clima_data.get('cod') != '200':
                return None, None

        temps = [item['main']['temp'] for item in clima_data['list']]
        descripciones = [item['weather'][0]['description'] for item in clima_data['list']]
        lluvia = any('rain' in item.get('weather', [{}])[0].get('main', '').lower()
                     for item in clima_data['list'])
        humedad_max = max(item['main']['humidity'] for item in clima_data['list'])

        resumen_clima = (
            f"🌡️ Temperatura: {min(temps):.0f}°C - {max(temps):.0f}°C\n"
            f"☕ Condición: {descripciones[0]}\n"
            f"🌧️ Lluvia próximas 24hrs: {'Sí' if lluvia else 'No'}\n"
            f"💧 Humedad máxima: {humedad_max}%"
        )

        cultivos_str = ', '.join(cultivos_lista) if cultivos_lista else 'café'

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
        Eres un agrónomo experto en café de la Sierra Norte de Puebla, México.
        El cafetalero cultiva: {cultivos_str} en {municipio_nombre}.

        Pronóstico del clima para las próximas 24 horas:
        {resumen_clima}

        Analiza el impacto del clima en CADA cultivo por separado.
        Prioriza alertas específicas del café como:
        - Humedad alta → riesgo de roya
        - Lluvia intensa → riesgo de lavado de suelo en laderas
        - Temperatura baja → riesgo en floración
        - Viento fuerte → caída de frutos

        Usa lenguaje simple, sin tecnicismos, máximo 2 líneas por cultivo.

        Formato:
        ☕ [nombre cultivo]: [favorable/neutral/riesgoso] — [explicación y acción si aplica]
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )

        return resumen_clima, response.text.strip()

    except Exception as e:
        print(f"Error clima detallado: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def obtener_prediccion_siembra(municipio_nombre, cultivo_nombre):
    try:
        municipio_key = municipio_nombre.lower().strip()
        coords = COORDENADAS_MUNICIPIOS.get(municipio_key)

        if coords:
            params = {
                'lat': coords[0],
                'lon': coords[1],
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es',
                'cnt': 40
            }
        else:
            params = {
                'q': f'{municipio_nombre},Puebla,MX',
                'appid': settings.OPENWEATHER_API_KEY,
                'units': 'metric',
                'lang': 'es',
                'cnt': 40
            }

        url = "https://api.openweathermap.org/data/2.5/forecast"
        response = requests.get(url, params=params, timeout=10)
        clima_data = response.json()

        if clima_data.get('cod') != '200':
            return None

        temps = [item['main']['temp'] for item in clima_data['list']]
        humedad = [item['main']['humidity'] for item in clima_data['list']]
        lluvia = sum(1 for item in clima_data['list']
                    if 'rain' in item.get('weather', [{}])[0].get('main', '').lower())

        resumen = (
            f"Temperatura promedio próximos 5 días: {sum(temps)/len(temps):.0f}°C\n"
            f"Temperatura mínima: {min(temps):.0f}°C\n"
            f"Temperatura máxima: {max(temps):.0f}°C\n"
            f"Humedad promedio: {sum(humedad)/len(humedad):.0f}%\n"
            f"Períodos con lluvia: {lluvia} de {len(clima_data['list'])}\n"
            f"Municipio: {municipio_nombre}, Sierra Norte de Puebla"
        )

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
        Eres un agrónomo experto en café de la Sierra Norte de Puebla, México.
        Un cafetalero quiere planear la siembra de {cultivo_nombre} en {municipio_nombre}.

        Datos climáticos actuales y próximos 5 días:
        {resumen}

        Responde breve y claro, máximo 8 líneas, lenguaje simple de campo.
        Sin saludos. Considera que estamos en zona de montaña entre 800-1800 msnm.
        Usa este formato exacto:

        [🟢/🟡/🔴] *¿Sembrar ahora?* [sí/esperar/no] — [razón en 1 línea]

        📅 *Mejores meses:* [mes] ([razón breve]), [mes] ([razón breve])

        ⚠️ *Evitar:* [mes] ([razón breve]), [mes] ([razón breve])

        💡 *Consejo para {municipio_nombre}:* [1 oración específica para café en Sierra Norte]
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )

        return response.text.strip()

    except Exception as e:
        print(f"Error predicción siembra: {e}")
        import traceback
        traceback.print_exc()
        return None

def formatear_diagnostico(diagnostico):
    if not diagnostico.get('es_cultivo', True):
        return (
            "🚫 *La imagen no es un cultivo*\n\n"
            "Para analizar plagas necesito una foto de:\n"
            "🌿 Hojas de tu planta de café\n"
            "🌱 Tallo o rama\n"
            "☕ Granos o frutos (cerezas) de cerca\n\n"
            "Toma la foto a 20-30cm de distancia 📸\n\n"
            "━━━━━━━━━━━━━━━\n"
            "✏️ Escribe *MENU* para volver al inicio"
        )

    if not diagnostico['tiene_plaga']:
        return (
            "✅ *Tu cafetal se ve sano*, no detecté plagas.\n\n"
            "Sigue monitoreando cada semana, especialmente en época de lluvias.\n\n"
            "━━━━━━━━━━━━━━━\n"
            "✏️ Escribe *MENU* para volver al inicio"
        )

    severidad_emoji = {
        'leve': '⚠️',
        'moderada': '🟠',
        'grave': '🔴'
    }
    emoji = severidad_emoji.get(diagnostico['severidad'], '⚠️')

    return (
        f"{emoji} *Plaga detectada: {diagnostico['nombre_plaga']}*\n"
        f"Severidad: {diagnostico['severidad']}\n\n"
        f"📋 *Recomendación:*\n{diagnostico['recomendacion']}\n\n"
        f"Confianza del análisis: {diagnostico['confianza']}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✏️ Escribe *MENU* para volver al inicio"
    )

def responder_precio(telefono):
    # ACTULIZACIÓN DE PRECIOS SIERRA NORTE Y SUBPRODUCTOS
    msg = (
        "☕ *Precios de Mercado hoy (Sierra Norte):*\n\n"
        "*Café Tradicional:*\n"
        "• Arábica (Cereza): $12-15/kg\n"
        "• Arábica (Pergamino): $38-45/kg\n"
        "• Arábica (Verde/Oro): $60-80/kg\n\n"
        "*Café de Especialidad (Verde):*\n"
        "• Typica / Bourbon: $80-100/kg\n"
        "• Garnica: $70-90/kg\n\n"
        "♻️ *Subproductos (Economía Circular):*\n"
        "• Cáscara (Té): $100-150/kg\n"
        "• Miel de Flor de Café: $250-300/kg\n"
        "• Madera de Cafeto: $40-60/kg\n"
        "• Abono de Pulpa: $10-20/kg\n\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* Los procesos Honey y Natural suben hasta 40% el valor de tu café.\n\n"
        "📸 Mándame foto de tu cafetal para detectar plagas\n\n"
        "✏️ Escribe *MENU* para volver al inicio"
    )
    Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
    enviar_whatsapp(telefono, msg)

def responder_apoyos(telefono):
    programas = ProgramaApoyo.objects.filter(vigente=True)
    msg = (
        "🎪 *Eventos y ferias del café en Puebla:*\n\n"
        "📅 *Próximos eventos:*\n\n"
    )
    for i, p in enumerate(programas, 1):
        contacto_corto = p.contacto.split('.')[0]
        msg += (
            f"{i}. *{p.nombre}*\n"
            f"   📍 {contacto_corto}\n\n"
        )
    msg += (
        "━━━━━━━━━━━━━━━\n"
        "📋 Para ver detalles escribe:\n"
        "*evento 1*, *evento 2*...\n\n"
        "✏️ Escribe *MENU* para volver al inicio"
    )
    Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
    enviar_whatsapp(telefono, msg)

def responder_detalle_apoyo(telefono, numero):
    try:
        programas = list(ProgramaApoyo.objects.filter(vigente=True))
        idx = int(numero) - 1
        if 0 <= idx < len(programas):
            p = programas[idx]
            msg = (
                f"🎪 *{p.nombre}*\n\n"
                f"📋 *¿Qué es?*\n{p.descripcion}\n\n"
                f"💰 *¿Qué te dan?*\n{p.beneficio}\n\n"
                f"📝 *¿Qué necesitas?*\n{p.requisitos}\n\n"
                f"📞 *¿Cuándo y dónde?*\n{p.contacto}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✏️ Escribe *EVENTOS* para ver todos\n"
                f"✏️ Escribe *MENU* para volver al inicio"
            )
        else:
            msg = (
                "No encontré ese evento 🤔\n\n"
                "Escribe *EVENTOS* para ver la lista completa\n\n"
                "✏️ Escribe *MENU* para volver al inicio"
            )
        Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
        enviar_whatsapp(telefono, msg)
    except Exception as e:
        print(f"Error detalle evento: {e}")
        enviar_whatsapp(telefono,
            "Ocurrió un error 😔\n\n"
            "Escribe *EVENTOS* para ver la lista\n\n"
            "✏️ Escribe *MENU* para volver al inicio"
        )

def responder_mis_cosechas(telefono, agricultor):
    cosechas = Cosecha.objects.filter(agricultor=agricultor, disponible=True).order_by('-fecha')
    if not cosechas:
        enviar_whatsapp(telefono,
            "☕ No tienes café publicado aún.\n\n"
            "Escribe *VENDER* para publicar tu café\n\n"
            "✏️ Escribe *MENU* para volver al inicio"
        )
        return

    msg = "☕ *Tu café publicado:*\n\n"
    for i, c in enumerate(cosechas, 1):
        msg += (
            f"{i}. *{c.cultivo.nombre}*\n"
            f"   📦 {c.cantidad_kg} kg\n"
            f"   💰 ${c.precio_propuesto}/kg\n"
            f"   📍 {c.municipio.nombre if c.municipio else 'Sin municipio'}\n\n"
        )
    msg += (
        "━━━━━━━━━━━━━━━\n"
        "¿Qué quieres hacer?\n\n"
        "✏️ *editar 1* → Cambiar precio o cantidad\n"
        "💰 *vendido 1* → Registrar venta (total o parcial)\n\n"
        "✏️ Escribe *MENU* para volver al inicio"
    )
    enviar_whatsapp(telefono, msg)

def responder_clima(telefono, agricultor, municipio_override=None):

    # Si viene con municipio específico (ej: "clima Cuetzalan")
    if municipio_override:
        cultivos_en_municipio = list(
            Cosecha.objects.filter(agricultor=agricultor, disponible=True, municipio=municipio_override)
            .values_list('cultivo__nombre', flat=True)
            .distinct()
        )
        if not cultivos_en_municipio:
            cultivos_en_municipio = ['Café Arábica']

        enviar_whatsapp(telefono, "🌤️ Consultando el clima para tu cafetal...")
        resumen, alerta = obtener_alerta_clima(municipio_override.nombre, cultivos_en_municipio)

        if resumen:
            cultivos_str = ', '.join(cultivos_en_municipio)
            msg = (
                f"🌤️ *Clima en {municipio_override.nombre} — próximas 24hrs:*\n\n"
                f"{resumen}\n\n"
                f"☕ *Impacto en tu café:*\n"
                f"_({cultivos_str})_\n\n"
                f"{alerta}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"✏️ Escribe *MENU* para volver al inicio"
            )
        else:
            msg = (
                "No pude obtener el clima en este momento 😔\n"
                "Intenta: *clima Cuetzalan*\n\n"
                "✏️ Escribe *MENU* para volver al inicio"
            )
        Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
        enviar_whatsapp(telefono, msg)
        return

    # Sin municipio específico — agrupa por municipio
    cosechas = Cosecha.objects.filter(
        agricultor=agricultor,
        disponible=True
    ).select_related('cultivo', 'municipio')

    if not cosechas:
        if agricultor.municipio:
            cosechas_por_municipio = {
                agricultor.municipio: ['Café Arábica']
            }
        else:
            enviar_whatsapp(telefono,
                "🌤️ Para darte el clima necesito saber tu municipio.\n\n"
                "Escribe: *clima* seguido de tu municipio de Sierra Norte\n"
                "Ejemplo: *clima Cuetzalan* o *clima Xicotepec*\n\n"
                "✏️ Escribe *MENU* para volver al inicio"
            )
            return
    else:
        # Agrupar cultivos por municipio
        cosechas_por_municipio = {}
        for c in cosechas:
            if c.municipio not in cosechas_por_municipio:
                cosechas_por_municipio[c.municipio] = []
            if c.cultivo.nombre not in cosechas_por_municipio[c.municipio]:
                cosechas_por_municipio[c.municipio].append(c.cultivo.nombre)

    enviar_whatsapp(telefono, "🌤️ Consultando el clima para todos tus cafetales...")

    msg_total = ""

    for municipio, cultivos_lista in cosechas_por_municipio.items():
        resumen, alerta = obtener_alerta_clima(municipio.nombre, cultivos_lista)
        cultivos_str = ', '.join(cultivos_lista)

        if resumen:
            msg_total += (
                f"📍 *{municipio.nombre}*\n"
                f"_({cultivos_str})_\n\n"
                f"{resumen}\n\n"
                f"{alerta}\n\n"
                f"━━━━━━━━━━━━━━━\n\n"
            )
        else:
            msg_total += (
                f"📍 *{municipio.nombre}* — No pude obtener el clima 😔\n\n"
                f"━━━━━━━━━━━━━━━\n\n"
            )

    if msg_total:
        msg_final = (
            f"🌤️ *Clima para tus cafetales — próximas 24hrs:*\n\n"
            f"{msg_total}"
            f"✏️ Escribe *MENU* para volver al inicio"
        )
    else:
        msg_final = (
            "No pude obtener el clima en este momento 😔\n"
            "Intenta: *clima Cuetzalan*\n\n"
            "✏️ Escribe *MENU* para volver al inicio"
        )

    Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg_final)
    enviar_whatsapp(telefono, msg_final)

def iniciar_vender(telefono, estado_conv):
    estado_conv.estado = 'esperando_cultivo'
    estado_conv.datos_temp = {}
    estado_conv.save()
    cultivos = ', '.join(CULTIVOS_CAFE)
    enviar_whatsapp(telefono,
        f"☕ *Vamos a publicar tu café o subproducto*\n\n"
        f"¿Qué variedad o producto tienes?\n\n"
        f"Opciones disponibles:\n{cultivos}\n\n"
        f"✏️ Escribe *MENU* para cancelar"
    )

def iniciar_planear(telefono, estado_conv):
    estado_conv.estado = 'esperando_cultivo_planear'
    estado_conv.datos_temp = {}
    estado_conv.save()
    cultivos = ', '.join(CULTIVOS_CAFE)
    enviar_whatsapp(telefono,
        f"🗓️ *Planear mi siembra de café*\n\n"
        f"Te ayudo a saber cuándo y cómo sembrar.\n\n"
        f"¿Qué variedad de café quieres sembrar?\n\n"
        f"Opciones: {cultivos}\n\n"
        f"✏️ Escribe *MENU* para cancelar"
    )

@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse('Token inválido', status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            if 'messages' not in value:
                return JsonResponse({'status': 'ok'})

            message = value['messages'][0]
            message_id = message.get('id', '')
            telefono = message['from']

            if telefono.startswith('521'):
                telefono = '52' + telefono[3:]

            print(f"Número normalizado: {telefono}")

            agricultor, _ = Agricultor.objects.get_or_create(telefono=telefono)
            estado_conv, _ = EstadoConversacion.objects.get_or_create(telefono=telefono)

            if message_id and estado_conv.ultimo_mensaje_id == message_id:
                print(f"Mensaje duplicado ignorado: {message_id}")
                return JsonResponse({'status': 'ok'})

            estado_conv.ultimo_mensaje_id = message_id
            estado_conv.save()

            tipo = message['type']

            if tipo == 'text':
                texto = message['text']['body'].lower().strip()
                print(f"TEXTO RECIBIDO: '{texto}'")

                if 'menu' in texto or texto == '0':
                    estado_conv.estado = 'inicio'
                    estado_conv.datos_temp = {}
                    estado_conv.save()
                    enviar_whatsapp(telefono, MENU)

                elif estado_conv.estado == 'esperando_nombre':
                    nombre = message['text']['body'].strip()
                    agricultor.nombre = nombre
                    agricultor.save()
                    estado_conv.estado = 'inicio'
                    estado_conv.save()
                    enviar_whatsapp(telefono,
                        f"✅ ¡Listo, *{nombre}*! Ya quedaste registrado.\n\n"
                        + MENU
                    )

                # LÓGICA ESTRATÉGICA: Si es subproducto, saltar proceso
                elif estado_conv.estado == 'esperando_cultivo':
                    cultivo = buscar_cultivo(texto)
                    if cultivo:
                        estado_conv.datos_temp = {'cultivo_id': cultivo.id}
                        
                        es_subproducto = any(sub in cultivo.nombre for sub in ['Cáscara', 'Abono', 'Pulpa', 'Miel', 'Madera'])
                        
                        if es_subproducto:
                            estado_conv.datos_temp['proceso'] = 'sin_procesar'
                            estado_conv.estado = 'esperando_cantidad'
                            estado_conv.save()
                            enviar_whatsapp(telefono,
                                f"✅ Producto: *{cultivo.nombre}*\n\n"
                                f"¿Cuántos kilogramos o litros tienes para vender?\n"
                                f"_(Escribe solo el número, ejemplo: 50)_\n\n"
                                f"✏️ Escribe *MENU* para cancelar"
                            )
                        else:
                            estado_conv.estado = 'esperando_proceso'
                            estado_conv.save()
                            enviar_whatsapp(telefono,
                                f"✅ Variedad: *{cultivo.nombre}*\n\n"
                                f"🔄 *¿Qué proceso de transformación tiene tu café?*\n\n"
                                f"Responde con el *número* o la *palabra*:\n"
                                f"1️⃣ Sin procesar (Café en cereza o crudo)\n"
                                f"2️⃣ Lavado\n"
                                f"3️⃣ Natural\n"
                                f"4️⃣ Honey\n"
                                f"5️⃣ Fermentación Anaeróbica\n\n"
                                f"✏️ Escribe *MENU* para cancelar"
                            )
                    else:
                        enviar_whatsapp(telefono,
                            f"No reconocí ese producto ☕\n\n"
                            f"Escribe uno de estos:\n{', '.join(CULTIVOS_CAFE)}\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_proceso':
                    proceso_db = MAPA_PROCESOS.get(texto)
                    if proceso_db:
                        estado_conv.datos_temp['proceso'] = proceso_db
                        estado_conv.estado = 'esperando_cantidad'
                        estado_conv.save()
                        
                        nombres_legibles = {
                            'sin_procesar': 'Sin procesar', 'lavado': 'Lavado',
                            'natural': 'Natural', 'honey': 'Honey', 'anerobic': 'F. Anaeróbica'
                        }
                        
                        enviar_whatsapp(telefono,
                            f"✅ Proceso: *{nombres_legibles[proceso_db]}*\n\n"
                            f"¿Cuántos kilogramos tienes disponibles para vender?\n"
                            f"_(Escribe solo el número, ejemplo: 500)_\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            f"No reconocí ese proceso 🤔\n\n"
                            f"Por favor responde con el *número* (1 al 5) o la *palabra* exacta:\n"
                            f"1. Sin procesar\n2. Lavado\n3. Natural\n4. Honey\n5. Anaeróbica\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_cantidad':
                    try:
                        cantidad = float(texto.replace('kg', '').strip())
                        estado_conv.datos_temp['cantidad'] = cantidad
                        estado_conv.estado = 'esperando_precio'
                        estado_conv.save()

                        cultivo = Cultivo.objects.get(id=estado_conv.datos_temp['cultivo_id'])
                        precio_ref = PrecioMercado.objects.filter(cultivo=cultivo).order_by('-fecha').first()
                        precio_sugerido = precio_ref.precio_kg if precio_ref else 45.00

                        enviar_whatsapp(telefono,
                            f"📦 Cantidad: *{cantidad}*\n\n"
                            f"💰 *¿A qué precio quieres vender?*\n\n"
                            f"📊 Precio de referencia hoy: *${precio_sugerido}/kg o Litro*\n"
                            f"_(Recuerda que los cafés procesados o productos orgánicos valen más)_\n\n"
                            f"Escribe solo el número, ejemplo: *65*\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    except:
                        enviar_whatsapp(telefono,
                            "Por favor escribe solo el número 🙏\n"
                            "Ejemplo: *500*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_precio':
                    try:
                        precio = float(texto.replace('$', '').replace('kg', '').strip())
                        if precio <= 0:
                            raise ValueError
                        estado_conv.datos_temp['precio'] = precio
                        estado_conv.estado = 'esperando_municipio'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            f"💰 Precio: *${precio}/kg o L*\n\n"
                            f"¿En qué municipio de Sierra Norte está tu terreno?\n"
                            f"_(Ejemplos: {MUNICIPIOS_SIERRA_NORTE})_\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    except:
                        enviar_whatsapp(telefono,
                            "Por favor escribe solo el número del precio 🙏\n"
                            "Ejemplo: *65*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_municipio':
                    municipio = buscar_municipio(texto)
                    if municipio:
                        datos = estado_conv.datos_temp
                        cultivo = Cultivo.objects.get(id=datos['cultivo_id'])
                        precio_justo = datos.get('precio', 45.00)
                        proceso_final = datos.get('proceso', 'sin_procesar')

                        Cosecha.objects.create(
                            agricultor=agricultor,
                            cultivo=cultivo,
                            cantidad_kg=datos['cantidad'],
                            precio_propuesto=precio_justo,
                            municipio=municipio,
                            proceso=proceso_final,
                            disponible=True
                        )

                        agricultor.municipio = municipio
                        agricultor.cultivo_principal = cultivo
                        agricultor.save()

                        estado_conv.estado = 'inicio'
                        estado_conv.datos_temp = {}
                        estado_conv.save()
                        
                        nombres_legibles = {
                            'sin_procesar': 'Sin procesar / Natural', 'lavado': 'Lavado',
                            'natural': 'Natural', 'honey': 'Honey', 'anerobic': 'F. Anaeróbica'
                        }

                        enviar_whatsapp(telefono,
                            f"🎉 *¡Tu producto fue publicado con éxito!*\n\n"
                            f"🌿 Producto: {cultivo.nombre}\n"
                            f"🔄 Proceso: {nombres_legibles.get(proceso_final, 'N/A')}\n"
                            f"📦 Cantidad: {datos['cantidad']}\n"
                            f"💰 Tu precio: ${precio_justo}\n"
                            f"📍 Municipio: {municipio.nombre}\n\n"
                            f"Los compradores podrán verlo y te contactarán "
                            f"directo por WhatsApp. ¡Sin intermediarios!\n\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"✏️ Escribe *MIS COSECHAS* para verlo\n"
                            f"✏️ Escribe *MENU* para volver al inicio"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            "No reconocí ese municipio 🤔\n\n"
                            f"Escribe tu municipio de Sierra Norte:\n"
                            f"{MUNICIPIOS_SIERRA_NORTE}...\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_editar_campo':
                    datos = estado_conv.datos_temp
                    if texto in ['precio', '1']:
                        datos['campo'] = 'precio'
                        estado_conv.datos_temp = datos
                        estado_conv.estado = 'esperando_nuevo_valor'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            "💰 ¿Cuál es el nuevo precio?\n"
                            "Ejemplo: *65.00*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )
                    elif texto in ['cantidad', '2']:
                        datos['campo'] = 'cantidad'
                        estado_conv.datos_temp = datos
                        estado_conv.estado = 'esperando_nuevo_valor'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            "📦 ¿Qué cantidad tienes ahora?\n"
                            "Ejemplo: *300*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            "Escribe *precio* o *cantidad* para elegir qué editar\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_nuevo_valor':
                    datos = estado_conv.datos_temp
                    cosecha_id = datos.get('cosecha_id')
                    campo = datos.get('campo')
                    try:
                        valor = float(texto.replace('kg', '').replace('$', '').strip())
                        cosecha = Cosecha.objects.get(id=cosecha_id, agricultor=agricultor)
                        if campo == 'precio':
                            cosecha.precio_propuesto = valor
                            cosecha.save()
                            msg = f"✅ Precio actualizado a *${valor}*\n\n"
                        elif campo == 'cantidad':
                            cosecha.cantidad_kg = valor
                            cosecha.save()
                            msg = f"✅ Cantidad actualizada a *{valor}*\n\n"
                        msg += (
                            f"🌿 *{cosecha.cultivo.nombre}*\n"
                            f"📦 {cosecha.cantidad_kg}\n"
                            f"💰 ${cosecha.precio_propuesto}\n\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"✏️ Escribe *MIS COSECHAS* para ver todas\n"
                            f"✏️ Escribe *MENU* para volver al inicio"
                        )
                        estado_conv.estado = 'inicio'
                        estado_conv.datos_temp = {}
                        estado_conv.save()
                        enviar_whatsapp(telefono, msg)
                    except:
                        enviar_whatsapp(telefono,
                            "Por favor escribe solo el número 🙏\n"
                            "Ejemplo: *65.00*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_kg_vendidos':
                    try:
                        kg_vendidos = float(texto.replace('kg', '').strip())
                        cosecha_id = estado_conv.datos_temp.get('cosecha_id')
                        cosecha = Cosecha.objects.get(id=cosecha_id, agricultor=agricultor)

                        if kg_vendidos >= float(cosecha.cantidad_kg):
                            cosecha.disponible = False
                            cosecha.save()
                            msg = (
                                f"✅ *¡Felicidades, vendiste todo tu producto!* 🎉\n\n"
                                f"🌿 {cosecha.cultivo.nombre} — {cosecha.cantidad_kg} vendidos\n\n"
                                f"Ya no aparece en el marketplace.\n\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"✏️ Escribe *VENDER* para publicar más café\n"
                                f"✏️ Escribe *MENU* para volver al inicio"
                            )
                        else:
                            kg_restantes = float(cosecha.cantidad_kg) - kg_vendidos
                            cosecha.cantidad_kg = kg_restantes
                            cosecha.save()
                            msg = (
                                f"✅ *Venta registrada* 👍\n\n"
                                f"🌿 {cosecha.cultivo.nombre}\n"
                                f"📦 Vendidos: {kg_vendidos}\n"
                                f"📦 Disponibles: {kg_restantes}\n\n"
                                f"Tu producto sigue publicado con las cantidades restantes.\n\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"✏️ Escribe *MIS COSECHAS* para ver tu perfil\n"
                                f"✏️ Escribe *MENU* para volver al inicio"
                            )

                        estado_conv.estado = 'inicio'
                        estado_conv.datos_temp = {}
                        estado_conv.save()
                        enviar_whatsapp(telefono, msg)

                    except:
                        enviar_whatsapp(telefono,
                            "Por favor escribe solo el número 🙏\n"
                            "Ejemplo: *20*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_cultivo_planear':
                    cultivo = buscar_cultivo(texto)
                    if cultivo:
                        estado_conv.datos_temp = {'cultivo_planear': cultivo.nombre}
                        estado_conv.estado = 'esperando_municipio_planear'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            f"✅ Variedad: *{cultivo.nombre}*\n\n"
                            f"¿En qué municipio de Sierra Norte vas a sembrar?\n\n"
                            f"Ejemplos: {MUNICIPIOS_SIERRA_NORTE}\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            f"No reconocí esa variedad ☕\n\n"
                            f"Escribe una de estas:\n{', '.join(CULTIVOS_CAFE)}\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_municipio_planear':
                    municipio = buscar_municipio(texto)
                    cultivo_nombre = estado_conv.datos_temp.get('cultivo_planear', 'café')

                    if municipio:
                        enviar_whatsapp(telefono,
                            f"🔍 Analizando el mejor momento para sembrar "
                            f"*{cultivo_nombre}* en *{municipio.nombre}*...\n\n"
                            f"Dame un momento ⏳"
                        )
                        prediccion = obtener_prediccion_siembra(municipio.nombre, cultivo_nombre)

                        if prediccion:
                            msg = (
                                f"🗓️ *Plan de siembra: {cultivo_nombre} en {municipio.nombre}*\n\n"
                                f"{prediccion}\n\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"✏️ Escribe *PLANEAR* para consultar otra variedad\n"
                                f"✏️ Escribe *MENU* para volver al inicio"
                            )
                        else:
                            msg = (
                                "No pude obtener la predicción en este momento 😔\n"
                                "Intenta de nuevo en unos minutos.\n\n"
                                "✏️ Escribe *MENU* para volver al inicio"
                            )

                        estado_conv.estado = 'inicio'
                        estado_conv.datos_temp = {}
                        estado_conv.save()
                        Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
                        enviar_whatsapp(telefono, msg)
                    else:
                        enviar_whatsapp(telefono,
                            f"No reconocí ese municipio 🤔\n\n"
                            f"Escribe tu municipio de Sierra Norte:\n"
                            f"{MUNICIPIOS_SIERRA_NORTE}...\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )

                elif texto in ['1', 'foto']:
                    enviar_whatsapp(telefono,
                        "📸 *Diagnóstico de plagas en tu cafetal*\n\n"
                        "Toma una foto de cerca de tu planta de café (20-30cm)\n"
                        "enfocando hojas, granos o tallos con síntomas.\n\n"
                        "¡Mándame la foto cuando estés listo! ☕\n\n"
                        "✏️ Escribe *MENU* para volver al inicio"
                    )

                elif texto in ['2', 'precio']:
                    responder_precio(telefono)

                elif texto in ['3', 'vender']:
                    if not agricultor.nombre:
                        estado_conv.estado = 'esperando_nombre'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            "👋 Antes de publicar necesito saber tu nombre.\n\n"
                            "¿Cómo te llamas?\n"
                            "_(Así aparecerás en el marketplace para los compradores)_"
                        )
                    else:
                        iniciar_vender(telefono, estado_conv)

                elif texto in ['4', 'evento', 'eventos', 'apoyo', 'apoyos']:
                    responder_apoyos(telefono)

                elif texto.startswith('evento ') and texto.replace('evento ', '').strip().isdigit():
                    numero = texto.replace('evento ', '').strip()
                    responder_detalle_apoyo(telefono, numero)

                elif texto.startswith('clima '):
                    municipio_texto = texto.replace('clima ', '').strip()
                    municipio = buscar_municipio(municipio_texto)
                    if municipio:
                        responder_clima(telefono, agricultor, municipio_override=municipio)
                    else:
                        enviar_whatsapp(telefono,
                            "No reconocí ese municipio 🤔\n\n"
                            "Escribe: *clima* seguido de tu municipio de Sierra Norte\n"
                            "Ejemplo: *clima Cuetzalan* o *clima Xicotepec*\n\n"
                            "✏️ Escribe *MENU* para volver al inicio"
                        )

                elif texto in ['5', 'clima']:
                    responder_clima(telefono, agricultor)

                elif texto in ['6', 'mis cosechas', 'mis cosecha', 'cosechas', 'mi cafe', 'mi café']:
                    responder_mis_cosechas(telefono, agricultor)

                elif texto in ['7', 'planear', 'planeacion', 'cuando sembrar', 'siembra']:
                    iniciar_planear(telefono, estado_conv)

                elif texto.startswith('vendido ') and texto.replace('vendido ', '').strip().isdigit():
                    numero = int(texto.replace('vendido ', '').strip())
                    cosechas = list(Cosecha.objects.filter(agricultor=agricultor, disponible=True).order_by('-fecha'))
                    idx = numero - 1
                    if 0 <= idx < len(cosechas):
                        cosecha = cosechas[idx]
                        estado_conv.estado = 'esperando_kg_vendidos'
                        estado_conv.datos_temp = {'cosecha_id': cosecha.id}
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            f"🌿 *{cosecha.cultivo.nombre}* — {cosecha.cantidad_kg} disponibles\n\n"
                            f"¿Qué cantidad vendiste?\n\n"
                            f"_(Escribe el número, ejemplo: 20)_\n"
                            f"_(Si vendiste todo escribe: {cosecha.cantidad_kg})_\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            "No encontré ese producto 🤔\n\n"
                            "Escribe *MIS COSECHAS* para ver tu lista\n\n"
                            "✏️ Escribe *MENU* para volver al inicio"
                        )

                elif texto.startswith('editar ') and texto.replace('editar ', '').strip().isdigit():
                    numero = int(texto.replace('editar ', '').strip())
                    cosechas = list(Cosecha.objects.filter(agricultor=agricultor, disponible=True).order_by('-fecha'))
                    idx = numero - 1
                    if 0 <= idx < len(cosechas):
                        cosecha = cosechas[idx]
                        estado_conv.estado = 'esperando_editar_campo'
                        estado_conv.datos_temp = {'cosecha_id': cosecha.id}
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            f"✏️ *Editar: {cosecha.cultivo.nombre}*\n\n"
                            f"📦 Cantidad actual: {cosecha.cantidad_kg}\n"
                            f"💰 Precio actual: ${cosecha.precio_propuesto}\n\n"
                            f"¿Qué quieres cambiar?\n"
                            f"1️⃣ *precio*\n"
                            f"2️⃣ *cantidad*\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            "No encontré ese producto 🤔\n\n"
                            "Escribe *MIS COSECHAS* para ver tu lista\n\n"
                            "✏️ Escribe *MENU* para volver al inicio"
                        )

                else:
                    estado_conv.estado = 'inicio'
                    estado_conv.save()
                    enviar_whatsapp(telefono, MENU)

            elif tipo == 'image':
                enviar_whatsapp(telefono,
                    "🔍 *Analizando tu cafetal...*\n\n"
                    "💡 *Para mejores resultados:*\n"
                    "Toma la foto a 20-30 cm de la planta,\n"
                    "enfocando hojas, granos o tallos con síntomas."
                )
                image_id = message['image']['id']
                image_url = obtener_url_imagen(image_id)
                diagnostico = analizar_imagen_gemini(image_url)
                mensaje = formatear_diagnostico(diagnostico)
                Consulta.objects.create(telefono=telefono, tipo='plaga', respuesta_ia=mensaje)
                enviar_whatsapp(telefono, mensaje)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'Error detallado: {e}')

        return JsonResponse({'status': 'ok'})