from django.db import models

# Create your models here.


class Municipio(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.CharField(max_length=50, default='Puebla')

    def __str__(self):
        return f"{self.nombre}, {self.estado}"

class Cultivo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

class PrecioMercado(models.Model):
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE)
    municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE)
    precio_kg = models.DecimalField(max_digits=8, decimal_places=2)
    fecha = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.cultivo} - {self.municipio} - ${self.precio_kg}/kg"

class Agricultor(models.Model):
    nombre = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=20, unique=True)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True)
    cultivo_principal = models.ForeignKey(Cultivo, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre or self.telefono}"

class Cosecha(models.Model):
    agricultor = models.ForeignKey(Agricultor, on_delete=models.CASCADE)
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE)
    cantidad_kg = models.DecimalField(max_digits=10, decimal_places=2)
    precio_propuesto = models.DecimalField(max_digits=8, decimal_places=2)
    municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True)
    disponible = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cultivo} - {self.cantidad_kg}kg - {self.agricultor}"

class Consulta(models.Model):
    TIPOS = [
        ('plaga', 'Análisis de plaga'),
        ('precio', 'Consulta de precio'),
        ('clima', 'Consulta de clima'),
        ('registro', 'Registro de cosecha'),
    ]
    telefono = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    imagen = models.ImageField(upload_to='consultas/', null=True, blank=True)
    respuesta_ia = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.telefono} - {self.tipo} - {self.fecha}"

class EstadoConversacion(models.Model):
    ESTADOS = [
        ('inicio', 'Inicio'),
        ('esperando_nombre', 'Esperando nombre'),
        ('esperando_cultivo', 'Esperando cultivo'),
        ('esperando_cantidad', 'Esperando cantidad'),
        ('esperando_municipio', 'Esperando municipio'),
        ('esperando_editar_campo', 'Esperando campo a editar'),
        ('esperando_nuevo_valor', 'Esperando nuevo valor'),
        ('esperando_cultivo_planear', 'Esperando cultivo a planear'),
        ('esperando_municipio_planear', 'Esperando municipio para planear'),
        ('esperando_kg_vendidos', 'Esperando kg vendidos'),
        ('esperando_precio', 'Esperando precio'),
    ] 
    telefono = models.CharField(max_length=20, unique=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='inicio')
    datos_temp = models.JSONField(default=dict)
    actualizado = models.DateTimeField(auto_now=True)
    ultimo_mensaje_id = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f"{self.telefono} - {self.estado}"

class ProgramaApoyo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    beneficio = models.TextField()
    requisitos = models.TextField()
    contacto = models.CharField(max_length=200)
    vigente = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre