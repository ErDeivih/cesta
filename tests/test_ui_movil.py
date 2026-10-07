"""Las reglas de movil del proyecto, comprobadas.

Estas reglas estan escritas en los documentos y en comentarios del codigo, y hasta
hoy **no las comprobaba nadie**: se cumplian porque quien escribio las pantallas se
acordo. Eso dura hasta la primera prisa.

Son cuatro, y las cuatro tienen un motivo concreto que ya costo caro en la interfaz
vieja:

1. **44 px para pulsar.** Se usa de pie, con una mano y el carro en la otra. Un
   boton de 24 px se falla, y fallar en la tienda es pulsar dos veces.
2. **16 px en los campos.** Por debajo, Safari hace zoom al enfocar el campo, la
   pagina se queda descolocada y hay que pellizcar para volver.
3. **La raya del iPhone.** Sin `safe-area-inset-bottom`, la barra de abajo se come
   el ultimo boton en los moviles que tienen raya.
4. **Cuatro destinos en la barra de abajo, y no cambian.** Es una decision escrita
   en `docs/USABILIDAD.md`: una barra de ocho iconos no se lee, se busca a tientas.

No comprueba el aspecto -- eso no se puede comprobar leyendo -- sino las reglas que
se pueden comprobar leyendo, que son justo las que no dan error al incumplirlas.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "plataforma" / "web" / "app"
UI = APP / "src" / "componentes" / "ui.tsx"
NAV = APP / "src" / "componentes" / "Nav.tsx"
PUERTA = RAIZ / "plataforma" / "prueba_navegador.py"

sin_interfaz = pytest.mark.skipif(
    not APP.exists(), reason="esta copia no trae la interfaz nueva")


@sin_interfaz
def test_el_boton_nunca_baja_de_44_px():
    """El minimo para pulsar con el pulgar sin fallar.

    Se mira `Boton`, que es el sitio por el que pasan todos: si el minimo vive en
    un solo sitio, no hay que revisar catorce pantallas cada vez que se toca una.
    """
    fuente = UI.read_text(encoding="utf-8")
    assert "min-h-[44px]" in fuente, (
        "el boton ha perdido los 44 px minimos: se usa de pie, con una mano y el "
        "carro en la otra, y un boton bajo se falla")
    # Y en las dos ramas: el compacto tambien tiene que llegar a 44.
    assert fuente.count("min-h-[44px]") >= 2, (
        "solo una de las dos variantes del boton conserva los 44 px")


@sin_interfaz
def test_los_numeros_que_se_leen_no_se_formatean_a_mano():
    """`toFixed` escribe el punto decimal en inglés: «3.89 €», «8.5», «2.3 g».

    Medido el 27 de septiembre de 2026, con la pantalla delante, en cuatro sitios que se leen:
    la promesa de un aviso («Te aviso si baja de 3.89 €»), la nota de una alternativa en la
    ficha del grupo («8.5 de 100»), los componentes de «por qué está en esta posición» (0.85) y
    la tabla de nutrición (que decía «2.3 g»), todos ellos **al lado de precios con coma**. Los
    números que se leen pasan por `numero`, `euros` o `porcentaje` (`api/formato.ts`), que son
    los que saben de comas; `toFixed` se queda para lo que no lee nadie, como las coordenadas
    de un `path` de SVG.
    """
    lectura = re.compile(r"€|%")
    mal = []
    for fichero in sorted((APP / "src").rglob("*.tsx")):
        for numero_linea, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            if "toFixed(" not in linea:
                continue
            limpia = linea.strip()
            # Lo que se pinta: una unidad que lee una persona, o un `{...}` en medio del JSX.
            if lectura.search(linea) or ">{" in linea or limpia.startswith("{"):
                mal.append(f"{fichero.name}:{numero_linea}: {limpia[:70]}")
    assert not mal, (
        "hay numeros que se leen formateados con `toFixed`, que pone el punto decimal:\n  "
        + "\n  ".join(mal) + "\nUsa `numero`, `euros` o `porcentaje`.")
    # Y la prueba mira, con los cuatro casos que la pusieron a punto.
    def se_lee(linea: str) -> bool:
        limpia = linea.strip()
        return bool("toFixed(" in linea and (
            lectura.search(linea) or ">{" in linea or limpia.startswith("{")))

    assert se_lee('? `Te aviso si baja de ${(a.umbral_cent / 100).toFixed(2)} €`')
    assert se_lee("{alternativa.puntos === null ? 'no lo sé' : alternativa.puntos.toFixed(1)}")
    assert se_lee('<Etiqueta tono="bien">−{f.ahorro_pct.toFixed(0)} %</Etiqueta>')
    assert not se_lee("      .map((p, i) => `${i ? 'L' : 'M'}${x(p.fecha).toFixed(1)},"
                      "${y(p.indice).toFixed(1)}`)"), "las coordenadas de un SVG no se leen"


def _etiqueta_completa(texto: str, inicio: int) -> str:
    """El texto de una etiqueta JSX, desde `<x` hasta su `>` de cierre.

    **No vale cortar en el primer `>`**, y esto se aprendio midiendo: el
    `<select>` de `FiltrosBusqueda.tsx` lleva `onChange={(e) => ...}`, o sea un `>`
    dentro de una llave, y cortando ahi el `className` -- que va despues -- se
    quedaba fuera del trozo mirado. La prueba pasaba sin haber mirado nada: el
    mismo fallo silencioso que persigue, cometido por la prueba.

    Se recorre contando llaves y comillas, y el `>` que cierra es el que esta fuera
    de las dos y no forma parte de un `=>`.
    """
    i, comillas, llaves = inicio, None, 0
    while i < len(texto):
        c = texto[i]
        if comillas:
            if c == comillas:
                comillas = None
        elif c in "\"'`":
            comillas = c
        elif c == "{":
            llaves += 1
        elif c == "}":
            llaves -= 1
        elif c == ">" and llaves == 0 and texto[i - 1] != "=":
            return texto[inicio:i + 1]
        i += 1
    return texto[inicio:]


@sin_interfaz
def test_las_cadenas_se_pintan_con_su_nombre_y_no_con_el_identificador():
    """El identificador de una cadena (`dia`, `alcampo`) **no es su nombre**.

    Viene en minusculas porque es la clave que usa el colector, y durante meses se pinto tal
    cual en las pastillas de cinco pantallas, en el desglose del reparto de la cesta, en la
    leyenda del indice, en cuatro tablas del panel y en la tabla de equivalencias de la ficha:
    «alcampo», «dia», «carrefour», mientras la ficha del grupo decia «Aldi» y «Mercadona». La
    que decide como se llama una cadena es `nombreCadena` (`api/formato.ts`), que ademas tiene
    las excepciones escritas (DIA va con las tres letras en mayuscula). Medido y arreglado el
    27 de septiembre de 2026.

    Se mira **el texto que se pinta**, no los atributos: `key={c.cadena}` o
    `to={/producto/${f.fuente}/...}` son identificadores, y ahi es donde tienen que estar.
    """
    crudo = re.compile(r"\{(?:[a-z_]+\.)?(?:cadena|fuente)\}")
    atributo = re.compile(r"\b(?:key|to|href|aria-label|style|className|background|value|id)=")

    def se_pinta(linea: str) -> bool:
        """Si la linea acaba pintando el identificador en la pantalla."""
        limpia = linea.strip()
        # Un comentario no se pinta, y una prop (`cadena={cadena}`) es un dato que se pasa, no
        # texto que se lee: lo que se persigue es el `{...}` que acaba delante de alguien.
        if limpia.startswith(("*", "//", "/*")) or atributo.search(linea) \
                or "nombreCadena" in linea:
            return False
        for encontrado in crudo.finditer(linea):
            # Interpolacion de un identificador en JS no es texto JSX visible.
            if linea[encontrado.start() - 1:encontrado.start()] in ("=", "$"):
                continue
            return True
        return False

    mal = []
    for fichero in sorted((APP / "src").rglob("*.tsx")):
        for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            if se_pinta(linea):
                mal.append(f"{fichero.name}:{numero}: {linea.strip()[:70]}")
    assert not mal, (
        "hay sitios que pintan el identificador de la cadena en vez de su nombre "
        "(usa `nombreCadena`):\n  " + "\n  ".join(mal))
    # Y la prueba mira, con los cuatro casos que la pusieron a punto: el que la hizo falta, los
    # dos que NO son texto pintado y el que ya esta arreglado.
    assert se_pinta("<Td>{c.cadena}</Td>"), "el patron ya no caza el caso que lo motivo"
    assert not se_pinta("              <tr key={c.cadena}>"), "`key` no es texto que se pinte"
    assert not se_pinta("  cadena={cadena}"), "una prop no es texto que se pinte"
    assert not se_pinta(" *  `/producto/{cadena}/{id_fuente}`."), "un comentario no se pinta"
    assert not se_pinta("<Td>{nombreCadena(c.cadena)}</Td>"), "ya arreglado, no se señala"


@sin_interfaz
def test_ningun_campo_de_texto_baja_de_16_px():
    """16 px o Safari hace zoom al enfocar, que descuadra la pagina entera."""
    diminutos = []
    for fichero in sorted((APP / "src").rglob("*.tsx")):
        texto = fichero.read_text(encoding="utf-8")
        for etiqueta in ("<input", "<select", "<textarea"):
            for trozo in re.finditer(re.escape(etiqueta), texto):
                etiqueta_completa = _etiqueta_completa(texto, trozo.start())
                if re.search(r"text-(xs|sm|\[1[0-5]px\])", etiqueta_completa):
                    linea = texto[:trozo.start()].count("\n") + 1
                    diminutos.append(f"{fichero.name}:{linea}")
    assert not diminutos, (
        "hay campos con la letra por debajo de 16 px, y Safari hara zoom al "
        "enfocarlos:\n  " + "\n  ".join(diminutos) +
        "\nEl tamano se hereda del `html` a proposito: quita la clase del campo.")


@sin_interfaz
def test_la_barra_de_abajo_reserva_la_raya_del_iphone():
    """Sin esto, en un iPhone con raya el ultimo boton queda debajo."""
    fuente = NAV.read_text(encoding="utf-8")
    assert "env(safe-area-inset-bottom)" in fuente, (
        "la barra de abajo ya no reserva el hueco de la raya del iPhone: el "
        "ultimo boton se queda debajo y no se puede pulsar")


@sin_interfaz
def test_la_barra_de_abajo_tiene_seis_destinos_y_el_ultimo_esta_medido():
    """Los destinos de la barra, y por que son seis y no cinco.

    Lo dice `docs/USABILIDAD.md`: una barra de ocho iconos no se lee, se busca a
    tientas. El quinto entro el 23 de septiembre de 2026 **decidido y escrito**, no
    colado: Avisos no es un sitio donde estar, es **lo unico que la aplicacion hace por
    ti mientras no la miras**, y es la respuesta a *"¿ha bajado algo de lo mio?"*. El
    encargo de esa fecha pide literalmente *"un punto en el icono"*, y un punto necesita
    un icono donde estar -- dentro de otra pantalla seria esconderlo en una esquina.

    **El sexto entro el 25 de septiembre de 2026, tambien decidido y medido**: el dueno
    pidio *"poner la opcion de lista de la compra y favoritas"*, y Favoritos existia desde
    hacia dias **sin forma de llegar a ella** (habia que escribir la direccion). Una
    pantalla a la que no se llega no es una pantalla.

    Y el limite no era el numero de iconos sino **cuanto mide cada uno**, que es lo unico
    medible: medido en el navegador a 390 px despues del cambio, los seis destinos miden
    entre 58 y 65 px de ancho por 56 de alto, todos por encima del minimo de 44 px que se
    pulsa con el pulgar. Con siete serian 55 px y empezaria a apretar; ese dia lo que
    toca no es apretarlos mas, es sacar de aqui lo que no se usa en el pasillo.
    """
    fuente = NAV.read_text(encoding="utf-8")
    bloque = re.search(r"const ITEMS = \[(.*?)\] as const", fuente, re.S)
    assert bloque, "no he sabido leer los destinos de la barra: revisa esta prueba"
    destinos = re.findall(r"a:\s*'([^']+)'", bloque.group(1))
    assert destinos == ["/", "/cesta", "/favoritos", "/escaner", "/avisos", "/panel"], (
        f"la barra de abajo tiene {destinos}. Son seis a proposito: buscar, la lista, los "
        f"favoritos, el escaner, los avisos y el panel. Anadir otro es una decision, no "
        f"un detalle")
    # Y el porque tiene que estar donde se lee, que es con los destinos.
    assert "lo unico que" in fuente and "punto en el icono" in fuente, \
        "el destino de Avisos tiene que llevar su razon escrita al lado"
    assert "65 px por cabeza" in fuente or "44 px" in fuente, \
        ("el sexto destino tiene que llevar escrito por que cabe: el minimo que importa "
         "no es el numero de iconos, sino lo que mide cada uno")


def test_los_objetivos_de_la_ficha_del_producto_tienen_44_px():
    """Los cuatro que se escaparon por no medir esa pantalla (23 sep 2026).

    La puerta medía todas las pantallas menos la ficha del producto, y ahí había **cuatro
    objetivos por debajo de 44 px** desde el primer día, medidos en un móvil de 390 x 844:

        el enlace al producto de al lado, en la tabla    161 x 19
        (y el mismo enlace con el nombre en dos líneas)  158 x 39
        el desplegable «Ingredientes»                    324 x 20

    El enlace es la forma de saltar a la ficha de otro producto del grupo, que es lo que se
    hace **con el paquete en la mano**, y el desplegable abre los ingredientes, que es donde
    se mira si algo lleva lo que no se puede comer. Ninguno de los dos se acierta de pie a
    19 px. La pantalla entró en la pasada de la puerta en el mismo cambio.
    """
    ficha = (APP / "src" / "paginas" / "Producto.tsx").read_text(encoding="utf-8")
    # El desplegable se pinta con `Resumen`, que ya trae los 44 px (y la flecha: ver
    # `test_lo_que_se_despliega_lleva_su_flecha`). Lo que se vigila aqui es que **siga** pasando
    # por ahi y no vuelva a ser un `<summary>` a mano con su altura de texto.
    assert re.search(r"<Resumen[^>]*>\s*\n\s*Ingredientes", ficha), \
        "el desplegable de ingredientes no usa el resumen de 44 px (volveria a medir 20 px)"
    assert not re.search(r"<summary[^>]*min-h", ficha), \
        "volvio el `<summary>` a mano"
    assert re.search(r"<Link to=\{`/producto/\$\{p\.fuente\}.*?min-h-\[44px\]", ficha, re.S), \
        "el enlace al producto de al lado vuelve a medir 19 px"
    # Y la puerta tiene que medir esta pantalla, que es de donde salió el fallo.
    puerta = PUERTA.read_text(encoding="utf-8")
    assert '/producto/{con_historial[0]}/{con_historial[1]}' in puerta, \
        "la ficha del producto no está en la lista de pantallas que se miden"
    assert "/escaner" in puerta, "la pantalla del escáner tampoco"


def test_la_puerta_mide_que_ninguna_pantalla_se_deslice_de_lado():
    """Una página que se sale obliga a moverla con el pulgar para leer el final de las
    líneas, y en la tienda eso es soltar el carro.

    Las tablas anchas se deslizan **dentro de su caja** (`TablaScroll`), que es a propósito:
    lo que no puede deslizarse es la página. La puerta lo mide en cada pantalla que visita
    (`documentElement.scrollWidth` contra `clientWidth`) y el 23 de septiembre de 2026, con
    ocho pantallas, todas dan 390 de 390.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "document.documentElement.scrollWidth" in puerta, \
        "la puerta no comprueba que la pagina quepa a lo ancho"
    assert "la pagina no se sale de la pantalla" in puerta, \
        "la comprobacion del ancho no dice lo que está midiendo"


