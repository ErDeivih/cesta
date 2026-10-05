# Traspaso a otro agente

Este documento existe para que **otro asistente** (ChatGPT, Claude, el que sea) pueda ayudar en
este proyecto sin conocerlo de antes y **sin romperlo**. Es hermano de `docs/TRASPASO-CLAUDE.md`,
que se escribio en una ocasion parecida; si algo se contradice, manda este.

Fecha: **5 de octubre de 2026**. Todo lo que dice aqui esta medido en esa fecha; lo que cambia
todos los dias vive en `docs/CIFRAS.md` y no se copia aqui a proposito.

---

## 1. Que es esto, en un parrafo

**Cesta** compara precios de supermercado entre cinco cadenas espanolas (Mercadona, Carrefour,
DIA, Alcampo y Aldi) para que una persona decida **donde le sale mejor la compra**, producto a
producto, sin tener que mirar cinco webs.

Tres piezas:

1. **Un recolector** que visita las cinco webs cada dia y guarda lo que publican (precio, nombre,
   marca, formato, foto, ingredientes, sellos, promociones...).
2. **Un emparejador** que decide **que producto de una cadena es el mismo que el de otra** -- es lo
   dificil del proyecto, y donde esta la mayor parte del trabajo fino -- y calcula el precio por
   kg/litro para que la comparacion sea honesta.
3. **Una aplicacion web** (movil primero, 390x844) donde el dueno apunta su lista de la compra, ve
   donde le cuesta menos, sigue productos que le interesan, recibe avisos cuando algo baja y
   consulta la ficha de cada producto.

Es un proyecto **de una sola persona**, que lo usa a diario con su familia, y esta escrito con una
obsesion poco comun: **cada decision lleva al lado el numero que la sostiene**, y los documentos se
escriben para que un desconocido pueda seguir la pista. Eso es una virtud y tambien una carga: hay
mucho que leer. La seccion 5 dice por donde empezar.

**No es** un rastreador de precios a lo grande ni un negocio (todavia). Es una herramienta que
funciona, con datos reales de cinco cadenas, y con una pregunta abierta muy interesante: **si esto
se abriera a mas gente, que haria falta** (seccion 9).

---

## 2. Lo que funciona hoy

Cifras de la pasada del **5 de octubre de 2026** (las de hoy estan siempre en `docs/CIFRAS.md`):

| | |
|---|---:|
| productos en el catalogo | 53.140 |
| grupos comparables entre cadenas | 8.800 |
| productos con precio por kg/l/m | 42.665 |
| con codigo de barras (EAN) | 25.578 |
| con Nutri-Score | 8.458 |
| con tabla nutricional | 3.946 |
| con sello o certificado | 11.847 / 947 |
| historico de precios | mas de 1,2 millones de filas |

La aplicacion se usa a diario. Las **puertas** (seccion 7) estaban verdes el 5 de octubre:

    prueba_funciones     115 de 115 comprobaciones ("TODAS LAS FUNCIONES CONTESTAN")
    prueba_navegador     TODO BIEN (las cuatro preguntas, contraste, escaner, invitaciones)
    prueba_produccion    TODO BIEN (lo que sirve Caddy: paquete compilado y CSP)
    pytest               1.049 pruebas, 0 fallos

Y el material de aprendizaje (`/aprende`, 15 capitulos escritos en `docs/aprende/`) explica el
proyecto desde cero: que es parquet, que publica cada cadena, como se decide que dos productos son
el mismo. **Es la mejor introduccion que hay**, mejor que este documento.

---

## 3. Como esta montado

    core/                     lo comun: config, almacenamiento, esquemas, WAF, comparacion
      waf.py                  superar el reto de AWS WAF (solo Alcampo) con un navegador
      cobertura.py            "¿falta media tienda?" (rama por rama)
      secciones.py            el mapa de pasillos: que producto va a que seccion de la lista

    projects/cesta/           el recolector y el pipeline
      collectors/<cadena>.py  UNO POR CADENA (mercadona, carrefour, dia, alcampo, aldi)
      pipeline.py             raw -> bronze -> silver
      emparejar.py            silver -> gold   (LOS GRUPOS: el corazon del proyecto)
      run.py                  la pasada diaria entera
      verificar_ingesta.py    "¿lo que la cadena declaro lo guardamos?"
      cobertura_diaria.py     "¿trajo cada cadena lo que esa cadena sabe traer?"
      verificar_docs.py       vigila los numeros, las citas y los comandos de los documentos

    plataforma/               la aplicacion web (NO se mezcla con el recolector)
      api/                    FastAPI + PostgreSQL (cuentas, listas, favoritos, avisos)
      web/app/                React + Vite + TypeScript (movil primero)
      sql/                    migraciones, por orden de nombre, idempotentes
      prueba_*.py             las puertas
      docker-compose.yml      api + db + Caddy (:8080, misma origen que /api)

    tests/                    pruebas de lo que no necesita ni red ni base de datos

