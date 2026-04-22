from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def webhook(request):
    if request.method == 'GET':
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        if verify_token == 'agroscan2026':
            return HttpResponse(challenge)
        return HttpResponse('Token inválido', status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)  # por ahora solo imprimimos
        return JsonResponse({'status': 'ok'})