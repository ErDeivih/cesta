# Cesta — empieza por aqui

Esto es una fabrica de datos de precios de supermercado y la app que los
consulta. Lo lleva David, funciona sin supervision desde el 6 de septiembre de
2026, y esta documentado a conciencia porque los errores que ya hemos cometido
son caros de repetir.

## En dos minutos

    cinco cadenas     Mercadona, Carrefour, Alcampo, DIA, Aldi
    cada dia          ~52.575 precios, automatico, al encender el PC
    lo que hace       comparar el mismo producto y equivalentes entre cadenas
    donde vive        el PC de David; nada en la nube
    quien lo usa      David y su madre, desde el movil

## Los documentos

### Para empezar a trabajar (leer estos cinco)

    docs/LEEME-AGENTE.md      esto
    docs/FASES.md             **el plan, fase por fase, desglosado hasta tareas
                              que se hacen de una sentada. EMPIEZA AQUI.**
    docs/ARQUITECTURA.md      donde va cada cosa, con que se hace y por que
    docs/DATOS.md             que es parquet, DuckDB y las cuatro capas
    docs/CADENAS.md           que publica de verdad cada supermercado
    docs/PARIDAD-CAMPOS.md    **la matriz campo x cadena con el % de hoy**.
                              Mirar ESTO antes de prometer una pantalla: si una
                              columna esta al 0 % en Alcampo y Carrefour, que son
                              el 77 % del catalogo, la funcionalidad no se puede
                              hacer todavia
    docs/CERTIFICADOS.md      sellos de dieta y certificaciones de tercero: dos
                              vocabularios distintos, y por que no se mezclan
    docs/INGESTA-18SEP.md     **como se revisa una ingesta y que se le escapa**:
                              el dia que Alcampo entrego un catalogo sin frescos
                              con cero errores. Leer antes de fiarse de un log
    docs/EROSKI.md            **la sexta cadena, si empareja**: se lee entera y sin
                              navegador. Y las tres veces que el sondeo dio un
                              falso veredicto, que es lo que mas ensena
    docs/FICHAS.md            **la auditoria que faltaba**: el crudo de las fichas
                              de producto, nunca mirado. La de DIA tiene 200
                              claves y dos de ellas tapaban huecos del 0 %
    docs/CIFRAS.md            **los numeros de la ultima ejecucion**, y solo eso.
                              Se reescribe entero cada dia; los demas documentos
                              guardan los suyos con su fecha
    docs/INGESTA-19SEP.md     **el dia que Cloudflare bloqueo desde la peticion
                              numero 1**: por que recorrer 653 categorias
                              bloqueadas es coleccionar 653 fallos iguales, y el
                              umbral que lo corta
    docs/MOVIMIENTOS.md       **bajadas, subidas y ofertas que no lo son**: las
                              dos pantallas copiadas a la competencia, por que
                              una bajada del -96,7 % no era una bajada, y las
                              1.244 ofertas de tarjeta que se contaban como
                              rebajas de verdad
    docs/DATOS-SIN-USAR-18SEP.md  **lo que ya esta descargado y no leemos**, con
                              su medicion al lado y la spec de cada uno. Empieza
                              por las 199 ofertas de Aldi que aun no han empezado
    docs/SCRAPLING.md         que es Scrapling, por que por dentro es curl_cffi +
                              patchright (lo que ya usamos) y la unica prueba que
                              merece la pena hacerle
    docs/PRUEBAS-18SEP.md     **como se prueba la cadena sin tocar los datos de
                              casa**, incluido el ensayo que corre run.py entero
                              contra supermercados de mentira. Y lo que salio al
                              hacerlo: el historico no se podia rehacer desde
                              bronze, habia 20.559 filas sin bronze detras, y
                              verificar_docs aprobaba sin comparar nada
    docs/AUDITAR-RECORRIDO.md **la herramienta que encuentra las categorias que
                              no pedimos**, con el fallo de una linea que se
                              trago la rama Frescos entera
    docs/RELANZAR.md          cuando merece la pena relanzar una captura y por
                              que hay que arreglar ANTES de relanzar
    docs/AUDITAR-CRUDO.md     **la herramienta que encuentra los datos que ya
                              tenemos y no leemos**, lo que ha encontrado y lo
                              que se descarto con su medicion al lado. EJECUTALA
                              antes de pedirle nada nuevo a una web
    docs/PRECIO-POR-UNIDAD.md **las cuatro reglas que deciden si dos precios se
                              pueden restar**. Es la pieza central de la app: sin
                              ellas, "donde sale mas barato" es una loteria. Y
                              trae la comprobacion que lo descubre todo: mirar
                              los productos con el MISMO codigo de barras

### Antes de nada, si retomas el proyecto

    docs/VEREDICTO.md         **que se puede hacer y que no**, funcion por
                              funcion, de las 38 encontradas en la competencia
    docs/REVISION-17SEP.md    los seis fallos que salieron en la ultima
                              revision y como se arreglaron

### Para decidir que hacer y que no

    docs/FUNCIONALIDADES.md   catalogo de ideas con veredicto, coste y lo que
                              aguantan los datos. Incluye **lo descartado y por
                              que**, para no volver a discutirlo.
    docs/COMPETENCIA.md       nueve apps estudiadas: QueFalta, Bring!, Listonic,
                              Soysuper/OCU, Tiendeo, Yuka, El CoCo, NoWaste y
                              Mi Carrefour

