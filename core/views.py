from django.shortcuts import render, get_object_or_404
from .models import Cosecha, Cultivo, Municipio, Consulta

def home(request):
    cosechas = Cosecha.objects.filter(disponible=True).order_by('-fecha')
    cultivos = Cultivo.objects.all()
    municipios = Municipio.objects.all()

    cultivo_filter = request.GET.get('cultivo')
    municipio_filter = request.GET.get('municipio')

    if cultivo_filter:
        cosechas = cosechas.filter(cultivo__id=cultivo_filter)
    if municipio_filter:
        cosechas = cosechas.filter(municipio__id=municipio_filter)

    return render(request, 'core/home.html', {
        'cosechas': cosechas,
        'cultivos': cultivos,
        'municipios': municipios,
    })

def detalle_cosecha(request, pk):
    cosecha = get_object_or_404(Cosecha, pk=pk)
    return render(request, 'core/detalle.html', {'cosecha': cosecha})

def dashboard(request):
    consultas = Consulta.objects.all().order_by('-fecha')[:50]
    cosechas = Cosecha.objects.filter(disponible=True).count()
    agricultores = Cosecha.objects.values('agricultor').distinct().count()
    return render(request, 'core/dashboard.html', {
        'consultas': consultas,
        'total_cosechas': cosechas,
        'total_agricultores': agricultores,
    })