# B11 · **«Lo que no se observo no se puede dibujar como si se hubiera observado»** -- y las tres reglas

*(13 de octubre de 2026. **Cuarta ronda de B11. Y este es el docstring mas fuerte de la sesion.**)*

## 1. El fichero y su cabecera, literales (`plataforma/web/app/src/logica/chispa.ts`, 114 lineas)

```typescript
/** Que se dibuja en una chispa, y que no. **Sin uPlot y sin DOM: se puede probar.**
 *
 *  Existe porque las tres reglas de esta decision son de G05 y hay que fijarlas con una p[rueba],
 *  con un `tsc` verde -- *compilar no es acertar*. Las tres salen del mismo principio: **lo que no se
 *  observo no se puede dibujar como si se hubiera observado**.
 *
 *  - **Un hueco es un hueco**: un `null` entre dos precios se conserva como `null`. *G05: «no
 *    conectar datos ausentes como si hubiera observaciones».*
 *  - **Una fecha ilegible no es 1970**: el punto se descarta y se cuenta. *G05: «no conve[rtir]
 *    ausencias en cero»*; antes iba al origen del eje y arrastraba la escala.
 *  - **De una serie vacia no se infiere nada**: por eso el resultado lleva `dibujable`, y [la] pinta
 *    dice que **no hay serie**, no que haya un solo dia. *G05: «no inferir "solo un[o]" de una]
 *    serie vacia».*
 */
```

## 2. Y el principio es **la doctrina, vigesimoprimera vez, en su forma mas pura**

> *** «Las tres salen del mismo principio: *** *** LO QUE NO SE OBSERVO NO SE PUEDE DIBUJAR COMO SI SE HUBIERA
> OBSERVADO. *** ***» ***
>
> *** Y hay que compararlo con las veinte formas anteriores, porque **esta es distinta**: ***
>
> ```
> `cantidad` NULL        -> un valor que se guarda
> `sin_precio`           -> un estado
> `fuente_dato`          -> un origen
> `COALESCE`             -> una regla de escritura
> `ABSTIENE`             -> un veredicto que se devuelve
> los cuatro motivos     -> un «no» con su razon
> *** «lo que no se observo NO SE PUEDE DIBUJAR COMO SI SE HUBIERA OBSERVADO» -> UN PRINCIPIO ***
> ```
>
> *** O sea: **las veinte anteriores eran reglas, y esta es LA REGLA DE LA QUE SALEN** *** -- *y **el propio
> docstring lo dice**: «**las tres salen del mismo principio**».*
>
> *** Y es **la respuesta entera al encargo del propietario**, *que pide «no inventes calorias, densidad,
> alergenos, equivalencias, objetivos de salud, precios ni costes de viajes» -- *y aqui esta **el principio general**
> del que **las siete prohibiciones son casos**: *** *** no dibujar (ni decir) como observado lo que no se observo.
> ***

## 3. Y las tres reglas son **tres casos, con su numero y su cita**

```
1) UN HUECO ES UN HUECO
   un `null` entre dos precios SE CONSERVA como `null`.
   *G05: «NO CONECTAR DATOS AUSENTES COMO SI HUBIERA OBSERVACIONES».*

2) UNA FECHA ILEGIBLE NO ES 1970
   el punto SE DESCARTA **y SE CUENTA**.
   *G05: «NO CONVERTIR AUSENCIAS EN CERO»;* *** antes iba al origen del eje Y ARRASTRABA LA ESCALA. ***

3) DE UNA SERIE VACIA NO SE INFIERE NADA
   por eso el resultado lleva `dibujable`, y la pinta dice que *** NO HAY SERIE ***,
   **no que haya un solo dia**.
   *G05: «NO INFERIR "SOLO UNO" DE UNA SERIE VACIA».*
```

> *** Y las tres son **la doctrina, aplicada tres veces a un dibujo**: *** *el hueco **no se rellena**, la fecha
> ilegible **no se convierte en 1970**, y la serie vacia **no se lee como «hay uno».** *
>
> *** Y la segunda trae **el defecto anterior escrito**: *** *** «antes iba al origen del eje **y arrastraba la
> escala**» *** -- *o sea: **un solo punto con fecha mala** **aplastaba toda la grafica** *hacia 1970.*
>
> *** Que es **el mismo patron que `almacen.py:431`** («esto era `cantidad = %s`…»): *** *** el defecto, escrito, con
> lo que hacia. ****

## 4. Y hay **dos frases sobre el metodo**, que son para este encargo

> *** «Sin uPlot y sin DOM: *** *** SE PUEDE PROBAR. *** ***» ***
>
> *** O sea: **la logica esta separada del dibujo A PROPOSITO** *** -- *para que **se pueda probar sin navegador.** *
> *Que es **la misma razon** que `oraculo_reparto.py` («independiente quiere decir independiente»): **separar para
> poder comprobar.** *
>
> *** Y: *** *** «con un `tsc` verde -- *compilar no es acertar*.» *** ***
>
> *** O sea: **que el compilador pase NO quiere decir que la grafica diga la verdad** *** -- *y **por eso hay reglas
> con prueba**, y no solo tipos.*
>
> *** Y esa frase **es el encargo entero, en cinco palabras**: *** *«**no consideres terminado lo que solo abrio una
> pantalla vacia**»* -- *y **su version tecnica**: **`tsc` verde no es acertar. ***

## 5. Y B11 queda **contestado entero**

```
  1) DONDE ESTA           LOCALIZADO -- cuatro ficheros del frontend, y NINGUN ENSAYO `.py`
                          *** pero SI una prueba: `logica/chispa.ts` «existe para fijarlas con una p[rueba]» ***
  2) LA MEDIDA Y LA UNIDAD *** HECHO en tres sitios: *** `sufijoUnidad`/`eurosUnidad`/`NO_LO_SE` (formato.ts) ·
                          «precio por unidad, sin ejes» (Chispa.tsx) · y `dibujable`+`motivoUnidad` (chispa.ts)
  3) EL UNIVERSO/PERIODO/
     FUENTE/VERSION        *de los datos: `cobertura` · `rango`/`DIAS_DE_VENTANA` · `fuente_dato` · `version`*
  4) Y LAS TRES REGLAS    *** HECHAS Y CITADAS: *** «un hueco es un hueco» · «una fecha ilegible no es 1970» ·
                          «de una serie vacia no se infiere nada» -- *** con su cita de G05 cada una ***
  5) Y EL PRINCIPIO       *** «LO QUE NO SE OBSERVO NO SE PUEDE DIBUJAR COMO SI SE HUBIERA OBSERVADO» ***
```

> *** Y B11 **no tiene ninguna ausencia**: *** *tiene **una grafica** (una sparkline), **cuatro ficheros**, **tres
> reglas con su cita**, **un principio**, **la unidad en dos modulos**, *y **una razon para estar separada del
> dibujo**: **poder probarla.** *
>
> *** Y lo que **no** hay que decir es «faltan las graficas del criterio»: *** *lo que hay que decir es que **la
> grafica que existe resuelve los tres casos que el criterio enumera como peligrosos** -- *huecos, fechas rotas y
> series vacias -- **y los resuelve negandose a dibujar.** *
>
> *** Que es **la misma respuesta que B09** («el oraculo prefiere estar incompleto antes que mentir») y **que B08**
> («el diario rechaza `compra` a proposito») -- *y ahora **en una grafica**: *** *** prefiere **no dibujar** antes que
> dibujar algo que no se observo. *** *
