# B13 · **El fallo del recorrido 4, EXPLICADO**: hay DOS formularios, y el de alta tiene TRES campos

*(13 de octubre de 2026. **Y la causa esta en `Cesta.tsx:141`, no en el navegador ni en el API.**)*

## 1. La respuesta, en cuatro lineas

```
`plataforma/web/app/src/paginas/Cesta.tsx`

  l141  *** function FormularioAlta({ alEntrar }) { ***      <- *** y es OTRO componente ***
  l142  const [nombre,  setNombre]  = useState('')
  l143  const [usuario, setUsuario] = useState('')
  l144  const [clave,   setClave]   = useState('')
  l146  mutationFn: () => *** registrarse(usuario.trim(), nombre.trim(), clave) ***
  l155  if (*** nombre.trim() && usuario.trim() && clave ***) alta.mutate()
  l159  <span>*** «Tu nombre» ***</span>            <- *** y EL PRIMER CAMPO ES ESE ***
```

> *** O sea: *** *** el alta **SI manda `nombre`** -- *el frontend **no tiene el fallo (B)** que se temia. *
>
> *** Y **hay DOS formularios, y son distintos**: ***
> ```
> *** ENTRAR ***   -> *`textbox «Usuario»` y `textbox «Clave»`, y `button «Entrar»`*   -- *dos campos*
> *** ALTA ***     -> *** `«Tu nombre»` + `«Usuario»` + `«Clave»` ***                    -- *** TRES campos ***
> ```
>
> *** Y **lo que hace `button «Créala»` es **CAMBIAR de formulario** *** -- *del de entrar **al de alta.** *
> *Y **por eso la captura de `/compra/listas` mostraba dos**: *mostraba **el de entrar**, *y **el de alta todavia
> no estaba.** *

## 2. Y entonces **el fallo del recorrido 4 queda explicado, paso por paso**

```
MI RECORRIDO HIZO:
  1. goto `/compra/listas`                  -> *el formulario de ENTRAR*
  2. fill textbox «Usuario» = b13-recorrido-2251
  3. fill textbox «Clave»   = ensayo-b13-2251
  4. *** click button «Créala» ***           -> *** y esto CAMBIA al formulario de ALTA ***
  5. wait_for textbox «Usuario» *hidden*     -> *** FAILED: timed out ***

*** Y POR QUE FALLO, ahora se sabe: ***
  *** al pulsar «Créala», el formulario de alta aparece *** con *** «Tu nombre» VACIO ***
  -> *y su `onSubmit` tiene la guarda de `l155`: **`if (nombre.trim() && usuario.trim() && clave)`** *
  *** -> y como `nombre` esta vacio, `alta.mutate()` NO SE LLAMA ***
  *** -> no hay peticion, no hay 422, no hay error: NO PASA NADA ***
  *** -> y el `textbox «Usuario»` ... SIGUE AHI *** -- *porque **es el del formulario de alta.** *
```

> *** O sea: *** *** **el fallo fue mio, y la aplicacion hizo lo correcto.** *
>
> *** Y **la guarda de `l155` es la que lo explica sin ruido**: *** *un formulario **incompleto** *con un `onSubmit`
> **que comprueba los tres campos** -- *y **si falta uno, NO manda nada.** *
>
> *** Y **fue sin error visible**: *** *ni 422, ni consola, ni peticion. *Por eso **la consola no habria dicho
> nada** -- *y **la medida que yo creia que faltaba (console, page-errors) NO era la que hacia falta.** *
>
> *** Y **lo que hacia falta era leer el formulario** *** -- *que es **exactamente lo que dije en la ronda 226**:
> *«la comprobacion es una: leer el componente del formulario.» *

## 3. Y el recorrido 4 **se puede hacer**: solo hay que **rellenar el campo que falta**

```
RECORRIDO 4 · corregido, y con SEIS campos llenados:

  PASO 1  `goto`  *** `/compra/listas` ***
  PASO 2  `fill`  *** rol textbox, nombre «Usuario» ***  = b13-recorrido-<sello>
  PASO 3  `fill`  *** rol textbox, nombre «Clave» ***    = ensayo-b13-<sello>
  PASO 4  `click` *** rol button, nombre «Créala» ***      *-- y CAMBIA al formulario de alta*
  PASO 5  *** `fill`  rol textbox, nombre «Tu nombre» *** = *un nombre legible, y **el que faltaba***
  PASO 6  *y volver a rellenar «Usuario» y «Clave»*  *** si el cambio de formulario los vacia ***
          *-- y **eso es un dato, no una suposicion**: *se ve **en el paso siguiente** *
  PASO 7  `click` *** rol button, nombre «Créala» ***      *-- *el del formulario de alta, si es otro*
  PASO 8  *** `wait_for` -> que el `textbox «Usuario»` YA NO ESTE ***   -- *** y ahora si: porque ENTRARA ***
  PASO 9  `goto`  *** `/calorias` ***
```

> *** Y **los pasos 5 y 6 son la leccion**: *** *al cambiar de formulario, **hay que volver a mirarlo** -- *y **no
> suponer que los dos campos siguen.** *
>
> *** Y **el paso 8 es el mismo de antes, y ahora significa otra cosa**: *** *antes **no pasaba porque el formulario
> seguia ahi**; *y **ahora pasara porque se habra ido** -- *que es **lo que «entrar» quiere decir.** *

## 4. Y **una cosa mas, que la lectura deja dicha**: `api/registro.py` tiene la verdad de las reglas

```
`Cesta.tsx:136-139`:  *** «Las reglas viven en la API. *** `minLength` es solo la pista del navegador para no
escribir tres caracteres y enterarse despues; *** LA VERDAD LA DICE `api/registro.py` Y SU 422 SE ENSEÑA TAL CUAL. ***
Copiar aqui el minimo de la clave seria *** UNA SEGUNDA COPIA QUE SE QUEDA VIEJA EL DIA QUE CAMBIE. ***» *
```

> *** Y **es la doctrina otra vez, y aplicada a un formulario**: *** *** la validacion **no se duplica**; *se **deja
> en el API**, *y **su 422 se enseña.** *
>
> *** Y **explica la guarda de `l155`**: *** *esa **no es** una regla de negocio (no comprueba longitudes); *es
> **«no mandes un formulario a medias»** -- *y **eso si es del formulario.** *
>
> *** Y **por eso el `422` de mi sonda fue **util y no un fallo**: *** *el API dijo **que campo faltaba**, *y
> **`api/registro.py` es quien lo sabe.** *

## 5. Y el estado, que cambia

```
RECORRIDO 4 · `/calorias`  -> *** INTENTADO, FALLO, Y EL FALLO ESTA EXPLICADO ***
   *** y NO es un fallo de la aplicacion: *** *es **un recorrido mal hecho** -- *me faltaba **un campo.** *
   *** y la aplicacion hizo lo correcto: *** *no mando un formulario **incompleto**, *y **no dejo un error.** *
*** Y AHORA SE PUEDE HACER: *** *los nueve pasos de arriba, y **el 5 es el que faltaba.** *
```
