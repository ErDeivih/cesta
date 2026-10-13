# B13 · **Recorrido 1 HECHO**: el lanzador sirve las tres aplicaciones, y la CSP esta probada en vivo

*(13 de octubre de 2026. **La primera ejecucion de B13, y con la decision del propietario cumplida: automatico y sin que nadie toque nada.**)*

## 0. Como se hizo, y por que asi

```
*** DECISION DEL PROPIETARIO (ronda 217): *** *** «que se haga de forma automatica sin que tenga que hacer yo nada» ***
   -> *Chromium *** en modo OCULTO *** (`headless: true`), *lanzado por el proveedor, *con **perfil temporal propio.** *

   `capture_browser_scenario` · Chrome 155.0.8059.40 · 11,0 s · *** 18 eventos de red, y NINGUNO fallo ***
```

> *** Y **el resultado es «parcial» por una sola razon, y hay que decirla**: *** *** `cleanup_incomplete` -- «Browser
> scenario cleanup could not be confirmed: timed out after 1000ms» ***. *
>
> *** O sea: **la observacion se recogio entera** (los 18 eventos, el DOM, la accesibilidad), *y **lo que no se pudo
> confirmar fue la limpieza del navegador** -- *y **el proveedor lo dice en `limitations`**: *«Scenario observations
> are partial because browser cleanup could not be confirmed.» *
>
> *** Y **NO se declara completo por eso**: *se declara **el recorrido, si**; *y **la limpieza, como lo que es.** *

## 1. Lo que se observo, literal

```
URL:      *** http://127.0.0.1:8080/ ***  -> *y la respuesta del documento es *** HTTP 200 ***
TITULO:   *** «Cesta» ***
H1:       *** «Cesta» ***
Y debajo: *** «La compra de casa, las recetas y lo que comes. *** TRES APLICACIONES, UNA CASA. ***» ***

NAVEGACION *** aria-label="Aplicaciones" *** -- y son TRES, con su descripcion:
  *** «Compra» ***    -> */compra*   -> *** «Buscar, la lista, favoritos y lo que gastas.» ***
  *** «Recetas» ***   -> */recetas*  -> *** «Tu recetario, el modo cocina y el plan de la semana.» ***
  *** «Calorias» ***  -> */calorias* -> *** «Tu diario, tus alimentos y las tendencias.» ***

FOOTER:   «Cuenta y preferencias» -> */ajustes*
```

> *** Y las tres cosas que B13 queria comprobar estan aqui: ***
> 1. *** el lanzador sirve *** -- *y **no una pantalla vacia**: *hay **un H1, un parrafo, tres enlaces con
>    descripcion y un footer.** *
> 2. *** y la navegacion separa las TRES aplicaciones *** -- *que es **`SUPERAPP-01`**: *«tres aplicaciones», *y
>    *el texto lo dice: **«Tres aplicaciones, una casa.»** *
> 3. *** y estan **conectadas por el lanzador**, no **fundidas**. *

## 2. Y la **CSP esta probada en vivo**, con el comentario del propio HTML

```html
<!-- *** Nada de scripts ni estilos en linea: la CSP que pone Caddy es
     script-src 'self' y style-src 'self', asi que un <script> incrustado no
     se ejecutaria. *** Vite saca el JS y el CSS a /assets, que si entran. -->
<script type="module" crossorigin="" src="/assets/index-CmoznUpO.js"></script>
<link rel="stylesheet" crossorigin="" href="/assets/index-12pVBXnq.css">
```

> *** Y **la cabecera que `test_nada_en_linea_porque_el_csp_de_caddy_lo_prohibe` prueba, vista en la respuesta real**: ***
> *el evento **2** de la red lista, entre las cabeceras del documento: *** `content-security-policy` ***, junto a
> `referrer-policy`, `x-content-type-options` y `x-frame-options`. *
>
> *** O sea: **la undecima forma de imposibilidad -- la impuesta por un servidor -- esta AHI**, *en **una cabecera de
> la respuesta**, *y **el HTML se explica a si mismo por que no lleva nada en linea.** *
>
> *** Y **es la primera vez en esta sesion que una de las once formas se ve **en la respuesta del servidor**, *y no
> en un fichero del repositorio.* *

## 3. Y la red: **18 eventos, todos 200, y uno de ellos dice que hay sesion**

```
documento  GET /                 -> *** 200 ***   (+ content-security-policy)
script     GET /assets/index-CmoznUpO.js      -> *** 200 ***
stylesheet GET /assets/index-12pVBXnq.css     -> *** 200 ***
script     GET /assets/Cocina-DLvtzNJw.js     -> *** 200 ***   *-- modulo precargado*
script     GET /assets/formato-_ZiAiV6x.js    -> *** 200 ***   *-- modulo precargado*
*** fetch  GET /api/yo ***        -> *** 200 ***   *-- y este es el que importa*
```

> *** Y `/api/yo` es **la app preguntando quien eres** *** -- *y **responde 200**, *o sea: **hay sesion de ensayo, y
> el lanzador la usa.** *
>
> *** Y **las peticiones salen con `referer` y `origin` de `http://127.0.0.1:8080`** *** -- *que es **el mismo
> origen**, *y **eso es lo que `test_fase2_f04_csrf.py` prueba con `SameSite=Lax`**: *una peticion **del mismo sitio**
> **si lleva la cookie.** *
>
> *** O sea: **el recorrido 1 **confirma en vivo** la mitad del contrato de CSRF** *que B14 leyo en los ensayos. *

## 4. Y lo que queda de B13, con su estado

```
RECORRIDO 1 · *** el lanzador y las tres raices ***   -> *** HECHO *** (18 eventos, DOM, accesibilidad)
   y **NO es «una pantalla vacia»**: *H1 + parrafo + tres enlaces con descripcion + footer*
   y **las tres aplicaciones estan separadas por navegacion** -- *que es `SUPERAPP-01`*

RECORRIDO 2 · *** /compra ***   (buscar, la lista, favoritos, lo que gastas)   -> *por hacer*
RECORRIDO 3 · *** /recetas ***  (recetario, modo cocina, plan de la semana)     -> *por hacer*
RECORRIDO 4 · *** /calorias *** (diario, alimentos, tendencias)                 -> *por hacer*
RECORRIDO 5 · *** la restriccion del propietario ***: *traspasar una receta desde la web*
              *** y mirar las lineas de esa lista ***                            -> *por hacer*

*** Y LOS CINCO SE PUEDEN HACER IGUAL: *** *navegador oculto, y **sin que nadie toque nada** -- *que es la decision
del propietario, **y ya esta probado que funciona.** *
```

> *** Y **una nota de metodo, que importa para los otros cuatro**: *** *el proveedor **timeouteo en la limpieza**
> (1000 ms), *y **la observacion salio entera.** *Asi que **el timeout no invalida los datos** -- *pero **se declara
> cada vez**, porque **«parcial» es lo que es.** *
