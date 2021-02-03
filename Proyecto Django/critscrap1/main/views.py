# encoding: utf-8
from django.shortcuts import render
from bs4 import BeautifulSoup
import time
import os
import urllib.request
from datetime import datetime
from main.forms import FormularioUnaEntrada
from whoosh import query
from whoosh.fields import DATETIME, TEXT, NUMERIC, Schema
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser, QueryParser
from main.models import Plataforma, Genero, Juego, Desarrolladora, Valoracion
from django.http.response import HttpResponseRedirect, HttpResponse
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required


PLATFORMS_URL = {'ps4':'ps4', 'xbox_one':'xboxone', 'switch':'switch', 'pc':'pc', 'wii_u':'wii-u', '3ds':'3ds', 'ps_vita':'vita', 'ios':'ios', 'stadia':'stadia', 'xbox_sx': 'xbox-series-x', 'ps5': 'ps5' }
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36", 'Accept-Language':'en-ES', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'Referer':'http://www.google.com/'}
#PLATAFORMAS = {'PS4', 'Xbox One', 'Switch', 'PC', 'Wii U', '3DS', 'PS Vita', 'iOS', 'Stadia', 'Xbox SX', 'PS5'}
PLATAFORMAS = {}

# Obtenemos todas las plataformas y generos actuales de la web
def extraer_plataformas_y_generos():
    f = urllib.request.Request(url="https://www.metacritic.com/game", headers=HEADERS)
    page = urllib.request.urlopen(f)
    s = BeautifulSoup(page, 'lxml')
    plataformas = []
    generos = []
    
    for elemento in s.find('ul', class_='platforms current_platforms').find_all('li'):
        plataforma = elemento.find('a').string.strip()
        plataformas.append(plataforma)
    
    plataformas.remove('Legacy')
    print("Se han obtenido " + str(len(plataformas)) + " plataformas.\n")
    
    for elemento in s.find('ul', class_='genre_nav').find_all('li'):
        genero = elemento.find('a').string.strip()
        generos.append(genero.title())
    
    print("Se han obtenido " + str(len(generos)) + " géneros.\n")
    
    return (plataformas, generos)

def popular_BD_plataformas_generos(plataformas, generos):
    Plataforma.objects.all().delete()
    Genero.objects.all().delete()
    
    for plataforma in plataformas:
        p = Plataforma(nombre=plataforma)
        p.save()
    
    for genero in generos:
        g = Genero(nombre=genero)
        g.save()


def extraer_valoraciones_metacritic(auxURLcritica):
    valoraciones = []
    
    url = 'http://www.metacritic.com' + auxURLcritica
    f = urllib.request.Request(url=url, headers=HEADERS)
    page = urllib.request.urlopen(f)
    s1 = BeautifulSoup(page, 'lxml')
    
    #Algunas valoraciones no tienen fecha
    fecha = "Sin datos registrados"
    
    #Primera crítica
    aux = s1.find('ol', class_='reviews critic_reviews').find('li', class_='review critic_review first_review')
    
    if aux.find('div', class_='date'):
        fecha = aux.find('div', class_='date').string.strip()
    usuario = aux.find('div', class_='source').string.strip()
    sitio = 'Metacritic'
    puntuacion = aux.find('div', class_='review_grade').text.strip()
    texto = aux.find('div', class_='review_body').text.strip()
    mi_valoracion = False
    
    valoracion = [fecha, usuario, sitio, puntuacion, texto, mi_valoracion]
    valoraciones.append(valoracion)
         
    #Las demás críticas               
    for critica in s1.find('ol', class_='reviews critic_reviews').find_all('li', class_='review critic_review'):
        valoracion = []
        fecha = "Sin datos registrados"
        if critica.find('div', class_='date'):
            fecha = critica.find('div', class_='date').string.strip()
        usuario = critica.find('div', class_='source').string.strip()
        sitio = 'Metacritic'
        puntuacion = critica.find('div', class_='review_grade').text.strip()
        texto = critica.find('div', class_='review_body').text.strip()
        mi_valoracion = False
        
        valoracion = [fecha, usuario, sitio, puntuacion, texto, mi_valoracion]
        valoraciones.append(valoracion)
        
    return valoraciones

