"""A09, parte del navegador — **las tres anchuras, los dos temas y el zoom al 200 %**, medidos.

**Lo que pide A09**, de su criterio:

> «390/768/1440 px, tema claro/oscuro y zoom 200%; **controles, textos y errores reales, no solo conteo de
> pixeles**. Guardar capturas y resultados con commit/imagen/version.»

**Y lo que se midio el 12 de octubre de 2026, contra la web del Docker en `localhost:8080`:**

```
ancho / tema / zoom  |  desborda  |  letra minima
    390 light   100%  |  False     |  12
    390 light   200%  |  True      |  12   <-- DESBORDA
    390 dark    100%  |  False     |  12
    390 dark    200%  |  True      |  12   <-- DESBORDA
    768 light   100%  |  False     |  12
    768 light   200%  |  False     |  12
    768 dark    100%  |  False     |  12
    768 dark    200%  |  False     |  12
   1440 light   100%  |  False     |  12
   1440 light   200%  |  False     |  12
   1440 dark    100%  |  False     |  12
   1440 dark    200%  |  False     |  12
```

**Doce combinaciones, y **una sola** desborda**: *el movil, con el zoom al doble.* **Y desborda en los dos
temas**, asi que no es del tema: *es del ancho.*

**Por que esto es un hallazgo y no un detalle.** *El zoom al 200 % no es un capricho*: **es el nivel que
la WCAG 1.4.4 exige que se pueda alcanzar sin perder contenido ni funcionalidad** -- *y «desborda» aqui
significa que aparece una barra horizontal y hay que arrastrar para leer una linea*, *que es exactamente
lo que ese criterio prohibe.*

**Y a 390 px sin zoom no desborda**, *asi que no es que la pantalla este mal hecha en movil: es que **al
doblarla** algo no encoge.*

=== LO QUE ESTA PRUEBA NO HACE, Y SE DICE ===

**No es una prueba automatica.** *Es un ensayo que se corre a mano y cuyo resultado se lee*, porque mide
una propiedad del **navegador** -- `scrollWidth` contra `clientWidth` -- que no esta en el codigo.
*Convertirlo en prueba exigiria levantar la web en cada corrida de `pytest`, y **eso no se ha hecho**.*

*Y la segunda mitad del criterio* -- **«controles, textos y errores reales, no solo conteo de pixeles»** --
**tampoco esta hecha**: *aqui se cuentan pixeles, que es justo lo que el criterio dice que no basta.*
*Queda dicho como el limite que es.*

=== Y EL 404 QUE APARECIO AL MIRARLO, que vale tanto como lo anterior ===

*Antes de medir anchuras se comprobo la API de esa web:*

```
http://localhost:8080/api/estado              ->  200   y vigencia_precio.coherente = false
http://localhost:8080/api/estado/publicacion  ->  404   <-- LA RUTA NUEVA NO ESTA
```

**La ruta `/api/estado/publicacion`, que se anadio en A01, NO existe en la imagen de API del Docker.**
*No es una sospecha: es un `404`.* **Y es la confirmacion empirica de lo que la revision del 12 de octubre
decia con estas palabras**: *«las correcciones del backend probadas en el arbol local; **no se reconstruyo
la imagen de API**».*

*Lo que si llega es `/api/estado`, con `coherente: false`* -- *o sea que la imagen vieja **si tiene** el
detector de incoherencia, porque es anterior a las huellas pero posterior a esa comprobacion.*
"""


---

## 2. El `404`, resuelto: **la imagen de API ya lleva las correcciones**

*(Ronda 242. **Y la causa estaba en el `Dockerfile`, no en la imagen «vieja».**)*

### Por que faltaba la ruta, y no era «una imagen desactualizada» a secas

**`plataforma/Dockerfile` hace `COPY core/ /app/core/` y `COPY plataforma/ /app/plataforma/`.** *El codigo
va **dentro** de la imagen, no montado.* **Y la imagen `cesta-api` era del `2026-10-08`** -- *cuatro dias
antes de que se anadiera `/api/estado/publicacion`.*

> **Asi que no era un misterio: era un `COPY`.** *Lo unico que se monta es `data/` en `/datos`, en solo
> lectura* -- *que es lo correcto y no tiene nada que ver.*

### Lo que se hizo, y lo que se midio despues

```
docker compose build api   ->  Service api  Built            (exit 0)
docker compose up -d api   ->  Container cesta-api-1 Started (exit 0)
```

**Y la ruta que daba `404` da `200`:**

```
GET /api/estado/publicacion  ->  200
    version: 20261007-103000
    publicado_en: 2026-10-07T10:30:00
    coherente: None          <- «no se sabe»
    no_cuadran: []           <- nada desajustado
GET /api/estado              ->  200
    vigencia_precio.coherente: False,  huellas_en_el_puntero: 0
```

### Y lo que dicen esos numeros, que es lo mismo que decia la prueba local

**Por fechas esta mal, y por contenido no se sabe.** *Las dos cosas son verdad y la pila servida las dice
las dos* -- *que es lo que A01 buscaba: **que la coherencia se pudiera comprobar desde fuera, no solo en
una prueba**.*

*Y conviene fijarse en `no_cuadran: []` con `coherente: None`*: **no es que este bien, es que no se puede
saber** -- *el puntero es anterior a las huellas, y la ruta lo dice con esas dos palabras en vez de
inventarse un veredicto.*

### **Y esto no es un despliegue publico**

*Lo dice el encargo con esas palabras* -- *«no realices despliegues publicos ni gastos nuevos»* --, **y esto
no es ninguna de las dos cosas**: *es reconstruir una imagen **local** del mismo `docker compose` que ya
estaba corriendo, para que sirva el codigo que ya esta en el arbol.* **`cesta-web-1` sigue en `0.0.0.0:8080`
y no se ha abierto nada nuevo** -- *que es un limite que A10 tiene apuntado y que **este cambio no
empeora**.*
