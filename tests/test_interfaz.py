"""La interfaz nueva: que el sitio donde compila y el sitio que se sirve sean el mismo.

Es la misma clase de prueba que `test_imagen_api.py`, y por el mismo motivo: el
fallo no esta en el codigo, esta en dos ficheros de configuracion que tienen que
decir lo mismo y que nadie compara.

Aqui el fallo concreto es facil de cometer y dificil de ver: Vite compila a
`plataforma/web/dist` y Caddy sirve lo que le monte docker-compose en `/srv`. Si
los dos lados se separan -- se cambia `outDir`, o se deja el montaje antiguo de
`./web` --, la aplicacion **no da error**: Caddy sirve un `index.html` que existe,
el navegador carga, y lo que sale es la interfaz vieja. O una pagina en blanco,
segun el dia. Sin un error por ningun lado.

Esto no ejecuta npm ni levanta Docker: lee los tres ficheros y comprueba que
dicen lo mismo. Tarda milisegundos.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "plataforma" / "web"
APP = WEB / "app"
VITE = APP / "vite.config.ts"
COMPOSE = RAIZ / "plataforma" / "docker-compose.yml"
CADDY = RAIZ / "plataforma" / "Caddyfile"


def _out_dir() -> str | None:
    """El `build.outDir` de Vite, tal cual, sin resolverlo."""
    if not VITE.exists():
        return None
    m = re.search(r"outDir:\s*['\"]([^'\"]+)['\"]", VITE.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def _montaje_de_la_web() -> str | None:
    """La linea de docker-compose que monta la interfaz en la web."""
    if not COMPOSE.exists():
        return None
    for linea in COMPOSE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*(\S+/web[^:]*):/srv:ro", linea)
        if m:
            return m.group(1)
    return None


@pytest.mark.skipif(not VITE.exists(), reason="esta copia no trae la interfaz nueva")
def test_vite_compila_al_sitio_que_ensena_el_readme():
    """`outDir` es `../dist`, o sea `plataforma/web/dist`."""
    assert _out_dir() == "../dist"


@pytest.mark.skipif(not COMPOSE.exists(), reason="no hay docker-compose en esta copia")
def test_docker_compose_sirve_lo_que_vite_compila():
    """La comprobacion que evita servir la interfaz vieja sin que nadie se entere."""
    montaje = _montaje_de_la_web()
    assert montaje is not None, (
        "docker-compose ya no monta ninguna carpeta de `web` en /srv: Caddy no "
        "tendria que servir.")
    assert montaje.endswith("web/dist"), (
        f"docker-compose monta `{montaje}` en /srv, pero Vite compila a "
        f"`web/dist`. Caddy serviria la interfaz vieja (o una pagina en blanco) "
        f"sin dar ningun error.")


def test_la_interfaz_vieja_sigue_ahi():
    """No se borra hasta que la nueva tenga paridad: es el plan B, y es una linea."""
    if not APP.exists():
        pytest.skip("esta copia no trae la interfaz nueva")
    assert (WEB / "index.html").exists()
    assert (WEB / "app.js").exists()


def test_caddy_sirve_una_sola_pagina_y_manda_la_api_al_backend():
    """El `try_files` es lo que hace falta para una aplicacion de una sola pagina."""
    if not CADDY.exists():
        pytest.skip("no hay Caddyfile en esta copia")
    texto = CADDY.read_text(encoding="utf-8")
    assert "try_files {path} /index.html" in texto
    assert "reverse_proxy api:8000" in texto


def test_el_csp_no_permite_origenes_de_fuera_para_codigo_ni_fuentes():
    """La aplicacion no carga codigo, estilos ni fuentes de otro sitio, y el CSP lo dice.

    El `style-src` admitia `https://fonts.googleapis.com` y habia un `font-src` para
    `fonts.gstatic.com`: eran de la interfaz vieja, que cargaba Archivo desde ahi, y **el permiso
    se quedo escrito cuando el codigo se arreglo**. Una puerta abierta por costumbre es lo
    contrario de lo que dice el proyecto («nada de fuentes ni imagenes traidas de internet»), y
    medido el 27 de septiembre de 2026 no habia ni un `fonts.googleapis` en el codigo ni en lo
    servido. `img-src` si admite `https:`: las fotos de los productos las sirven las cadenas
    desde sus CDN y **se enlazan, no se copian** -- esa es la unica puerta que esta abierta a
    proposito, y por eso la prueba la nombra en vez de prohibir todo `https:`.
    """
    if not CADDY.exists():
        pytest.skip("no hay Caddyfile en esta copia")
    texto = CADDY.read_text(encoding="utf-8")
    linea = next((ln for ln in texto.splitlines() if "Content-Security-Policy" in ln), None)
    assert linea, "el Caddyfile no pone el CSP"
    assert "fonts.googleapis" not in linea and "fonts.gstatic" not in linea, (
        "vuelven a estar permitidas las fuentes de Google, y no las usa nadie")
    assert "script-src 'self'" in linea and "style-src 'self'" in linea, (
        "el codigo y los estilos tienen que ser del propio origen")
    assert "img-src 'self' https: data:" in linea, (
        "las fotos de las cadenas se enlazan desde sus CDN: img-src las tiene que admitir")
    assert "base-uri 'none'" in linea and "form-action 'self'" in linea, (
        "faltan los dos cierres: sin `<base>` y con los formularios al mismo origen")


def _sin_comentarios(texto: str) -> str:
    """Quita los comentarios de bloque y las lineas que son comentario entero.

    Hace falta porque la primera version de estas pruebas fallaba con el codigo
    BIEN: la interfaz dice en varios sitios "aqui no hay ningun boton de aprobar
    ni de rechazar", que es la regla escrita, y buscar la palabra a pelo la
    encontraba. No se quitan los `//` de dentro de una linea a proposito: eso
    romperia `http://localhost:8000`, que es justo lo que hay que detectar.
    """
    sin_bloques = re.sub(r"/\*.*?\*/", " ", texto, flags=re.S)
    return "\n".join(ln for ln in sin_bloques.splitlines()
                     if not ln.strip().startswith("//"))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_pide_la_api_por_rutas_relativas():
    """Un solo origen: nada de `http://localhost:8000`, que rompe Tailscale y CORS."""
    sospechosas = []
    for fichero in list((APP / "src").rglob("*.ts")) + list((APP / "src").rglob("*.tsx")):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        for mal in ("localhost:8000", "127.0.0.1:8000"):
            if mal in limpio:
                sospechosas.append(f"{fichero.name}: {mal}")
    assert not sospechosas, (
        f"la interfaz llama a la API por direccion absoluta ({sospechosas}). "
        f"Tiene que ser por rutas relativas `/api/...`: Caddy manda /api al "
        f"backend en el mismo origen. El proxy de desarrollo vive en "
        f"vite.config.ts, que es el unico sitio donde esa direccion vale.")


# --------------------------------------------------------------- colores ---
#
# Esta prueba existe por un fallo real, no por gusto. La interfaz usaba 27 veces
# seis colores con nombre (`text-tinta-suave`, `border-borde`, `bg-fondo`...) que
# NO estaban definidos en `tailwind.config.js`. Tailwind, cuando no reconoce una
# clase, no avisa: la omite. Asi que no habia error de compilacion, no habia
# aviso en el navegador, y media interfaz salia sin su color. Se descubrio
# buscando `tinta-suave` en el CSS construido y encontrando cero resultados.
#
# `tsc` y `vite build` no pueden ver esto: una clase desconocida es una cadena de
# texto perfectamente valida. Solo se ve comparando lo que se escribe con lo que
# el tema define, que es lo que hace esta prueba.

PALETAS = {
    "slate", "gray", "zinc", "neutral", "stone", "red", "orange", "amber",
    "yellow", "lime", "green", "emerald", "teal", "cyan", "sky", "blue",
    "indigo", "violet", "purple", "fuchsia", "pink", "rose",
}
CLAVES = {"transparent", "current", "inherit", "black", "white", "none", "auto"}
UTILIDADES = (
    "text", "bg", "border", "ring", "divide", "outline", "decoration", "fill",
    "stroke", "placeholder", "accent", "caret", "shadow", "from", "via", "to",
)
# Lo que no es un color aunque empiece como una utilidad de color: lados del
# borde, grosores, tamanos de letra, alineaciones, estilos de linea.
NO_ES_COLOR = {
    "x", "y", "t", "r", "b", "l", "s", "e",
    "solid", "dashed", "dotted", "double", "hidden", "collapse", "separate", "wavy",
    "xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl", "inner",
    "left", "center", "right", "justify", "start", "end",
    "wrap", "nowrap", "balance", "pretty", "ellipsis", "clip",
    "inset", "offset", "opacity", "gradient", "cover", "contain",
    "fixed", "local", "scroll", "repeat", "no-repeat", "auto",
    # *** Y lo que anadio la direccion visual del 15/10/2026. *** *
    #
    # **Esto no es una lista de conveniencia: es una colleccion de colisiones
    # reales.** *`text-` sirve para **color** y para **tamano**, *y `shadow-` para
    # **color de sombra** y para **tamano de sombra**.* *Asi que los seis tamanos
    # de letra y los tres niveles de profundidad **empiezan como una utilidad de
    # color y no lo son**, *y sin ponerlos aqui el test de colores los denunciaria
    # como «`titulo` no esta en el tema», *que es **cierto y no es el problema.** *
    #
    # *Y se comprueban donde toca: *los tamanos en
    # `test_las_escalas_que_se_escriben_existen`, *y los de sombra en la misma.*
    "antetitulo", "etiqueta", "cuerpo", "entrada", "titulo", "portada",
    "apoyado", "alzado", "flotante",
}


def _bloque_de_colores(texto: str) -> str:
    """El contenido de `colors: { ... }`, contando llaves para no cortar mal."""
    inicio = texto.find("colors:")
    if inicio == -1:
        return ""
    abre = texto.find("{", inicio)
    if abre == -1:
        return ""
    nivel = 0
    for i in range(abre, len(texto)):
        if texto[i] == "{":
            nivel += 1
        elif texto[i] == "}":
            nivel -= 1
            if nivel == 0:
                return texto[abre + 1:i]
    return ""


def _nombres_del_tema(texto_config: str) -> set[str]:
    """Los colores que el tema define, con los anidados como `padre-hijo`."""
    bloque = _bloque_de_colores(texto_config)
    nombres: set[str] = set()
    for padre, dentro in re.findall(r"([\w-]+)\s*:\s*\{([^}]*)\}", bloque):
        nombres.add(padre)
        for hijo in re.findall(r"([\w-]+)\s*:", dentro):
            nombres.add(f"{padre}-{hijo}")
    # Lo que queda fuera de los objetos anidados son colores planos.
    plano = re.sub(r"[\w-]+\s*:\s*\{[^}]*\}", " ", bloque)
    for nombre in re.findall(r"['\"]?([\w-]+)['\"]?\s*:", plano):
        nombres.add(nombre)
    return nombres


def _codigo(fichero: Path) -> list[str]:
    """Las lineas del fichero con los comentarios EN BLANCO, sin perder la numeracion.

    *Hace falta un ayudante propio y no `_sin_comentarios`: *aquel **quita las
    lineas enteras de comentario**, *y con ellas **se corre la numeracion** *-- *y
    entonces un aviso como «`Cabecera.tsx:52`» **señala otra linea.*** *
    *Aqui el comentario se sustituye por una linea vacia: *el numero sigue siendo
    el del fichero de verdad.* *
    """
    texto = fichero.read_text(encoding="utf-8")
    # *Un comentario de bloque se cambia por sus propios saltos de linea, *para no
    # mover nada de sitio.* *
    texto = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)
    return ["" if ln.strip().startswith("//") else ln for ln in texto.splitlines()]


def _clases_de_color(fichero: Path) -> list[tuple[int, str]]:
    """Las clases que usan una utilidad de color, con su numero de linea.

    *** Los comentarios se quitan, y no es un detalle. *** *Hasta el 15/10/2026 no
    se quitaban, *y **un comentario que explicaba justo lo que NO hay que hacer**
    *(-- «`bg-bosque/90` no se puede» --)* *** hacia fallar esta prueba.*** *O sea:
    *el test **prohibia documentar el error**, *que es lo contrario de lo que
    quiere.* *Y el fallo se descubrio porque **el comentario era mio** y el test
    me lo denuncio.* *
    """
    salida = []
    for numero, linea in enumerate(_codigo(fichero), 1):
        for palabra in re.findall(r"[A-Za-z0-9_\-:\[\]\./%#]+", linea):
            # `dark:hover:bg-neutral-700` -> `bg-neutral-700`.
            tras_variantes = palabra.rsplit(":", 1)[-1]
            for utilidad in UTILIDADES:
                if tras_variantes.startswith(f"{utilidad}-"):
                    salida.append((numero, tras_variantes[len(utilidad) + 1:]))
                    break
    return salida


def _motivo(resto: str, nombres: set[str], con_variable: set[str]) -> str | None:
    """Por que esta clase no es un color valido, o `None` si lo es."""
    # `bg-white/95` es blanco al 95 %: la opacidad se pega con una barra.
    base = re.sub(r"/(?:\d+|\[[^\]]*\])$", "", resto)
    if base != resto:
        if base in con_variable:
            # Tailwind resuelve la opacidad escribiendo `rgb(255 255 255 / 0.95)`,
            # y una variable con un `#rrggbb` dentro no vale ahi: saldria un color
            # invalido que el navegador ignora. Es el mismo fallo silencioso.
            return (f"`{resto}` pide opacidad sobre `{base}`, que es una variable "
                    f"de CSS: no se puede")
        return _motivo(base, nombres, con_variable)
    if base in CLAVES or base in nombres:
        return None
    primero = base.split("-")[0]
    if primero in PALETAS:
        return None
    if primero in NO_ES_COLOR or primero.isdigit() or primero.endswith("%"):
        return None
    if base.startswith("["):
        return None
    return f"`{base}` no esta en el tema"


def _nombres_con_variable(texto_config: str) -> set[str]:
    """Los colores del tema cuyo valor es una variable de CSS."""
    return set(re.findall(r"['\"]?([\w-]+)['\"]?\s*:\s*'var\(--[\w-]+\)'", texto_config)) | set(
        re.findall(r"([\w-]+)\s*:\s*'var\(--[\w-]+\)'", texto_config))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_colores_conocidos():
    """Toda clase de color que se escribe tiene que existir en el tema.

    Un color sin definir no da error: Tailwind lo omite y el estilo desaparece.
    """
    config = (APP / "tailwind.config.js").read_text(encoding="utf-8")
    nombres = _nombres_del_tema(config)
    con_variable = _nombres_con_variable(config)
    assert "tinta-suave" in nombres, (
        f"no he sabido leer los colores con nombre del tema: {sorted(nombres)}")
    assert "tinta-suave" in con_variable, (
        f"no he sabido leer que colores usan variable: {sorted(con_variable)}")

    fallos = []
    for fichero in sorted((APP / "src").rglob("*.tsx")) + sorted((APP / "src").rglob("*.ts")):
        if fichero.name.endswith(".d.ts"):
            continue
        for numero, resto in _clases_de_color(fichero):
            if (motivo := _motivo(resto, nombres, con_variable)) is not None:
                fallos.append(f"{fichero.name}:{numero}: {motivo}")
    assert not fallos, (
        "hay clases de color que el tema no define, asi que Tailwind las omite "
        "en silencio y el estilo no se aplica:\n  " + "\n  ".join(fallos) +
        "\nAnadelas a `theme.extend.colors` en tailwind.config.js (y sus valores "
        "en estilos.css, en los dos temas).")


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_los_colores_del_tema_tienen_valor_en_los_dos_temas():
    """Un color definido a medias es un color que no se ve de noche.

    Los nombres con significado se usan sin el prefijo `dark:` a proposito, asi
    que su valor tiene que cambiar solo. Si estan en el tema pero no en el CSS,
    la variable no existe y el color se cae: mismo fallo silencioso que arriba.
    """
    config = (APP / "tailwind.config.js").read_text(encoding="utf-8")
    css = (APP / "src" / "estilos.css").read_text(encoding="utf-8")
    variables = re.findall(r"['\"]?[\w-]+['\"]?\s*:\s*'var\((--[\w-]+)\)'", config)
    assert variables, "el tema no usa variables: revisa esta prueba"
    for variable in variables:
        definiciones = len(re.findall(rf"{variable}\s*:", css))
        assert definiciones >= 2, (
            f"`{variable}` tiene {definiciones} valor(es) en estilos.css: hace "
            f"falta uno para el tema claro y otro para el oscuro.")


# ------------------------------------------------- la interfaz y la API ---
#
# La prueba que compara lo que la interfaz PIDE con lo que la API OFRECE. Es la
# misma familia que las de arriba: el fallo no esta en el codigo, esta en dos
# sitios que tienen que decir lo mismo y que nadie compara.
#
# Una pantalla que llama a un endpoint que no existe **compila, arranca y se
# pinta**: TypeScript no sabe de rutas HTTP. El fallo aparece cuando alguien abre
# esa pantalla, que es la peor manera de enterarse. Y ha pasado: `/api/ean` y
# `/api/panel/matching` estaban escritos en el front antes de existir en la API.
#
# Ojo con lo que esta prueba NO comprueba: compara el front con el **codigo** de
# la API, no con la imagen que corre en Docker. Que el contenedor tenga la
# version vieja no lo ve esto, porque necesita importar la app. Eso se mira a
# mano con el contenedor levantado, y en `docs/BACKLOG.md` esta el comando y la
# matriz de rutas.

def _rutas_de_la_interfaz() -> list[tuple[str, str, int]]:
    """Las rutas que pide el front, con el fichero y la linea de cada una.

    Solo cuenta las llamadas con la ruta escrita a mano. Las que se construyen en
    una variable no se pueden comprobar leyendo, y no se inventan.

    Se miran los tres ayudantes que tiene el front, no solo el primero: `pide`
    (GET), `conCuerpo` (los favoritos) y `escribe` (la cesta). Los tres llevan la
    ruta en el primer argumento y los tres le pegan `/api` delante. Mirar solo
    `pide` dejaba fuera **todas** las escrituras, que son justo las que mas
    duelen si la ruta no existe: una pantalla que no puede leer algo se ve vacia,
    pero una que no puede guardar pierde lo que el usuario acaba de escribir.
    Las definiciones no cuelan: su primer argumento es `ruta: string`, sin
    comillas.
    """
    patrones = [rf"\b{ayudante}\b[^(]*\(\s*['\"`]"
                for ayudante in ("pide", "conCuerpo", "escribe")]
    patrones.append(r"\bfetch\(\s*['\"`]")
    salida: list[tuple[str, str, int]] = []
    for fichero in sorted((APP / "src").rglob("*.ts")):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        for patron in patrones:
            for trozo in re.finditer(patron, limpio):
                resto = limpio[trozo.end() - 1:]
                m = re.match(r"(['\"`])(.*?)\1", resto, re.S)
                if not m:
                    continue
                linea = limpio[:trozo.start()].count("\n") + 1
                salida.append((m.group(2), fichero.name, linea))
    return salida


def _normaliza(ruta: str) -> str:
    """Una ruta comparable: sin query y con los parametros como `{}`."""
    ruta = ruta.split("?")[0]
    ruta = re.sub(r"\$\{[^}]*\}", "{}", ruta)   # un parametro del front
    ruta = re.sub(r"\{[^}]*\}", "{}", ruta)     # un parametro de FastAPI
    return ruta.rstrip("/") or "/"


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_solo_llama_a_rutas_que_la_api_tiene():
    """Ni una ruta inventada: cada una que pide el front tiene que existir."""
    pytest.importorskip("fastapi", reason="falta el extra `plataforma`")
    from plataforma.api.main import app

    # Por el esquema y no por `app.routes`: la app monta sub-routers
    # (`plataforma.api.cesta`, `ajustes`...), y esos no tienen `.path`. El
    # esquema es lo que FastAPI publica de verdad, con las rutas ya resueltas.
    de_la_api = {_normaliza(ruta) for ruta in app.openapi().get("paths", {})}
    assert len(de_la_api) >= 20, (
        f"solo he sabido leer {len(de_la_api)} rutas de la API: revisa esta prueba")

    pedidas = _rutas_de_la_interfaz()
    assert len(pedidas) >= 10, (
        f"solo he sabido leer {len(pedidas)} rutas del front: revisa esta prueba")

    inventadas = []
    for ruta, fichero, linea in pedidas:
        # `new URL(`/api${ruta}`)`: eso es el ayudante que arma la ruta a partir
        # de un parametro, no una ruta. Esas se comprueban donde se llaman.
        if ruta.startswith("/api$") or "${" in ruta.split("/")[1]:
            continue
        completa = ruta if ruta.startswith("/api/") else f"/api{ruta}"
        if _normaliza(completa) not in de_la_api:
            inventadas.append(f"{fichero}:{linea}: {ruta}")
    assert not inventadas, (
        "la interfaz pide rutas que la API no tiene, y eso no se nota hasta que "
        "alguien abre esa pantalla:\n  " + "\n  ".join(sorted(set(inventadas))))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_interfaz_no_tiene_botones_de_validacion_humana():
    """La ley del encargo: no hay validacion humana, nunca.

    Se buscan **elementos de interfaz**, no palabras: la interfaz explica en
    varias pantallas que no hay botones de aprobar, y buscar la palabra a secas
    marcaba esa explicacion. Un boton es un `<button` o un `onClick`, asi que se
    exige que la palabra este cerca de uno de los dos.
    """
    prohibidas = ("aprobar", "rechazar", "validar equivalencia")
    encontradas = []
    for fichero in (APP / "src").rglob("*.tsx"):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        bajo = limpio.lower()
        for palabra in prohibidas:
            inicio = 0
            while (pos := bajo.find(palabra, inicio)) != -1:
                ventana = bajo[max(0, pos - 300):pos + 300]
                if "<button" in ventana or "onclick" in ventana:
                    encontradas.append(f"{fichero.name}: {palabra}")
                    break
                inicio = pos + 1
    assert not encontradas, (
        f"hay botones de validacion humana ({encontradas}). El encargo dice que "
        f"el matching es automatico y que nadie valida nada.")


# --------------------------------------------------------------- escalas ---
#
# **La misma familia que los colores, y el mismo fallo.** *Tailwind, cuando no
# reconoce una clase, **no avisa: la omite.** Asi que `rounded-tarjeta` con
# `tarjeta` sin definir **no da error**, no sale en la consola, y la tarjeta se
# pinta con las esquinas rectas.* *`tsc` y `vite build` tampoco lo ven: una clase
# desconocida es una cadena de texto perfectamente valida.*
#
# **Y esto es nuevo del 15/10/2026.** *Antes el tema tenia **paleta y una sola
# medida** (`maxWidth.app`), *asi que **cada pantalla se inventaba sus numeros***:
# *de ahi las 996 lineas de clases en linea y que dos tarjetas del mismo rango no
# se parecieran.* *Ahora hay escalas, *y esto comprueba que lo que se escribe esta
# en ellas.*
#
# **Lo que esta prueba NO comprueba, y se dice**: *las escalas de **espaciado** y
# de **ancho maximo**.* *Sus utilidades son **numericas** *(-- `p-4`, `gap-6`,
# `max-w-3xl` --)* *y su lista de valores por defecto es larga y abierta, *asi que
# una comprobacion por nombre daria **mas ruido que señal** *-- *y un test que
# grita en falso se acaba ignorando.* *Se revisan a ojo al migrar cada pantalla.*

# *Lo que Tailwind trae de serie.* **Sin esta lista la prueba seria ruido**: *cada
# `rounded-md` y cada `shadow-sm` que ya existen saldrian como fallo, *y el aviso
# bueno se perderia entre cientos de falsos.*
POR_DEFECTO = {
    "borderRadius": {"none", "sm", "", "md", "lg", "xl", "2xl", "3xl", "full"},
    "boxShadow": {"none", "sm", "", "md", "lg", "xl", "2xl", "inner"},
    "transitionDuration": {"0", "75", "100", "150", "200", "300", "500", "700", "1000"},
    "transitionTimingFunction": {"linear", "in", "out", "in-out"},
    "fontSize": {"xs", "sm", "base", "lg", "xl", "2xl", "3xl", "4xl", "5xl",
                 "6xl", "7xl", "8xl", "9xl"},
    # *** Y la de espaciado, *que FALTABA, y por eso el test no cazo un fallo real. *** *
    #
    # *El 15/10/2026 un script mio escribio `gap-space-y-4` -- una clase **que no
    # existe** -- *y esta prueba paso **limpia**.* *Y Tailwind **omite en silencio** las
    # clases que no conoce, *asi que ni `tsc` ni el `build` lo ven: *es **una cadena.*** *
    #
    # *El hueco tenia DOS partes y la primera vez solo vi una: *faltaba `spacing` en
    # `POR_DEFECTO` **y** los prefijos en `ESCALAS`.* *Sin la de aqui, el test ni
    # siquiera llegaba a mirar: *reventaba con `KeyError: 'spacing'` en la linea donde
    # se indexa esta tabla.* *
    #
    # *Y son **los nombres de fabrica de Tailwind**, *que en espaciado son numeros.* *
    "spacing": {"0", "px", "auto", "0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "5", "6",
                "7", "8", "9", "10", "11", "12", "14", "16", "20", "24", "28", "32",
                "36", "40", "44", "48", "52", "56", "60", "64", "72", "80", "96"},
}

# prefijo de la clase -> clave del tema donde tiene que estar
ESCALAS = {
    "rounded": "borderRadius",
    "shadow": "boxShadow",
    "duration": "transitionDuration",
    "ease": "transitionTimingFunction",
    # *Y las que **consumen la escala de espaciado**, *que es la que usa media
    # aplicacion.* *Con esto, `gap-space-y-4` **falla**, *que es lo que tenia que haber
    # hecho el 15/10/2026.* *
    # *`gap` NO va: *`gap-x-4` se parte por el primer guion en `gap` + `x-4`, *y `x-4`
    # no es un valor. *Un prefijo que da **falsos positivos** es peor que no tenerlo.* *
    "space-y": "spacing",
    "space-x": "spacing",
    "p": "spacing",
    "px": "spacing",
    "py": "spacing",
    "pt": "spacing",
    "pb": "spacing",
    "pl": "spacing",
    "pr": "spacing",
    "m": "spacing",
    "mx": "spacing",
    "my": "spacing",
    "mt": "spacing",
    "mb": "spacing",
}


def _bloque(texto: str, clave: str) -> str:
    """El contenido de `clave: { ... }`, contando llaves para no cortar mal."""
    inicio = texto.find(f"{clave}:")
    if inicio == -1:
        return ""
    abre = texto.find("{", inicio)
    if abre == -1:
        return ""
    nivel = 0
    for i in range(abre, len(texto)):
        if texto[i] == "{":
            nivel += 1
        elif texto[i] == "}":
            nivel -= 1
            if nivel == 0:
                return texto[abre + 1:i]
    return ""


def _nombres_de_escala(texto_config: str, clave: str) -> set[str]:
    """Los nombres de una escala del tema, a un solo nivel.

    *A un nivel porque estas escalas son planas* *(-- `nota: '4px'` --)*, *a
    diferencia de `colors`, que anida.*

    *** Y los comentarios se quitan ANTES, y no es un detalle. *** *La primera
    version de esto no los quitaba, *y **cayo sola**: *un comentario del config
    decia «*15 px y no **16**: ...*», *y la expresion regular leyo ese `16:` como
    **un tamano de letra llamado `16`**.* *Y el aviso era cierto y no hablaba del
    tema: *hablaba de que **estaba leyendo prosa.*** *
    """
    bloque = _bloque(_sin_comentarios(texto_config), clave)
    # *Se quitan los objetos anidados *(-- `antetitulo: ['0.68rem', { ... }]` --)*
    # para que el `lineHeight` de dentro no se cuele como un nombre mas.*
    plano = re.sub(r"\{[^{}]*\}", " ", bloque)
    return set(re.findall(r"['\"]?([\w-]+)['\"]?\s*:", plano))


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_las_escalas_que_se_escriben_existen():
    """Toda clase de una escala propia tiene que existir en el tema.

    *Un `rounded-tarjeta` mal escrito no da error: *Tailwind lo omite y la
    tarjeta sale con las esquinas rectas. *Es el mismo fallo silencioso que los
    colores, *y por eso se comprueba igual.*
    """
    config = (APP / "tailwind.config.js").read_text(encoding="utf-8")

    del_tema = {clave: _nombres_de_escala(config, clave) for clave in POR_DEFECTO}
    # *Si esto falla, es que la prueba ha dejado de leer el tema, no que el tema
    # este mal* *-- y una prueba que no lee nada y pasa es peor que ninguna.*
    assert del_tema["borderRadius"], "no he sabido leer `borderRadius` del tema"
    assert del_tema["boxShadow"], "no he sabido leer `boxShadow` del tema"
    assert del_tema["transitionDuration"], "no he sabido leer `transitionDuration`"
    assert "nota" in del_tema["borderRadius"], sorted(del_tema["borderRadius"])
    assert "apoyado" in del_tema["boxShadow"], sorted(del_tema["boxShadow"])

    fallos = []
    for fichero in sorted((APP / "src").rglob("*.tsx")) + sorted((APP / "src").rglob("*.ts")):
        if fichero.name.endswith(".d.ts"):
            continue
        for numero, linea in enumerate(_codigo(fichero), 1):
            for palabra in re.findall(r"[A-Za-z0-9_\-:\[\]\./%#]+", linea):
                # `dark:hover:shadow-alzado` -> `shadow-alzado`.
                utilidad = palabra.rsplit(":", 1)[-1]
                # *Un valor a medida se escribe entre corchetes y es legitimo.*
                if "[" in utilidad:
                    continue
                for prefijo, clave in ESCALAS.items():
                    if not utilidad.startswith(f"{prefijo}-"):
                        continue
                    resto = utilidad[len(prefijo) + 1:]
                    if resto in del_tema[clave] or resto in POR_DEFECTO[clave]:
                        break
                    fallos.append(
                        f"{fichero.name}:{numero}: `{utilidad}` no esta en "
                        f"`{clave}` del tema")
                    break

    assert not fallos, (
        "hay clases de una escala que el tema no define, asi que Tailwind las "
        "omite en silencio y el estilo no se aplica:\n  " + "\n  ".join(fallos) +
        "\nAnadelas a `theme.extend` en tailwind.config.js, y su motivo en "
        "docs/ui/DIRECCION.md.")


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_las_escalas_que_se_usan_tienen_tamano_de_letra_conocido():
    """*Un `text-` es color **o** tamano, y hay que saber cual.*

    *`text-titulo` no es un color: *es un tamano de letra.* *Y el test de colores
    no puede distinguirlo solo* *-- por eso los seis nombres estan en
    `NO_ES_COLOR` --, *asi que aqui se comprueba **la otra mitad**: que un `text-`
    que no es color, *o es un tamano **del tema**, *o es uno de los de Tailwind,
    *o no es un tamano y entonces lo dira el test de colores.*
    """
    config = (APP / "tailwind.config.js").read_text(encoding="utf-8")
    tamanos = _nombres_de_escala(config, "fontSize")
    assert tamanos, "no he sabido leer `fontSize` del tema"
    for esperado in ("cuerpo", "titulo", "portada"):
        assert esperado in tamanos, sorted(tamanos)

    # *Y los seis del tema tienen que estar en `NO_ES_COLOR`.* *Si alguien anade
    # un tamano y se olvida de la lista, el test de colores empezaria a fallar con
    # un mensaje que no habla de esto* *-- y se perderia media tarde.*
    faltan = sorted(t for t in tamanos
                    if t not in NO_ES_COLOR and t not in POR_DEFECTO["fontSize"])
    assert not faltan, (
        f"estos tamanos de letra del tema no estan en `NO_ES_COLOR`, asi que el "
        f"test de colores los leera como colores y fallara sin decir por que: "
        f"{faltan}")


# ------------------------------------------- la paleta de fabrica, que no crezca ---
#
# **La causa de que la app pareciera generica TENIENDO componentes**, medida el
# 15/10/2026: **611 clases usaban la paleta de Tailwind** *(-- `neutral` 355,
# `sky` 113, `amber` 50, `emerald` 47, `red` 42 --)* *y **398 la propia**.* *O sea,
# **mas de la mitad pintada de fabrica.** *
#
# *Y el test de colores **no lo ve**, *porque `neutral`, `sky`, `amber`, `red` y
# `emerald` estan en `PALETAS`* *-- la lista de «esto es un color de Tailwind y es
# legitimo» --.* *Asi que el fallo pasaba **con el test en verde.** *
#
# *** Por que un trinquete y no una regla. *** *Prohibirlas de golpe dejaria 495
# fallos y **nadie podria trabajar**; *pero dejarlas crecer **sin limite** es como
# se llego aqui.* *Asi que el numero **solo puede bajar**: *se migra una pantalla,
# **se baja el numero a mano en el mismo commit**, *y **el test impide que suba.** *
#
# *Es la misma idea que el test de rutas: *compara **dos sitios que tienen que
# decir lo mismo** *y que nadie compara.* *

# *El censo del 15/10/2026, **sin contar los comentarios** *-- *que citan las
# clases viejas a proposito, *para que se lea que se cambio y por que --.* *
# *Los que mas tienen son las pantallas grandes: *`Panel` 66, *`Grupo` 52,
# `Inicio` 42, *`RepartoEnTiendas` 34, *`FiltrosBusqueda` 32.* *
PALETA_DE_FABRICA_HOY = 9
#
# *** 15/10/2026 -- de 611 a 43. *** *El censo de la paleta de fabrica bajo un **93 %**
# en el dia: *611 al empezar, *495 con las piezas, *463 con la navegacion, *421 y 357 con
# las pantallas grandes, *195 con el segundo bloque, *y **43 con el resto.** *
#
# *Y las 43 que quedan son **justo las que se dejan a proposito**: *
#   *-- *** las cinco con OPACIDAD *** *(-- `bg-neutral-800/60`, `/800/95`, `/900/40`,
#      `bg-amber-950/30` y `bg-amber-50/50` --), *que necesitan **tokens de canal con
#      `alpha-value`** *y eso es **una decision**, no un reemplazo:* *la opacidad sobre una
#      variable **no vale** ✓
#   *-- *y **los dos ficheros MUERTOS** *(-- `Cabecera.tsx` y `paginas/Inicio.tsx` --),
#      *que **no se migran** porque **no se pintan**: *esta en
#      `docs/ui/LOS-FICHEROS-MUERTOS.md` ✓✓✓
#
# *Asi que este numero **ya no puede bajar mucho mas** sin las dos decisiones de arriba.*
# *Y eso es exactamente lo que un trinquete tiene que decir.* *

# *15/10/2026, FASE 5 (4): *bajo de **357 a 195** *al migrar el segundo bloque:*
# *Panel.tsx (143), Grupo.tsx (100), RepartoEnTiendas.tsx (76) y Producto.tsx (65).*
# *Y el script conservo el fin de linea de cada uno: *Panel y Producto en LF, *Grupo
# y RepartoEnTiendas en CRLF.* *Quedan las pantallas pequenas.* *
# *15/10/2026, FASE 5 (3): *bajo de **421 a 357** *al migrar el **flujo de busqueda***
# *(-- `Buscar.tsx`, `FiltrosBusqueda.tsx` y `TablaResultados.tsx`, *132 clases --), *que es
# la primera pantalla de Compra.* *Lo pidio el trinquete otra vez.* *Quedan sobre todo*
# `Panel` y `Grupo`.* *
# *15/10/2026, FASE 5 (1): *bajo de **463 a 421** *al migrar* `Inicio.tsx` *(-- *la
# pantalla real de Compra, *64 clases --).* *Y lo pidio el propio trinquete: «has bajado
# a 421 y el suelo sigue alto».* *Quedan sobre todo* `Panel` 66, *`Grupo` 52 y*
# `RepartoEnTiendas` 34.* *
# *15/10/2026, FASE 3: *bajo de **495 a 463** *al migrar la navegacion* *(-- `Nav.tsx` y
# `Cabecera.tsx`, *58 clases --).* *El techo **solo baja**, *y lo recuerda la propia
# prueba cuando te olvidas.* *Los que mas quedan son las pantallas grandes: *`Panel` 66,
# `Grupo` 52, *`Inicio` 42.* *

_PALETA = ("slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|"
           "teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose")
_PALETA_DE_FABRICA = re.compile(
    rf"\b(?:bg|text|border|ring|from|to|via|divide|outline|decoration|fill|stroke|"
    rf"placeholder|accent|caret|shadow)-(?:{_PALETA})-")


@pytest.mark.skipif(not APP.exists(), reason="esta copia no trae la interfaz nueva")
def test_la_paleta_de_fabrica_no_crece():
    """Las clases de la paleta de Tailwind solo pueden **bajar**.

    *Un color de fabrica no es un error de sintaxis: *pinta, *y por eso se queda.*
    *Y son los que hacen que la app **no tenga estilo propio** *aunque tenga
    componentes, *porque **los grises y los azules son los de Tailwind y no los de
    la casa.*** *

    *Al migrar una pantalla, **baja el numero de `PALETA_DE_FABRICA_HOY`** en el
    mismo commit.* *Si este test falla, es que has **anadido** color de fabrica:
    *mira `docs/ui/DIRECCION.md` y usa un token.* *
    """
    cuenta = 0
    peores: list[tuple[int, str]] = []
    for fichero in (sorted((APP / "src").rglob("*.tsx"))
                    + sorted((APP / "src").rglob("*.ts"))
                    + sorted((APP / "src").rglob("*.css"))):
        limpio = _sin_comentarios(fichero.read_text(encoding="utf-8"))
        # *Y los comentarios de CSS, *que `_sin_comentarios` ya quita.* *
        n = len(_PALETA_DE_FABRICA.findall(limpio))
        if n:
            cuenta += n
            peores.append((n, fichero.name))

    peores.sort(reverse=True)
    detalle = ", ".join(f"{n} en {nombre}" for n, nombre in peores[:6])
    assert cuenta <= PALETA_DE_FABRICA_HOY, (
        f"hay {cuenta} clases de la paleta de Tailwind y el maximo acordado es "
        f"{PALETA_DE_FABRICA_HOY}: **has anadido color de fabrica.**\n"
        f"Los que mas tienen: {detalle}.\n"
        f"Usa los tokens de `docs/ui/DIRECCION.md` (marfil, papel, papel-alto, "
        f"bosque, terracota, tinta-fuerte, secundaria, borde, borde-fuerte, error, "
        f"aviso, bien) en vez de `neutral`, `sky`, `amber`, `red` o `emerald`.")

    # *Y tambien al reves: *si has migrado y no has bajado el numero, *el trinquete
    # se queda flojo y deja de apretar.* *
    if cuenta < PALETA_DE_FABRICA_HOY - 25:
        pytest.fail(
            f"has bajado a {cuenta} clases de fabrica (de {PALETA_DE_FABRICA_HOY}) "
            f"y el suelo sigue alto. **Baja `PALETA_DE_FABRICA_HOY` a {cuenta}** en "
            f"este mismo commit, que para eso es un trinquete.")

