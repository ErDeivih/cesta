# La dirección visual · **qué es cada token y por qué** -- 15/10/2026

*Este documento **no es un adorno**: *es **el contrato** entre lo que se decide y lo que se escribe.* *
*Existe porque el 15/10/2026 se midio que la app tenia **paleta y una sola medida**, *y con eso
**cada pantalla se inventaba sus numeros**: *996 lineas de clases en linea, *y dos tarjetas del mismo
rango con distinto aspecto en dos pantallas.* *

*Y **lo que se escribe aqui tiene que estar en `tailwind.config.js`**, *y al reves: *hay una prueba
(`tests/test_interfaz.py`) que **falla si una clase no existe en el tema**, *porque Tailwind **la omite
en silencio** y el estilo desaparece sin un solo aviso.* *

---

## 1. *** La idea, *en una frase ***

> *** Un archivo doméstico: papel, tinta y un solo acento. *** *

*No es un panel de control: *es **el cuaderno de la casa** *-- la lista de la compra, el recetario, lo
que se ha comido.* *Y de ahi sale todo lo demas: *los colores son **de papel y no de pantalla**, *
las superficies tienen **grosor**, *y el acento **aparece poco** porque en un cuaderno subrayar todo
es no subrayar nada.* *

*La frase ya estaba escrita en el codigo *(-- `estilos.css`: *«Direccion visual de SUPERAPP-01:
archivo domestico, no panel generico» --)*. *Lo que faltaba era **desarrollarla.*** *

## 2. *** El color: *seis papeles y una tinta ***

*Los valores estan en `estilos.css`, **en los dos temas**, *y son variables porque estas clases se
escriben **sin el prefijo `dark:`** *-- y asi **un mismo `text-tinta-suave` vale de dia y de noche**, *
sin que nadie tenga que acordarse del par.* *

| token | que es | por que |
|---|---|---|
| `marfil` | **el lienzo** | *el fondo de la casa: *un blanco crudo, **calido** |
| `papel` | **una superficie dentro** | *la tarjeta, el formulario |
| **`papel-alto`** | *** lo que flota por encima *** | *sin esta, **en modo oscuro una tarjeta y un dialogo son el mismo color**, *y la profundidad **no se puede ver** por mucho que se sombree* |
| `tinta-fuerte` | **el texto** | *13,42:1 sobre marfil |
| `secundaria` | **el texto auxiliar** | *5,74:1 |
| `borde` / `borde-fuerte` | **el limite** | *el suave **no vale para delimitar un control**: *da 1,43:1 |
| `terracota` | *** el unico acento *** | *la seccion activa y la accion: *4,86:1 |
| **`terracota-suave`** | *** el acento como fondo *** | *para la seccion activa y los avisos suaves, *donde el terracota puro **seria un grito** |
| `error` · `aviso` · `bien` | **lo que significa algo** | *siempre el mismo tono: *un rojo en esta app **quiere decir lo mismo siempre** |

*** Lo que NO se hace con el color ***: *no se usa `terracota` en un texto largo, *no se anaden
paletas de Tailwind *(-- `bg-slate-100` --)* *a una pantalla nueva, *y **no se inventa un tono**:
*si falta uno, **se anade aqui primero y en los dos temas.*** *

## 3. *** La tipografia: *seis pasos, y las fuentes se sirven ***

```
*** `antetitulo` ***  *0,6875 rem*  *-- *versalitas: *en que seccion estas. *** Ya existia y se conserva *** *
*** `etiqueta` ***    *0,8125 rem*  *-- *etiquetas, metas y notas al pie *
*** `cuerpo` ***      *0,9375 rem*  *-- *el texto. *15 y no 16: *en una tabla de precios, 16 obliga a menos columnas *
*** `entrada` ***     *1,0625 rem*  *-- *el parrafo que explica de que va la pantalla *
*** `titulo` ***      *1,5 rem*     *-- *titulo de seccion. *** Serif *** *
*** `portada` ***     *2,25 rem*    *-- *el titulo de la pantalla. *** Serif *** *
```

*** Seis y ni uno mas. *** *Antes cada pantalla elegia su `text-lg` o `text-2xl` **a ojo**, *y por eso
dos titulos del mismo rango salian de distinto tamano.* *

*** Y el interlineado va PEGADO al tamano ***, *no suelto: *un titulo de 36 px con el interlineado
del cuerpo son **dos lineas que se tocan.*** *

*** Y las fuentes se SIRVEN, en local. *** *Estaban declaradas *(-- `Fraunces` y `IBM Plex Sans` --)*
*y **no se servian**, *asi que los titulos salian en **Georgia** *-- lo dice su propio comentario y lo
confirma la captura `docs/ui/capturas/01-inicio.png`.* *Y se sirven **desde el propio sitio** porque la
app se sirve desde casa y **la primera pintada no puede depender de `fonts.googleapis.com`** *-- que ya
estaba decidido antes.* *

