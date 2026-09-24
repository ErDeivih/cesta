---
seccion: Investigación y anexos
resumen: Como se investigo, que no se pudo verificar y un error propio que enseña.
---

# 92 · Anexo: cómo se hizo esta investigación

Un material de aprendizaje que cita fuentes tiene que decir **de dónde salen** y **qué no se
pudo comprobar**, o se convierte en otra cosa. Este anexo es el registro del método, con las
fechas, los encargos y las limitaciones.

## Qué se investigó, cuándo y dónde acabó

El 24 de septiembre de 2026 se lanzaron cuatro investigaciones independientes sobre fuentes
públicas (2020-2026), cada una con un encargo escrito y con la obligación de decir «no lo sé»
cuando no encontrara un dato:

    emparejamiento de productos   anexo 90   resolucion de entidades, blocking, matchers,
                                             clustering y metricas de evaluacion
    indices de precios            anexo 91   metodologia oficial con datos de escaner, mas
                                             una auditoria de lo que hace este proyecto
    analisis avanzados            capitulo 09  cesta de la compra, elasticidad, promociones,
                                             anomalias, prevision, clustering y grafos
    ingenieria de datos           capitulo 02  capas, formatos, motores, idempotencia,
                                             orquestacion, calidad, observabilidad y coste

Los dos primeros se guardaron enteros como anexos, porque son el material más denso. Los otros
dos se integraron en sus capítulos con las fuentes citadas en el texto.

## Las reglas que se les pusieron

1. **Castellano, y sin relleno.** Si un dato no aparece, se escribe «no lo sé».
2. **Cada afirmación con su fuente** (URL y título) y, cuando es un número, de dónde sale.
3. **Distinguir la teoría de la aplicación.** Las fuentes sostienen el método; qué hacer con él
   en *este* proyecto es razonamiento propio, y va marcado como tal.
4. **Nada de recomendaciones que no se puedan medir aquí.** Cada propuesta trae «cómo
   comprobarlo».

## Un aviso sobre el método, contado porque enseña

En el encargo de la investigación sobre índices de precios se describió el recorte de relativos
del proyecto como «fuera del rango 0,5×-2×». **Era un error de quien escribió el encargo** (este
material): el código usa `RECORTE_MIN = 1.0/3` y `RECORTE_MAX = 3.0`
(`plataforma/api/analisis.py:55-56`), y los documentos del proyecto nunca dijeron otra cosa. La
investigación lo detectó y lo señaló como discrepancia, que es exactamente lo que debe hacer:
**un auditor que no comprueba el dato que le dan no está auditando**.

Se deja escrito aquí en vez de corregirlo en silencio por dos razones: es un ejemplo de manual
de por qué hay que citar la línea de código, y es la clase de error que un lector de este
material debe aprender a cometer y a detectar.

## Lo que no se pudo verificar

Las investigaciones declararon sus huecos, y se copian aquí porque **un hueco dicho vale más
que un número inventado**:

- Cifras concretas de rendimiento de las comparativas DuckDB/Polars/Daft/Spark: los extractos
  consultados no las exponen.
- Recall frente a latencia de búsqueda vectorial aproximada (HNSW/IVF con FAISS, pgvector,
  Qdrant) frente a búsqueda exacta.
- Regla oficial explícita sobre cómo debe entrar una promoción de lote (2x1, 3x2) en un índice
  de precios.
- Mínimo oficial de observaciones por agregado elemental en un índice con datos de escáner.
- Series públicas españolas de precios por cadena con las que validar el índice de forma
  externa.
- Literatura específica sobre sobre-bloqueo por marca blanca en supermercados españoles.
- Dos URL de encuestas académicas devolvieron HTTP 403 desde este entorno: se citan con esa
  salvedad.

## Lo que hay que hacer con esta investigación, en corto

De las cuatro investigaciones salen **siete** cosas que se pueden medir con lo que ya hay, y
están ordenadas por coste en el capítulo 09. La primera, y la que más puede cambiar el
proyecto, es medir la **pair completeness del bloqueo** del emparejador: si el bloqueo ya deja
fuera al 35 % de los pares ciertos, el 65 % de recall no es una nota del matcher sino un techo
estructural, y perseguir un modelo mejor sería perder el tiempo con estilo.
