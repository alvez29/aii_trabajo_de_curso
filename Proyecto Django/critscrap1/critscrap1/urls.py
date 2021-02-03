"""critscrap URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('extraer/', views.vista_extraer_juegos),
    path('principal/', views.vista_principal),
    path('precarga/', views.vista_precarga),
    path('inicio/', views.vista_inicio),
    path('valoraciones/', views.vista_valoraciones),
    path('busqueda/descripcion', views.vista_busqueda_por_descripcion_titulo),
    path('busqueda/generos', views.vista_busqueda_por_generos),
    path('busqueda/desarrolladora', views.vista_busqueda_por_desarrollador),
    path('busqueda/explorar', views.vista_explorar_valoraciones),
    path('busqueda/explorar/valoraciones/juego', views.vista_buscar_valoracion_juego)

]
