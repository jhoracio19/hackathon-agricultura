from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from google import genai
from core.models import Agricultor, Cosecha, Cultivo, Municipio, PrecioMercado, Consulta, EstadoConversacion

MENU = (
    "👋 ¡Hola! Soy tu asistente agrícola de *CosechaDirecta*\n\n"
    "¿En qué te puedo ayudar hoy?\n\n"
    "1️⃣ *FOTO* → Toma una foto de tu planta y te digo si tiene plaga y cómo curarla\n\n"
    "2️⃣ *PRECIO* → Te digo cuánto vale hoy tu cosecha en el mercado\n\n"
    "3️⃣ *VENDER* → Publica tu cosecha para que compradores te contacten directo, sin intermediarios\n\n"
    "4️⃣ *APOYOS* → Te informo sobre programas del gobierno que te pueden dar dinero o fertilizantes gratis\n\n"
    "5️⃣ *CLIMA* → Te digo el clima de tu municipio y si afecta tu cultivo\n\n"
    "━━━━━━━━━━━━━━━\n"
    "💡 En cualquier momento escribe *MENU* para ver estas opciones"
)

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
    Eres un agrónomo experto en cultivos de Puebla y Tlaxcala, México.
    Analiza esta imagen agrícola.
    Si la imagen es muy lejana o borrosa para hacer un diagnóstico preciso,
    indica tiene_plaga como false y en recomendacion pide que tome la foto más cerca a 20-30cm.
    Responde SOLO en formato JSON sin markdown ni texto adicional:
    {
      "tiene_plaga": true,
      "nombre_plaga": "nombre o null si no hay",
      "severidad": "leve/moderada/grave/ninguna",
      "recomendacion": "acción concreta en máximo 2 oraciones",
      "confianza": "alta/media/baja"
    }
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
            "tiene_plaga": False,
            "nombre_plaga": None,
            "severidad": "ninguna",
            "recomendacion": "No pude analizar la imagen. Por favor toma la foto más cerca, a 20-30cm de la planta.",
            "confianza": "baja"
        }

    return json.loads(texto)

def obtener_alerta_clima(municipio_nombre, cultivo_nombre):
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': f'{municipio_nombre},MX',
            'appid': settings.OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'es',
            'cnt': 8
        }
        response = requests.get(url, params=params, timeout=10)
        clima_data = response.json()
        
        print(f"OpenWeather response: {clima_data}")

        if clima_data.get('cod') != '200':
            return None, None

        temps = [item['main']['temp'] for item in clima_data['list']]
        descripciones = [item['weather'][0]['description'] for item in clima_data['list']]
        lluvia = any('rain' in item.get('weather', [{}])[0].get('main', '').lower()
                     for item in clima_data['list'])
        humedad_max = max(item['main']['humidity'] for item in clima_data['list'])

        resumen_clima = (
            f"🌡️ Temperatura: {min(temps):.0f}°C - {max(temps):.0f}°C\n"
            f"☁️ Condición: {descripciones[0]}\n"
            f"🌧️ Lluvia próximas 24hrs: {'Sí' if lluvia else 'No'}\n"
            f"💧 Humedad máxima: {humedad_max}%"
        )

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
        Eres un agrónomo experto en cultivos de Puebla y Tlaxcala, México.
        El agricultor tiene cultivo de {cultivo_nombre} en {municipio_nombre}.

        Pronóstico del clima para las próximas 24 horas:
        {resumen_clima}

        Dame una alerta agrícola específica para este cultivo con este clima.
        Responde en máximo 3 líneas, en lenguaje simple para un agricultor sin estudios.
        Incluye si hay riesgo de plaga o enfermedad por el clima y qué hacer.
        No uses tecnicismos.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )

        return resumen_clima, response.text.strip()

    except Exception as e:
        print(f"Error clima detallado: {e}")
        import traceback
        return None, None
        traceback.print_exc()