def test_la_puerta_mide_que_las_cuatro_respuestas_quepan_en_la_primera_pantalla():
    """(a) no la puede cerrar una prueba, pero lo que no quepa queda descartado antes.

    La condicion (a) se juzga con el movil en la mano y **sin saber donde esta el boton**:
    una respuesta que obliga a desplazar la pantalla no se lee en quince segundos ni
    sabiendo donde esta. La puerta del navegador mide la **banda util** del movil
    (`_franja_util`: la cabecera y la barra de abajo se comen 109 y 57 px de los 844) y
    comprueba que las cuatro respuestas caben enteras dentro, con la pantalla arriba:

        1 y 3  la primera linea de la lista             y=661..677
        2      la frase del grupo al que se llega
               buscando                                  y=520..564
        4      "lo tuyo que ha bajado": su cabecera      y=613..646
               y su primera fila, que es la respuesta    y=646..706
        4      la seccion de los avisos                 y=186..210

    Medido asi el 27 de septiembre de 2026, con la banda util en 109..787. Esto **no**
    quiere decir que (a) este cumplida -- eso lo dice una persona --, pero si alguna de
    las cuatro se fuera por debajo de 787, seria imposible cumplirla y se sabria por que.

    **Las dos medidas del 27 de septiembre cambiaron de sitio y de objeto, y hay que decir
    por que**, porque las dos parecian la misma medida de antes:

      - la primera linea de la lista estaba a **1.269 px** porque la tarjeta «Dónde compro
        cada cosa» (592 px) iba por encima; se bajo la tarjeta y ahora esta a 661;
      - la tabla de «lo tuyo que ha bajado» se medía **entera**, y es un ranking que crece
        solo (94 px el 24, 242 el 27): exigir que quepa entera es una prueba que se pone roja
        por tener mas datos. Ahora se miden su cabecera y su primera fila, que es lo que
        contesta la pregunta.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    assert "def _franja_util(" in puerta, \
        "la puerta no sabe cual es la banda util de la pantalla"
    assert "def _cabe_en_la_primera(" in puerta, \
        "la puerta no comprueba si una respuesta cabe en la primera pantalla"
    assert "--alto-cabecera" in puerta and "la banda util" in puerta, \
        "la banda util tiene que salir de la cabecera de verdad, no de un numero a ojo"
    for que in ("1 y 3: la primera linea de la lista se ve sin desplazar",
                "2: la frase que contesta «¿esto esta caro?» se ve sin desplazar",
                "4: la primera fila de lo tuyo que ha bajado se ve sin desplazar",
                "4: la seccion de los avisos se ve sin desplazar"):
        assert que in puerta, f"la puerta no comprueba «{que}»"

    # Y lo que dejo de medirse, con su motivo: en el movil las tablas se apilan (27 sep 2026),
    # asi que **no hay cabecera** que quepa o deje de caber; lo que hay que ver es la fila.
    assert "ninguna tabla se desliza en horizontal" in puerta, \
        "la puerta no comprueba que las tablas no se deslicen en el movil"


def test_la_puerta_mide_que_el_precio_no_se_vaya_de_la_pantalla():
    """Los resultados, sin deslizar en horizontal: el precio tiene que verse (27 sep 2026).

    La tabla de resultados media 52rem de ancho minimo y en un movil habia que deslizarla: se
    veian «Producto» y «Cadena» y **el PVP y el €/L no**. Lo dijo una captura, no una prueba,
    que es justo lo que este proyecto llama "una respuesta que no se ve". Ahora la puerta lo
    mide, y esto vigila que la medida siga estando.
    """
    puerta = PUERTA.read_text(encoding="utf-8")
    for que in ("nada que deslizar en horizontal",
                "y el precio, que es la respuesta, dentro de la pantalla",
                "y las cadenas a un toque, encima de los resultados",
                "solo salen resultados de"):
        assert que in puerta, f"la puerta no comprueba «{que}»"
    assert "aria-label='Cadena de los resultados'" in puerta, (
        "la puerta no encuentra las cadenas de encima de los resultados por su etiqueta")
    # Y la razon, escrita donde se lee.
    assert "52rem" in puerta or "deslizar en horizontal" in puerta, (
        "el caso que lo destapo tiene que estar contado al lado de la medida")


def test_ninguna_etiqueta_de_celda_es_un_simbolo_suelto():
    """La etiqueta de una celda apilada **dice de que es el numero**, no repite su simbolo.

    Medido en la captura de `/panel?pestana=cadenas` el 28 de septiembre de 2026: la columna «%»
    del panel llevaba `etiqueta="%"` y el valor ya traia su «%», asi que en el movil la linea se
    leia «compite en 1008  gana 700  **% 69,4 %**». La cabecera de la tabla se esconde al apilar,
    y la etiqueta es lo unico que queda para decir de que es ese porcentaje.
    """
    fuente = list(APP.glob("src/**/*.tsx"))
    malas: list[str] = []
    for fichero in fuente:
        for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            for etiqueta in re.findall(r'etiqueta="([^"]*)"', linea):
                if len(etiqueta.strip(" %€$/-")) <= 1:
                    malas.append(f"{fichero.name}:{numero} etiqueta={etiqueta!r}")
    assert not malas, f"hay etiquetas de celda que no dicen nada: {malas}"


def test_la_casilla_se_anuncia_con_el_nombre_de_su_linea():
    """Un `input` sin nombre se lee «casilla, activada»: quien no ve, no sabe que tacha.

    Lo mide la puerta de las funciones ya pintado (el nombre **accesible** sale del `<label>`, no
    del `value`, que en todas las casillas es «on»). Aqui se vigila el sitio donde eso se decide:
    `Casilla` (`componentes/ui.tsx`) envuelve el `input` en un `label` **con `htmlFor` al id del
    input** y con el texto dentro. Sin ese `htmlFor` la asociacion se rompe y ninguna medida de
    la pantalla lo notaria, porque el clic sigue funcionando.
    """
    ui = (APP / "src" / "componentes" / "ui.tsx").read_text(encoding="utf-8")
    trozo = ui.split("export function Casilla(", 1)[1].split("\nexport function ", 1)[0]
    assert "htmlFor={mio}" in trozo, (
        "la casilla no asocia su etiqueta con el input: se anuncia sin nombre")
    assert "id={mio}" in trozo, "el `<label htmlFor>` apunta a un id que el input no tiene"
    assert "useId()" in trozo, "el id tiene que ser unico por casilla, no uno escrito a mano"
    # Y el nombre accesible no puede salir del `value`: es «on» en todas las casillas.
    assert "value=" not in trozo, "el nombre de la casilla no puede ser su `value`"


def test_la_puerta_mide_la_aplicacion_con_el_teclado():
    """El teclado, que no lo medía ninguna puerta: la app tambien se usa en el ordenador."""
    puerta = (RAIZ / "plataforma" / "prueba_funciones.py").read_text(encoding="utf-8")
    for que in ("controles alcanzados con el tabulador",
                "cada casilla se anuncia con el nombre de su linea",
                "y una linea se tacha con la barra espaciadora"):
        assert que in puerta, f"la puerta no comprueba «{que}»"
    assert "keyboard.press(\"Tab\")" in puerta, "la puerta no tabula"
    produccion = (RAIZ / "plataforma" / "prueba_produccion.py").read_text(encoding="utf-8")
    assert "«/» lleva el foco al buscador" in produccion, (
        "la puerta de produccion no mide el atajo del buscador del material")
    assert "«Escape» cierra la lista de resultados" in produccion, (
        "y no mide que se pueda cerrar")


def test_las_novedades_de_la_lista_se_pintan():
    """Un campo que viaja en la respuesta y no se pinta es una funcion que no existe.

    **Paso dos veces, y las dos con el mismo aspecto de estar hechas.** `nombre_visto` viajaba en
    `GET /listas/{id}` desde el primer dia y no lo pintaba nadie (23 de septiembre de 2026), y
    `novedades` igual: `docs/PANTALLAS.md` decia «**[hecho]** las dos secciones, el marcador, las
    novedades», `docs/VEREDICTO.md` decia «novedades al abrir — hecho», la API las mandaba... y la
    palabra `novedades` **no aparecia en `app/src`**. Una lista compartida seguia siendo un sitio
    donde las cosas aparecen y desaparecen solas.

    La puerta del navegador lo mide con las dos personas delante (una toca, la otra abre y se
    entera, y al volver a abrir desaparece). Esto vigila lo que la puerta no puede: que la pantalla
    siga pintandolo, y que el campo siga **declarado** en el tipo.
    """
    cesta = (APP / "src" / "paginas" / "Cesta.tsx").read_text(encoding="utf-8")
    assert "<Novedades" in cesta, "la pantalla de la lista no pinta las novedades"
    assert "function Novedades(" in cesta, "falta el componente que las pinta"
    assert "Desde la última vez que miraste" in cesta, "y falta el titulo que las presenta"
    tipos = (APP / "src" / "api" / "cesta.ts").read_text(encoding="utf-8")
    assert "novedades?: Novedad[]" in tipos, (
        "el campo no esta declarado en `DetalleLista`: TypeScript no lo vigilaria")
    # Y el filtro que las hace utiles: lo que he tocado yo no es una novedad.
    trozo = cesta.split("function Novedades(", 1)[1].split("\nexport ", 1)[0]
    assert "quien !== yo" in trozo, (
        "sin filtrar por quien lo hizo, la pantalla te cuenta lo que acabas de hacer tu")


def test_lo_que_se_despliega_lleva_su_flecha():
    """Nada de `<summary>` sueltos: el marcador nativo desaparece con `display: flex`.

    Lo encontro **mirar una captura**, no leer el codigo: en la cabecera, «Estado de las cadenas»
    salia como una linea suelta con un hueco debajo -- parecia un encabezado sin nada -- y la caja
    de filtros del buscador parecia un segundo campo de texto. La causa es una linea de CSS que no
    se ve: el triangulo que el navegador pinta en un `<summary>` **desaparece en cuanto se le pone
    `display: flex`**, que es justo lo que hace falta para que mida los 44 px de pulsar.

    Ahora los diez desplegables de la aplicacion se pintan con `Resumen` (`componentes/ui.tsx`),
    que pone la flecha, y una regla de `estilos.css` la gira al abrirse. Esto lo vigila leyendo:
    que no vuelva a haber un `<summary>` a mano es lo unico que no puede comprobar la puerta,
    porque la puerta solo ve las pantallas que visita.
    """
    fuente = list(APP.glob("src/**/*.tsx"))
    assert fuente, "no encuentro el codigo de la aplicacion"
    sueltos: list[str] = []
    for fichero in fuente:
        for linea in fichero.read_text(encoding="utf-8").splitlines():
            # Solo la etiqueta de verdad, no la que se nombra dentro de un comentario: en este
            # proyecto los comentarios citan `<summary>` al contar la medida que costo.
            limpio = linea.strip()
            if limpio.startswith("<summary"):
                sueltos.append(f"{fichero.name}: {limpio[:60]}")
    assert sueltos == ["ui.tsx: <summary"], (
        f"hay desplegables escritos a mano, y esos no llevan flecha: {sueltos}")

    ui = (APP / "src" / "componentes" / "ui.tsx").read_text(encoding="utf-8")
    assert "export function Resumen(" in ui, "no existe el resumen con flecha"
    assert 'className="flecha ml-auto shrink-0' in ui, "la flecha se perdio en el camino"
    assert "list-none" in ui, (
        "sin `list-none`, en Safari el triangulo nativo sigue saliendo **ademas** del nuestro")
    assert 'aria-hidden' in ui.split("export function Resumen(")[1][:900], (
        "la flecha es decorativa: si lleva texto visible, el lector de pantalla lee «▾»")

    css = (APP / "src" / "estilos.css").read_text(encoding="utf-8")
    assert "details[open] > summary .flecha" in css and "rotate(180deg)" in css, (
        "la flecha no dice en que estado esta: abierta y cerrada se ven igual")
    # Y la puerta lo mide ya pintado, en tres pantallas.
    puerta = (RAIZ / "plataforma" / "prueba_funciones.py").read_text(encoding="utf-8")
    assert "lo que se despliega: que se note que se despliega" in puerta, (
        "la puerta no mira que los desplegables se noten")
    assert "la flecha gira al abrirse" in puerta, (
        "la puerta no comprueba que la flecha cambie al abrirse")
