# La curva de precios, encima de la web del supermercado

Extensión de Chrome. Cuando abres un producto en Carrefour, DIA, Aldi, Mercadona
o Alcampo, aparece abajo a la derecha un recuadro con **su histórico de precios**
y **dónde está más barato**.

La idea es de `supermarket-tracker`, y es la mejor que le hemos copiado a nadie:
el histórico sólo sirve en el momento de decidir, y ese momento no ocurre en
nuestra aplicación, ocurre delante del producto. Una pestaña más es una pestaña
que no se abre.

## Instalar

1. Arranca Cesta (`plataforma\arrancar.bat`).
2. Chrome → `chrome://extensions` → activa **Modo de desarrollador**.
3. **Cargar descomprimida** → elige esta carpeta `extension`.
4. Si usas Cesta desde otro equipo por Tailscale, entra en las opciones de la
   extensión y cambia la dirección a `http://cesta:8080`.

## Qué ve y qué no ve

- **El supermercado nunca ve una petición a tu Cesta.** La consulta la hace el
  *service worker*, no la página: `carrefour.es` no se entera de que la
  extensión existe.
- La extensión **no lee el DOM** del supermercado. Lo único que saca de la
  página es el identificador del producto, que está en la URL. Un selector CSS
  ajeno se rompe cada dos semanas.
- **No manda nada a ningún sitio.** Sólo habla con la dirección que tú pongas.

## Cómo saca el identificador

    carrefour   /R-521028123/p          y también /R-VC4AECOMM-647163/p
    dia         /p/49608
    aldi        /p/<nombre>-279705
    mercadona   /product/13294/
    alcampo     /products/181786

`tests/test_extension.py` comprueba estos patrones **contra las URL reales del
último bronze**. Así, el día que una cadena cambie su formato, sale en rojo en la
ejecución diaria y no cuando alguien lo pruebe a mano.

Esa prueba ya encontró dos fallos el día que se escribió: el identificador de
Carrefour **no siempre es un número** (10.835 de 16.560 son del tipo
`VC4AECOMM-647163`, y con `\d+` la extensión se quedaba muda en dos de cada tres
páginas), y el patrón de Alcampo sin anclar devolvía `72` para la URL vieja con
UUID — un identificador inventado que habría pedido un producto que no es.

## Fuera de casa

Cesta corre en el ordenador de casa. Fuera de casa el recuadro dice que no
responde, y eso no es un fallo: es que no estás en casa.
