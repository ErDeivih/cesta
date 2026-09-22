"""Los certificados oficiales que una cadena cuelga de un producto.

Que es esto y por que no esta dentro de `sellos`
------------------------------------------------
`core/sellos.py` traduce las etiquetas *dieteticas* que escribe cada cadena
("Sin Gluten", "Bio", "Alternativa Vegetal") a un vocabulario unico. Esto es
otra cosa: son **certificaciones de terceros**, con su organismo detras y su
auditoria, que la cadena publica como un logotipo junto a la ficha. DOP, IGP,
MSC, Fairtrade, Rainforest Alliance, Bienestar Animal AENOR, FSC, Oeko-Tex.

Se guardan aparte de los sellos a proposito. Un sello responde a "¿puedo
comerlo?" y filtra una compra; un certificado responde a "¿de donde sale y como
se hizo?" y ordena una comparacion entre dos productos que ya valen los dos.
Mezclarlos haria que el filtro "ecologico" devolviera camisetas de algodon
organico, que es justo el error que la OCU le reprocha a las apps de la
competencia: dar alternativas de otra categoria.

El hallazgo (17 de septiembre de 2026)
--------------------------------------
Durante once dias leiamos `assets` de Aldi para sacar **solo la foto**:

    imagen = next(a["url"] for a in assets if a["type"] == "primary")

y tirabamos los otros dos tipos. Uno de ellos, `certificate`, aparece en 1.106
de los 2.065 productos de Aldi (53,6 %) y trae **32 certificados distintos**.
No es texto libre: es un catalogo cerrado de imagenes con nombre estable, o sea
el dato mas limpio que da Aldi y el unico que da sobre origen.

De ahi salen, medido hoy sobre la captura del dia:

    sin-gluten     181      origen nacional   205     marca propia   63
    vegano         129      Rainforest        124     comercio justo 59
    sin-lactosa    108      ecologico          52     pesca MSC/ASC  27
    vegetariano      8      bienestar animal   25     DOP/IGP/ETG    19

Los 205 de origen importan mas de lo que parece: el 5 de septiembre se midio que
el origen tenia un techo del 3,7 % del catalogo (~1.900 de 51.781) y se dio por
imposible el filtro "producto espanol". Aldi no publica origen en ningun campo
de texto; lo publica **en este logotipo**. No arregla el techo, pero lo sube, y
sobre todo demuestra que el dato existe donde no lo buscabamos.

Aviso sobre el 1,7 % que no se traduce
--------------------------------------
Cuatro nombres de fichero son el nombre por defecto de Illustrator: "Mesa de
trabajo 1", "Mesa de trabajo 3", "ES Portrait (1)", "ES Landscape (1)" (36
productos). Alguien subio el logo sin renombrarlo. No se adivinan: se cuentan en
`sin_traducir()` para que salgan en la auditoria el dia que Aldi los arregle o
aparezca uno nuevo.
"""
from __future__ import annotations

import re

