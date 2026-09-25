# Cesta — listas propias y listas compartidas

Escrito el 15 de septiembre de 2026. Detalla el punto 5 de `APP.md` y las tablas
`lista` y `lista_linea` de `MODELO.md`.

El caso que hay que resolver, con tus palabras: **una lista de casa sobre la que
varias personas puedan escribir y modificar**, sin dejar de tener cada uno las
suyas.

---

## 1. Tres clases de lista, no dos

    MIA          la creo yo, la veo yo. Nadie mas sabe que existe.
    DE CASA      la creamos entre los dos y los dos escribimos en ella.
                 Es la que de verdad importa.
    COMPARTIDA   mia, pero le doy acceso a alguien. Puede mirar, y si le dejo,
                 escribir.

Una lista no nace compartida y luego se privatiza: **nace con un dueno y se le
invita gente**. El dueno es quien puede borrarla; los demas pueden salirse.

La de casa es un caso particular con nombre propio porque merece la pena que lo
tenga: es la lista que se abre por defecto al entrar en la app, la que no hay
que buscar.

---

## 2. Las tablas

    lista
      id              uuid
      nombre          "Casa", "Fin de semana", "Ferreteria"
      dueno_id        quien la creo
      es_de_casa      solo una por hogar; es la que se abre al entrar
      creada_en

    lista_acceso
      lista_id
      usuario_id
      papel           'dueno' | 'escribe' | 'mira'
      invitado_por
      aceptado_en     null mientras no acepte

    lista_linea
      id              uuid, generado en el MOVIL (ver punto 4)
      lista_id
      grupo_id        que se compra, no de que cadena
      producto_id     solo si el usuario fijo una cadena a mano
      cantidad
      nota            "la de cristal", "si hay del grande"
      anadido_por     usuario_id
      anadido_en
      tachado_por     usuario_id o null
      tachado_en      timestamp o null
      borrado_en      timestamp o null   <- no se borra de verdad, ver punto 5

**`papel` tiene tres valores y no dos** porque hay un caso real: ensenarle la
lista a alguien sin que la pueda cambiar. Hoy sois dos y siempre sera
`'escribe'`, pero el dia que no lo sea, el modelo ya lo aguanta y no hay que
migrar nada.

**`anadido_por` y `tachado_por` no son auditoria, son interfaz.** Cuando abres la
lista de casa quieres ver quien ha puesto que:

    Leche entera 1 L  x6        anadido por mama
    Cafe en grano 1 kg          tachado por ti, hace 10 min
    Papel de cocina             anadido por ti

Sin eso, una lista compartida es un sitio donde las cosas aparecen y desaparecen
solas, y eso desconcierta mas de lo que ayuda.

---

## 3. Que pasa cuando los dos tocais a la vez

Estais los dos en el supermercado, cada uno con su movil, y a lo mejor uno de los
dos sin cobertura. Esto tiene que estar decidido de antemano, no improvisado.

**Cada linea se resuelve por su cuenta.** No hay "version de la lista": hay
lineas, y dos personas tocando lineas distintas no chocan nunca. Esto por si solo
elimina casi todos los conflictos.

**Tachar es idempotente.** Tachar algo ya tachado no hace nada. Si tu madre y tu
tachais la leche a la vez, gana el que lo hizo antes segun su reloj, y el otro no
ve ningun error: ve la leche tachada, que es lo que queria.

**La cantidad es el unico caso con conflicto de verdad.** Tu pones 6 leches y
ella pone 2. La regla es **gana el ultimo**, y se avisa una vez:

    Mama cambio la cantidad de leche entera a 2 (hace 1 min)

No se suman las dos cifras, no se abre un dialogo de "resolver conflicto". Gana
el ultimo, se dice quien fue, y quien no este de acuerdo lo vuelve a cambiar.
Para una lista de la compra entre dos personas eso es suficiente, y cualquier
cosa mas lista es peor.

---

## 4. Sin cobertura, que es donde de verdad pasa

El supermercado es el sitio con peor cobertura, y es justo donde se usa la lista.
Tres decisiones lo hacen funcionar:

**1. El identificador de la linea lo genera el movil.** Un uuid, no un numero
que da el servidor. Asi puedes anadir "papel de cocina" sin red, y cuando vuelva
la conexion esa linea se sube con la identidad con la que nacio. Si se sube dos
veces por lo que sea, el servidor la reconoce y no la duplica.

**2. Cada cambio viaja con su hora.** No con la hora en que llego al servidor,
sino con la del movil en que se hizo. Tachar la leche a las 18:04 sin cobertura y
subirlo a las 18:20 tiene que contar como las 18:04, porque si no el orden de
los hechos se inventa.

**3. La lista abierta se guarda entera en el movil.** Los productos, las
cantidades, los precios y la tienda elegida. Son unos pocos KB. Es lo unico que
la app guarda, y es exactamente lo que necesitas mientras andas por los pasillos
con el PC de casa apagado.