**Capas de datos** (todo en `data/`, que no se toca a mano):

    raw/        lo que devolvieron las webs, tal cual (cache de 30 dias)
    bronze/     limpio y normalizado por cadena, particionado fuente=/fecha=
    silver/     todas las cadenas juntas, sin decidir todavia quien es quien
    gold/       grupos.parquet (el producto unico con sus precios), enlaces, precio_diario

Tecnologia: **Python 3.11 + uv**, DuckDB y Polars sobre Parquet, FastAPI, PostgreSQL 16, React +
Vite + TypeScript, Caddy. Para el navegador de los colectores y de las puertas: **patchright**.

---

## 4. El dia a dia

    ejecutar.bat                 la pasada (una vez al dia; si ya se hizo hoy, sale enseguida)
    ejecutar.bat --forzar        otra vez hoy, a proposito
    registrar-tarea.ps1          da de alta la tarea programada (PowerShell como administrador)

Lo lanza el Programador de tareas de Windows al arrancar o al iniciar sesion. Hace, en orden: las
cinco cadenas **en paralelo**, las fichas maestras, el pipeline, el emparejador, el resumen, las
cifras, `verificar_docs` y `cobertura_diaria`. **Tarda entre una y dos horas**, casi todo Alcampo
peleandose con su WAF.

Mientras corre escribe `data/ejecuciones.log` (se puede leer en vivo: los recolectores no
bufferizan). Al final:

    === todo correcto ===                                  todo fue bien
    === fallaron: alcampo ===                              una cadena no colaboro
    === dia completado con 4 de 5 cadenas ===              y aun asi el dia vale
    === dia NO completado: se reintentara... ===           el pipeline no llego a correr

**Dos ficheros que se confunden con facilidad:**

    data/ejecucion_en_curso.txt    lo escribe run.py al empezar y lo borra al terminar. Si sigue
                                   ahi, la pasada anterior NO llego al final.
    data/ultima_ejecucion.txt      lo escribe ejecutar.bat si el codigo de salida es 0, o sea si
                                   **el pipeline corrio con algo fresco**. Que falte una cadena NO
                                   impide marcar el dia: reintentar dos horas no arregla que un
                                   WAF corte.

---

## 5. Los documentos, por orden de lectura

Si eres un agente y vas a tocar algo, lee **en este orden** (no hace falta entero, pero si lo
que toca tu tarea):

| documento | para que sirve | tamaño |
|---|---|---|
| `docs/aprende/*.md` | el curso: el proyecto explicado desde cero | 15 capitulos |
| `README.md` y `COMANDOS.md` | que es y los comandos del dia a dia | corto |
| `docs/OPERACION.md` | **el manual**: desplegar, cada herramienta, y que hacer cuando algo se rompe | 69 KB |
| `docs/DATOS.md` | parquet, DuckDB y por que cuatro capas | |
| `docs/CADENAS.md` | **que publica de verdad cada supermercado** (y que no) | |
| `docs/DIAGNOSTICO-MATCHING.md` | el emparejador a fondo: como decide, donde falla, cuanto acierta | 83 KB |
| `docs/API.md` | el contrato de la API, ruta por ruta | 57 KB |
| `docs/PANTALLAS.md` | cada pantalla de la app y por que es asi | 52 KB |
| `docs/CIFRAS.md` | los numeros de hoy (lo reescribe la pasada) | |
| `docs/BACKLOG.md` | **lo que esta hecho, lo que falta y por que** (253 KB: usar el indice) | 253 KB |
| `docs/COMPETENCIA-IMPLANTABLE.md` | que hacen las otras apps, **y que se puede implantar aqui** | 142 KB |
| `docs/DESPLIEGUE.md` | sacar esto del PC: fases, costes, avisos legales | |
| `docs/PARIDAD-CAMPOS.md` | que dato tiene cada cadena, campo a campo | |
| `docs/PRUEBA-15-SEGUNDOS.md` | **la barra (a)**: el dueno delante del movil, 15 segundos | |

