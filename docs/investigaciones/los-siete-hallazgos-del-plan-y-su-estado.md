# Los **siete hallazgos** del plan, y en que estado esta cada uno

*`docs/SUPERAPP-PLAN-DEEPSEEK-2026-10-13.md:48-68` (la seccion «Hallazgos nuevos de codigo que impiden
cerrar el encargo»). **Y los leí tarde**: *llevaba cinco rondas diciendo «el plan pide B00–B16»
*sin haber leido **su lista**, *que esta **en la pagina 2** *y **nombra lo que yo estaba arreglando**,
*con **el numero delante.*** *

---

## El mapa

| # | lo que dice el plan | estado |
|---|---|---|
| **1** | *`run._una_cadena` llama `mod.main()`; *el colector Lidl **exige origen y region**; *«no hay adaptador que convierta **incluirlo en `ORDEN`** en una ingesta diaria funcional»* | *** corre, y se midio *** |
| **2** | *`api/cesta.py` ***excluye Lidl globalmente*** por ser parcial; ***«parcial no significa que todos sus precios observados sean invalidos»***; *la elegibilidad **por articulo, region, fecha**; *la cobertura **por separado*** | *** NO ESTA *** ⚠️ |
| **3** | *`_del_plan` no escala por comensales, *deduplica por **nombre** y **anade una unidad** | *** HECHO *** ✓ |
| **4** | *el POST de receta individual: `round(ln.cantidad) or 1`, *unidad omitida, *`isdigit()`; ***«una identidad `fuente:id` no sobrevive»*** | *** HECHO *** ✓ |
| **5** | *`PlanSemanal.tsx` elige la lista de casa **o la primera**; ***«debe elegir destino explicito, no escribir en otra lista silenciosamente»*** | *** CONFIRMADO, sin arreglar *** ⚠️ |
| **6** | *«el recorrido del adjunto ***observa estados vacios***; *prueba que las paginas abren, ***no cinco recetas, cantidades, consumo y persistencia»*** | *** probado por la API, NO por la pantalla *** ⚠️ |
| **7** | *««SameSite=Lax + POST sin cookie → 401» ***no reproduce un ataque CSRF***; *falta ***auditar origen, metodos y ataques con sesion***» | *** MEDIDO *** ✓ |

## 1 · Lidl en el ciclo — **corre, y se midio**

```
*** `data/runs.csv`, ciclo del 14/10 ***: *** `2026-10-14T08:16:21,lidl,79,0,146.9,True` *** *
*** y `LastTaskResult: 0` *** *(-- termino --), *con **las seis fuentes** ✓
*** -> o sea: *«no hay adaptador que convierta incluirlo en `ORDEN` en una ingesta funcional» *** ya no
   es cierto *** *-- *corre, *y deja fila con `ok=True`.* *PERO: *el plan **no pedia que corriera**,
   *pedia que **fuera funcional** *-- *y **eso es el 2.** *
```

## 2 · La exclusion global — *** el unico sin mirar, y es el que el encargo repite dos veces ***

```
*** `plataforma/api/cesta.py:62` ***  *** `if cadena == "lidl":` *** *
   *** -> la exclusion es POR CADENA: *cualquier articulo, region, fecha y condicion *** ⚠️
*** y su comentario la justifica: *** *«meterlo en las comparaciones haria que **pareciera tener precio
   para cosas que no cataloga** -- *y un «Lidl no lo tiene» que en realidad es «no lo hemos capturado»»*
*** y el plan responde: *** *** «parcial no significa que TODOS sus precios observados sean invalidos» *** *
*** -> y LOS DOS TIENEN RAZON: *la diferencia es **el grano*** *
   *-- *el proyecto separo **capturar** (`CADENAS_QUE_SE_CAPTURAN`, seis) de **comparar** (`CADENAS`,
      cinco), *y **lo dice en la pantalla** con `por_que_no_se_compara`*
   *-- *y **falta el paso intermedio**: *«¿este precio concreto es comparable?»* *-- *por **articulo,
      region y fecha***
   *-- *y **la cobertura se declara aparte**: *«no aparece» **no es** «no lo tiene»*
*** y las piezas ya estan: *** *`region` en el catalogo (`region='28'`), *`fecha` en el historico, *
   *y `por_que_no_se_compara` para decirlo en la pantalla* ✓
```

## 5 · El destino silencioso — *** confirmado, literal ***

```
*** `plataforma/web/app/src/paginas/PlanSemanal.tsx:96` *** *
  *** `const listaId = listas.data?.find((l) => l.es_de_casa)?.id ?? listas.data?.[0]?.id ?? null` *** *
*** -> **exactamente** lo que el plan describe: *«elige la lista de casa ***o, si no existe, la primera
   lista***»* ⚠️
*** y la pantalla dice «Del plan a la lista» (l120) *** *** pero NO en cual *** ⚠️
```

## 7 · El CSRF — *** medido, y con una correccion que me toca ***

```
*** lo que el plan pide ***: *auditar *** origen, metodos y ataques con sesion *** *
*** lo que se hizo ***: *con sesion real, tres mutaciones cambiando **solo** el `Origin` -> las tres
   `201`, *y comprobado **en la lista*** ✓
*** y el plan advierte, en su bibliografia (l387-389) ***: *
  *** «revisar la conclusion excesiva de SameSite… NO convertir la recomendacion en un requisito
  de token impuesto sin analizar contexto» *** ⚠️
*** -> o sea: *** *** mi «hay un hueco de CSRF» es la conclusion que el plan ya habia marcado
   como excesiva *** *-- *y **lo que aporte es la medicion**, *que es **la parte que faltaba.** *
```

## Y el metodo, que el plan tambien deja escrito

```
*** l76-77 ***  *** «Antes de cambiar cada camino, *** convertir el caso en regresion ejecutable
   controlada ***» *** *
*** y l43-46 ***  *** «No llamar «irreparable» a un volumen sin *** inventariar backups/volumenes de
   forma no destructiva ***» *** *
   *-- *y **eso es lo que hice**: *inventarie **sin borrar nada**, *y **resulto que no habia ningun
   respaldo** -- *y **sin esa medicion** habria dicho «no hay copias» **sin saber por que.*** ✓
```

## Lo que queda, en orden de peso

```
*** 2) LA ELEGIBILIDAD POR ARTICULO ***  *-- *es **el encargo** *(-- «sin presentar ausencias de captura
   como indisponibilidad» *y «ni darle una cesta completa no cubierta» --), *y **es el unico de los siete
   sin empezar*** ⚠️
*** 5) EL DESTINO EXPLICITO ***  *-- *confirmado en el codigo, *y **falta decidir**: *¿selector,
   *o parar cuando no hay lista de casa?*
*** 6) EL RECORRIDO POR LA PANTALLA ***  *-- *el plan pide **probar**, y **lo probe por la API** ⚠️
*** 1) ***  *-- *corre; *lo que **no** esta es la elegibilidad *(-- o sea: *el 1 y el 2 son **el mismo
   problema visto desde dos sitios** --)*
```
