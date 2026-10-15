"""*** La paleta de fabrica, *a los tokens de la casa. *** *

*Es el trabajo de la FASE 5, *y va **por pantallas**, *no de golpe: *se le pasan los
ficheros y los migra.* *Y **conserva el fin de linea de cada uno**, *que es la leccion
de las dos rondas en que lo hice mal: *`newline` **no conserva, impone.*** *

*El mapa completo, *con el porque de cada regla: *

  *-- *`neutral` **son los grises**, *y `neutral-100/200/300` y `neutral-600/700` son
     **el mismo borde** en tema claro y en oscuro.* *El token **`borde`** ya cambia
     solo con el tema, *asi que **los dos van al mismo sitio** *-- *que es
     precisamente para lo que existe el token.* *
  *-- *`neutral-500` es **el gris de un control**, *y ese va a **`borde-fuerte`**:
     *el suave da **1,43:1** *y **no vale para delimitar** *-- lo dice `estilos.css`
     con su numero.* *
  *-- *`sky` **no esta en la direccion.** *El acento es **`terracota`**, *y `bosque`
     es la accion.* *
  *-- *`emerald` / `amber` / `red` **ya tienen nombre en esta casa**: *`bien`, *`aviso`
     y *`error`.* *Y colapsar tres tonos de esmeralda en `bien` **no pierde nada**,
     porque el token **ya es distinto en cada tema** *-- *que era lo que los tres
     tonos estaban imitando a mano.* *
  *-- *Y **las tres con opacidad NO se tocan**: *`bg-neutral-900/40` *(-- el velo del
     dialogo --)*, *`bg-neutral-800/60` y *`bg-neutral-800/95`.* *La opacidad **sobre
     una variable no vale** *-- Tailwind escribe `rgb(var(--x) / .4)` *y ahi dentro hay
     un `#rrggbb`, *o sea un color invalido --.* *Esos tres son **el caso que
     `DIRECCION.md` deja escrito**: *hacen falta **tokens de canal** con
     `<alpha-value>`, *y **eso es una decision, no un reemplazo.*** *

Uso:  `uv run python scripts/ui_a_tokens.py <fichero> [<fichero> ...]`
      `uv run python scripts/ui_a_tokens.py --seco <fichero>`   (solo cuenta)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# *El orden IMPORTA: *lo mas especifico primero*, *y **las que llevan opacidad se
# saltan antes de que las pille el nombre a secas** *-- *que fue el destrozo de la
# cabecera en la FASE 3: *dejo un `/95` suelto.* *
NO_SE_TOCAN = (
    "bg-neutral-900/40", "bg-neutral-800/60", "bg-neutral-800/95",
)

MAPA: list[tuple[str, str]] = [
    # --- el acento, que era azul -------------------------------------------------
    ("bg-sky-700", "bg-terracota"),
    ("bg-sky-800", "bg-terracota"),
    ("bg-sky-500", "bg-terracota"),
    ("hover:bg-sky-700", "hover:brightness-110"),
    ("text-sky-900", "text-terracota"),
    ("text-sky-800", "text-terracota"),
    ("text-sky-700", "text-terracota"),
    ("text-sky-400", "text-terracota"),
    ("text-sky-300", "text-terracota"),
    ("text-sky-100", "text-marfil"),
    ("text-sky-950", "text-tinta-fuerte"),
    ("border-sky-700", "border-terracota"),
    ("border-sky-500", "border-terracota"),
    ("border-sky-400", "border-borde-fuerte"),
    ("bg-sky-100", "bg-terracota-suave"),
    ("bg-sky-50", "bg-marfil"),
    ("bg-sky-950", "bg-marfil"),
    ("accent-sky-700", "accent-terracota"),
    ("accent-sky-500", "accent-terracota"),
    # --- lo que significa algo ---------------------------------------------------
    ("bg-emerald-600", "bg-bien"),
    ("bg-emerald-500", "bg-bien"),
    ("bg-emerald-100", "bg-bien-suave"),
    ("bg-emerald-800", "bg-bien"),
    ("text-emerald-800", "text-bien"),
    ("text-emerald-700", "text-bien"),
    ("text-emerald-400", "text-bien"),
    ("text-emerald-300", "text-bien"),
    ("border-emerald-700", "border-bien"),
    ("border-emerald-500", "border-bien"),
    ("bg-amber-400", "bg-aviso"),
    ("bg-amber-100", "bg-marfil"),
    ("bg-amber-50", "bg-marfil"),
    ("bg-amber-950", "bg-marfil"),
    ("text-amber-950", "text-aviso"),
    ("text-amber-800", "text-aviso"),
    ("text-amber-700", "text-aviso"),
    ("text-amber-400", "text-aviso"),
    ("text-amber-300", "text-aviso"),
    ("text-amber-100", "text-aviso"),
    ("border-amber-800", "border-aviso"),
    ("border-amber-300", "border-aviso"),
    ("bg-red-600", "bg-error"),
    ("bg-red-500", "bg-error"),
    ("bg-red-100", "bg-marfil"),
    ("bg-red-50", "bg-marfil"),
    ("bg-red-950", "bg-marfil"),
    ("bg-red-800", "bg-error"),
    ("text-red-950", "text-error"),
    ("text-red-800", "text-error"),
    ("text-red-700", "text-error"),
    ("text-red-400", "text-error"),
    ("text-red-300", "text-error"),
    ("text-red-100", "text-error"),
    ("border-red-800", "border-error"),
    ("border-red-300", "border-error"),
    # --- y los grises, que son la mayoria ---------------------------------------
    # *Primero los que son un CONTROL, *que van al borde fuerte.* *
    ("divide-neutral-800", "divide-borde"),
    ("divide-neutral-700", "divide-borde"),
    ("divide-neutral-200", "divide-borde"),
    ("divide-neutral-100", "divide-borde"),
    ("border-neutral-600", "border-borde"),
    ("border-neutral-700", "border-borde"),
    ("border-neutral-500", "border-borde-fuerte"),
    ("border-neutral-300", "border-borde"),
    ("border-neutral-200", "border-borde"),
    ("border-neutral-100", "border-borde"),
    ("stroke-neutral-700", "stroke-borde"),
    ("stroke-neutral-500", "stroke-borde-fuerte"),
    ("stroke-neutral-400", "stroke-secundaria"),
    ("stroke-neutral-200", "stroke-borde"),
    # *Superficies.* *
    ("bg-neutral-50", "bg-marfil"),
    ("bg-neutral-100", "bg-marfil"),
    ("bg-neutral-200", "bg-borde"),
    ("bg-neutral-300", "bg-borde"),
    ("bg-neutral-400", "bg-borde-fuerte"),
    ("bg-neutral-600", "bg-secundaria"),
    ("bg-neutral-700", "bg-papel"),
    ("bg-neutral-800", "bg-papel"),
    ("bg-neutral-900", "bg-papel"),
    # *Y el texto, *de mas fuerte a mas suave.* *
    ("text-neutral-100", "text-tinta-fuerte"),
    ("text-neutral-200", "text-tinta-fuerte"),
    ("text-neutral-800", "text-tinta-fuerte"),
    ("text-neutral-900", "text-tinta-fuerte"),
    ("text-neutral-300", "text-secundaria"),
    ("text-neutral-400", "text-secundaria"),
    ("text-neutral-500", "text-secundaria"),
    ("text-neutral-600", "text-secundaria"),
    ("text-neutral-700", "text-secundaria"),
    # *Y los tamanos y radios de fabrica, *que son la otra mitad del problema.* *
    ("text-xs", "text-etiqueta"),
    ("text-sm", "text-cuerpo"),
    ("text-base", "text-entrada"),
    ("rounded-md", "rounded-campo"),
    ("rounded-lg", "rounded-campo"),
    ("rounded-xl", "rounded-tarjeta"),
    ("rounded-2xl", "rounded-tarjeta"),
]

# *Y los `dark:` que sobran: *los tokens **son** variables que cambian solas.* *
# *Con frontera de palabra, *no `\\S*`* *-- *que se comio una comilla en la FASE 3.* *
FUERA_DARK = re.compile(
    r"dark:(?:bg|text|border|ring|divide|fill|stroke|accent|shadow|placeholder)-"
    r"(?:marfil|papel|papel-alto|bosque|terracota-suave|terracota|tinta-fuerte|tinta-suave|"
    r"secundaria|borde-fuerte|borde|error|aviso|bien-suave|bien|fondo)"
    r"(?![\w-])\s?")


def es_comentario(linea: str) -> bool:
    t = linea.strip()
    return t.startswith(("//", "*", "/*", "/**"))


def migra(ruta: Path, seco: bool) -> tuple[int, bool]:
    datos = ruta.read_bytes()
    tenia_crlf = b"\r\n" in datos
    texto = datos.decode("utf-8").replace("\r\n", "\n")
    antes = texto
    n = 0

    salida = []
    for linea in texto.splitlines():
        if es_comentario(linea):
            salida.append(linea)
            continue
        nueva = linea
        for viejo, nuevo in MAPA:
            # *Las de opacidad se saltan: *`(?![\w-])` no basta, *porque `/` no es
            # palabra* *-- *asi que se comprueba a mano.* *
            if any(viejo in salto or viejo + "/" in linea for salto in NO_SE_TOCAN):
                continue
            patron = rf"(?<![\w/-]){re.escape(viejo)}(?![\w-])"
            nueva, k = re.subn(patron, nuevo, nueva)
            n += k
        nueva, k = FUERA_DARK.subn("", nueva)
        n += k
        salida.append(nueva.rstrip() if linea.rstrip() != linea else nueva)

    texto = "\n".join(salida)
    if texto == antes:
        return 0, tenia_crlf
    if not seco:
        b = texto.encode("utf-8")
        if tenia_crlf:
            b = b.replace(b"\n", b"\r\n")
        ruta.write_bytes(b)
    return n, tenia_crlf


def main(argv: list[str]) -> int:
    seco = "--seco" in argv
    objetivos = [a for a in argv if not a.startswith("--")]
    if not objetivos:
        print(__doc__)
        return 1
    total = 0
    for nombre in objetivos:
        ruta = Path(nombre)
        if not ruta.is_absolute():
            ruta = RAIZ / "plataforma" / "web" / "app" / nombre
        n, crlf = migra(ruta, seco)
        total += n
        print(f"  {ruta.name:26} {n:>4} clases   "
              f"fin de linea {'CRLF' if crlf else 'LF'}"
              f"{'   (SECO)' if seco else ''}")
    print(f"  TOTAL: {total} clases{'  (no se ha escrito nada)' if seco else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