def extraer_juego(tr):
    url = 'http://www.metacritic.com' + tr.find('td', class_='clamp-image-wrap').find('a')['href']
    generos = []
    
    f = urllib.request.Request(url=url, headers=HEADERS)
    page = urllib.request.urlopen(f)
    s = BeautifulSoup(page, 'lxml')
    
    titulo = s.find('div', class_='product_title').find('h1').string.strip()
    url_imagen = s.find('img', class_='product_image large_image')['src']
    
    descripcion = []
    
    if s.find('li', class_='summary_detail product_summary'):
        if s.find('li', class_='summary_detail product_summary').find('span', class_='data'):
            if s.find('li', class_='summary_detail product_summary').find('span', class_='data').find('span',class_='blurb blurb_expanded'):
                descripcion = s.find('li', class_='summary_detail product_summary').find('span', class_='data').find('span',class_='blurb blurb_expanded').text
            else:
                descripcion = s.find('li', class_='summary_detail product_summary').find('span', class_='data').text
                
    puntuacion_critica = s.find('a', class_='metascore_anchor').find('div').find('span').string
    fecha = s.find('li', class_='summary_detail release_data').find('span', class_='data').string
    aux = s.find('li', class_='summary_detail product_genre').find_all('span', class_='data')
    for element in aux:
        generos.append(element.string)
    
    desarrolladora = ""
    
    if s.find('li', class_='summary_detail developer'):
        desarrolladora = s.find('li', class_='summary_detail developer').find('span', class_='data').string.strip()
    else:
        desarrolladora = s.find('div', class_="product_data").find('li', class_='summary_detail publisher').find('span', class_='data').text.strip()
    auxURLcritica = s.find('li', class_='nav nav_critic_reviews').find('a')['href']
    valoraciones = extraer_valoraciones_metacritic(auxURLcritica)
    
    juego = [titulo, url_imagen, descripcion, puntuacion_critica, fecha, generos, desarrolladora,valoraciones]

    return juego


def extraer_juegos_en_pagina(url):
    juegos = []
    contador = 0
    
    f = urllib.request.Request(url=url, headers=HEADERS)
    #time.sleep(3)
    page = urllib.request.urlopen(f)
    s = BeautifulSoup(page, 'lxml')
    
    aux1 = s.find('div', class_='browse_list_wrapper one browse-list-large')
    aux2 = s.find('div', class_='browse_list_wrapper two browse-list-large')
    aux3 = s.find('div', class_='browse_list_wrapper three browse-list-large')
    aux4 = s.find('div', class_='browse_list_wrapper four browse-list-large')
    
    if aux1:
        for tr in aux1.find_all('tr', class_=False):
            juego = extraer_juego(tr)
            #Cargar-----------
            contador += 1
            print(contador)
            #---   --------------
            juegos.append(juego)
            #time.sleep(5)
    if aux2:    
        for tr in aux2.find_all('tr', class_=False):
            juego = extraer_juego(tr)
            #Cargar-----------
            contador += 1
            print(contador)
            #-----------------
            juegos.append(juego)
            #time.sleep(5)
    if aux3: 
        for tr in aux3.find_all('tr', class_=False):
            juego = extraer_juego(tr)
            #Cargar----------
            contador += 1
            print(contador)
            #----------------
            juegos.append(juego)
            #time.sleep(5)
    if aux4:
        for tr in aux4.find_all('tr', class_=False):
            juego = extraer_juego(tr)
            #Cargar----------
            contador += 1
            print(contador)
            #----------------
            juegos.append(juego)
            #time.sleep(5)

    return juegos

