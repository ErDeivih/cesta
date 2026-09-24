---
seccion: Empieza aquí
resumen: El mapa, las reglas de la casa, los comandos y cómo se lee esto.
en_una_frase: Se lee de arriba abajo, cada capítulo trae la teoría, el caso con números medidos y lo que no se sabe, y todo se reproduce en este PC.
---

# 00 · Cómo usar este material

Esto no es la documentación de una aplicación. Es **el material de un curso** que usa un
proyecto real como caso práctico: comparar los precios de cinco supermercados españoles,
todos los días, en un PC de casa, y contestar con esos datos preguntas que la gente se hace
de verdad en el pasillo.

Se lee de arriba abajo, y cada capítulo hace lo mismo:

1. **La teoría**, en corto y con las fuentes donde está mejor contada.
2. **El caso**: qué hace este proyecto, con **los números medidos** y el comando que los
   reproduce. No hay ni un número de ejemplo.
3. **Lo que no se sabe** o no se puede hacer con estos datos, dicho antes de que alguien lo
   dé por hecho.

## Dónde se lee esto

De dos maneras, y las dos valen:

- **En el PC, sin servidor**: `plataforma/web/aprende/index.html`, con doble clic. El buscador
  lleva su índice embebido, así que funciona sin conexión. Se navega por el índice de la
  izquierda, y cada página tiene su propio índice a la derecha.
- **Desde el móvil o cualquier cacharro de casa**: `http://<el-PC>:8080/aprende/`.

El sitio se genera a partir de estos documentos, que son la fuente:

```bash
uv run --extra docs python -m plataforma.aprende
```

> **Nota:** cada capítulo abre con un recuadro **En una frase**, y dentro vas a encontrar cinco
> tipos de recuadro, y ninguno es decoración. **Nota** matiza algo que se podría malinterpretar;
> **Aviso** señala un límite que conviene no olvidar; **Trampa** cuenta un error que ya se cometió
> aquí; **La lección** cierra una idea que merece recordarse; y **Regla** es una decisión del
> proyecto que no se salta. Si un recuadro no te aporta nada, sáltalo: el texto de al lado se lee
> igual.

## Lo que hay que saber antes de empezar

No hace falta ser ninguna de estas tres cosas, pero ayuda tener idea de:

    Python          leer un script y ejecutarlo. Nada mas.
    SQL             SELECT, JOIN, GROUP BY. Es lo que se usa aqui el 80 % del tiempo.
    estadistica     saber que una mediana no es una media. El resto se explica.

Y **no hace falta**: ni saber de Docker, ni de AWS, ni de machine learning. Cuando algo de
eso aparece, se explica por qué está ahí y qué costaría quitarlo.

## Las reglas de la casa

Estas cuatro reglas son el 80 % de lo que se aprende aquí, y están metidas en el código, no
en un manual:

1. **Un dato que no tenemos es «no lo sé»**, nunca un cero. Un `0,00 €` se lee como «gratis»
   y una letra vacía como «malo»; las dos cosas serían mentira.
2. **Se mide antes y después, sobre el mismo dato.** Si el dato de entrada cambia entre las
   dos medidas, no sabes qué causó la diferencia. Esto es lo que separa un cambio de una
   opinión.
3. **Comparar solo dentro de la misma unidad.** Un precio por kilo y un precio por unidad no
   se comparan: compararlos da «te ahorras 6.872 €» en la ficha de un azafrán.
4. **El que calla no bloquea.** Si un dato no dice nada de un atributo, no está afirmando que
   sea igual: es que no lo sabemos. Eso no es tolerancia, es ausencia de prueba.

## Cómo se ejecuta cada cosa

Todo lo de este material se puede reproducir en este PC. Los cuatro comandos que aparecen una
y otra vez:

```bash
uv run python -m projects.cesta.verificar_docs    # las cifras de los documentos, contra el dato de hoy
uv run python -m projects.cesta.ejes              # las condiciones de dato (ejes, grupos, packs)
uv run python -m projects.cesta.emparejar --medir # el recall del emparejador sobre el banco de pares
uv run pytest -q                                  # las pruebas del proyecto
```

Y para mirar los datos a mano, que es de donde salen casi todos los hallazgos:

```bash
uv run python -c "import duckdb; print(duckdb.sql(\"select count(*) from 'data/gold/grupos.parquet'\"))"
```

## El mapa

El temario está agrupado en secciones, y en el sitio se ve en el índice de la izquierda. Este es
el orden de lectura:

    EMPIEZA AQUI
      00  como usar este material      el mapa, las reglas de la casa y los comandos
    FUNDAMENTOS
      01  el problema y los datos      que hay, de donde sale y que NO se puede concluir
      03  unidades y comparabilidad    por que un catalogo de envases no se compara sin normalizar
      13  fundamentos del dato         valor, grano, clave y ausencia: que es un dato
      98  glosario                     los terminos, en una linea cada uno
    INGENIERIA DE DATOS
      02  ingenieria de datos          capas, formatos, motores, idempotencia, la cadena diaria
      11  servir los datos             API, PostgreSQL, migraciones y despliegue
      14  el stack explicado           cada pieza, por que esta y que costaria quitarla
      15  scraping                     como se recoge el dato de cinco webs distintas
    ALGORITMOS Y EVALUACION
      04  emparejar productos          resolucion de entidades: bloqueo, similitud, hungaro, ejes
      05  medir el emparejador         el banco de pares, el techo del bloqueo, invariantes
    MEDIDAS Y AGREGADOS
      06  estadistica del catalogo     medianas frente a medias, percentiles, muestra, recortes
      07  indices de precios           Jevons encadenado, formulas oficiales y el sesgo medido
      08  promociones y anomalias      que se anuncia, que sostiene el historico y que no se juzga
    ANALISIS Y DECISION
      09  que mas se puede hacer       12 analisis en una tabla, con lo que se puede y lo que no
      10  cuando NO usar ML            tres intentos medidos y descartados, con su numero
    PRACTICA DEL ANALISIS
      12  medir sin enganarse          los instrumentos que mintieron, y la senal que los delata
    INVESTIGACION Y ANEXOS
      90  la investigacion sobre emparejamiento, entera y con sus fuentes
      91  la investigacion sobre indices de precios, y la auditoria de este proyecto
      92  como se hizo la investigacion, y que no se pudo verificar
      93  las formulas                   todas, con sus simbolos, su origen y el numero que dan hoy

Si vas a leer dos capítulos y parar, que sean el 13 (qué es un dato) y el 12 (cómo se mide sin
engañarse): el resto se apoya en esos dos. Y cuando te preguntes «¿y ese 0,55 de dónde sale?», la
respuesta está en el 93, que es el capítulo para volver.

Los documentos largos del proyecto (el registro del día a día, los informes, la operación)
están en **la referencia**, que es donde se comprueba de dónde sale cada cosa. Este curso los
cita continuamente con la forma `docs/BACKLOG.md`, y esos nombres se pueden abrir en el mismo
sitio: son las páginas de la sección *Referencia*.

## Lo que este material NO es

- **No es un tutorial de herramientas.** DuckDB, Polars o FastAPI aparecen porque hacen falta
  para algo concreto, no como temario.
- **No es un caso de éxito.** La mitad de los capítulos cuentan cosas que se intentaron, se
  midieron y **no se adoptaron** (el canal de vectores, el medoide, dos modelos de decisión
  de los que se habla hoy). Un proyecto de datos de verdad es eso.
- **No tiene los números inventados.** Si un dato no se ha medido, pone «no lo sé». Y eso es
  una respuesta, no un hueco.
