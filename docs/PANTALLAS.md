# Cesta — las pantallas, una por una

Especificacion funcional de la interfaz. Que se ve, que pasa al tocar, y **que se
ve cuando algo falla**, que es la mitad que se olvida siempre.

Complementa `docs/UX-MOVIL.md` (las reglas generales) y `docs/API.md` (los
contratos). Lo que ya esta hecho se marca **[hecho]**; lo que falta, **[falta]**
con la tarea de `BACKLOG.md` que lo cubre.

---

## Las reglas que valen para todas

**Se usa con una mano y el carro en la otra.** Navegacion abajo. Areas de pulsar
de 44 px para arriba. Nada importante en la esquina superior.

**Nada espera al servidor para pintarse.** Anadir, tachar y cambiar cantidad se
ven al instante y se mandan despues. En el pasillo, un boton que tarda dos
segundos se pulsa tres veces.

**Cada pantalla tiene cuatro estados, y los cuatro se disenan**: cargando,
con contenido, vacia, y rota. La vacia dice **que hacer**, no "no hay datos". La
rota dice **que ha pasado**, no una rueda girando.

**Un numero nunca sin contexto.** El total dice que es aproximado. Lo que no
tiene precio se cuenta aparte, no como cero. Un precio de otro dia lleva su
fecha.

---

## 1. Entrar

**[hecho]**

Usuario, contrasena, y el nombre de la app. Nada mas: no hay registro, no hay
"he olvidado mi contrasena" (las cuentas las crea David desde el contenedor).

    error   "Usuario o contrasena incorrectos." Sin decir cual de los dos.
    tras    si habia una invitacion pendiente en el enlace, se aplica ahora
            y se avisa: "Ya estas en «Casa»"

---

## 2. Buscar

**[hecho]** el buscador, los filtros de cadena, los resultados con foto
**[falta]** el mosaico de habituales (tarea 3), la voz (tarea 3), el escaner
(tarea 8)

### Lo que se ve al abrir, con el buscador vacio

Aqui esta la mejora mas grande que queda por hacer. Hoy: nada. Deberia:

    [ buscar...                          🎤  📷 ]
    [ Alcampo ][ Aldi ][ Carrefour ][ DIA ][ Merc ]

    LO DE SIEMPRE
    ┌──────┐ ┌──────┐ ┌──────┐
    │ foto │ │ foto │ │ foto │      cuadricula de 3 columnas
    │Leche │ │Atun  │ │Papel │      un toque = a la lista
    │0,95 €│ │3,45 €│ │2,10 €│      24 como mucho
    └──────┘ └──────┘ └──────┘

Sale de `GET /api/habituales`. **Si no hay historial, no se pinta nada** y se ve
solo el buscador. No se rellena con "populares": no es lo mismo y no sirve.

### Los resultados

Una tarjeta por grupo: foto, nombre, cuantas cadenas, el ahorro si lo hay,
precio desde. Se abre y salen las filas por cadena, ordenadas de barata a cara,
con su barra de color.

    vacia   "Nada con «xxx». Prueba con una palabra mas corta, o vuelve a
             activar alguna cadena."   <- dice que hacer
    rota    "No llego a casa ahora mismo. Tu lista sigue disponible en la
             pestana Lista."           <- dice que si funciona

### El microfono **[falta — tarea 3]**

`SpeechRecognition` del navegador. Rellena el campo de busqueda y ya. **No es un
asistente.** Si el navegador no lo soporta, **el boton no se dibuja**. No se
dibuja y falla al pulsarlo: no se dibuja.

### El escaner **[falta — tarea 8]**

Abre la camara a pantalla completa con un marco en el centro. Al reconocer un
codigo, vibra (`navigator.vibrate`, si existe) y abre la ficha del punto 6.

    sin camara o sin permiso   el boton NO SE DIBUJA
    sin HTTPS                  tampoco: getUserMedia no funciona sin el
    codigo desconocido         pantalla 3 del punto 6, con salida al buscador

---

## 3. La lista

**[hecho]** las dos secciones, el marcador, las novedades, compartir
**[falta]** notas (tarea 5), agrupar por pasillos (tarea 1), cerrar compra
(tarea 10)

