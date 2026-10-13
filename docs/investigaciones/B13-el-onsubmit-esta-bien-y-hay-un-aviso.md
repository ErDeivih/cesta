# B13 · **El `onSubmit` es CORRECTO -- y hay un `Aviso` de error que no se capturo**

*(13 de octubre de 2026. **Y la lectura contesta, y a la vez dice cual es la prueba que falta.**)*

## 1. `FormularioEntrar`, entero (l71-116)

```tsx
l71  function FormularioEntrar({ alEntrar }: { alEntrar: () => void }) {
l72    const [usuario, setUsuario] = useState('')
l73    const [clave, setClave] = useState('')
l74    const entrar_ = useMutation({
*** l75      mutationFn: () => entrar(usuario.trim(), clave), ***
l76      onSuccess: alEntrar,
l77    })
l80    <form
l82      onSubmit={(e) => {
l83        e.preventDefault()
*** l84        if (usuario.trim() && clave) entrar_.mutate() ***
l85      }}
l89      <input
*** l90        value={usuario} ***
*** l91        onChange={(e) => setUsuario(e.target.value)} ***
l92        autoComplete="username"
l96        autoCapitalize="none"  spellCheck={false}
l103     <input
l104       type="password"
*** l105       value={clave} ***
*** l106       onChange={(e) => setClave(e.target.value)} ***
l107       autoComplete="current-password"
*** l111     <Boton type="submit" disabled={entrar_.isPending}> ***
l112       {entrar_.isPending ? 'Entrando…' : 'Entrar'}
l114     {entrar_.isError && (
*** l115       <Aviso tono="mal"> ***
*** l116         <p>{textoDeError(entrar_.error)}</p> ***
```

## 2. Y el codigo esta **bien**: `preventDefault`, guarda, `mutate`, y los dos campos controlados

```
*** Y POR TANTO: *** *** el sexto sospechoso TAMBIEN SE CAE *** -- *no hay **nada raro** en el `onSubmit`. *
   -> *`preventDefault()` esta (l83)*
   -> *la guarda es la del alta (l84), *y **por eso se sospechaba de ella***
   -> *y los campos son **controlados** (`value` + `onChange`), *que es **la forma correcta** *
```

> *** O sea: **el `onSubmit` no es el fallo.** *Y **los seis sospechosos se han caido**, *y **cada uno con su
> evidencia.** *

## 3. *** PERO HAY ALGO QUE NO SE MIRÓ, Y ES LA PIEZA (l115): EL AVISO DE ERROR ***

```
l114  {entrar_.isError && (
l115    <Aviso tono="mal">
l116      <p>{textoDeError(entrar_.error)}</p>
```

> *** O sea: *** *** si el login **falla**, la pantalla **pinta un aviso con el error del API** *** -- *y **el API
> tiene dos errores distintos**: *
> ```
> *** 401 «Usuario o contrasena incorrectos.» ***   *-- `main.py:91`*
> *** 422 «Field required» ***                      *-- *y es **el que da si falta un campo***
> ```
>
> *** Y **MIS CAPTURAS NO LO HABRIAN VISTO**, *y hay dos razones, y las dos son mias: ***
> ```
> 1) *** la captura del final fue de `/recetas`, no de `/compra/listas` ***
>    -> *o sea: **mire la pantalla de despues, y no **la de la puerta**, *que es **donde saldria el aviso** *
> 2) *** y si la guarda de l84 NO se cumplio, tampoco hay aviso ***
>    -> *porque `mutate` **no se llama**, *y `isError` **se queda en falso** *
> ```
>
> *** O sea: **el aviso distingue los dos casos que quedan**, *y **es una sola captura.** *
> ```
> *** SI HAY AVISO ***  -> *el `onSubmit` **SI mando**, *y **el API dijo que no** -- *y **el aviso dice por que**
>                        *(401 o 422)*
> *** SI NO HAY AVISO *** -> *la guarda de l84 **no se cumplio**: *el estado de React **estaba vacio** *
> ```

## 4. Y la prueba, entonces, es **la misma llamada con la captura en el sitio correcto**

```
*** LA PRUEBA · cinco acciones, y se captura LA PUERTA, no la pantalla de despues: ***

  1. `goto`  *** `/compra/listas` ***
  2. `wait_for_timeout` 2000          *-- *para que monte*
  3. `fill`  «Usuario»  = b13-recorrido-2301
  4. `fill`  «Clave»    = ensayo-b13-2301
  5. `click` «Entrar»

  *** y `capture.at_end: [url, accessibility]`  --  *** Y SIN SALIR DE `/compra/listas` *** ***
```

> *** Y **eso es lo que decide**, *y **es barato**: *cinco acciones, y **una captura en el sitio donde el aviso
> vive.** *
>
> *** Y **no hizo falta antes porque **las capturas fueron de la pantalla siguiente** *** -- *y **eso es el error de
> metodo de esta serie**: *se miro **el efecto** *y **no **la causa**; *y **la causa esta en `l114`.** *

## 5. Y el estado, con **seis descartes y una prueba**

```
RECORRIDO 4b  ->  *** NO ***, y los seis sospechosos:
  1. ~~la cuenta~~     -> *esta en la base*                        *** DESCARTADO ***
  2. ~~la clave~~      -> *`/api/entrar` da **200***                *** DESCARTADO ***
  3. ~~el montaje~~    -> *`fill` de 52 ms, y sigue igual*          *** DESCARTADO ***
  4. ~~el submit~~     -> *`l111`: `type="submit"`*                  *** DESCARTADO ***
  5. ~~`credentials`~~ -> *`l26` y `l58`: los dos lo mandan*        *** DESCARTADO ***
  6. ~~el `onSubmit`~~ -> *** `l82-85`: preventDefault, guarda y mutate -- esta BIEN ***  *** DESCARTADO ***
  *** -> y por tanto el fallo esta EN LA GUARDA (l84) o EN LA RESPUESTA (l114-116) ***
  *** y el `Aviso` de l115 los distingue. ***
```

> *** Y **es un buen sitio para parar**: *se descarto **lo que se podia medir**, *y **lo que queda es **una captura
> bien colocada** *** -- *que es **lo contrario de adivinar.** *
