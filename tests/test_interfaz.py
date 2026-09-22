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


def _clases_de_color(fichero: Path) -> list[tuple[int, str]]:
    """Las clases que usan una utilidad de color, con su numero de linea."""
    salida = []
    for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
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