### Para escribir codigo

    docs/API.md               **el contrato de todas las rutas**, las que hay y
                              las que faltan
    docs/COLECTORES.md        que deja cada colector sin coger, y como se anade
                              una cadena nueva
    docs/BACKLOG.md           las tareas sueltas, con criterios de aceptacion
    docs/PANTALLAS.md         que se ve en cada pantalla, incluido cuando algo
                              falla
    docs/UX-MOVIL.md          las reglas de interfaz en el movil
    docs/USABILIDAD.md        los sitios donde alguien de fuera se queda
                              colgado, y como se arreglan
    docs/AMIGOS.md            que cambia si un dia la usan tus amigos
    docs/MODELO.md            campos y consultas
    docs/LISTAS.md            listas propias y compartidas
    plataforma/LEEME.md       como se levanta la plataforma

### Para entender por que las cosas son como son

    docs/APP.md               las cinco pantallas y las decisiones de fondo
    docs/DESPLIEGUE.md        contenedores y acceso remoto
    docs/TAILSCALE.md         como entra la madre de David
    docs/DASHBOARD.md         el cuadro de mando, y los estudios ya hechos
    docs/OFERTAS-Y-ML.md      ofertas y donde tiene sentido el aprendizaje
                              automatico (y donde no)
    docs/OPERACION.md         la ejecucion diaria
    docs/AUDITORIA.md         lo que se reviso antes de dejarlo solo
    docs/PARIDAD.md           por que la unidad 'ud' no se compara entre cadenas
    docs/RECON.md             como se investigo cada web
    docs/PATCHRIGHT.md        el navegador parcheado para el WAF de Alcampo

## Las dos mitades, y por que no se mezclan

    EL SCRAPER          Windows, fuera de Docker. Necesita un Chrome de verdad
                        para el WAF de Alcampo.
                        ejecutar.bat  →  data/gold/*.parquet

    LA PLATAFORMA       Docker. API + PostgreSQL + web.
                        arrancar.bat  →  lee /datos/gold en SOLO LECTURA

Solo se hablan por el disco. Eso significa que se pueden parar, arreglar y
arrancar por separado, y que si un dia la recoleccion falla, la app sigue
sirviendo lo de ayer y lo dice en pantalla.

## Comprobar que todo esta bien

    uv run pytest                     todas, en verde
    uv run ruff check .               limpio, todo el proyecto
    uv run python -m projects.cesta.verificar_docs
                                      los numeros de los documentos cuadran
                                      con los datos de hoy
    uv run python -m projects.cesta.emparejar --medir
                                      57 % de aciertos sobre 1.748 pares conocidos

Ese 57 % es el indicador de salud del proyecto. **Mide antes y despues de tocar
el emparejador.** La ultima vez que se cambio sin medir, la cobertura cayo del
53 % al 43 % y costo dias entenderlo.

## Los numeros que hay que saberse

Antes de prometer nada en una pantalla, mira si el dato existe. Medido el 17 de
septiembre de 2026 sobre 51.781 productos:

    tienen precio comparable por kilo o litro       40.799   (76,9 %)
    estan en un grupo con otra cadena               ~20.000  (39 %)
    tienen codigo de barras                         25.094   (48 %)
      Mercadona 100 % · DIA 100 % · Carrefour 93 % · Alcampo 0 % · Aldi 0 %
    tienen ingredientes o Nutri-Score               11.724   (22,6 %)
    tienen origen declarado                          1.296   (2,5 %)

**El 22,6 % de nutricion es el numero mas importante de esta lista.** Significa
que cualquier pantalla que ensene una nota de salud dira "no lo se" cuatro de
cada cinco veces. Eso no se tapa: se disena.

## Las cuatro reglas que no se deshacen

1. Una letra de calidad sacada del precio se llama **gama**, no calidad. El 77 %
   lo son. Mezclarlas concluye que lo barato es peor, y es falso.
2. Una oferta es **una regla**, no un precio. Y los descuentos de tarjeta no
   bajan el total: no se descuentan en caja.
3. Ninguna correccion de dato se aplica sin que **algo independiente la
   confirme**. El patron esta en `pipeline.py`.
4. Cada precio lleva **su fecha**, y uno de mas de tres dias no decide en que
   tienda comprar.

## Como se trabaja aqui

**Medir antes de afirmar.** Cada numero de estos documentos sale de una consulta.
Cuatro veces esta semana una medida ha contradicho lo que parecia evidente: el
precio por kilo de Alcampo (se tiraba), la marca de Aldi (se tiraba), las ofertas
de Carrefour (se tiraban), y el estudio de marca blanca (salia al reves porque el
76,9 % de las letras de calidad son el precio disfrazado).

**Un fallo se arregla con una prueba.** Las 180 que hay existen porque algo
fallo. Si arreglas algo, deja la prueba que impide que vuelva.

**Los comentarios explican por que, no que.** Si hay un numero raro en el codigo,
al lado esta la medicion que lo justifica.

**Castellano en el codigo y en los documentos.** Nombres de funcion, variables,
comentarios y mensajes. Es el idioma de quien lo mantiene.
