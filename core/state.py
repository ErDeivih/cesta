"""Extraer el objeto JSON que las webs SSR incrustan en el HTML.

Tres de las cuatro cadenas (Carrefour, DIA, Alcampo) sirven todos los productos
dentro del HTML. No hace falta navegador: basta con recortar el objeto y parsearlo.
"""
from __future__ import annotations

import json
import re


def js_object(html: str, var_name: str) -> dict:
    """Recorta `window.<var_name> = {...}` contando llaves (respeta strings).

    Un regex no vale: el objeto contiene llaves dentro de cadenas de texto.
    """
    i = html.find(var_name)
    if i < 0:
        raise ValueError(f"no encontrado: {var_name}")
    start = html.index("{", i)
    depth = 0
    in_str = False
    esc = False
    for j in range(start, len(html)):
        c = html[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start:j + 1])
    raise ValueError(f"objeto sin cerrar: {var_name}")


_SCRIPT = r'<script[^>]*id="{}"[^>]*>(.*?)</script>'


def json_script(html: str, element_id: str) -> dict:
    """Lee un <script type="application/json" id="..."> (patron de DIA/Vike)."""
    m = re.search(_SCRIPT.format(re.escape(element_id)), html, re.DOTALL)
    if not m:
        raise ValueError(f"no encontrado: script#{element_id}")
    return json.loads(m.group(1))


def to_cents(value) -> int | None:
    """'0,95 €' | '19.95' | 1.85 -> centimos enteros. Nunca floats para dinero."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return round(float(value) * 100)
    s = str(value).replace("€", "").replace("EUR", "").strip()
    s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return round(float(s) * 100)
    except ValueError:
        return None