Lo que se ve mientras no hay conexion:

    Lista de casa                    sin conexion con casa
    14 productos, 3 tachados         los cambios se guardaran al volver

---

## 5. Nada se borra del todo

`borrado_en` en vez de borrar la fila. Dos razones, y la segunda es la buena:

1. Si dos moviles borran y anaden a la vez, una fila borrada de verdad vuelve a
   aparecer cuando el otro sincroniza. Con una marca de borrado, no.
2. **Deshacer.** Tu madre borra sin querer media lista en el pasillo del
   supermercado. Con filas marcadas, "deshacer" es quitar una marca. Sin ellas,
   es una llamada de telefono.

Las lineas borradas se limpian de verdad a los 30 dias, cuando ya nadie las va a
echar de menos. **Una lista entera tambien se puede quitar del tiron** (lo pidio el
dueno el 25 de septiembre de 2026): eso **archiva** (`archivada_en`), o sea desaparece
de la pantalla y se puede recuperar. Borrarla de verdad seria quitarle la compra a otra
persona de un toque, y estas listas se comparten.

---

## 6bis. En que tienda se compra cada cosa

Desde el 25 de septiembre de 2026, cada linea guarda **su** tienda (`cadena_elegida`).
Es lo que pidio el dueno: *"en la lista poder elegir en que supermercado lo quiero
comprar y hacer en una lista que tenga, sublistas dependiendo de donde he puesto que voy
a comprar ese producto, con el precio final de la lista entera y de cada sublista
(explicando tambien aplicacion de descuentos)"*.

Hasta ese dia la aplicacion calculaba donde salia mas barata la lista entera y **no
guardaba ninguna decision**: cada vez que se abria la pantalla volvia a proponer. Eso
vale para mirar y no vale para comprar. Quien decide "el pan en DIA, que me pillo de
camino" tiene que poder dejarlo escrito, y que el total lo tenga en cuenta.

Tres reglas, y las tres son de dinero:

1. **Tres estados, no dos**: sin decidir, decidida y comprada. Lo que no se ha decidido
   **no suma** al total; sale aparte con su opcion mas barata al lado. Sumarlo por lo mas
   barato daria un total que no corresponde a ninguna compra posible.
2. **Una linea puesta en una tienda que no la tiene no desaparece**: sale por su nombre
   ("en Aldi no lo hay"). Es la misma regla que `donde`, aplicada a lo ya decidido.
3. **Las ofertas van desglosadas**: el total con ofertas, el total sin ellas y la lista de
   las que se aplican con lo que ahorran. Un 2x1 es una regla sobre cuantas unidades
   compras, asi que con una unidad no se aplica y el total lo dice.

Y la comparacion se enseña siempre al lado, porque es lo que convierte el total en una
decision: *"asi pagas 4,81; todo en Carrefour serian 5,05; repartido entre Aldi y
Carrefour, 4,81 (el ahorro no paga la segunda parada)"*.

---

## 7. Lo que hace la lista cuando esta llena

Esto es lo que justifica todo lo anterior. Una vez hay catorce cosas apuntadas,
la app tiene que contestar **donde se compra**:

    TODO EN UNA TIENDA
      Mercadona    47,30 EUR     le faltan 2 de 14
      Alcampo      48,10 EUR     los 14
      Carrefour    51,05 EUR     los 14

    REPARTIDO
      Alcampo + Mercadona    41,80 EUR    ahorras 6,30 EUR
      (9 productos en Alcampo, 5 en Mercadona)

Tres reglas que no se negocian:

- **Maximo dos tiendas por defecto.** Un reparto entre cinco tiendas que ahorra
  ocho euros no lo hace nadie, y ofrecerlo es ruido con aspecto de consejo.
- **Lo que falta se dice por su nombre**, no como un numero: "en Mercadona no
  encuentro: cafe en grano 1 kg, atun en aceite pack 6".
- **Los precios de mas de tres dias se ensenan con su fecha pero no deciden.**
  Si Carrefour no se dejo capturar ayer, sus precios no eligen tienda.

Y una cosa que se calcula pero no se ensena por defecto: **cada persona ve el
reparto segun las cadenas que tiene cerca**. Si tu madre no tiene Aldi al lado,
su pantalla no le puede decir que lo mas barato esta en Aldi.

---

## 7. Lo que no lleva

- **Historial de cambios visible.** `anadido_por` y `tachado_por` bastan. Una
  pantalla de "actividad" es un producto de equipo, no una lista de la compra.
- **Comentarios por linea.** El campo `nota` cubre "la de cristal". Una
  conversacion dentro de una lista de la compra no la quiere nadie.
- **Plantillas y listas recurrentes.** Suenan bien y nunca se usan. Si al cabo
  de unos meses ves que repites la misma lista, se anade entonces, sabiendo cual
  es.
- **Notificaciones push.** Necesitan un servidor siempre accesible, y el PC se
  apaga. La app ensena los cambios al abrirla.
