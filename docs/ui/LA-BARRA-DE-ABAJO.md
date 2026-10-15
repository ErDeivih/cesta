# *** La barra de abajo del movil: *escrita, *y perdida en un refactor *** *

*15/10/2026. *Existe porque **el objetivo la pide por su nombre** *(-- «*y la barra de
abajo del movil **que ya tiene reglas escritas**» --)* *y porque **yo di la FASE 3 por
cerrada sin comprobarlo.*** *

---

## 1. *** Que hay, *exactamente ***

```
*** `src/componentes/Nav.tsx:143-145` *** *
   *// `pb-[env(safe-area-inset-bottom)]` para el iPhone, que tiene una raya*
   *className="fixed inset-x-0 bottom-0 z-40 border-t border-borde bg-papel …"*
*** -> *la barra esta ENTERA: *fija abajo, *con su borde, *su `z-40`, *y el hueco
   *del iPhone resuelto con `env(safe-area-inset-bottom)` ✓
```

## 2. *** Y por que no se ve ***

```
*** `Nav.tsx` NO LO IMPORTA NADIE *** *-- *salvo `Cabecera.tsx`, *que **tambien esta
   *muerto.*** *Los dos estan en `LOS-FICHEROS-MUERTOS.md` ⚠️
*** y **NO HAY OTRA**: *buscando `fixed bottom-`, *`inset-x-0 bottom`, *`safe-area` *
   *y `bottom-0` en TODO `src/`, *los unicos resultados son **las tres lineas de
   *`Nav.tsx`*** ✓
*** -> *** la barra de abajo del movil esta escrita y NO SE RENDERIZA *** ⚠️⚠️
```

## 3. *** Y como se perdio, *que es lo que importa ***

```
*** `Cabecera.tsx` + `Nav.tsx` eran el layout ANTERIOR: *cabecera arriba, *barra abajo,
   *y **la barra tenia sus reglas escritas** ✓
*** `Suite.tsx` los SUSTITUYO *(-- es el que tiene `APLICACIONES`, *el lateral y el
   *cajon de movil --)* *y **se llevo el lateral y el cajon, *pero NO la barra** ⚠️
*** -> *** no es que la barra no se hiciera nunca: *es que se PERDIO al cambiar de
   *layout *** ✓✓✓
*** -> *y por eso esta en un fichero muerto: *los ficheros muertos **no son solo
   *basura**, *son **la version anterior de la app**, *y ahi dentro hay cosas que la
   *nueva no tiene ✓✓✓
```

## 4. *** Y LO QUE DIJE MAL ***

```
*** dije, en cinco informes seguidos, que la FASE 3 estaba CERRADA *** *
*** y **no lo esta**: *la mire por el lado del lateral *(-- que si quedo hecho: *
   *los iconos, *el estado activo, *el cajon --)* *y **no mire el otro lado**, *
   *que es la barra de abajo ⚠️
*** -> *y el objetivo la nombra **en la misma frase** que lo que si hice ✓
*** -> *** comprobar la mitad de un requisito y dar el requisito por bueno es
   *exactamente el defecto que llevo toda la sesion cazando, *cometido por mi *** ✓✓✓
```

## 5. *** Y lo que falta, *concreto ***

```
*** 1) La barra, *en `Suite.tsx` *(-- que es el que se pinta --)*, *con las tres
   *aplicaciones y su icono, *`fixed inset-x-0 bottom-0`, *y **solo en pantalla
   *estrecha** *-- *el lateral ya lleva `lg:` --.* *
*** 2) Y el hueco del iPhone: *la regla **ya esta escrita** en `Nav.tsx`, *asi que
   *no hay que inventarla: *`pb-[env(safe-area-inset-bottom)]`.* *
*** 3) Y el sitio para que no tape: *el `main` de `LayoutSuite` necesita un
   *`pb` que deje hueco a la barra, *o el ultimo renglon de cada pantalla queda
   *detras ✓
*** 4) Y decidir **que lleva**: *las tres aplicaciones bastan para no perder la
   *orientacion, *pero el menu de secciones del cajon **tambien esta en el
   *lateral**, *asi que la barra **no necesita repetirlo.*** *
```

*** Y no se copia `Nav.tsx`: *se **rehace** en `Suite.tsx` con los tokens y con los
iconos que ya existen.* *Lo que se **reutiliza** es **la regla del iPhone**, *que es la
unica parte que era dificil de recordar.* *