def popular_indice_juegos(juegos):
    juegos_directory = 'ixjuegos'
    valoraciones_directory = 'ixvaloraciones'
    
    if not os.path.exists(juegos_directory):
        os.mkdir(juegos_directory)
    if not os.path.exists(valoraciones_directory):
        os.mkdir(valoraciones_directory)
         
    ixjuegos = create_in(juegos_directory, schema=esquema_juego())
    ixvaloraciones = create_in(valoraciones_directory, schema=esquema_valoracion())
    
    writerJuego = ixjuegos.writer()
    writerValoracion = ixvaloraciones.writer()
    
    cont = 1
    for juego in juegos:
        print('Indexando -> '+juego[0])
        nombre = str(juego[0])
        url_imagen = str(juego[1])
        descripcion = str(juego[2])
        puntuacion_critica = int(juego[3])
        fecha = datetime.strptime(juego[4], '%b %d, %Y')
        generos = ', '.join(map(str, juego[5]))
        desarrolladora = str(juego[6])
        valoraciones = juego[7]
        writerJuego.add_document(idJuego=cont,nombre=nombre,url_imagen=url_imagen,descripcion=descripcion,puntuacion_critica=puntuacion_critica, fecha=fecha, generos=generos, desarrolladora=desarrolladora)
        for valoracion in valoraciones:
            if valoracion[0] == 'Sin datos registrados':
                fecha =  datetime.strptime('Jan 12, 1800', '%b %d, %Y')
            else:
                fecha = datetime.strptime(valoracion[0], '%b %d, %Y')
            usuario = str(valoracion[1])
            sitio = str(valoracion[2])
            puntuacion = int(valoracion[3])
            texto = str(valoracion[4])
            mi_valoracion = bool(valoracion[5])
            writerValoracion.add_document(fecha=fecha, usuario=usuario, sitio=sitio, puntuacion=puntuacion, texto=texto, mi_valoracion=mi_valoracion, idJuego=cont)
        cont = cont + 1
    
    writerJuego.commit()
    writerValoracion.commit()    
    
    print('Se han indexado '+ str(cont-1) +' juegos')

def extraer_numero_paginas(url):
    f = urllib.request.Request(url=url, headers=HEADERS)
    page = urllib.request.urlopen(f)
    s = BeautifulSoup(page, 'lxml')
    aux = s.find('li', class_="page last_page").find('a', class_="page_num").string
    return int(aux)
    

def extraer_juegos_metacritic(plataforma):
    platform_url = PLATFORMS_URL.get(str(plataforma))
    lista_juegos = []
    #pages_num = extraer_numero_paginas('https://www.metacritic.com/browse/games/score/metascore/all/' + platform_url + '/filtered')
    
    i = 0
    # Se puede cambiar el numero de páginas del Scrapping hasta el numero de paginas maxima pages_num (linea 252)
    for i in range(0, 1):
        url = 'https://www.metacritic.com/browse/games/score/metascore/all/' + str(platform_url) + '/filtered?page=' + str(i)
        juegos = extraer_juegos_en_pagina(url)
               
        print("Se han extraido " + str(len(juegos)) + " juegos de la página " + str(i))
       
        lista_juegos.extend(juegos)
    
    return lista_juegos

def esquema_juego():
    schema = Schema(idJuego=NUMERIC(stored=True),
                    nombre=TEXT(stored=True),
                    url_imagen=TEXT(stored=True),
                    descripcion=TEXT(stored=True),
                    puntuacion_critica= NUMERIC(stored=True),
                    fecha = DATETIME(stored=True),
                    generos = TEXT(stored=True),
                    desarrolladora = TEXT(stored = True))
    return schema


def esquema_valoracion():
    schema = Schema(fecha=DATETIME(stored=True),
                    usuario=TEXT(stored=True),
                    sitio=TEXT(stored=True),
                    puntuacion = NUMERIC(stored=True),
                    texto = TEXT(stored=True),
                    mi_valoracion = NUMERIC(stored=True),
                    idJuego = NUMERIC(stored=True))
    return schema

def vista_inicio(request): 
    global PLATAFORMAS
    
    if request.method == 'POST':
        plataformas = extraer_plataformas_y_generos()[0]
        PLATAFORMAS = plataformas
        
    return render(request, 'inicio.html', {'plataformas':PLATAFORMAS})