---

## 6. Las reglas de la casa (esto es lo que mas ayuda a un agente nuevo)

Estan en el codigo, en los documentos y en los commits. **Saltarselas es la forma mas rapida de
que el trabajo se rechace**, aunque tecnicamente sea correcto:

1. **Todo numero que se escribe en un documento se ha medido**, y si es de un dia concreto lleva
   su fecha. Un numero sin fecha envejece y miente: ya ha pasado seis veces.
2. **Los documentos van en el mismo commit que el codigo.** Siempre.
3. **Un instrumento que no puede medir tiene que decirlo, no aprobar.** Varias veces la prueba
   pasaba porque no estaba mirando nada.
4. **Instrumentos que se puedan repetir**, y con ellos la prueba de que sirven: si un control no
   es capaz de encontrar un fallo puesto a proposito, no vale. (Se hace: se mete el fallo, se ve
   que salta, se quita.)
5. **La tarea diaria no se rompe.** Si algo puede hacer que la pasada de la manana falle, no se
   hace, o se hace de forma que no pueda tumbar el dia.
6. **La barra (a) la cierra el dueno**: una persona que no ha escrito estas pantallas contesta
   cuatro preguntas en 15 segundos con el movil. El codigo no decide eso.
7. **La clave de Stitch no se escribe nunca en el repositorio** (vive en `data/debug/`, ignorado).
8. **`core/datos/secciones.yml` no se commitea** (es estado de trabajo del mapa de secciones).
9. **No se toca `data/` a mano.** Un bronze malo **se aparta, no se borra** (hay una carpeta de
   descartados con el motivo en el nombre).
10. Codigo y comentarios en **espanol sin tildes**; los documentos, en espanol con tildes.
11. **El dueno no quiere ver "dato no encontrado".** Si un dato no esta, la pantalla dice **por
    que** y que se puede hacer; y nunca se ensena un cero donde lo que hay es "no lo se".

---

## 7. Como se verifica

Cuatro puertas, y **las cuatro se pueden correr en el PC**:

    uv run pytest -q                                  1.049 pruebas, sin red ni base de datos
    uv run python -m plataforma.prueba_produccion     lo que sirve Caddy (paquete y CSP)
    uv run python -m plataforma.prueba_navegador      el recorrido del encargo, movil 390x844
    uv run python -m plataforma.prueba_funciones      **cada accion del usuario, de verdad**

Las tres ultimas necesitan la aplicacion levantada. La de funciones hace 115 comprobaciones con
una cuenta desechable: alta, entrar, salir, darse de baja desde la pantalla, varias listas,
compartir, anadir, cantidad en los dos sentidos, tachar, quitar, deshacer, notas, cerrar la compra,
buscar, filtrar, ordenar, vistas guardadas, ficha de grupo y de producto, favoritos, avisos,
escaner, las diez pestanas del panel, ajustes y el manejo con el teclado.

Y una mas, que vigila los documentos:

    uv run python -m projects.cesta.verificar_docs     cifras, citas de codigo, comandos y campos

Si vas a proponer un cambio, **di como se comprueba**. Si no se puede comprobar con nada de esto,
dinero: probablemente la respuesta correcta sea anadir la comprobacion.

---

## 8. Problemas abiertos (5 de octubre de 2026)

**Resueltos hoy, pendientes de confirmar con la pasada:**

| problema | solucion | estado |
|---|---|---|
| Alcampo llevaba 4 dias sin capturas: se leia la pagina mientras el reto del WAF la recargaba, la excepcion no estaba recogida y el dia se perdia entero | `core.waf.contenido()`: reintenta la lectura y devuelve `None` si no puede | pruebas OK; **la pasada de hoy lo dira** |
| Ningun control miraba el **volumen**: Alcampo cayo de 37.019 a 24.120 y luego a cero sin un solo aviso | `projects/cesta/cobertura_diaria.py`: cada cadena contra el maximo de 30 dias, en la pasada diaria | hecho: dijo Alcampo 0 contra 37.019 |
| El barrido que recupera lo que falta no se disparaba nunca: comparaba contra el mayor de **7 dias** | ventana de **30 dias**: medido, 7 dias daban 24.120 (no barre) y 30 dan 37.019 (barre) | hecho |

**Abiertos:**

