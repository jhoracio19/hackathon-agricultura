from django.contrib import admin
from .models import Municipio, Cultivo, PrecioMercado, Agricultor, Cosecha, Consulta, EstadoConversacion, ProgramaApoyo

@admin.register(Municipio)
class MunicipioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'estado']
    search_fields = ['nombre']

@admin.register(Cultivo)
class CultivoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']

@admin.register(PrecioMercado)
class PrecioMercadoAdmin(admin.ModelAdmin):
    list_display = ['cultivo', 'municipio', 'precio_kg', 'fecha']
    list_filter = ['cultivo', 'municipio']

@admin.register(Agricultor)
class AgricultorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'municipio', 'cultivo_principal', 'fecha_registro']
    search_fields = ['nombre', 'telefono']

@admin.register(Cosecha)
class CosechaAdmin(admin.ModelAdmin):
    list_display = ['cultivo', 'agricultor', 'cantidad_kg', 'precio_propuesto', 'disponible', 'fecha']
    list_filter = ['cultivo', 'disponible']

@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['telefono', 'tipo', 'fecha']
    list_filter = ['tipo']

@admin.register(EstadoConversacion)
class EstadoConversacionAdmin(admin.ModelAdmin):
    list_display = ['telefono', 'estado', 'actualizado']

@admin.register(ProgramaApoyo)
class ProgramaApoyoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'beneficio', 'vigente']
    list_filter = ['vigente']