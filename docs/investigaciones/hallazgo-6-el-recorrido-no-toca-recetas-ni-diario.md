# Hallazgo 6 · **El recorrido no toca Recetas ni Calorias** -- medido

*`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:65-66`:*
*** «El recorrido de Recetas/Calorias del adjunto *** observa estados vacios ***. *Prueba que las paginas
abren, *** no cinco recetas, cantidades, consumo y persistencia»***.

*Y el encargo lo repite en su aceptacion principal: *** «cinco recetas semanales con cantidades, compra
y porciones reales que persisten tras recargar».** *

---

## 1. La medicion, y es un `grep` vacio

```
*** `plataforma/prueba_e2e.py` *** *** 718 lineas ***, *y es **el recorrido de verdad** del proyecto* ✓
*** `git grep -n "recetas|diario|comensales|kcal" plataforma/prueba_e2e.py` *** *** -> VACIO *** ⚠️
*** -> o sea: *el recorrido cubre **listas, compras, cierre, permisos, ofertas, pasillos, alertas,
   el vigilante, y hasta CUANTO TARDA** *-- *y **no menciona Recetas ni Calorias ni una vez.*** *
*** -> **no es que «observe estados vacios» por casualidad**: *** es que esas dos pantallas
   NO ESTAN en el recorrido *** ✓
```

## 2. Y las tres piezas para extenderlo, con su linea

```
*** `l175` ***  *** `cliente = TestClient(main.app)` *** *
   *-- *y `l171`/`l174`: *`main.app.dependency_overrides[main.usuario_actual] = lambda: yo` *
   *-- *o sea: *el recorrido **no pasa por HTTP de verdad**, *va **en el mismo proceso** *(-- y
   **el propio fichero lo dice en `l297`**: «^ eso NO es la aplicacion: es httpx en el mismo proceso» --)*
   *** -> y **eso limita lo que se puede afirmar**: *prueba **las operaciones y los datos**, *
      *no **el HTML ni el CSS*** *
*** `l177` ***  *** `def pide(ruta, **params)` *** *-- *el helper de GET, *con `fallos` por `nonlocal`*
*** `l400`/`l520`/`l717` ***  *** `cliente.post(f"/api/listas/{…}", json={…})` *** *-- *y asi se muta* ✓
*** `l66` ***  *** `comprueba_que_es_una_prueba(os.environ["CESTA_POSTGRES"])` *** *
   *-- *¡**usa LA GUARDA** de `ajustes.py`! *(-- *la que veta **5432** y **5433**, *y exige que el
   resto sea el puerto de pruebas --)* ✓
*** y el final (l712-715) ***  *** `almacen.para()` · `print(f"\n== {'TODO BIEN' if not fallos else
   f'{fallos} FALLO(S)'}")` · `return 1 if fallos else 0` *** ✓
```

## 3. *** Y lo que falta, que son tres bloques y tienen nombre ***

```
*** 1) LAS CINCO RECETAS *** *
   *-- `POST /api/recetas` con `nombre`, `comensales` y `ingredientes[{texto,cantidad,unidad}]`*
   *-- *y **las cinco con datos conocidos** *(-- el plan pide «datos conocidos» --)*
*** 2) EL PLAN -> LA LISTA, CON LAS CANTIDADES Y LOS ENVASES *** *
   *-- `POST /api/recetas/plan` con `receta_id`, `fecha`, `comida`*
   *-- `GET/POST /api/listas/{id}/desde-el-plan?desde=&hasta=`* *(-- el POST devuelve 201 --)*
   *-- *** y aqui va LO DEL DUEÑO ***: *que la linea traiga **`cantidad`** *y* **`envases`** *
      *-- *y **el caso exacto**: *un ingrediente con **`tamano_envase`** y **necesidad > tamaño**
      *tiene que dar **envases >= 2** *(-- *y **hoy el defecto era `cantidad = 1`** --)*
*** 3) EL DIARIO, Y QUE PERSISTA *** *
   *-- `POST /api/diario` con `fecha`, `comida`, `tipo`, `referencia`, `cantidad_g`, `clave_operacion`*
   *-- `GET /api/diario/{fecha}`* *(-- **por FECHA**, *no por `/resumen`: *eso lo supuse y **no existe** --)*
   *-- *** y la cobertura DICHA ***: *`kcal_conocida`, `completo`* *-- *que es **la regla del encargo**:
      *«el diario solo registra las porciones confirmadas … *** con receta/version/snapshot y cobertura***»*
   *-- *y **la persistencia**: *volver a pedirlo **con el usuario otra vez**, *y que siga*
*** -> y **no hace falta nada nuevo**: *ni dependencias, *ni rutas, *ni un fichero. *
   *** Extender `prueba_e2e.py` con tres bloques y el patron que ya tiene. *** *
```

## 4. Y lo que **no** hay que hacer, dicho por lo que paso hoy

```
*** YO ESCRIBI UN RECORRIDO NUEVO ***, *`plataforma/recorrido_cinco_recetas.py`, *y lo **borre**:
  *-- *** invente rutas ***: *`/api/usuarios` **no existe**, *y el diario **no se lee por `/resumen`** ⚠️
  *-- *y **no mire**: *`prueba_e2e.py` (718 lineas) **ya estaba**, *con `prueba_f07_lista.py`,
     `prueba_funciones.py` y `prueba_transaccion.py` al lado*
  *-- *y **`docs/BACKLOG.md:1911` me lo dijo tres rondas antes**: *«`uv run python -m
     plataforma.prueba_e2e`»* *-- *lo lei **cuando buscaba la base de pruebas**, *y no lo segui* ⚠️
*** -> y el duplicado **se quito**: *un recorrido **que no corre** *y **repite lo que ya hay** es ruido*
```

## 5. Y por que **no lo escribi entero hoy**

*Tengo **las tres piezas y los numeros de linea**, *y **no voy a escribir tres bloques con el contexto
agotado**: *un recorrido **mal escrito que «pasa»** es **exactamente** la clase de mentira que esta
sesion lleva cazando* *-- *y **hoy ya escribi un duplicado con rutas inventadas**, *que es la prueba
de que **cuando escribo rapido, invento.*** *
