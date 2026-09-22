# ¿Relanzar la captura de hoy? Si, y sale barato

Escrito el 18 de septiembre de 2026, cuando Alcampo y Carrefour se quedaron con
los precios del dia anterior.

---

## 1. Por que sale barato: la cache del dia

`load_raw_bytes` guarda cada respuesta bajo `data/raw/fuente=X/fecha=HOY/` y la
reutiliza **dentro del mismo dia**. O sea que relanzar no repite el trabajo: solo
pide lo que falta.

| cadena | pedido hoy | lo que pediria al relanzar |
|---|---:|---|
| carrefour | 1.012 paginas | solo las **373 categorias que dieron 403**; las 1.012 salen del disco |
| alcampo | 366 respuestas | las que el arreglo del recorrido haga bajar, y **Frescos** |

Y hay un efecto de rebote que importa: al pedir mucho menos, **es mucho menos
probable volver a activar el bloqueo de Cloudflare**, que es justo lo que paso
esta manana al arrancar en frio con 653 categorias.

## 2. Por que hay que arreglar ANTES de relanzar

Relanzar Alcampo sin el arreglo del recorrido habria repetido el fallo:

- las 366 respuestas de hoy se leen de la cache, **incluida** la del nodo que se
  trago Frescos
- esa respuesta no es un reto del WAF ni un error: es un JSON valido con 0
  productos y sus hijas dentro
- con el codigo de esta manana, ese caso cae en el `else`, no encola nada, y
  Frescos se vuelve a perder **sin pedir nada por la red**

Es el mismo patron que ya mordio el 7 de septiembre con el reto del WAF guardado
como si fuera catalogo. La cache es una buena idea y multiplica cualquier fallo
de interpretacion: lo que se lee mal hoy, se lee mal todas las veces.

Con el arreglo puesto, esa misma respuesta cacheada **ahora si** encola sus hijas,
y esas hijas no estan en la cache, asi que se piden de verdad.

## 3. Como relanzar

```
cd F:\aprendizaje\scrap
.\ejecutar.bat
```

O solo las dos que hacen falta, que es lo suyo:

```
uv run python -m projects.cesta.run --solo alcampo carrefour
```

Tarda, a ojo, entre veinte y cuarenta minutos: Alcampo va a una peticion cada
6,7 segundos a proposito (es la unica palanca que hay contra su WAF) y Carrefour
hace hasta tres vueltas de rescate con esperas de 2, 4 y 6 minutos.

## 4. Que mirar cuando termine

```
=== resumen 2026-09-18 ===
  cadenas: 5 | (sin la linea "SIN REFRESCAR HOY")
```

Y las tres senales nuevas, que antes no existian:

    faltan ramas enteras respecto a la ultima captura buena:   <- si sale, NO se guarda
    N categorias quedaron sin recoger; se espera 120s...       <- el rescate de Carrefour
    rescatadas 341 de 373

Si Alcampo vuelve a salir sin Frescos, **el bronze no se escribe** y se conserva
el del 17. Esa es la diferencia con esta manana: antes se escribia y salia a la
app.

## 5. Si no se relanza

No pasa nada grave. La app sigue funcionando con los precios del 17 para esas dos
cadenas y lo dice en pantalla ("datos del 17 de septiembre"). Los precios de
supermercado se mueven poco de un dia para otro; lo que no se podia consentir era
un catalogo **sin la seccion de frescos**, y eso ya esta resuelto apartando esa
captura.

La ejecucion de esta noche lleva los arreglos, asi que manana se arregla solo.
Relanzar hoy solo sirve para no esperar.
