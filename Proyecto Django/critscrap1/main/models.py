#encoding:utf-8
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Genero(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Género")
    
    def __str__(self):
        return self.nombre
    
class Plataforma(models.Model):
    nombre = models.CharField(max_length=10, verbose_name="Plataforma")
    
    def __str__(self):
        return self.nombre
    
class Desarrolladora(models.Model):
    nombre = models.CharField(max_length=10, verbose_name="Desarrolladora")
    
    def __str__(self):
        return self.nombre

class Juego(models.Model):
    idJuego = models.AutoField(primary_key=True, default=None)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    url_imagen = models.URLField()
    descripcion = models.TextField(verbose_name="Descripción")
    puntuacion_critica = models.PositiveSmallIntegerField()
    fecha = models.DateField(verbose_name='Fecha de salida')
    generos = models.ManyToManyField(Genero)
    desarrolladora = models.ForeignKey(Desarrolladora, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.nombre
   
class Valoracion(models.Model):
    idValoracion = models.AutoField(primary_key=True, default=None)
    fecha = models.DateField(null=True)
    usuario = models.CharField(max_length=100)
    sitio = models.CharField(max_length=100)
    puntuacion = models.IntegerField(models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)]))
    texto = models.TextField()
    mi_valoracion = models.BooleanField()
    juego = models.ForeignKey(Juego, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return str(self.sitio) + '- ('+ str(self.usuario) +' - '+str(self.fecha)+') : ' + str(self.puntuacion)