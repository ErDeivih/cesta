# El cierre de la tanda · **15/10/2026** -- *lo que se midió, *lo que se hizo, *y lo que queda como límite*

*Y **este cierre no es por número de rondas**: *es **por el criterio que el complemento del 14/10 pone** *
*-- sus **cuatro correcciones** *y **B00-B16** --* *y **por las seis puertas.*** *

---

## 1. *** Las seis puertas ***

```
*** `ruff check .` ***        *** All checks passed! *** ✓
*** `pytest -q` ***           *** 2.078 passed · 0 failed · 17 skipped *** ✓✓✓
*** `prueba_e2e` ***          *** == TODO BIEN *** ✓✓✓
*** `npm test` ***            *** 81 pass · 0 fail *** ✓
*** `npx tsc --noEmit` ***    *** limpio *** ✓
*** `npm run build` ***       *** built *** ✓
```

## 2. *** Las cuatro correcciones del complemento, *una por una ***

```
*** 1) «*el fallo del dueno *** SI *** se reproduce» *** *
   *-- *hoy `main.py:1842` escribe *** `uno.envases or 1` *** en *** `cantidad` ***, *
      *y **no solo en la nota** ✓
*** 2) «*el ingrediente sin catalogo *** se queda FUERA ***» *** *
   *-- *la migracion *** `014_la_linea_sin_destino` *** quito la restriccion, *y la linea *
      *** se apunta *** *como «Pendiente de identificar» ✓
*** 3) «*Lidl puede fallar *** sin fila en `runs.csv` ***» *** *
   *-- *hoy tiene *** DOS filas, dos dias seguidos *** *
      *(-- `2026-10-14T08:16` lidl 79 *y `2026-10-15T08:43` lidl 79 --)* ✓✓✓
   *-- *y **el de hoy corrio dentro del ciclo diario** ✓
*** 4) «*restaurar en una *** base NUEVA y desechable ***» *** *
   *-- *** `scripts/ensayo_de_restauracion.py` ***, *con sus guardas ✓
```

## 3. *** B00-B16, y **los tres que decian «cerrado como lectura»** ***

```
*** LOS 17 CON ESTADO EN EL CONTROL *** ✓
*** Y LOS TRES REABIERTOS ***: *
   *** B05 ***  *** implementado *** *(-- conflicto por clave, huellas, lease, 5 ensayos de dos pestañas --)* ✓
   *** B06 ***  *** implementado · causa medida · y una limitacion de la fuente *** ✓
   *** B07 ***  *** un SSRF CERRADO *** · *la **ocurrencia con identidad** · *«duplicar semana» · *
      *la **pantalla** · *el **recorrido** *-- y **con ensayos** ✓✓✓
*** -> *y **reabrirlos dio**: *dos paquetes **implementados que la fila no contaba**, *
   *y **uno con un agujero real** ✓
```

## 4. *** Y las cuatro decisiones, *contestadas y ejecutadas ***

```
*** 1) CSRF ***       *** se declara el limite *** ✓
*** 2) LIDL ***       *** ambito regional declarado ***, *y `'28'` **sin identificar** ✓
*** 3) LA LISTA ***   *** ACUMULA ***: *migracion `020`, *columna, *`anade_linea`, *`lineas_de`, *
   *`ya` *(-- *por la operacion **y por `None`** --)*, *el id con `traspaso.id_de_linea`, *
   *y *** seis ensayos *** ✓✓✓
*** 4) `ver_lista` *** *** se declara la excepcion *** ✓
```

## 5. *** Lo que queda **declarado como limite**, *y no como hecho ***

```
*** «preparado / vendido» ***  *-- *no es un olvido: *** ninguna de las seis cadenas lo publica *** *
   *-- *y **la forma de implementarlo, si algun dia hay dato, esta decidida por medicion**: *
      *columna aparte ✓
*** EL AMBITO DE LIDL ***  *-- *es *** regional ***, *y **`region='28'` sigue SIN IDENTIFICAR** ✓
   *-- *y **no se inventa** ✓
*** EL CSRF SIN `Origin` ***  *-- *** se declara el limite ***, *no se cierra ✓
```

## 6. *** Y **lo que me llevo de la sesion**, *que es el metodo ***

```
*** DE LOS OCHO ERRORES DE MEDICION MIOS ***, *** siete los cazo un instrumento ***: *
   *`ruff` · *los ensayos · *o **el recorrido** *
*** y **el octavo lo cace yo** al ir a arreglarlo ✓
*** -> *y **la conclusion no es «acertar a la primera»**: *
   *** es tener instrumentos que digan que te equivocas, *** y no ajustarlos nunca hasta que pasen *** ✓
*** Y **los tres patrones que se repitieron**: *
   *-- *** una anotacion que no se corresponde con lo que hay *** *
      *(-- `findstr /i running` describia mas; *«cerrado como lectura» describia menos --)*
   *-- *** el instrumento que mide mal *** *
      *(-- la sangria copiada del dump, *el glob `*import*`, *el `TZ` fijo, *
      *y **siete veces** el vocabulario equivocado --)*
   *-- *** y lo que parece hecho porque esta por dentro *** *
      *(-- el `PlanSemanal` que devolvia `null`, *el API sin pantalla, *
      *y el recorrido que solo tocaba estados vacios --)*
*** -> *y **lo que los caza**, *en orden de eficacia: *
   *** el recorrido de punta a punta *** > *los ensayos con dobles honestos* > *`ruff`* > *leer*
```
