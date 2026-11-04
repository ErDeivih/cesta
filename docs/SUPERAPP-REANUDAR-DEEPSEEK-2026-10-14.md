# Reanudar DeepSeek: revisión del cierre del 14/10/2026

Complemento al plan B00–B16 del 13; no reinicia la arquitectura ni borra avances.
HEAD revisado: `ce7582f`. Mantener los criterios del plan original. Esta revisión
no autoriza restaurar sobre ninguna base existente ni afirma haber reactivado
el objetivo de la aplicación externa.

## Estado observado, no heredado

- Tarea `Cesta diaria`: Running; última ejecución 14/10 a las 10:11:50.
  No se lanzó otra ni se interrumpió esta.
- API: versión `20261013-155356`, datos del 13, publicación coherente y seis huellas.
  No cambiar el puntero durante las escrituras de la captura actual.
- El log de hoy muestra múltiples HTTP 403 de Carrefour. Diagnosticar resultado,
  tolerancia y recuperación antes de hablar de captura correcta.
- `runs.csv` completo no contiene fila de Lidl en el momento inspeccionado.
  La última pasada terminada registrada es la del 13. El log de aquella pasada
  contiene `FALLO: el colector termino su CLI (codigo 2)` para Lidl y cinco de seis.
  Ese resultado no demuestra qué ocurrirá con el código actual: la adaptación
  CLI existe ahora y el trabajo de hoy sigue activo.
- Ruff limpio; `tests/test_b04_los_dos_puentes.py`: **7 passed**, ejecutados aquí.
  Las cifras 2.033/81 son las del traspaso: no se reejecutó aquí la suite completa.
- Se conservan los cambios ajenos en secciones, CIFRAS y control del 13, y los
  tres scripts sin seguimiento. No se ha restaurado ni alterado ningún almacén real.

## 1. Los dos bloqueos declarados no justifican cerrar el trabajo

**Esperar a las 06:00 no necesita otra decisión de producto.** Ya pasó esa hora
y existe una ejecución activa. Mirar su estado, log y resultado; mientras corre,
trabajar en los fallos independientes de abajo. Si se requiere seguimiento futuro,
usar el mecanismo de espera/monitor del entorno, no declarar todos los paquetes
bloqueados por el reloj. No duplicar una captura.

**Restaurar en un destino nuevo no es restaurar sobre una base existente.** El
plan B00/B14 pide expresamente un ensayo aislado. No hay que pedir permiso para
borrar casa o pruebas: eso sigue prohibido y no es necesario para este ensayo.
Crear un contenedor/base nuevos, con nombre único, puertos libres, etiqueta de
propiedad del ensayo y DSN construido por el propio ensayo. Verificar la identidad
del destino real antes de DDL. No reutilizar 5432, 5433 ni 5434; tampoco nombres
constantes sin comprobar que no pertenecen a otro trabajo. No ejecutar el guion
actual a ciegas: auditar sus eliminaciones y subprocesos primero.
Restaurar allí una copia, comparar contenido y conservar evidencia; limpiar solo
recursos creados y acreditados como propios. La prueba debe incluir PostgreSQL,
recetas/diario SQLite y permisos/snapshots, no solo una tabla vacía.

## 2. Hallazgo reproducido: dos envases calculados, uno persistido

Reproducción ejecutada con `_acceso`, `_del_plan` y `almacen.anade_linea` simulados,
sin red ni bases. Una línea normalizada pide 1.400 g, tiene envases=2 y sobrante=600 g:

```text
envases_calculados: 2
cantidad_insertada: 1
nota: del plan: R1 + R2 (1400 g) · 2 envases, sobran 600 g
recibo: anadidos=1, ya_estaban=[], sin_catalogo=[]
```

`main.traer_del_plan` añade el número de envases a texto, pero llama a
`almacen.anade_linea(..., uno.producto_id, 1, detalle)`. La nota no gobierna el
cálculo de coste ni el cierre. El puente de receta individual también pasa 1.
Por tanto, sumar correctamente 300 g en la previa NO completa la corrección de
ambos puentes hasta que la cantidad de compra y su identidad se persistan bien.

Primera regresión a implementar: 1,4 kg de un producto en envase de 1 kg debe
guardar **dos envases**; estimación/cierre/histórico usan dos. Repetir con tres
envases, fracción de receta y desconocimiento del tamaño. Con tamaño desconocido,
conservar necesidad pendiente y coste parcial; no afirmar que un envase basta.

## 3. Otros criterios que siguen abiertos por lectura

1. **Ingrediente sin catálogo.** `traer_del_plan` lo devuelve en `sin_catalogo`
   y no lo añade. El resultado `anadidos=0` para tomate prueba rechazo, no que
   se conserve como línea pendiente. El plan exigía sal/ingredientes manuales
   visibles con cantidad y unidad, sin precio ni equivalencia inventados.
2. **Dedupe por nombre.** El POST del plan sigue usando `nombre.lower() in ya`.
   Distintas marcas con el mismo texto, cambios de raciones y una nueva compra
   legítima pueden saltarse. El UUID por lista+clave tampoco identifica una nueva
   operación planificada. Separar contribuciones por identidad y operación.
