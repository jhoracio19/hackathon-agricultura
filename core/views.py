from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Cosecha, Cultivo, Municipio, ProgramaApoyo

MUNICIPIOS_SIERRA_NORTE = [
    'Cuetzalan del Progreso', 'Cuetzalan', 'Xicotepec de Juárez', 'Xicotepec',
    'Zihuateutla', 'Hueytamalco', 'Tlatlauquitepec', 'Tetela de Ocampo',
    'Jonotla', 'Zapotitlán de Méndez', 'Naupan', 'Honey', 'Jalpan', 'Tlaola',
    'Huauchinango', 'Zacatlán', 'Teziutlán', 'Huitzilan de Serdán',
    'Zongozotla', 'San Felipe Tepatlán', 'Cuautempan'
]

CULTIVOS_CAFE = [
    'Café Arábica', 'Café Garnica', 'Café Typica',
    'Café Bourbon', 'Café Cereza', 'Café Pergamino', 'Café Verde',
    'Cáscara de Café (Cascara Tea)',
    'Pulpa para Abono Orgánico',
    'Miel de Flor de Café',
    'Madera de Cafeto (Ahumado)'
]

ORDENES_VALIDOS = {
    '-fecha': '-fecha',
    'fecha': 'fecha',
    '-precio_propuesto': '-precio_propuesto',
    'precio_propuesto': 'precio_propuesto',
}

def home(request):
    cultivos = Cultivo.objects.filter(nombre__in=CULTIVOS_CAFE)
    municipios = Municipio.objects.filter(nombre__in=MUNICIPIOS_SIERRA_NORTE)
    cosechas = Cosecha.objects.filter(
        disponible=True,
        cultivo__nombre__in=CULTIVOS_CAFE,
        municipio__nombre__in=MUNICIPIOS_SIERRA_NORTE
    ).select_related('agricultor', 'cultivo', 'municipio')

    cultivo_filter = request.GET.get('cultivo')
    municipio_filter = request.GET.get('municipio')
    tipo_filter = request.GET.get('tipo')
    proceso_filter = request.GET.get('proceso')
    orden_filter = request.GET.get('orden', '-fecha')

    if cultivo_filter:
        cosechas = cosechas.filter(cultivo__id=cultivo_filter)
    if municipio_filter:
        cosechas = cosechas.filter(municipio__id=municipio_filter)
    if tipo_filter == 'marca':
        cosechas = cosechas.exclude(agricultor__marca__isnull=True).exclude(agricultor__marca='')
    elif tipo_filter == 'independiente':
        cosechas = cosechas.filter(agricultor__marca__isnull=True) | cosechas.filter(agricultor__marca='')
    if proceso_filter:
        cosechas = cosechas.filter(proceso=proceso_filter)

    orden = ORDENES_VALIDOS.get(orden_filter, '-fecha')
    cosechas = cosechas.order_by(orden)

    return render(request, 'core/home.html', {
        'cosechas': cosechas,
        'cultivos': cultivos,
        'municipios': municipios,
        'tipo_filter': tipo_filter,
        'proceso_filter': proceso_filter,
        'orden_filter': orden_filter,
    })

def detalle_cosecha(request, pk):
    cosecha = get_object_or_404(Cosecha, pk=pk)
    return render(request, 'core/detalle.html', {'cosecha': cosecha})

def dashboard(request):
    total_cosechas = Cosecha.objects.filter(disponible=True).count()
    total_kg = Cosecha.objects.filter(disponible=True).aggregate(Sum('cantidad_kg'))['cantidad_kg__sum'] or 0
    total_productores = Cosecha.objects.filter(disponible=True).values('agricultor').distinct().count()
    cosechas_recientes = Cosecha.objects.filter(disponible=True).select_related('agricultor', 'cultivo', 'municipio').order_by('-fecha')[:5]
    return render(request, 'core/dashboard.html', {
        'total_cosechas': total_cosechas,
        'total_kg': total_kg,
        'total_productores': total_productores,
        'cosechas_recientes': cosechas_recientes,
    })

def eventos(request):
    programas = ProgramaApoyo.objects.filter(vigente=True)
    return render(request, 'core/eventos.html', {'programas': programas})