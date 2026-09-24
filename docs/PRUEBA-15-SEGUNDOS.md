# La prueba de los quince segundos

Es la condicion (a) de la barra y **la unica que no puede cerrar quien escribe el
codigo**. El encargo lo dice asi:

> La prueba de aceptacion no es un porcentaje: coger el movil y contestar las cuatro
> preguntas **en menos de quince segundos sin saber donde esta el boton**. Y se juzga
> **contra la madre del dueno**, no contra quien escribio el codigo: no va a leer ayuda,
> no va a explorar menus, y si algo no se entiende a la primera **no pregunta, deja de
> usarlo**.

Aqui esta el guion para medirlo: que se hace, en que orden, que cuenta como quince
segundos y **donde se escriben los numeros**. Un guion y no una opinion, porque una
prueba de usabilidad que se recuerda a medias se convierte en "yo creo que si".

## Antes de empezar: donde se abre, y con que cuenta

La aplicacion esta en **`http://<el-PC>:8080`**, servida por Caddy. Desde el movil se entra
**por Tailscale** (`docs/TAILSCALE.md`), que es como esta montado para que no haga falta
abrir nada en el router. Y desde el 24 de septiembre de 2026 el 8080 sirve **la interfaz
nueva** (`web/dist`), no la vieja: si sale el `app.js` de siempre, el despliegue no esta
hecho.

Dos cosas que hay que preparar **antes** de cronometrar nada, porque si se hacen con el
cronometro en marcha ya no se esta midiendo lo mismo:

  - **Una cuenta nueva por persona.** La primera pantalla que ve quien se registra es la
    parte que se quiere ver (§2 del encargo), y una cuenta con la lista ya hecha no la
    enseña. Ojo: la API limita las altas a **10 por hora** (`almacen.ALTAS_POR_HORA`), asi
    que si se van a hacer varias pruebas seguidas, contarlas.
  - **La pantalla, en la primera pantalla y con la sesion ya dentro** (o fuera, si lo que
    se mide es el registro). El cronometro empieza ahi, no en la pantalla de entrar.

## Como se mide

**Una persona que no haya escrito la pantalla**, con un movil de verdad, en una mano, de
pie. Nada de escritorio, nada de ventana estrecha del navegador, y nada de ayuda.

El cronometro empieza **con la aplicacion abierta en la primera pantalla** y termina
cuando la persona dice la respuesta en voz alta. Si pregunta algo, si abre el menu de
ayuda o si explora sin rumbo, **cuenta como fallo aunque llegue**: lo que se mide no es
si se puede, es si se entiende a la primera.

Cada pregunta se lanza **como se pregunta en la vida**, no con el nombre del boton:

    1. «¿Que me falta comprar y donde lo compro?»
    2. «Esto que tengo en la mano, ¿esta caro?»
    3. «¿Voy tachando bien?»
    4. «¿Ha bajado algo de lo mio?»

## Lo que ya esta descartado antes de empezar

No todo se puede medir antes de que alguien coja el movil, pero una parte si, y esa parte
**ya esta medida**: lo que la hace imposible. Lo que se descarta aqui no hay que medirlo
despues.

    que la pantalla cargue                 la puerta: abrir la aplicacion en un movil
    que haya respuesta que leer            las cuatro, con su frase
    que la respuesta no obligue a
      desplazar la pantalla                las cuatro caben en la banda util de un
                                           390 x 844: 109 px de cabecera arriba, 57 de
                                           barra de abajo. Medido el 23 sep 2026:
                                           la primera linea de la lista 557..573 ·
                                           la frase del grupo 520..564 · "lo tuyo que ha
                                           bajado" 437..557 · la seccion de avisos
                                           186..210. **Todas dentro de 109..787.**
    que lo que hay que pulsar se acierte   44 px minimo, y medido ya pintado
    que el texto se lea                    contraste en claro y en oscuro, medido

Todo eso lo comprueba `plataforma/prueba_navegador.py` en cada pasada. **Lo que queda es
lo unico que no se puede medir desde aqui: si se entiende a la primera.** Y eso es lo que
se viene a apuntar en la tabla de abajo.

**Y lo que si se puede medir de "no saber donde esta el boton": los toques.** Un boton a
cinco toques no se pulsa en quince segundos ni sabiendo donde esta, y ese numero es de
codigo, no de usabilidad. La puerta los **cuenta andando de verdad** desde la primera
pantalla (`prueba_navegador.py`, «cuantos toques hay desde la primera pantalla hasta cada
respuesta»); medido el 24 de septiembre de 2026:

    1. que me falta y donde lo compro   1 toque    Buscar -> Cesta
    2. esto esta caro                   1 toque    escribir en Buscar -> el resultado
    3. voy tachando bien                0 toques   el numero esta en la barra de abajo
                                                    (1 toque si se quiere ver la lista)
    4. ha bajado algo de lo mio         1 toque    Avisos (si tienes avisos pedidos)
                                        3 toques   Panel -> Bajadas -> «Solo lo mío»
                                                   (esta ultima contesta **sin haber pedido
                                                    nada antes**, que es el caso normal)