3. **Identidad de receta individual.** El POST conserva solo identificadores
   `isdigit()`, convirtiéndolos a int. `dia:fixture` queda None; un grupo puede
   evitar el rechazo, pero no preservar el artículo elegido. Probar un producto
   exacto sin grupo y dos marcas de una familia; no degradar exacto a familia.
4. **Despensa por nombre.** La previa pregunta textos de despensa y el comentario
   admite que no hay identidad. Eso no acredita reservas, cantidades compatibles
   ni ausencia de doble descuento. No cerrar B05/R08 por tener esta consulta.
5. **Recorrido real.** Un POST que no añade líneas, datos nutricionales todos
   desconocidos o capturas de vacíos no prueban cinco recetas→lista→compra→consumo.
   Hace falta escenario controlado con cantidades, raciones, energía conocida,
   cobertura parcial adicional y persistencia después de recargar.

No deshacer avances útiles: el escalado y consolidación de la previa tienen sus
pruebas. Completar las capas siguientes y ampliar las pruebas, no volver al bug antiguo.

## 4. Lidl: medir ejecución real y hacer visibles todas las salidas

El runner actual sí tiene adaptador `ARGUMENTOS['lidl']=['--web','--escribir']`.
Está integrado por llamada, no acreditado por ello como captura diaria correcta.

No usar solo `Get-Content ... -Tail 8`: un registro puede quedar más atrás; filtrar
el CSV completo por fuente y por intervalo/día en Europe/Madrid. Una fila `ok=True`
con productos tampoco cierra bronze→silver→gold→API/UI, ámbito y elegibilidad.

Carencia concreta por lectura: al no acreditar región, `collectors/lidl.main`
imprime causa y retorna 1 sin `log_run`. También pueden escapar excepciones de
HTTP/parsing antes de registrar. En consecuencia, ausencia de fila puede ser
ejecución fallida sin telemetría, no ausencia de ejecución.

Implementar registro de intento y resultado terminal en TODOS los caminos,
con causa, inicio/fin, ámbito y checkpoint; sin duplicar entradas ni almacenar
cookies. Fixture de región desconocida y excepción de red debe dejar evidencia
de fallo, y no escribir bronze. Probar el adaptador y la captura con dato local
antes de otro ensayo real, respetando runlock y la ejecución en curso.

**No afirmar que las otras cinco cadenas son nacionales porque `region` es NULL.**
NULL dice que ese campo no contiene ámbito. Mercadona usa CP/almacén; canal,
tienda, zona y campaña pueden importar en otras fuentes. Documentar procedencia
y ámbito por cadena. El CP de config no prueba que el propietario haya elegido
ese domicilio si sigue siendo el valor predeterminado.

`region_del_cp` compara provincia con `regionName` y devuelve la clave de
`regionsV2`, no el valor de `regionPriceId`; conservar ambos por separado. Si se
consulta qué es '28', leer el mapa publicado de la captura y distinguir id de
región, nombre y grupo de precios. No inventar la correspondencia ni su stock.

## 5. Cambiar el criterio de avance

Los checkpoints de identificación de grupos NO acreditan reanudación de una
captura interrumpida; la cola de fichas NO demuestra checkpoint de categorías.
Localizar y ejecutar el caso específico que pide cada criterio.

7,6 % de cobertura o 72.319 fichas pendientes son medidas de situación, no cierre
de mejora de ingesta. Distinguir nutrición nativa/enriquecida/manual, alimentos
aplicables y huecos de extractor antes de culpar a la fuente. Resolver una cola
con presupuesto/prioridades y recuperación; contarla cada ronda no la reduce.

No cerrar B05/B06/B07/B09/B10/B11/B12 como «contestados por lectura» cuando el plan
pide implementación/ensayo. Reabrir SOLO criterios no satisfechos, conservando
evidencia válida. Ni 271 documentos ni un build dan aceptación funcional.

## Texto de continuación para pegar en el objetivo

Continúa el plan B00–B16 y lee primero este complemento del 14/10. No está todo
bloqueado: espera/verifica la ingesta activa sin duplicarla y trabaja mientras
tanto en las regresiones de ambos puentes. La reproducción actual calcula dos
envases y guarda uno: persiste el número correcto, necesidad/unidad e identidad
exacta, conserva ingredientes sin catálogo como pendientes y elimina dedupe por
nombre como identidad de operación. Ensaya cinco recetas con datos conocidos,
compra, cierre y porciones consumidas; recarga, permisos e idempotencia incluidos.
Completa telemetría de Lidl en todas sus salidas y demuestra publicación/consulta
regional, no solo presencia en ORDEN o una fila del CSV. La restauración se
ensaya en bases NUEVAS desechables con guardas: nunca casa 5432, facylf 5433 ni
pruebas compartidas 5434. No pidas autorización para sobrescribirlas porque no
es necesario ni está permitido. Reabre criterios cerrados por lectura y trabaja
en implementación y evidencia, no en más rondas de resúmenes. El objetivo externo
lo reanuda David desde su aplicación; este fichero no modifica su estado.
