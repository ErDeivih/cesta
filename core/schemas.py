"""Contratos de datos. Si un registro no valida, no entra."""
from __future__ import annotations

from datetime import datetime

import polars as pl
from pydantic import BaseModel, Field

# Esquema unico de bronze para TODAS las cadenas. Fijar los tipos aqui evita que
# una columna que sale entera a None se quede como Null y rompa la union de
# esquemas al juntar dias o cadenas.
ESQUEMA_BRONZE = {
    "fuente": pl.Utf8,
    "id_fuente": pl.Utf8,
    "nombre": pl.Utf8,
    "marca": pl.Utf8,
    "ean": pl.Utf8,
    "origen": pl.Utf8,
    "proveedores_txt": pl.Utf8,
    "nombre_legal": pl.Utf8,
    "ingredientes": pl.Utf8,
    "alergenos": pl.Utf8,
    "formato_txt": pl.Utf8,
    "cantidad_declarada": pl.Float64,
    "unidad_declarada": pl.Utf8,
    "precio_cent": pl.Int64,
    "precio_ref_nativo_cent": pl.Int64,
    "unidad_ref_nativa": pl.Utf8,
    # El otro precio de referencia de Mercadona, y el unico que va de verdad en la
    # unidad que dice su `reference_format`. Medido el 26 de septiembre de 2026 sobre
    # el bronze del dia (4.324 productos): `reference_price` y `bulk_price` coinciden
    # en 3.522 y difieren en 802, porque `bulk_price` va en la unidad del TAMANO
    # (EUR/kg, EUR/l, EUR/ud) y `reference_price` en la de la referencia (EUR/lavado,
    # EUR/docena, EUR/100 g). Se guarda entero: un detergente son 14 centimos por
    # lavado, y a esa escala el redondeo al centimo es un 3 %.
    "precio_referencia_nativo_cent": pl.Int64,
    "precio_anterior_nativo_cent": pl.Int64,
    "ha_bajado_nativo": pl.Boolean,
    "promo": pl.Boolean,
    "promo_txt": pl.Utf8,
    "promo_hasta": pl.Datetime("us", "UTC"),
    "iva": pl.Utf8,
    "es_pack": pl.Boolean,
    # Cuantas piezas trae el envase, **dicho por la cadena**. Mercadona lo
    # publica en 1.256 productos y hasta ahora se adivinaba dividiendo precios.
    # Medido el 18 de septiembre de 2026: de esos 1.256, nuestra deduccion
    # coincidia en 169 y se equivocaba en 1.087, casi siempre diciendo "1" para
    # un pack de seis yogures. La cantidad total si la teniamos bien (0,75 kg),
    # asi que el precio por kilo nunca estuvo mal; lo que no se podia decir era
    # cuanto sale CADA yogur, ni aplicar un "2a unidad" con sentido.
    "unidades_envase": pl.Int32,
    "peso_variable": pl.Boolean,
    "categoria": pl.Utf8,
    "disponible": pl.Boolean,
    "url": pl.Utf8,
    "imagen": pl.Utf8,
    # DIA publica una tabla nutricional completa en el 66 % de sus fichas y
    # durante doce dias la tiramos entera. Son ~3.570 productos con dato de
    # ETIQUETA, no inferido de Open Food Facts. Las cadenas que no la publiquen
    # dejan estas cuatro a None, que es una respuesta valida.
    "nutricion": pl.Utf8,          # JSON: kcal, grasas, saturadas, hidratos,
                                   # azucares, fibra, proteinas, sal
    "nutricion_por": pl.Utf8,      # "100g" | "100ml" | "porcion"
    # Ninguna otra app de la competencia tiene esto. Alimenta la despensa
    # deducida: se compro hace 12 dias, dura 15, se acaba el viernes.
    "dias_caducidad": pl.Int32,
    # En conservas, comparar por peso escurrido en vez de por peso total cambia
    # cual es mas barato. Mercadona lo da en 179 fichas.
    #
    # DIA parecia darlo en el 100 %, y era mentira: su campo `drained_weight`
    # trae el peso del envase entero, no lo que queda al escurrir. Se vio porque
    # coincidia exactamente con la cantidad neta en 4.323 de 4.995 productos, y
    # porque para un litro de aceite de oliva decia 916, que no es peso escurrido
    # sino la densidad del aceite. Ese dato va a `peso_neto_g`, no aqui.
    "peso_escurrido_g": pl.Int32,
    # Lo que pesa de verdad lo que hay dentro, en gramos, aunque se venda por
    # volumen. Es el puente entre una cadena que vende el aceite por litros y
    # otra que lo vende por kilos: sin el, los dos productos no se pueden poner
    # en la misma columna. DIA lo publica para 4.995 productos.
    "peso_neto_g": pl.Int32,
    # Normalizado con core/envases.py: "brik", "botella", "paquete". DIA lo
    # publica en 5.410 fichas y Mercadona en el 86 % de las suyas, cada uno con
    # su vocabulario.
    "envase": pl.Utf8,
    # El grado alcoholico que declara la ficha. Sirve para el filtro "sin
    # alcohol" y para que el emparejador no ponga una cerveza 0,0 al lado de una
    # normal como si fueran el mismo producto.
    "grado_alcohol": pl.Float64,
    # DIA clasifica cada producto en un tipo fino ("Leche infantil", no
    # "Lacteos"). Es una etiqueta limpia y gratis para 5.410 productos, y el
    # emparejador hoy lo adivina del nombre.
    "tipo_producto": pl.Utf8,
    # Los sellos que la gente busca de verdad: sin gluten, sin lactosa, vegano,
    # ecologico. Creiamos que solo podian venir de Open Food Facts, o sea solo
    # para productos con codigo de barras. Falso: Alcampo y Carrefour los
    # publican ellos mismos, y Alcampo NO tiene EAN. Medido el 17 de septiembre:
    # las dos cadenas juntas dan 9.398 sellos, mas que los 8.055 de OFF, y
    # llegan justo a los productos donde OFF nunca podria llegar.
    # Se guarda como texto separado por comas, ordenado, para que se pueda
    # filtrar con un LIKE sin montar otra tabla.
    "sellos": pl.Utf8,
    # De donde salio cada sello, porque no todos valen lo mismo:
    #   "certificado"  logotipo de un organismo con auditoria (Aldi)
    #   "etiqueta"     la cadena lo marca en su ficha (Alcampo, Carrefour)
    #   "nombre"       solo lo dice el nombre del producto: es marketing
    #   "mixto"        las dos cosas
    # Lo rellena silver, no los colectores, porque el nombre lo tienen todas.
    "sellos_origen": pl.Utf8,
    # "refrigerado" | "congelado" | "ambiente". Alcampo lo dice en el 27 % de su
    # catalogo y Carrefour marca los congelados. QueFalta lo ensena en su ficha.
    "conservacion": pl.Utf8,
    # Que la cadena diga que es marca propia es mas fiable que deducirlo del
    # texto de la marca, que es lo que hace hoy el panel.
    "es_marca_propia": pl.Boolean,
    # Certificaciones de terceros, con organismo y auditoria detras: DOP, IGP,
    # MSC, Fairtrade, Rainforest Alliance, bienestar animal, FSC. Se guardan
    # aparte de `sellos` a proposito: un sello responde a "¿puedo comerlo?" y
    # filtra la compra; un certificado responde a "¿de donde sale y como se
    # hizo?" y ordena una comparacion entre dos productos que ya valen los dos.
    # Aldi los publica como logotipos en 729 productos (35,3 %). Ver
    # core/certificados.py.
    "certificados": pl.Utf8,
    # La frase que la cadena escribe sobre el producto ("Sin colorantes ni
    # conservadores", "Antiedad. Reduce arrugas en 7 dias"). Es lo unico que
    # Aldi dice de un producto ademas del nombre, y va en la ficha del movil.
    # No confundir con `longDescription`, que en Aldi es aviso legal el 99,3 %
    # de las veces y no se guarda.
    "descripcion": pl.Utf8,
    # ---- lo que salio de auditar_crudo.py el 17 de septiembre de 2026 --------
    # Las siete veces anteriores, un dato guardado y sin leer aparecio porque a
    # alguien se le ocurrio mirar. `projects/cesta/auditar_crudo.py` lo dice
    # solo, y de su primera pasada salieron estas seis columnas.
    #
    # 90 de cada 100 ofertas de DIA son **solo con la tarjeta Club**, y en el
    # proyecto ya estaba decidido que un descuento de tarjeta NO baja lo que
    # pagas en caja (se acumula en un monedero). Sin esta columna, anadir el
    # texto de oferta de DIA habria hecho que la app anunciara 200 rebajas que
    # no existen en el ticket.
    "promo_club": pl.Boolean,
    "promo_solo_online": pl.Boolean,
    # Cuantas unidades hay que comprar para que la oferta valga, dicho por la cadena en
    # numero y no en el texto de la oferta. Alcampo lo publica en 1.900 productos (7,8 %) y
    # es la unica cadena que lo da: `2` es "2a unidad al 50 %". Hoy se guarda y no se usa,
    # por la misma razon por la que un precio de tarjeta no cuenta: una oferta que exige
    # comprar dos unidades no es el precio de una. Ver `docs/DATOS-QUE-NO-COGEMOS.md`.
    "promo_unidades_minimas": pl.Int32,
    # Aldi publica este booleano en sus 2.065 productos: marca un lote retirado
    # de la venta. Hoy vale False en todos, pero existir es lo que importa,
    # porque sabemos que hay en cada lista de la compra. Ninguna app de la
    # competencia avisa de retiradas de producto.
    "es_recall": pl.Boolean,
    # Alcampo marca 1.589 productos con alcohol y Mercadona los suyos con
    # `requires_age_check`. Es el filtro que pide cualquiera que no beba, y no
    # se puede deducir del nombre: "cerveza 0,0" lleva "cerveza".
    "es_alcohol": pl.Boolean,
    # Para los productos al peso. Alcampo publica el rango real (min, tipico,
    # max) de 742 productos: un tomate "al peso" de 500 g que puede venir entre
    # 375 y 625. El precio por kilo es bueno; el total es una estimacion, y esta
    # columna dice de cuanto.
    "peso_variacion_pct": pl.Int32,
    # El distintivo que pone la propia cadena: "Mejor valorado" (282 productos
    # de DIA), "Novedad", "Precio destacado". Es la unica senal de popularidad
    # de todo el proyecto: ninguna cadena publica ventas ni resenas utiles.
    "distintivo": pl.Utf8,
    # Pictogramas de peligro (Reglamento CLP): "Corrosivo para la piel",
    # "Peligro para el medio ambiente". Alcampo los publica en 531 productos de
    # limpieza. Importa en una casa con ninos, y no lo ensena ninguna app.
    "advertencias": pl.Utf8,
    "capturado_en": pl.Datetime("us", "UTC"),
}


def vacio() -> dict:
    """Registro con todos los campos a None: cada colector rellena lo que tenga."""
    return {k: None for k in ESQUEMA_BRONZE}


class ProductoRaw(BaseModel):
    fuente: str
    id_fuente: str
    nombre: str
    marca: str | None = None
    formato_txt: str | None = None
    precio_cent: int | None = Field(default=None, ge=0)
    precio_ref_nativo_cent: int | None = Field(default=None, ge=0)
    unidad_ref_nativa: str | None = None
    disponible: bool = True
    categoria: str | None = None
    url: str | None = None
    capturado_en: datetime