### Lo que se ve

    Casa
    9 por coger · 4 en el carro

    ┌─────────────────────────────────────────┐
    │ VA A COSTAR              23,40 € en el  │
    │ 47,30 €                  carro          │
    │ aproximado, cogiendo      23,90 € por   │
    │ cada cosa donde este      coger         │
    │ mas barata                              │
    │ ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░               │
    └─────────────────────────────────────────┘

    POR COGER                               9

    ○ [foto] Leche entera 1 L        1,90 €
             lo puso Mama             0,95 c/u
             [−] 2 [+]

    EN EL CARRO                             4

    ● [foto] ~~Atun en aceite~~      3,45 €
             lo cogio Mama

**Dos secciones, no una lista tachada.** En el pasillo miras la lista veinte
veces y lo que necesitas saber cada vez es *que me queda*. Si lo tachado sigue en
medio, hay que leerlo todo para descartarlo.

### Agrupar por pasillos **[falta — tarea 1]**

Dentro de "Por coger", subtitulos por seccion, en el orden en que se recorre una
tienda:

    fruta y verdura · carniceria · pescaderia · lacteos y huevos · panaderia ·
    despensa · desayuno y dulces · aperitivos · congelados · bebidas ·
    droguería y limpieza · higiene y belleza · bebe · mascotas · hogar

Lo que no tenga seccion va al final, bajo "otros". **No se inventa una seccion**
para que no quede feo.

### Las novedades

Al abrir, si la otra persona ha tocado algo desde tu ultima visita:

    "Mama cogio la leche · Mama puso papel de cocina"

Sin esto, una lista compartida es un sitio donde las cosas aparecen y desaparecen
solas.

### Sin conexion

    "Sin conexion con casa. Esto es lo ultimo que vi; lo que cambies se
     guardara y se subira al volver."

Y si hay cola pendiente: "3 cambios por subir". Al volver la red se suben solos
y sale un aviso flotante.

### Cerrar la compra **[falta — tarea 10]**

Un boton al final: "He terminado la compra". Guarda lo que iba en el carro como
una compra, lo quita de la lista, y deja lo que no se cogio. Es lo que genera el
historial del que vive todo lo de diciembre.

---

## 4. Donde la compro

**[hecho]**

    TODO EN UNA TIENDA
      Alcampo        48,10 €     tiene los 14
      Mercadona      47,30 €     no encuentro: cafe en grano 1 kg, atun pack 6
      Carrefour      51,05 €     tiene los 14
                                 las ofertas te quitan 3,15 €

    REPARTIDO
      Alcampo + Mercadona    41,80 €
      9 en Alcampo, 5 en Mercadona
      ahorras 6,30 € yendo a dos sitios

**Lo que falta se dice por su nombre.** "Le faltan 2" no sirve para decidir.

**Si el reparto ahorra poco, se dice y no se propone**: "Repartir entre dos
tiendas solo ahorra 0,80 €. No compensa el viaje."

---

## 5. Favoritos

**[hecho]** la lista basica
**[falta]** ordenar por lo que ha cambiado (necesita mas historico)

Los pocos productos que se compran siempre. **No es una lista larga: es una
pantalla de vigilancia.** Ordenados por lo que ha cambiado, no alfabeticamente:
lo que ha bajado arriba, lo que ha subido debajo, lo quieto al final.

    vacia   "Todavia no sigues nada. Busca un producto, abrelo y pulsa Seguir."

---

## 6. La ficha del producto

**[hecho]** la hoja con foto, precio, alergenos, ingredientes, Nutri-Score
**[falta]** la nota nueva (tarea 9), "hay uno mejor y mas barato" (bloqueado)

Media pantalla que sube desde abajo. **El orden es el orden en que se mira algo
en el pasillo**, y no es negociable:

    1  la oferta, si la hay          lo que cambia el precio
    2  precio y precio por kilo
    3  alergenos                     EN ROJO: es lo unico que puede hacer dano
    4  ingredientes
    5  Nutri-Score y NOVA            se entienden de un vistazo, van despues
    6  la nota / la gama
    7  origen, codigo de barras
    8  "verlo en <cadena>"