## 4. *** La profundidad: *tres niveles, y en oscuro no la da la sombra ***

```
*** llano ***      *-- *nada. *El lienzo y el texto. *
*** apoyado ***    *-- *una tarjeta que se puede pulsar *
*** alzado ***     *-- *una tarjeta en primer plano, *una barra pegada *
*** flotante ***   *-- *lo que **interrumpe**: *dialogos y menus *
```

*** Y en claro las sombras son CALIDAS ***, *no grises: *una sombra gris pura sobre marfil **se ve
sucia**, *porque el marfil es calido y el gris es frio, *y el ojo lo nota aunque no sepa decir por
que.* *Asi que llevan **el marron del papel** dentro.* *

*** Y en oscuro, el aviso que importa ***: *una sombra sobre un fondo casi negro **no se ve** *-- *no hay
luz que oscurecer.* *Asi que alli **la profundidad la da el color de la superficie**: *lo que flota es
**mas claro** *(-- `papel-alto` --)*, *que es **como se comporta la luz de verdad**, *y la sombra solo
**la remata.*** *

## 4.bis *** Y por que **no hay opacidad** en la cabecera ***

*La cabecera pegada era `bg-white/95` con `backdrop-blur`, *y **se ha quedado solida**.*
*Y no es un atajo, *son **dos motivos**: *

```
*** 1) EL SISTEMA DE TOKENS NO HACE OPACIDAD, *A PROPOSITO *** *
   *-- *`bg-papel/95` **no vale**: *Tailwind escribira `rgb(var(--papel) / .95)`, *y
      *dentro hay un `#rrggbb`, *o sea **un color invalido que el navegador ignora** ⚠️
   *-- *y **lo dice el test de colores**, con ese motivo escrito ✓
*** 2) Y NO HACE FALTA *** *
   *-- *el contenido **pasa por debajo** igual, *asi que el desenfoque **no se ve** ✓
   *-- *una cabecera **solida sobre lienzo calido** es lo que la direccion quiere ✓
```

*Si algun dia hace falta de verdad, *la forma **no** es volver al `/95`: *es declarar el
token **como canales** *(-- `--papel-rgb: 251 249 244` --)* *y un color con
`<alpha-value>`, *que es **como Tailwind soporta opacidad sobre variables.** *
*Y entonces se anade aqui, *y a los dos temas.* *

## 5. *** Los radios: *tres y una pastilla ***

```
*** `nota` ***      4 px   *-- *lo mas pequeño: *una etiqueta dentro de una linea *
*** `campo` ***     8 px   *-- *lo que **se pulsa o se escribe** *
*** `tarjeta` ***   14 px  *-- *una superficie con contenido dentro *
*** `hoja` ***      20 px  *-- *lo que **flota** por encima *
```

*Antes habia `rounded`, `rounded-md`, `rounded-lg` y `rounded-full` mezclados **sin criterio**, *y una
tarjeta con **el mismo radio que un boton** no se lee como tarjeta.* *

## 6. *** El movimiento: *dos duraciones y una curva ***

```
*** `rapida` ***  *120 ms*  *-- *lo que **responde al dedo**: *hover, foco, un boton *
*** `normal` ***  *220 ms*  *-- *lo que **cambia de estado** o entra en pantalla *
*** `suave` ***   *cubic-bezier(0.2, 0, 0, 1)*  *-- *sale rapido y frena largo: *«esto ya ha llegado» *
```

*** Y `prefers-reduced-motion` YA ESTA RESUELTO, globalmente ***, *en `estilos.css`.* *No hay que
repetirlo en cada sitio* *-- *y **la decision esta escrita alli**: *quien activa el ajuste lo hace
porque **el movimiento le hace daño o le marea**, *asi que **el error caro es dejar algo moviendose**,
no apagar de mas.* *

## 7. *** El ritmo: *el hueco vertical ***

```
*** `bloque` ***   *1,5 rem*  *-- *entre dos cosas de la misma seccion *
*** `seccion` ***  *2,5 rem*  *-- *entre dos secciones *
*** `pagina` ***   *3,5 rem*  *-- *el aire de arriba y de abajo de una pantalla *
```

*** Es lo que arregla el «60 % vacio» *** *de la captura, *aunque **no entero**: *el hueco que sobra en
`01-inicio.png` **no es que falte ritmo**, *es que **falta estructura** *-- *y eso es la FASE 5.* *
*Lo que si arregla el ritmo es lo otro: *el contenido **deja de apiñarse arriba** y de flotar.* *

*Y hay un **ancho de lectura**: `max-w-lectura` (42 rem), *porque **78 rem de parrafo son 150
caracteres** y a partir de 80 la vista **se pierde de linea.*** *

## 8. *** Lo que **NO** entra en esta dirección, *y por qué ***

```
*** NO SE SUBE A TAILWIND v4 *** *para poder usar `shadcn-ui--lint`: *subir una version de base *
   *para ganar un analizador es **cambiar el suelo por la herramienta** ⚠️