def formatear_diagnostico(diagnostico):
    if not diagnostico['tiene_plaga']:
        return (
            "✅ *Tu cultivo se ve sano*, no detecté plagas.\n\n"
            "Sigue monitoreando cada semana.\n\n"
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
            telefono = message['from']

            if telefono.startswith('521'):
                telefono = '52' + telefono[3:]

            print(f"Número normalizado: {telefono}")

            agricultor, _ = Agricultor.objects.get_or_create(telefono=telefono)
            estado_conv, _ = EstadoConversacion.objects.get_or_create(telefono=telefono)

            tipo = message['type']

            if tipo == 'text':
                texto = message['text']['body'].lower().strip()
                print(f"TEXTO RECIBIDO: '{texto}'")

                if 'menu' in texto or texto == '0':
                    estado_conv.estado = 'inicio'
                    estado_conv.datos_temp = {}
                    estado_conv.save()
                    enviar_whatsapp(telefono, MENU)

                elif estado_conv.estado == 'esperando_cultivo':
                    cultivo = Cultivo.objects.filter(nombre__icontains=texto).first()
                    if cultivo:
                        estado_conv.datos_temp = {'cultivo_id': cultivo.id}
                        estado_conv.estado = 'esperando_cantidad'
                        estado_conv.save()
                        enviar_whatsapp(telefono,
                            f"✅ Cultivo: *{cultivo.nombre}*\n\n"
                            f"¿Cuántos kilogramos tienes disponibles para vender?\n"
                            f"_(Escribe solo el número, ejemplo: 500)_\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    else:
                        cultivos = ', '.join(Cultivo.objects.values_list('nombre', flat=True))
                        enviar_whatsapp(telefono,
                            f"No reconocí ese cultivo 🤔\n\n"
                            f"Escribe uno de estos:\n{cultivos}\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_cantidad':
                    try:
                        cantidad = float(texto.replace('kg', '').strip())
                        estado_conv.datos_temp['cantidad'] = cantidad
                        estado_conv.estado = 'esperando_municipio'
                        estado_conv.save()
                        municipios = ', '.join(Municipio.objects.values_list('nombre', flat=True)[:6])
                        enviar_whatsapp(telefono,
                            f"📦 Cantidad: *{cantidad} kg*\n\n"
                            f"¿En qué municipio está tu cultivo?\n"
                            f"_(Ejemplos: {municipios})_\n\n"
                            f"✏️ Escribe *MENU* para cancelar"
                        )
                    except:
                        enviar_whatsapp(telefono,
                            "Por favor escribe solo el número de kg 🙏\n"
                            "Ejemplo: *500*\n\n"
                            "✏️ Escribe *MENU* para cancelar"
                        )

                elif estado_conv.estado == 'esperando_municipio':
                    municipio = Municipio.objects.filter(nombre__icontains=texto).first()
                    if municipio:
                        datos = estado_conv.datos_temp
                        cultivo = Cultivo.objects.get(id=datos['cultivo_id'])
                        precio = PrecioMercado.objects.filter(cultivo=cultivo).order_by('-fecha').first()
                        precio_justo = precio.precio_kg if precio else 5.00

                        Cosecha.objects.create(
                            agricultor=agricultor,
                            cultivo=cultivo,
                            cantidad_kg=datos['cantidad'],
                            precio_propuesto=precio_justo,
                            municipio=municipio,
                            disponible=True
                        )

                        estado_conv.estado = 'inicio'
                        estado_conv.datos_temp = {}
                        estado_conv.save()

                        enviar_whatsapp(telefono,
                            f"🎉 *¡Tu cosecha fue publicada con éxito!*\n\n"
                            f"🌽 Cultivo: {cultivo.nombre}\n"
                            f"📦 Cantidad: {datos['cantidad']} kg\n"
                            f"💰 Precio justo de hoy: ${precio_justo}/kg\n"
                            f"📍 Municipio: {municipio.nombre}\n\n"
                            f"Los compradores podrán ver tu cosecha y te contactarán directo por WhatsApp. "
                            f"¡Sin intermediarios!\n\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"✏️ Escribe *MENU* para volver al inicio"
                        )
                    else:
                        enviar_whatsapp(telefono,
                            "No reconocí ese municipio\n\n"
                            "Intenta con: Puebla, Atlixco, Tlaxcala, Huamantla...\n\n"
                            "Escribe *MENU* para cancelar"
                        )

                elif 'precio' in texto:
                    cultivos = Cultivo.objects.all()
                    msg = "💰 *Precios de hoy en Puebla:*\n\n"
                    for cultivo in cultivos:
                        precio = PrecioMercado.objects.filter(
                            cultivo=cultivo
                        ).order_by('-fecha').first()
                        if precio:
                            msg += f"• {cultivo.nombre}: ${precio.precio_kg}/kg\n"
                    msg += (
                        "\n📸 ¿Quieres saber si tu cultivo tiene plagas?\n"
                        "Solo mándame una foto de cerca (20-30cm)\n\n"
                        "━━━━━━━━━━━━━━━\n"
                        "✏️ Escribe *MENU* para volver al inicio"
                    )
                    Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
                    enviar_whatsapp(telefono, msg)

                elif 'vender' in texto:
                    estado_conv.estado = 'esperando_cultivo'
                    estado_conv.datos_temp = {}
                    estado_conv.save()
                    cultivos = ', '.join(Cultivo.objects.values_list('nombre', flat=True))
                    enviar_whatsapp(telefono,
                        f"🌱 *Vamos a publicar tu cosecha*\n\n"
                        f"Primero dime: ¿Qué cultivo tienes?\n\n"
                        f"Opciones disponibles:\n{cultivos}\n\n"
                        f"✏️ Escribe *MENU* para cancelar"
                    )

                elif 'apoyo' in texto or 'apoyos' in texto or 'programa' in texto:
                    msg = (
                        "🏛️ *Programas de apoyo para agricultores:*\n\n"
                        "1️⃣ *PROCAMPO / PROAGRO*\n"
                        "Dinero directo por cada hectárea que cultives\n"
                        "📞 Llama gratis: 800 900 0200\n\n"
                        "2️⃣ *Sembrando Vida*\n"
                        "Te dan $5,000 al mes si eres productor pequeño\n"
                        "Pregunta en tu presidencia municipal\n\n"
                        "3️⃣ *FERTILIZANTES GRATIS*\n"
                        "El Gobierno de Puebla reparte fertilizante\n"
                        "Para maíz y frijol principalmente\n\n"
                        "4️⃣ *CRÉDITO PARA EL CAMPO*\n"
                        "Préstamos con poco interés para comprar herramientas\n"
                        "📞 FIRA: 800 800 3472\n\n"
                        "5️⃣ *SEGURO CONTRA DESASTRES*\n"
                        "Si se pierde tu cosecha por lluvia o helada, te pagan\n"
                        "Sin costo para pequeños productores\n\n"
                        "━━━━━━━━━━━━━━━\n"
                        "✏️ Escribe *MENU* para volver al inicio"
                    )
                    Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
                    enviar_whatsapp(telefono, msg)

                elif texto.startswith('clima '):
                    municipio_texto = texto.replace('clima ', '').strip()
                    municipio = Municipio.objects.filter(nombre__icontains=municipio_texto).first()
                    cultivo = agricultor.cultivo_principal

                    if municipio:
                        enviar_whatsapp(telefono, "🌤️ Consultando el clima para tu cultivo...")
                        resumen, alerta = obtener_alerta_clima(
                            municipio.nombre,
                            cultivo.nombre if cultivo else 'cultivo general'
                        )
                        if resumen:
                            msg = (
                                f"🌤️ *Clima en {municipio.nombre} — próximas 24hrs:*\n\n"
                                f"{resumen}\n\n"
                                f"🌾 *Alerta para tu {'cultivo' if not cultivo else cultivo.nombre}:*\n"
                                f"{alerta}\n\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"✏️ Escribe *MENU* para volver al inicio"
                            )
                        else:
                            msg = (
                                "No pude obtener el clima en este momento 😔\n"
                                "Intenta de nuevo en unos minutos.\n\n"
                                "✏️ Escribe *MENU* para volver al inicio"
                            )
                        Consulta.objects.create(telefono=telefono, tipo='precio', respuesta_ia=msg)
                        enviar_whatsapp(telefono, msg)
                    else:
                        enviar_whatsapp(telefono,
                            "No reconocí ese municipio 🤔\n\n"
                            "Escribe: *clima* seguido de tu municipio\n"
                            "Ejemplo: *clima Atlixco*\n\n"
                            "✏️ Escribe *MENU* para volver al inicio"
                        )

                elif 'clima' in texto:
                    municipio = agricultor.municipio
                    cultivo = agricultor.cultivo_principal

                    if municipio:
                        enviar_whatsapp(telefono, "🌤️ Consultando el clima para tu cultivo...")
                        resumen, alerta = obtener_alerta_clima(
                            municipio.nombre,
                            cultivo.nombre if cultivo else 'cultivo general'
                        )
                        if resumen:
                            msg = (
                                f"🌤️ *Clima en {municipio.nombre} — próximas 24hrs:*\n\n"
                                f"{resumen}\n\n"
                                f"🌾 *Alerta para tu {'cultivo' if not cultivo else cultivo.nombre}:*\n"
                                f"{alerta}\n\n"
                                f"━━━━━━━━━━━━━━━\n"
                                f"✏️ Escribe *MENU* para volver al inicio"
                            )
                        else:
                            msg = (
                                "No pude obtener el clima en este momento 😔\n"
                                "Intenta de nuevo en unos minutos.\n\n"
                                "✏️ Escribe *MENU* para volver al inicio"
                            )
                        enviar_whatsapp(telefono, msg)
                    else:
                        enviar_whatsapp(telefono,
                            "🌤️ Para darte el clima necesito saber tu municipio.\n\n"
                            "Escribe: *clima* seguido de tu municipio\n"
                            "Ejemplo: *clima Atlixco*\n\n"
                            "✏️ Escribe *MENU* para volver al inicio"
                        )

                else:
                    estado_conv.estado = 'inicio'
                    estado_conv.save()
                    enviar_whatsapp(telefono, MENU)

            elif tipo == 'image':
                enviar_whatsapp(telefono,
                    "🔍 *Analizando tu cultivo...*\n\n"
                    "💡 *Para mejores resultados:*\n"
                    "Toma la foto a 20-30 cm de la planta, "
                    "enfocando hojas o tallos con síntomas visibles."
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