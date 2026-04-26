from django.shortcuts import render, get_object_or_404

from .models import Cosecha, Cultivo, Municipio, Consulta, ProgramaApoyo

CULTIVOS_CAFE = [
    'Café Arábica', 'Café Garnica', 'Café Typica',
    'Café Bourbon', 'Café Cereza', 'Café Pergamino', 'Café Verde'
]

MUNICIPIOS_SIERRA_NORTE = [
    'Cuetzalan del Progreso', 'Cuetzalan', 'Xicotepec de Juárez', 'Xicotepec',
    'Zihuateutla', 'Hueytamalco', 'Tlatlauquitepec', 'Tetela de Ocampo',
    'Jonotla', 'Zapotitlán de Méndez', 'Naupan', 'Honey', 'Jalpan', 'Tlaola',
    'Huauchinango', 'Zacatlán', 'Teziutlán', 'Huitzilan de Serdán',
    'Zongozotla', 'San Felipe Tepatlán', 'Cuautempan'
]

def home(request):
    cultivos = Cultivo.objects.filter(nombre__in=CULTIVOS_CAFE)
    municipios = Municipio.objects.filter(nombre__in=MUNICIPIOS_SIERRA_NORTE)
    cosechas = Cosecha.objects.filter(
        disponible=True,
        cultivo__nombre__in=CULTIVOS_CAFE,
        municipio__nombre__in=MUNICIPIOS_SIERRA_NORTE
    ).order_by('-fecha')

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

def eventos(request):
    programas = ProgramaApoyo.objects.filter(vigente=True)
    return render(request, 'core/eventos.html', {'programas': programas})