### Cuando no hay datos

    nota sin datos   "no lo se", nunca un cero ni una nota gris
    sin alergenos    no se pone la fila. No se pone "sin alergenos conocidos",
                     que se lee como "no lleva" y no es lo que sabemos.

### Las cuatro respuestas del escaner **[falta — tarea 8]**

La misma hoja, entrando por codigo de barras:

    1  LO CONOZCO Y PUEDO COMPARAR   (42 %)
       "3,45 € aqui. En Alcampo 2,89 (-16 %)" + ficha + anadir

    2  LO CONOZCO, UNA SOLA CADENA
       "Lo tengo en DIA a 3,45 €. No lo encuentro en las demas."
       No inventar una comparacion que no existe.

    3  NO LO CONOZCO                 (lo normal en Alcampo y Aldi)
       "No tengo este codigo. Puede ser marca propia de Alcampo o Aldi,
        que no publican codigo de barras."
       + buscador por nombre. No un callejon sin salida.

    4  SIN NUTRICION                 (54 % de los que conozco)
       El precio se ensena igual. Donde iria la nota, "no lo se".

---

## 7. Compartir

**[hecho]**

    "Mandale este enlace. Al abrirlo entra en la lista y puede escribir en ella.
     Caduca en 7 dias y sirve para 3 personas."

    [ https://cesta:8080/unirme/abc123 ]  [ Copiar ]

    QUIEN ESTA DENTRO
    David  @david        creo la lista
    Mama   @mama         escribe

    [ Anular los enlaces que haya dado ]

**Por enlace, no por @usuario.** Pedirle a alguien que teclee `@davidpeve01` es
pedirle que se equivoque.

Si el navegador no deja copiar al portapapeles, el texto se queda seleccionado y
el boton pone "Copialo". Nadie se queda sin el enlace.

---

## 8. El panel

**[hecho]** cadenas, movimiento, marca propia, lo que falta por historico
**[falta]** secciones (bloqueado por tarea 1 y 2), productos

Es para David, no para su madre, y por eso va en su propia pestana.

**Cada numero lleva al lado de donde sale y de que fecha es.** Un panel que
ensena un 19,3 % sin decir sobre cuantos grupos no es un panel, es una opinion
con tipografia.

**El aviso de la calidad se ensena siempre** en la pantalla de marcas: dice que
porcentaje de las letras salen del precio. Sin el, el estudio se lee al reves.

**Lo que aun no se puede medir se dice, con la fecha**: "tendencia_30d — faltan
18 dias". No se dibuja una linea plana con doce puntos y se la llama tendencia.

---

## 9. Ajustes

**[hecho]** cadenas cercanas, reparto, salir
**[falta]** el aviso legal (tarea 5)

    SUPERMERCADOS QUE TENGO CERCA
    Los que quites no salen en las busquedas ni deciden donde comprar.
    Si no tienes un Aldi al lado, no tiene sentido que te diga que es el mas
    barato.

    [ Alcampo ][ Aldi ][ Carrefour ][ DIA ][ Mercadona ]

    LA APP
    Repartir entre dos tiendas                              [====O]
    Cerrar sesion                                          [ Salir ]

    Los precios son orientativos y pueden variar. Cesta no esta afiliada,
    asociada ni patrocinada por ninguno de estos supermercados.
    Los datos viven en el ordenador de casa y no salen de ahi.
    Informacion nutricional de Open Food Facts, bajo licencia ODbL.

El tema claro/oscuro sale del sistema. No hace falta un interruptor, y no hacen
falta siete colores de acento.

---

## 10. Lo que no hay, y no debe haber

**Pantalla de bienvenida o tutorial.** Si hace falta explicarla, esta mal hecha.

**Pantalla de actividad.** `anadido_por` y `tachado_por` en cada linea bastan.
Una pantalla de actividad es un producto de equipo, no una lista de la compra.

**Valoraciones ni comentarios de productos.** Sois dos.

**Publicidad ni patrocinados.** Ni ahora ni nunca: el dia que un producto suba
en la lista por dinero, la app deja de servir para lo que se hizo.