def popular_valoraciones_BD():
    Valoracion.objects.all().delete()
    print('Populando valoraciones en la base de datos...')
    dirr = 'ixvaloraciones'
    lista = []
    ind = open_dir(dirr)
    with ind.searcher() as searcher:
        docs = searcher.documents()
        for document in docs:
            j = Juego.objects.get(idJuego=document['idJuego'])
            v = Valoracion(fecha=document['fecha'], usuario=document['usuario'],sitio=document['sitio'], puntuacion = document['puntuacion'], texto = document['texto'], mi_valoracion = document['mi_valoracion'], juego = j)
            lista.append(v)
    Valoracion.objects.bulk_create(lista)
            

def popular_juegos_BD():
    Juego.objects.all().delete()
    print('Populando juegos en la base de datos...')
    dirr = 'ixjuegos'
    ind = open_dir(dirr)
    with ind.searcher() as searcher:
        document = searcher.documents()
        for fila in document:
            generos = fila['generos'].split(',')
            
            desarrolladoraDOM, creado = Desarrolladora.objects.get_or_create(nombre=fila['desarrolladora'])
            j = Juego(nombre= fila['nombre'], url_imagen = fila['url_imagen'], descripcion =fila['descripcion'], puntuacion_critica=fila['puntuacion_critica'], fecha=fila['fecha'], desarrolladora=desarrolladoraDOM)
           
            j.save()

            for genero in generos:
                g, creado = Genero.objects.get_or_create(nombre=genero.strip())
                j.generos.add(g)
                
            j.save()
     

def popular_base_de_datos():
    popular_juegos_BD()
    popular_valoraciones_BD()

@login_required(login_url='/precarga')
def vista_extraer_juegos(request):
    plataforma = request.GET['plataforma']
    juegos = extraer_juegos_metacritic(plataforma)
    popular_indice_juegos(juegos)
    popular_base_de_datos()
    
    numj = len(Juego.objects.all())
    numv = len(Valoracion.objects.all())
  
    return render(request, 'extraer.html', {'numj' : str(numj), 'numv': str(numv)})

def vista_precarga(request):
    resp = '/extraer?plataforma='+request.GET['plataforma']
    if request.user.is_authenticated:
        return(HttpResponseRedirect(resp))
    formulario = AuthenticationForm()
    if request.method == 'POST':
        formulario = AuthenticationForm(request.POST)
        usuario = request.POST['username']
        clave = request.POST['password']
        acceso = authenticate(username=usuario, password=clave)
        if acceso is not None:
            if acceso.is_active:
                login(request, acceso)
                return (HttpResponseRedirect(resp))
            else:
                #TODO: Mensajes de error
                return (HttpResponse('<html><body>Error: usuario no activo </body></html>'))
        else:
            return (HttpResponse('<html><body><b>Error: usuario o password incorrectos</b><br><a href=/inicio>Volver a la pÃ¡gina principal</a></body></html>'))

    return render(request, 'precargar.html', {'formulario': formulario})

def vista_principal(request):
    juegos = Juego.objects.all().order_by('nombre')
  
    if len(juegos) == 0:
        return render(request, 'principal.html', {'mensaje': True})
    else:
        return render(request, 'principal.html', {'juegos': juegos})
  
def vista_valoraciones(request):
    idJuego = request.GET['idJuego']
    if idJuego:
        valoraciones = Valoracion.objects.filter(juego=idJuego)
        nombreJuego = Juego.objects.filter(idJuego=idJuego).first().nombre
        return render(request, 'valoraciones.html', {'valoraciones': valoraciones, 'nombreJuego':nombreJuego})
    else:
        return render(request, 'valoraciones.html', {'valoraciones': Valoracion.objects.all()})

