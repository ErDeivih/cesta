# B02 · **Octava correccion**: la plantilla **no se copia**, y la cobertura de los dos hay que **diseñarla**

*(13 de octubre de 2026. **Se iba a «reusar la plantilla», y la plantilla no sirve tal cual.**)*

## 1. Lo que hay, medido

```
alcampo.py:1027:   aviso = check_drift(FUENTE, len(filas))     <- y NADA MAS
carrefour.py:                                                   <- NADA
```

> **Ni Alcampo ni Carrefour construyen un `resumen`.** *Lidl **si** lo construye (`lidl.py`, y de ahi salen los
> trece campos).*
>
> *Asi que **no hay «dict que ya se calcula»**: hay que **construirlo**, y eso significa **decidir sus campos**.*

## 2. Y los trece campos de Lidl **no todos aplican**, que es lo que yo habia dado por hecho

```
CAMPO DE LIDL                        ¿TIENE SENTIDO EN ALCAMPO/CARREFOUR?
  fuente                             si
  cobertura                          SI, Y CON OTRO VALOR: «ofertas_semanales_parcial» -> «catalogo_entero»
  url                                si (su catalogo)
  region                             *** NO: ninguno de los dos declara zona ***
  fecha                              si
  fichas_leidas                      *** NO: Lidl lee FICHAS; estos leen CATEGORIAS ***
  productos_padre                    *** dudoso: es concepto de campana ***
  guardados                          si (= len(filas))
  fuera_de_alcance                   SI, Y ALCAMPO YA LO CALCULA: `cobertura.solo_cesta_familiar`
  en_revision                        *** NO se sabe de donde sale en Lidl ***
  con_precio                         *** NO: si cataloga entero, todos traen precio o no se guardan ***
  precios_con_vigencia_comprobada    *** NO: eso es de la campana semanal de Lidl ***
  aviso                              si, y ya hay uno: `check_drift`
```

> **O sea: de trece campos, **seis no aplican** y **dos hay que pensarlos**.** *Y el que mas importa -- `cobertura`
> -- **no cambia de forma, cambia de valor**: «**catalogo_entero**».*
>
> ***Y esto es exactamente lo contrario de lo que yo habia escrito: «la plantilla es `lidl.py:278-285`, y el
> contenido ya se calcula».*** **La plantilla de ESCRITURA sirve. El CONTENIDO no existe.**

## 3. Y es la octava vez, con la misma forma

```
1) «no existe nada»                        -> habia RetoWAF, backoff, runlog, peticiones
2) «hay que construirlo»                   -> era completar
3) «falta la distincion»                   -> estaba en los dos
4) «una linea y nada mas»                  -> tenia backoff exponencial y _por_que_fallan
5) «no se sabe si hay fixtures»            -> la carpeta existia
6) «el tiempo no se mide»                  -> time.monotonic() - t0
7) «y nada mas»                            -> habia log_run y peticiones
8) «la plantilla se copia, el contenido ya se calcula»  -> NO: seis campos no aplican
```

> *Y las ocho son la misma cosa: **afirmar desde lo que se vio, sin haber mirado lo que falta**.*
>
> ***Y las ocho se cazan igual: mirando el sitio concreto al que se va a escribir, ANTES de decir como se
> escribe.*** *En esta ronda solo hubo que **buscar `resumen` en los dos ficheros** -- *y salio que no.*

## 4. Y entonces la cobertura de los dos **es un trabajo de diseño**, no de copia

**Y con el encargo delante, eso significa:**

```
LO QUE HAY QUE DECIDIR, CON EL PROPIETARIO O CON LO MEDIDO:
  - que campos tiene la cobertura de una cadena que CATALOGA ENTERO
  - y en particular: `cobertura` = «catalogo_entero»  (esto si se sabe)
  - que se dice cuando faltan categorias (Carrefour tiene 4 o 5 que fallan SIEMPRE,
    y las da por buenas: lo dice el docstring de log_run)
  - y si `fuera_de_alcance` de Alcampo (`solo_cesta_familiar`) va ahi o en otro sitio

LO QUE NO HAY QUE HACER:
  - rellenar los trece campos de Lidl con ceros o con `None` para que «se parezca»
    *** Eso seria inventar cobertura, que es justo lo que el encargo prohibe. ***
```

> **Y hay una pista que ya esta escrita y que hay que leer antes de decidir**: *el docstring de `log_run` dice que
> **Carrefour tiene siempre cuatro o cinco categorias que fallan** -- «papeleria rota, alguna difunta» -- **y las da
> por buenas porque entran en su tolerancia**.*
>
> ***Eso es exactamente lo que una cobertura tiene que decir***: *«se leyeron N categorias, **M fallaron, y se
> consideran tolerables por esto**».* *Que es **mas informativo que los trece campos de Lidl**, y **no se parece a
> ellos**.*

## 5. Y lo que se deja hecho

**Nada de codigo, y una correccion.** *La plantilla de escritura (`lidl.py:278-285`) **sirve**; **el contenido hay
que diseñarlo**, y **los trece campos de Lidl no se copian**.*

> *Que es mejor saberlo **antes** de escribir seis campos con `None` para que el fichero «se parezca» al de Lidl
> -- *porque eso habria sido **inventar cobertura**, y **el fichero habria dicho que se capturo lo que no se
> miro**.*
