# Hallazgo 2 del plan · **el grano**: la eleccion es por cadena, y la pregunta fina no existe

*`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:53-56`: *** «`api/cesta.py` excluye Lidl globalmente porque
su catalogo es parcial. *** Parcial no significa que todos sus precios observados sean invalidos ***.
*La elegibilidad debe decidirse *** por articulo, region, fecha y condiciones ***; *la cobertura de la
cesta se decide *** por separado ***.» ***

---

## 1. *** Lo que hay, leido entero ***

```
*** `plataforma/api/cesta.py:552-565` *** *
   *** `def donde_comprar(peticiones, cadenas=None, max_tiendas=None) -> dict:` *** *
   *** `    """Las dos respuestas: en una tienda, y repartido."""` *** *
   *** `    disponibles = [c for c in (cadenas or CADENAS) if c in CADENAS]` *** *
   *** `    for fuente in disponibles: por_cadena[fuente] = [_resolver(p, fuente, mejor) for p in peticiones]` *** *
*** y `l570-571` ***  *** «**`por_cadena` se queda SIN agrupar, y es a proposito.** *Aqui se agrupo para
   `una_tienda` -- *** que es una tienda entera ***--*, *pero el reparto no puede usar esas partes» *** *
```

## 2. *** Y entonces **no es un defecto**: es **otra pregunta** ***

```
*** LO QUE `donde_comprar` RESPONDE ***: *«**¿que tienda me cubre la cesta?**»* *
   *-- *y **lo hace bien**: *para cada cadena, *resuelve **todas** las peticiones *
   *-- *y **su comentario lo dice**: *«**que es una tienda entera**» ✓
   *-- *y **Lidl no puede** cubrir una cesta entera, *y **por eso no esta en `CADENAS`** ✓
*** LO QUE EL PLAN PIDE ***: *«la elegibilidad *** por articulo, region, fecha y condiciones ***»* *
   *-- *o sea: *«**¿este precio concreto vale?**»* *
*** Y ESA PREGUNTA *** *** NO ESTA ESCRITA EN NINGUN SITIO *** ⚠️ *
   *-- *ni en `donde_comprar`, *ni en `_resolver`, *ni en el reparto *
   *-- *lo que hay es **«esta cadena si o no»**, *que es **el grano grueso** *
```

## 3. *** Y las piezas para escribirla **ya estan** ***

```
*** `region` EN EL CATALOGO ***  *-- *medido: *los 79 productos de Lidl llevan *** `region = '28'` *** ✓
*** `fecha` EN EL HISTORICO ***  *-- *y **la frescura ya se juzga en otro sitio** *(-- `juzgaPrecio`,
   `diasDesde`, *en `src/logica/frescura.ts`, *con sus ensayos --)* ✓
*** Y `por_que_no_se_compara` ***  *-- *para **decirlo en la pantalla** *(-- *y **hoy da el motivo de
   la CADENA**, *no el del articulo --)* ✓
*** y `CADENAS_QUE_SE_CAPTURAN` (seis) frente a `CADENAS` (cinco) ***  *-- *la distincion **ya esta
   hecha**, *con **el motivo escrito en los tres sitios** *(-- `cesta.py`, `auditar_escurrido.py`,
   `peticiones.py` --)* ✓
```

## 4. *** Y por que no lo abro yo ahora ***

```
*** ES UN CAMBIO DE GRANO, NO UN ARREGLO *** *
   *-- *`donde_comprar` **esta bien**: *cambiarlo **rompe el reparto entero**, *
      *que es **la funcion que decide que tienda gana** *
   *-- *lo que hace falta es **una pregunta nueva al lado**, *no **bajar el grano de la que hay** ⚠️
*** Y LA PREGUNTA TIENE TRES DECISIONES DENTRO ***: *
   *** 1) ¿Un precio de Lidl **compite** con los de las otras cinco, *o **solo se ensena**? *** *
      *-- *y **la respuesta cambia el reparto**, *no solo la pantalla*
   *** 2) ¿Que se hace **cuando Lidl no tiene el articulo**: *se calla, *o se dice «no lo cataloga»? *** *
      *-- *y **el plan pide las dos cosas**: *«sin presentar ausencias de captura como
      indisponibilidad» *y *«ni darle una cesta completa no cubierta»*
   *** 3) ¿Y la cobertura de la cesta, *como se declara? ***  *-- *el plan dice **«por separado»**,
      *y **eso hay que disenarlo**, *no improvisarlo*
*** -> **ninguna de las tres es una linea**, *y **elegir mal** *(-- *darle a Lidl una cesta que no
   cubre --)* *es **exactamente lo que el encargo prohibe* ⚠️
```

## 5. Y el estado del hallazgo, entonces

```
*** `donde_comprar` ***  *** correcto para lo que hace *** ✓
*** LA EXCLUSION GLOBAL ***  *** quitada el 13/10 *** ✓✓ *(-- *la puerta admite las seis --)*
*** `por_que_no_se_compara` ***  *** existe y se dice en la pantalla *** ✓
*** Y LA PREGUNTA FINA ***, *por articulo, region y fecha: *** NO ESTA *** ⚠️ *
   *-- *y **no es un defecto**: *es **trabajo de diseno**, *con **tres decisiones dentro** *
   *-- *y **las piezas para hacerlo ya estan**: *`region`, *`fecha`, *`frescura`, *
      *y **la distincion de las dos listas** ✓
```