# Certificado -> (sello dietetico que implica, certificado nuestro, origen).
# Los tres campos son opcionales. Que un certificado NO ponga sello es una
# decision, no un olvido: Natrue certifica cosmetica natural y Oeko-Tex tejidos,
# y ninguno de los dos significa que algo sea ecologico en el sentido del
# Reglamento (UE) 2018/848, que es lo que la gente entiende al filtrar por "eco".
# OJO: las claves van en su forma ya limpia por `_clave()`, es decir sin
# _color, _rgb, sin el ano y sin los milimetros. Si se anade una tal como
# viene en la URL, no casara nunca; el test de ida y vuelta lo detecta.
_CATALOGO: dict[str, tuple[str | None, str | None, str | None]] = {
    # --- origen -----------------------------------------------------------
    "01_a_origen_nacional":  (None, "origen-espana", "España"),
    "01_b_carne_nacional":   (None, "origen-espana", "España"),
    # --- dieteticos -------------------------------------------------------
    "07_sin_gluten":         ("sin-gluten", "feacab", None),
    "48_adilac":             ("sin-lactosa", "adilac", None),
    "v-label_vegano":        ("vegano", "v-label", None),
    "vegantm-palette1-leafygreen": ("vegano", "vegan-trademark", None),
    "v-label_vegetariano":   ("vegetariano", "v-label", None),
    # --- ecologico de verdad (Reglamento europeo) -------------------------
    "eu_organic_logo_colour_outerline": ("ecologico", "eurohoja", None),
    # --- calidad diferenciada --------------------------------------------
    "43_dop":                (None, "dop", None),
    "44_igp":                (None, "igp", None),
    "45_etg":                (None, "etg", None),
    # --- pesca y acuicultura ---------------------------------------------
    "msc":                   (None, "msc", None),
    "42_asc":                (None, "asc", None),
    # --- comercio y cultivo ----------------------------------------------
    "51_rainforest_alliance":       (None, "rainforest-alliance", None),
    "51_a_rainforest_alliance_cacao": (None, "rainforest-alliance", None),
    "51_a_rainforest_alliance_cafe":  (None, "rainforest-alliance", None),
    "52_fairtrade_cocoa":    (None, "comercio-justo", None),
    "60_a_fairtrade":        (None, "comercio-justo", None),
    "66_ggn_certified_farming": (None, "ggn", None),
    # --- bienestar animal -------------------------------------------------
    "bienestar_animal_aenor_conform": (None, "bienestar-animal", None),
    "logotype-welfair-es-vertical-green-web": (None, "bienestar-animal", None),
    # --- no alimentarios: certifican, pero no son sellos de comida --------
    "63_natrue":             (None, "natrue", None),
    "64_ecolabel":           (None, "ecolabel", None),
    "fsc-r-logobackground_green": (None, "fsc", None),
    "62_pefc":               (None, "pefc", None),
    "standard_oekotex":      (None, "oeko-tex", None),
    "organiccotton_oekotex": (None, "algodon-organico", None),
}

# El logotipo de la casa: cuando Aldi lo cuelga de un producto esta diciendo que
# es suyo. Es mas fiable que deducirlo del nombre de la marca.
_MARCA_PROPIA = "12_aldi_nord_logo"

# Sufijos que Aldi le pone a la misma imagen segun la version o el tamano.
# Se quitan para que "MSC_0626" y "42_ASC_16_mm_de_alto" no cuenten como
# certificados distintos cada vez que les cambian el ano o los milimetros.
_RUIDO = re.compile(r"(_\d{4}|_\d{2}_?mm.*|_\d{4}$|_rgb|_color|-\d+)$", re.IGNORECASE)


def _clave(url: str) -> str:
    """El nombre del fichero del logotipo, sin ruta, extension ni version."""
    hoja = (url or "").rsplit("/", 1)[-1].split("?")[0]
    hoja = re.sub(r"\.(png|jpe?g|svg|webp)$", "", hoja, flags=re.IGNORECASE)
    anterior = None
    while hoja != anterior:
        anterior = hoja
        hoja = _RUIDO.sub("", hoja)
    return hoja.strip().lower()


def _busca(clave: str):
    if clave in _CATALOGO:
        return _CATALOGO[clave]
    # Prefijo, para que "msc_0626" y "42_asc_16_mm_de_alto" caigan en "msc"/"42_asc"
    # aunque el ruido no se haya limpiado del todo.
    for k, v in _CATALOGO.items():
        if clave.startswith(k):
            return v
    return None


def lee(urls) -> dict:
    """Los logotipos de un producto -> sellos, certificados, origen, marca propia.

    Devuelve solo las claves que tienen valor, para que el colector pueda hacer
    `r.update(certificados.lee(...))` sin pisar con None lo que ya sabia por
    otro camino.
    """
    sellos, certs, origen, propia = set(), set(), None, False
    for url in urls or ():
        clave = _clave(url)
        if not clave:
            continue
        if clave.startswith(_MARCA_PROPIA):
            propia = True
            continue
        hallado = _busca(clave)
        if hallado is None:
            continue
        sello, cert, org = hallado
        if sello:
            sellos.add(sello)
        if cert:
            certs.add(cert)
        if org and origen is None:
            origen = org

    salida: dict = {}
    if sellos:
        salida["sellos"] = ",".join(sorted(sellos))
    if certs:
        salida["certificados"] = ",".join(sorted(certs))
    if origen:
        salida["origen"] = origen
    if propia:
        salida["es_marca_propia"] = True
    return salida


def sin_traducir(urls) -> list[str]:
    """Los logotipos que no sabemos leer. Para la auditoria diaria."""
    fuera = []
    for url in urls or ():
        clave = _clave(url)
        if clave and not clave.startswith(_MARCA_PROPIA) and _busca(clave) is None:
            fuera.append(clave)
    return fuera