def vista_busqueda_por_descripcion_titulo(request):
    ix = open_dir("ixjuegos")
    
    formulario = FormularioUnaEntrada()
    res = [] 
    
    if request.method == 'POST':
        entrada = request.POST['entrada']
        
        with ix.searcher() as searcher:
            myquery = MultifieldParser(['nombre','descripcion'], esquema_juego()).parse(entrada)
            results = searcher.search(myquery)
            for r in results:
                generos = r["generos"].split(",")
                res.append({"idJuego":r["idJuego"],"nombre": r['nombre'],"puntuacion_critica": r["puntuacion_critica"],"url_imagen": r['url_imagen'], "descripcion": r["descripcion"], "fecha":r["fecha"], "generos": generos, "desarrolladora": r["desarrolladora"]})
            
    return render(request, 'busqueda_descripcion.html', {"formulario":formulario, "res":res})

def vista_busqueda_por_generos(request):
    ix = open_dir("ixjuegos")
    
    formulario = FormularioUnaEntrada()
    generos_list = Genero.objects.all()
    res = [] 
    
    if request.method == 'POST':
        entrada = request.POST['entrada']
        
        with ix.searcher() as searcher:
            myquery = QueryParser('generos', esquema_juego()).parse(entrada)
            results = searcher.search(myquery)
            for r in results:
                generos = r["generos"].split(",")
                res.append({"idJuego":r["idJuego"],"nombre": r['nombre'],"puntuacion_critica": r["puntuacion_critica"],"url_imagen": r['url_imagen'], "descripcion": r["descripcion"], "fecha":r["fecha"], "generos": generos, "desarrolladora": r["desarrolladora"]})
            
    return render(request, 'busqueda_generos.html', {"formulario":formulario, "generos_list": generos_list,"res":res})

def vista_busqueda_por_desarrollador(request):
    ix = open_dir("ixjuegos")
    
    formulario = FormularioUnaEntrada()
    des_list = Desarrolladora.objects.all()
    res = [] 
    
    if request.method == 'POST':
        entrada = request.POST['entrada']
        
        with ix.searcher() as searcher:
            myquery = QueryParser('desarrolladora', esquema_juego()).parse(entrada)
            results = searcher.search(myquery)
            for r in results:
                generos = r["generos"].split(",")
                res.append({"idJuego":r["idJuego"],"nombre": r['nombre'],"puntuacion_critica": r["puntuacion_critica"],"url_imagen": r['url_imagen'], "descripcion": r["descripcion"], "fecha":r["fecha"], "generos": generos, "desarrolladora": r["desarrolladora"]})
            
    return render(request, 'busqueda_desarrolladora.html', {"formulario":formulario, "des_list": des_list,"res":res})

def vista_explorar_valoraciones(request):
    ix = open_dir("ixvaloraciones")
    
    formulario = FormularioUnaEntrada()
    
    res = []
    
    if request.method == 'POST':
        entrada = request.POST['entrada']
        
        with ix.searcher() as searcher:
            myquery = MultifieldParser(['usuario', 'texto', 'puntuacion'], esquema_valoracion()).parse(entrada)
            results = searcher.search(myquery)
            for r in results:
                juego = Juego.objects.filter(idJuego=r['idJuego'])
                res.append({"fecha": r['fecha'],"usuario": r["usuario"],"sitio": r['sitio'], "puntuacion": r["puntuacion"], "texto":r["texto"], "juego":juego.values_list('nombre')[0][0]})
            
    return render(request, 'explorar_valoraciones.html', {"formulario":formulario,"res":res})

def vista_buscar_valoracion_juego(request):
    ix = open_dir("ixvaloraciones")
    
    formulario = FormularioUnaEntrada()
    idJuego = request.GET['idJuego']
    
    res = []
    
    if request.method == 'POST':
        entrada = request.POST['entrada']
        
        with ix.searcher() as searcher:
            myquery = QueryParser('texto', esquema_valoracion()).parse(entrada)
            
            allow_q = query.Term("idJuego", idJuego)
            
            results = searcher.search(myquery, filter=allow_q)
            for r in results:
                juego = Juego.objects.filter(idJuego=r['idJuego'])
                res.append({"fecha": r['fecha'],"usuario": r["usuario"],"sitio": r['sitio'], "puntuacion": r["puntuacion"], "texto":r["texto"], "juego":juego.values_list('nombre')[0][0]})
            
    return render(request, 'explorar_valoraciones_juego.html', {"formulario":formulario,"res":res})
