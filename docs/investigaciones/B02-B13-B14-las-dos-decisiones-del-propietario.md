# B02 · B13 · B14 · **Las dos decisiones del propietario**, y lo que se hace con ellas

*(13 de octubre de 2026. **Y son las dos preguntas que llevaban nueve rondas escritas sin preguntar.**)*

## Decision 1 · El navegador (B02 · B13)

> *** Pregunta: *** *«Alcampo abre una ventana real de navegador para pasar el reto AWS WAF, y el plan dice marcarlo
> `requiere_interaccion`. Y B13 necesita navegador para los cinco recorridos. ¿Qué hago?» *
>
> *** Respuesta del propietario, literal: ***
>
> > *** «Me da igual como, pero que se haga DE FORMA AUTOMATICA SIN QUE TENGA QUE HACER YO NADA.» ***

```
*** LA REGLA QUE SALE DE AHI, Y NO DEJA LUGAR A DUDAS: ***
  1) *** AUTOMATICO ***            -> *sin ventana visible, y **sin nadie delante.** *
  2) *** Y SIN QUE EL HAGA NADA *** -> *y **si el reto pide un clic humano, NO SE PIDE**: *
                                      *** se PARA, y se declara el alcance. ***
```

> *** Y **es exactamente lo que B02 midio que pasa**: *** *`RITMO["alcampo"] = 0.15` **ya es «menos presion»**, *y su
> comentario dice que **el 8 de sep el reto escalo a pedir un clic humano.** *
>
> *** O sea: **el limite esta medido, y la decision del propietario coincide con la doctrina del codigo**: ***
> *** bajar la presion **todo lo que se pueda**, y **si aun asi pide un humano, se dice.** *
>
> *** Y **NO se elude ningun CAPTCHA/WAF** *** -- *que es **lo que el encargo prohibe por escrito**: *«no eludas
> CAPTCHA/WAF ni confundas desafio con catalogo vacio». *
>
> *** Y **su consecuencia para B13**: *** *los cinco recorridos **se intentan en modo oculto**; *y **si la web
> responde sin necesitar nada, se hacen enteros.** *

## Decision 2 · Las copias (B14)

> *** Pregunta: *** *«`OPERACION.md:459` dice que el crudo es lo unico irrecuperable y que un `robocopy` semanal de
> `data\raw` cubre el riesgo entero. Pero `data/diario.sqlite` y `data/recetas.sqlite` tambien son irreemplazables y
> no estan en `data\raw`. ¿Que se copia hoy al disco externo?» *
>
> *** Respuesta del propietario, literal: ***
>
> > *** «No entiendo, LO QUE MEJOR CONSIDERES.» ***

```
*** Y «LO QUE MEJOR CONSIDERE» ES ESTO, Y POR LAS RAZONES QUE YA ESTAN MEDIDAS: ***
  1) *** el manual tiene razon en el criterio *** -- *«el crudo es lo unico irrecuperable» **como clase de dato**:
     lo derivado (bronce, plata, oro, API) **se recalcula**; lo observado (las capturas) **no.** *
  2) *** y le falta una pieza *** -- *porque **hay DOS datos que tampoco se recalculan**, y **no son crudo**:
     `data/diario.sqlite` (11 entradas: **lo que una persona comio**) y `data/recetas.sqlite` (42 recetas, 42 del
     plan, 43 versiones, 7 traspasos: **escrito a mano o importado**). *
  3) *** y por tanto, lo mejor es: la copia lleva LAS TRES COSAS *** -- `data\raw` + los dos `.sqlite` privados.
     *Y **el criterio del manual, aplicado con rigor, ya los incluia** -- *solo que **su frase solo nombra el crudo.** *
```

> *** Y **NO SE EJECUTA NINGUNA COPIA**, y hay dos motivos, y los dos son del encargo: ***
> ```
> *** «no despliegues publicamente ni abras puertos» ***      -> *un disco externo no es publico, pero **es un destino**
>                                                               *que **no conozco**, y **elegirlo yo seria
>                                                               «subir datos a un sitio elegido por el agente»** *
> *** «pregunta solo por... acciones fuera del encargo» ***     -> *copiar a un disco **es una accion de la maquina**,
>                                                               *no del repositorio*
> ```

## Y lo que se deja hecho, en vez de una promesa

```
*** UNA RECETA, para que la copia cubra lo irreemplazable: ***

  robocopy "F:\aprendizaje\scrap\data\raw"            "E:\cesta\raw"      /MIR /R:2 /W:5
  robocopy "F:\aprendizaje\scrap\data"  "E:\cesta\privado"  diario.sqlite recetas.sqlite /R:2 /W:5

  *** y NO se copian *** (porque **se recalculan**):
    data\bronze · data\silver · data\gold        <- *derivados del crudo*
    data\raw/**/*.parquet  ... *no: el crudo SI*
    __pycache__ · .git · node_modules            <- *reconstruibles*
    y *** `data/recetas.sqlite` NO: ese SI*** -- *es de los irreemplazables*
```

> *** Y **la comprobacion de que la copia sirve** es **una restauracion**, *y B14 la pide por escrito:*
> *** «copias de PostgreSQL, SQLite privados y metadatos; restauracion de LOS TRES, hashes, retencion y
> verificacion» *** -- *o sea: **una copia que no se ha restaurado nunca no es una copia: es una esperanza.** *
>
> *** Y **eso es lo que queda dicho y no hecho**, *con **su razon**: *restaurar **sobre las bases de casa** esta
> prohibido por el encargo («no restaures sobre bases existentes»), *y **restaurar en un disco que no conozco no lo
> puedo hacer yo.** *

## Y las dos decisiones, juntas, cierran **las tres cosas que quedaban**

```
1) *** EL NAVEGADOR *** -> *** DECIDIDO: automatico y oculto, y si pide un humano se para y se declara ***
                           *-> desbloquea **los cinco recorridos de B13**, y con ellos
                              **la ultima comprobacion de la restriccion del propietario.** *
2) *** LAS COPIAS ***   -> *** DECIDIDO: la copia lleva `data\raw` + los dos `.sqlite` privados ***
                           *-> y queda **la receta escrita**, y **la restauracion dicha como lo que falta.** *
3) *** LA PREDICCION *** -> *** manana a las 06:00 *** -- *y **no necesita a nadie.** *
```