*** NO SE ADOPTA `arc-library` ENTERA *** *(-- *MIT, React 19 + TS, *110 componentes --)*: *
   *se **leen sus fichas** y se adoptan **piezas**, *diciendo **cuales** y con **su licencia y su
   origen**, *porque MIT permite copiar **conservando el aviso** ✓
   *-- *y **no se usa su servidor MCP**, *que sale a `uiarc.dev`: *esto es una app de casa ✓
*** NO HAY INTERRUPTOR DE TEMA ***: *lo decide el sistema. *Un boton que nadie pulsa dos veces es
   *una cosa mas que mantener *-- *y ya estaba decidido ✓
*** Y NO SE INVENTAN DATOS ***: *la direccion **no toca** ni precios, *ni calorias, *ni densidades, *
   *ni equivalencias ✓
```

## 9. *** Y el desconocido, *declarado ***

```
*** LAS PIEZAS DE `arc-library` NO SE HAN PROBADO ***: *la ficha es **evidencia documental** *
   *-- *se leyeron README, licencia y metadatos, *y **no se clono, ni se instalo, ni se ejecuto** ⚠️
*** Y HAY CINCO FICHAS SIN LEER ***: *`vojtaholik--good-css`, *`tejashmakwana--motionmaxxing`, *
   *`glass-hq--liquid-glass`, *`deeplethe--solid-glass`, *`shader-effects-inc--shaders` ⚠️
*** Y EL ESPACIADO NO LO CUBRE LA PRUEBA ***: *sus utilidades son **numericas** *(-- `p-4`, `gap-6` --)* *
   *y su lista por defecto es larga y abierta, *asi que una comprobacion por nombre daria **mas ruido
   que señal** *-- *y **un test que grita en falso se acaba ignorando** ✓
```

---

# *** 10. *Un fallo de PANTALLA y un fallo de ACCION no son lo mismo *** *

*15/10/2026. *Esto no es una preferencia: *es una distincion que **costo cuatro rondas
de no entender por que los arreglos no cundian.*** *

```
*** FALLO DE PANTALLA ***: *la consulta que llena la pantalla **fallo**, *asi que *
   *** no hay nada que enseñar.*** *
   *-- *se pinta *** `Fallo` ***: *panel, *con titulo, *y con «Volver a intentarlo» ✓
   *-- *y va **donde iria el contenido**, *porque **no hay contenido.*** *

*** FALLO DE ACCION ***: *una operacion concreta **fallo**, *y **el resto sigue ahi.*** *
   *-- *«no he podido guardar», *«no he podido borrar», *«no he podido apuntar» ✓
   *-- *lo que hace falta es *** una linea, *al lado de lo que se pulso *** *
   *-- *y *** NO `Fallo` ***: *un panel de ancho completo con un titulo de pantalla,
   *en medio de un formulario que sigue funcionando, *dice *** algo mas grave de lo
   *que pasa *** ✓✓✓
*** -> *y `Fallo` acepta `titulo`, *pero **eso no lo arregla**: *el problema de un fallo
   *de accion **no es el texto, *es el TAMANO.*** ✓
```

*** Y de aqui sale lo que hay que hacer con los que quedan ***: *los `{x.error && <p…>}`
*-- *`crear`, *`planificar`, *`duplicar`, *`apuntar`, *`borrar` --* *** no son el mismo
defecto que los ocho que ya se arreglaron ***, *aunque **se parezcan**.* *Lo que
comparten es que estan **escritos a mano y con cuatro tamanos de letra**; *lo que **no**
comparten es que deban ser un panel.* *

*** Y lo que hace falta, *que todavia NO existe ***: *una pieza pequeña de mensaje de
accion *(-- *una linea, *tono de error o de aviso, *y sitio para un reintento al lado
del boton --).* *`Etiqueta` **se le parece** *y podria servir de base; *pero **decidirlo
mirando una pantalla**, *no aqui.* *

*** Y LA LECCION, *que es la de toda la noche otra vez ***: *dos cosas que **se parecen**
no son **la misma**, *y unificarlas porque se parecen es como se rompe una interfaz
**que funcionaba.*** *