Si una persona tarda mas de quince segundos con estos numeros, el problema **no es donde
esta el boton**: es que la respuesta no se entiende, y eso es lo que hay que apuntar en
voz alta.

## Por donde se contesta cada una, hoy

    1. Cesta. Dos secciones («Por coger» / «En el carro»), el total arriba y la
       comparacion por cadenas debajo. `paginas/Cesta.tsx`
    2. Escaner (codigo de barras) o buscador -> la ficha, con **la frase** antes que la
       tabla (`paginas/Producto.tsx`, `logica/frase.ts`). La frase **no se inventa** si
       el grupo no es de fiar: en ese caso hay que poder contestar "no lo se" sin que
       parezca un fallo.
    3. Cesta, la misma pantalla: los dos encabezados con su cuenta y el tachado. Y
       **el numero de la barra de abajo** (`Nav.tsx`), que contesta de un vistazo desde
       cualquier pantalla sin abrir nada.
    4. **Panel -> Bajadas -> «Solo lo mío»** (`paginas/Panel.tsx`, 3 toques). Es la que
       contesta **sin haber hecho nada antes**: *«Lo tuyo que ha bajado en 7 días»*, con
       la tabla y la regla escrita debajo (*"si lo que cambió fue el formato, eso no es
       una bajada"*). Se midió en un navegador el 23 de septiembre de 2026 y contesta
       con una fila de verdad: leche entera Lauki, Dia, 1,15 €/l -> 1,05 €/l, un -8,7 %.
       **Y hay una segunda ruta, que es la de un toque: «Avisos»** (`paginas/Avisos.tsx`).
       Contesta *lo que pediste con la campana*, y **solo eso**: con una cuenta que no ha
       pedido ningún aviso, la pantalla dice *«No sigues ningún producto»* con la
       explicación de cómo pedirlo. Es correcto, y no es una respuesta a la pregunta.
       Para la prueba de los quince segundos, la ruta buena es la del panel; si quien la
       hace ya tiene avisos pedidos, la de Avisos contesta en un toque.

## Que se apunta

Por pregunta: **los segundos**, si hizo falta ayuda, y **que dijo en voz alta** cuando no
encontro algo. Las frases de la gente valen mas que el numero: "esto no me dice nada" o
"¿aqui cual pulso?" es el defecto, y el numero solo dice cuanto cuesta.

Y lo que hay que apuntar aparte, porque es lo que decide si vuelve:

  - **la primera vez**: entrar con una cuenta nueva y ver si la aplicacion se entiende
    **sin que nadie explique nada**. El buscador vacio ya no esta vacio (cuatro productos
    con su diferencia de hoy, `componentes/LoQueSeCompra.tsx`), pero eso hay que verlo.
  - **sin cobertura**: apagar los datos y tachar algo en la lista. No puede salir nada
    rojo, y tiene que quedar claro que el cambio no se ha guardado.
  - **a la primera**: si hay que explicar algo una vez, ese algo esta mal.

## Donde se escriben los numeros

En este mismo fichero, debajo, en una tabla con la fecha. Un resultado que no esta escrito
no se puede comparar con el siguiente, y la barra pide **menos de quince segundos**: hay
que poder decir si se cumple.

La tabla, lista para rellenar. Una fila por persona y pasada; los segundos son los que
diga el cronometro, y **«ayuda» es si/no**: si hubo que explicar algo, esa respuesta
cuenta como fallo aunque llegara a tiempo.

    fecha        quien        p1      p2      p3      p4      ayuda   que dijo
    ____-__-__   ____________ ______  ______  ______  ______  ______  ____________________
    ____-__-__   ____________ ______  ______  ______  ______  ______  ____________________
    ____-__-__   ____________ ______  ______  ______  ______  ______  ____________________

Y debajo de la tabla, lo que decide si vuelve:

    la primera vez          ¿se entiende sin que nadie explique nada? (cuenta nueva)
    sin cobertura           apagar los datos y tachar: ¿sale algo rojo? ¿queda claro
                            que no se ha guardado? (no puede salir rojo)
    a la primera            si hay que explicar algo una vez, ese algo esta mal

**Estado: sin medir.** No lo puede hacer quien ha escrito estas pantallas: conoce los
botones de memoria, y la prueba se juzga contra alguien que no los conoce. Quien lo mida
que devuelva **defectos con su numero**, no parches: el codigo del front lo toca un solo
agente a la vez, y ya se mezclo una vez.
