from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import requests
from google import genai

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
    return json.loads(response.text)

def formatear_diagnostico(diagnostico):
    if not diagnostico['tiene_plaga']:
        return "Tu cultivo se ve sano, no detecté plagas.\n\nSigue monitoreando cada semana."

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
        f"Confianza del análisis: {diagnostico['confianza']}"
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

            # Normalizar número mexicano
            if telefono.startswith('521'):
                telefono = '52' + telefono[3:]

            print(f"Número normalizado: {telefono}")

            tipo = message['type']

            if tipo == 'text':
                texto = message['text']['body'].lower()

                if 'precio' in texto:
                    enviar_whatsapp(telefono,
                        "*Precios de hoy en Puebla:*\n\n"
                        "🌽 Maíz: $4.50/kg\n"
                        "🫘 Frijol: $18.00/kg\n"
                        "🌶️ Chile poblano: $12.00/kg\n"
                        "🥔 Papa: $6.00/kg\n"
                        "🌿 Nopal: $3.50/kg\n\n"
                        "Manda una foto de tu cultivo para detectar plagas 📸"
                    )
                else:
                    enviar_whatsapp(telefono,
                        "*Bienvenido a AgroScan*\n\n"
                        "Te puedo ayudar con:\n\n"
                        "📸 *Foto* → Detecto plagas en tu cultivo\n"
                        "💰 *Precio* → Precios de mercado hoy\n\n"
                        "¿Qué necesitas?"
                    )

            elif tipo == 'image':
                enviar_whatsapp(telefono, "🔍 Analizando tu cultivo, espera un momento...")

                image_id = message['image']['id']
                image_url = obtener_url_imagen(image_id)
                diagnostico = analizar_imagen_gemini(image_url)
                mensaje = formatear_diagnostico(diagnostico)
                enviar_whatsapp(telefono, mensaje)

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'Error detallado: {e}')

        return JsonResponse({'status': 'ok'})