1. **Alcampo y su WAF.** Es el problema mas grande del proyecto. El WAF corta entre 8 y 13 veces al
   dia; hay una sesion que se renueva (primero sin ventana, y si no pasa, abriendo un Chrome fuera
   de la vista), reintentos con la misma cookie y esperas crecientes. Aun asi, en octubre ha habido
   dias sin captura. **Todo lo que se haga aqui se mide en horas de reloj y presion sobre el WAF.**
2. **El emparejador** acierta en torno al 57 % medido con su banco de pruebas
   (`docs/DIAGNOSTICO-MATCHING.md`). Los grupos demasiado anchos son el bloqueo numero uno: dos
   productos que no son el mismo acaban comparados y la app da un ahorro falso.
3. **La nota del producto (0-100)**: existe la idea y los datos (Nutri-Score 16 %, NOVA 15 %,
   ingredientes 11 %, aditivos 4 %), pero **falta decidir la formula**: adoptar una publicada o
   fijar pesos propios. Es una decision del dueno y esta esperando.
4. **Faltan datos de varias cadenas**: la ficha nutricional de Carrefour y Aldi, los ingredientes
   de Alcampo y Aldi, el codigo de barras de Alcampo y Aldi... `docs/PARIDAD-CAMPOS.md` tiene la
   matriz campo a campo. Cuando una funcionalidad necesita un campo que esta al 0 %, no se puede
   prometer.
5. **Decisiones pequenas esperando**: si la ventana de favoritos se queda en 90 dias; que hacer con
   el producto de Alcampo a 1,00 € que aparece cada dia (¿error de la cadena o del emparejador?).
6. **La auditoria de secciones propone la seccion desde la rama**, sin mirar el convenio del
   congelado; la prueba del convenio lo caza el mismo dia, pero se corrige a mano.

---

## 9. La oportunidad: una aplicacion para la gente

Esto es lo que mas valor tiene que pensar y lo que menos escrito esta. Lo que **ya existe** es una
app privada, de una familia, con datos reales de cinco cadenas. Lo que **no existe** es nada que
otra persona pueda usar.

**Lo que ya esta resuelto y es dificil de conseguir:**

- El dato: cinco cadenas, todos los dias, con historico de mas de un mes y precios por unidad
  comparables. Eso es la barrera de entrada de cualquier competidor.
- El emparejamiento entre cadenas, con sus indices de calidad A/B/C.
- Una app movil que funciona: lista de la compra, comparacion, favoritos con aviso de bajadas,
  ficha de producto con ingredientes y sellos, panel de analisis con diez pestanas.
- Las tuberias de calidad: puertas que comprueban cada accion, verificacion de la ingesta,
  controles de cobertura. Es lo que hace que se pueda confiar en el numero que se ensena.

**Lo que falta para que otra gente la use** (y esto es una lista tecnica, no un deseo):

| hace falta | por que | dificultad |
|---|---|---|
| Base de datos y autenticacion de verdad | hoy es PostgreSQL en un PC de casa | media: `docs/DESPLIEGUE.md` ya tiene el plan (Supabase free + Vercel) |
| Servir la app desde internet sin abrir la casa | Tailscale vale para la familia, no para el publico | baja/media: la web es estatica + API |
| Que los datos se actualicen sin depender del PC encendido | la pasada necesita un Windows con sesion iniciada (por el WAF) | **alta**: es el nudo del asunto |
| Coste por usuario | hoy el coste es "un PC encendido" | hay que hacer numeros; el plan gratuito de Supabase son 500 MB |
| Legalidad | ver abajo | **hay que mirarlo antes que nada** |

**Los tres escenarios, de menos a mas:**

- **A. Privada (hoy).** Un PC, Tailscale, la familia. Coste cero, riesgo legal bajo, cero usuarios
  nuevos. Es lo que hay.
- **B. Invitados (el paso natural).** 20-50 personas conocidas. Hace falta sacar la app del PC
  (web en Vercel + base en Supabase), un aviso legal claro, y decidir que se ensena y que no.
  El scraping sigue en el PC. Riesgo legal: bajo si no hay dinero de por medio y se cita la fuente.
- **C. Publica.** Aqui cambian tres cosas a la vez: **el coste** (el scraping de cinco cadenas
  desde un PC no aguanta trafico), **la legalidad** y **la confianza** (un precio equivocado en
  una app publica es un problema, en la tuya es una anecdota).

