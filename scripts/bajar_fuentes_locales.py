"""*** Se baja las fuentes a local, *y genera su `@font-face`. *** *

*Por que existe esto, *y por que no se sirven desde Google: *

*La app **se sirve desde casa**, *y el 15/10/2026 se midio que las fuentes declaradas
*-- **Fraunces** y **IBM Plex Sans** -- **no se servian**: *la captura
`docs/ui/capturas/01-inicio.png` ensena los titulos en **Georgia**, *que es el respaldo que
el propio `tailwind.config.js` tenia escrito con un comentario admitiendolo.* *

*Y **no se enlazan desde `fonts.googleapis.com`** aunque sea lo comodo: *eso mete un tercero
en **la primera pintada de una app de casa**, *y ademas la deja sin tipografia cuando no hay
red* *-- que es justo cuando mas falta hace que la lista de la compra se lea bien.* *

*** Por que solo el subset `latin`. *** *Google parte cada familia en trozos *(-- latin,
latin-ext, cyrillic, greek, vietnamese... --)* *y sirve **nueve ficheros por familia**.*
*El **castellano entero cabe en `latin`** *(-- `U+0000-00FF`: *incluye `á é í ó ú ñ ¿ ¡` --)*,
*asi que bajarse los otros ocho es **triplicar el peso para nada.*** *

*** Y la licencia NO se ignora. *** *Las dos familias son **OFL-1.1**, *que permite
**empotrar y redistribuir** *a cambio de **conservar el aviso de copyright y la licencia**.*
*Por eso se baja tambien el texto de la OFL de cada familia y se deja junto a los ficheros:
*sin el, **redistribuir estas fuentes no esta permitido.*** *

Uso:  `uv run python scripts/bajar_fuentes_locales.py`
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "plataforma" / "web" / "app" / "public" / "fuentes"
# *El `@font-face` va a `src/` *(-- no a `public/` --)* para que Vite lo procese y se
# pueda importar ANTES que la app: *asi la fuente se pide en la primera pintada.* *Los
# `.woff2` si van a `public/`, *que es lo que se sirve tal cual.*
HOJA = RAIZ / "plataforma" / "web" / "app" / "src" / "fuentes.css"

# *El user-agent importa: **con uno viejo Google devuelve TTF**, *y queremos WOFF2.*
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

CSS = ("https://fonts.googleapis.com/css2"
       "?family=Fraunces:opsz,wght@9..144,600"
       "&family=IBM+Plex+Sans:wght@400;500;600"
       "&display=swap")

# *Y la OFL, que es la condicion para poder redistribuirlas.*
LICENCIAS = {
    "fraunces": "https://raw.githubusercontent.com/google/fonts/main/ofl/fraunces/OFL.txt",
    "ibmplexsans": "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexsans/OFL.txt",
}


def _trae(url: str) -> bytes:
    peticion = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(peticion, timeout=30) as r:
        return r.read()


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    print(f"  destino: {DESTINO.relative_to(RAIZ)}")

    hoja = _trae(CSS).decode("utf-8")
    # *Cada bloque lleva delante un comentario con su subset:*
    #   `/* latin */ @font-face { ... }`
    bloques = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", hoja, re.S)
    print(f"  bloques en la hoja: {len(bloques)}")

    elegidos = [b for b in bloques if b[0] == "latin"]
    print(f"  del subset `latin`: {len(elegidos)}")

    # *** Y AQUI ESTA LO QUE NO SE ESPERABA. *** *
    #
    # *Google **sirve la fuente variable** en los tres pesos de IBM Plex Sans: *se
    # bajaron 400, 500 y 600, *y los tres pesaban **45.712 bytes** y tenian **el
    # mismo SHA-256**.* *O sea: **el mismo fichero tres veces**, *y declararlo tres
    # veces serian **tres descargas del mismo binario** por parte del navegador.* *
    #
    # *Asi que se **agrupa por contenido** *(-- por huella, no por peso --)* *y se
    # declara **una vez con el rango**: `font-weight: 400 600`.* *Que es, *ademas,
    # **como se declara una fuente variable.*** *
    import hashlib

    por_huella: dict[str, dict] = {}
    for _, cuerpo in elegidos:
        familia = re.search(r"font-family:\s*'([^']+)'", cuerpo)
        peso = re.search(r"font-weight:\s*(\d+)", cuerpo)
        estilo = re.search(r"font-style:\s*(\w+)", cuerpo)
        rango = re.search(r"unicode-range:\s*([^;]+);", cuerpo)
        url = re.search(r"url\((https://[^)]+\.woff2)\)", cuerpo)
        if not all((familia, peso, url)):
            continue
        datos = _trae(url.group(1))
        huella = hashlib.sha256(datos).hexdigest()
        entrada = por_huella.setdefault(huella, {
            "familia": familia.group(1), "estilo": estilo.group(1) if estilo else "normal",
            "rango": rango.group(1).strip() if rango else None,
            "datos": datos, "pesos": set()})
        entrada["pesos"].add(int(peso.group(1)))

    reglas: list[str] = []
    for e in sorted(por_huella.values(), key=lambda x: x["familia"]):
        pesos = sorted(e["pesos"])
        # *Si la misma huella sirve a varios pesos, es **una fuente variable**.* *
        etiqueta = f"{pesos[0]}-{pesos[-1]}" if len(pesos) > 1 else str(pesos[0])
        declarado = f"{pesos[0]} {pesos[-1]}" if len(pesos) > 1 else str(pesos[0])
        nombre = f"{e['familia'].replace(' ', '')}-{etiqueta}.woff2"
        (DESTINO / nombre).write_bytes(e["datos"])
        print(f"    {nombre:34} {len(e['datos']):>7} bytes   peso {declarado}"
              + ("   <- variable" if len(pesos) > 1 else ""))
        reglas.append(
            f"@font-face {{\n"
            f"  font-family: '{e['familia']}';\n"
            f"  font-style: {e['estilo']};\n"
            f"  font-weight: {declarado};\n"
            f"  font-display: swap;\n"
            f"  src: url('/fuentes/{nombre}') format('woff2');\n"
            + (f"  unicode-range: {e['rango']};\n" if e["rango"] else "")
            + "}\n")

    for clave, url in LICENCIAS.items():
        try:
            texto = _trae(url).decode("utf-8", "replace")
        except (OSError, urllib.error.URLError) as error:
            # *La licencia no puede fallar en silencio: sin ella no se pueden redistribuir.*
            print(f"  FALLO bajando la licencia de {clave}: {error}", file=sys.stderr)
            return 1
        (DESTINO / f"OFL-{clave}.txt").write_text(texto, encoding="utf-8")
        print(f"    OFL-{clave}.txt  {len(texto)} bytes")

    HOJA.write_text(
        "/* *** GENERADO por scripts/bajar_fuentes_locales.py -- no editar a mano. *** *\n"
        " *\n"
        " * Las fuentes se sirven DESDE AQUI y no desde fonts.googleapis.com: la app se sirve\n"
        " * desde casa y la primera pintada no puede depender de un tercero ni de que haya red.\n"
        " * Y son OFL-1.1: el aviso de licencia esta en los OFL-*.txt de esta misma carpeta.\n"
        " */\n\n" + "\n".join(reglas),
        encoding="utf-8")
    print(f"  @font-face escritas: {len(reglas)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