**Legalidad, dicho como lo que es: hay que consultarlo.** Este proyecto **lee webs de terceros**
sin permiso y guarda lo que publican. Los puntos que un abogado miraria: las condiciones de uso de
cada cadena, el derecho *sui generis* sobre bases de datos en la UE, el `robots.txt`, la carga que
se le mete al servidor (aqui es deliberadamente baja: una vez al dia y con esperas), y que se
ensene el precio de otro como propio. Lo que ya hace bien y hay que mantener: citar la fuente, un
aviso legal en la app (no afiliada, precios orientativos, la nutricion viene de Open Food Facts con
su licencia ODbL), no revender el dato y no usar marcas ajenas. **Nada de esto es consejo legal**:
es la lista de lo que habria que preguntar.

**Que haria yo antes de escribir una linea de la version publica:** (1) hablar con alguien de
derecho, (2) decidir el escenario (B es donde yo empezaria), (3) medir el coste real por usuario
con 50 personas, y (4) solo entonces tocar el despliegue. La tentacion de empezar por la tecnologia
es fuerte y es el orden equivocado.

---

## 10. En que nos ayudaria un agente externo

Lo que **no** puede hacer: tocar el PC, correr la pasada, ver la app. Lo que **si** aporta valor,
ordenado por lo que mas falta hace:

1. **Auditar el emparejador** (`docs/DIAGNOSTICO-MATCHING.md` + `projects/cesta/emparejar.py`).
   Acierta ~57 % y los grupos anchos son el fallo grande. Con el diagnostico y los ejemplos del
   banco de pruebas se pueden proponer reglas nuevas y discutirlas.
2. **Disenar la nota 0-100** del producto: que se mide, con que pesos, y por que. Hay que decidir
   entre adoptar el Nutri-Score publicado o fijar una formula propia, y **justificarla**.
3. **Mirar el angulo legal** del punto 9 con calma: que se puede publicar, que no, y con que texto.
4. **Disenar el escenario B** (app para invitados): arquitectura, coste por 50 personas, que se
   ensena en la primera pantalla de alguien que no conoce el proyecto.
5. **Revisar el texto de la app**: cada frase que se le ensena a una persona. Aqui el criterio es
   del dueno ("no quiero ver dato no encontrado"), y un tercero lo ve antes que uno mismo.
6. **Proponer analisis nuevos sobre los datos ya existentes** (sin recolectar nada nuevo):
   estacionalidad, que productos suben siempre en la misma epoca, en que cadenas conviene comprar
   cada categoria, cuanto ahorra de verdad una familia al mes. El historico tiene mas de un millon
   de filas de precio esperando a que alguien lo mire bien.

---

## 11. Como no romper nada

- **No toques `data/`.** Ni borres, ni renombres, ni "limpies".
- **No lances la pasada diaria** (`ejecutar.bat`) sin decirlo: tarda horas y machaca el WAF de
  Alcampo. Si hay que repetir un dia, es `ejecutar.bat --forzar`, y se avisa.
- **No cambies `core/datos/secciones.yml`** salvo para corregir una linea concreta, y ese fichero
  no se commitea.
- **No metas claves ni contrasenas** en el repositorio. Nunca.
- Si propones un cambio de codigo, **trae la comprobacion**: una prueba de `tests/` (sin red, sin
  base de datos) o una comprobacion nueva en la puerta que corresponda.
- Si un numero no lo has medido, **no lo escribas**; y si lo has medido un dia, **pon la fecha**.

---

## 12. Por donde empezar si te piden algo y no sabes que

    ¿que es esto?                 docs/aprende/ (curso) y README.md
    ¿como funciona la app?        docs/PANTALLAS.md y docs/API.md
    ¿como se decide que dos productos son el mismo?   docs/DIAGNOSTICO-MATCHING.md
    ¿que se puede implantar de la competencia?        docs/COMPETENCIA-IMPLANTABLE.md
    ¿que falta y por que?         docs/BACKLOG.md (indice; es enorme)
    ¿que numeros son ciertos hoy? docs/CIFRAS.md
    ¿como se saca esto del PC?    docs/DESPLIEGUE.md
    ¿que se rompe y como se arregla?  docs/OPERACION.md

Y una ultima cosa, que resume el espiritu del proyecto mejor que nada: **cuando en este repositorio
algo no cuadra, casi siempre es un documento que decia algo que ya no era verdad** -- se han
encontrado seis casos en una semana, y por eso hay un control automatico que vigila las cifras, las
citas de codigo, los comandos y hasta los campos de las tablas. Si encuentras uno de esos, has
encontrado algo util, aunque parezca una tonteria.
