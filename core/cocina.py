"""F10 / `R05`: **el modo cocina** -- paso actual, ingredientes usados, temporizadores y reanudacion.

El criterio (`docs/SUPERAPP-COMPETENCIA-Y-REA.md:105`) dice:

> **Paso actual, ingredientes usados, temporizadores** y **reanudacion sin conexion cuando sea viable**.

**Medido el 11 de octubre de 2026** (`docs/investigaciones/F09-recetario.md` §10), *el modo cocina **no existe** --
y lo mejor del hallazgo fue que **el propio proyecto lo dijo sin querer**: `plataforma/prueba_navegador.py:603`,
«y no es una visita guiada: **no hay pasos que pasar**».*

## Y la parte que hay que pensar no es el paso: es el **tiempo**

**«Paso actual» e «ingredientes usados» son estado, y el estado se guarda.** *Pero **un temporizador no se
guarda**: se **cuenta**.*

**Y ahi esta la decision de este modulo:** ***un temporizador NO es una cuenta atras.*** *Una cuenta atras vive
en la pantalla, y **muere con ella**: *si se apaga el movil, o se recarga, o se va la conexion, **el tiempo
transcurrido se pierde** -- *y quien esta cocinando **no se entera** hasta que algo se quema.*

**Un temporizador es una **hora de fin**.** *Se guarda `empezo_en` y `minutos`, y **lo que queda se calcula**. Asi
**reanudar es volver a leer**, y **funciona sin conexion** *porque **no hay nada que consultar**: el reloj lo
lleva el aparato.*

> **Es la misma forma que `F15` encontro en la aplicacion**: *React Query **pausa** las mutaciones y las reanuda
> -- *no las pierde.* **Y aqui: el tiempo **no se pierde**, porque **no se estaba contando**.*

**Y por eso este modulo no tiene ningun `tick`, ningun `sleep` y ningun bucle**: *tiene una funcion que dice
**cuanto queda**, y quien la llama decide cada cuanto preguntar.*
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

#: **Los formatos de tiempo que se reconocen en un paso.** *«15 minutos», «1 h 30 min», «90 s».*
#: *Se aceptan los que aparecen en recetas de verdad, y **lo que no casa no se inventa**.**
_MINUTOS = re.compile(r"(\d+)\s*(?:h|hora|horas)\b", re.I)
_MINUTOS2 = re.compile(r"(\d+)\s*(?:min|minuto|minutos)\b", re.I)
_SEGUNDOS = re.compile(r"(\d+)\s*(?:s|seg|segundo|segundos)\b", re.I)


def minutos_de(texto: str | None) -> int | None:
    """**Cuanto tiempo pide un paso, si lo dice.** *Y `None` si no lo dice.*

    **No se inventa un tiempo por defecto.** *Un paso que no dice «15 minutos» **no tiene 15 minutos**: no tiene
    ninguno, y ponerle uno seria **inventarle una instruccion a quien cocina**.* *Es la misma regla que «lo que no
    tiene cantidad no la gana» (`R04`, `core.recetas.escala`).*
    """
    if not texto:
        return None
    t = str(texto)
    total = 0
    visto = False
    for patron, factor in ((_MINUTOS, 60), (_MINUTOS2, 1), (_SEGUNDOS, 1 / 60)):
        m = patron.search(t)
        if m:
            total += int(m.group(1)) * factor
            visto = True
    if not visto:
        return None
    # *Se redondea hacia arriba: **un segundo de menos en un temporizador es un segundo de menos cocinando**.*
    return max(1, int(total + 0.999))


@dataclass
class Temporizador:
    """**Una hora de fin, no una cuenta atras.** *Ver el docstring del modulo.*

    *`empezo_en` es un instante, y `minutos` cuanto dura. **Lo que queda se calcula**, asi que **reanudar es
    volver a leer** -- *y funciona igual con la pantalla apagada, recargada o sin conexion.*
    """

    paso: int
    minutos: int
    empezo_en: datetime

    @property
    def acaba_en(self) -> datetime:
        return self.empezo_en + timedelta(minutes=self.minutos)

    def queda(self, ahora: datetime | None = None) -> timedelta:
        """*Cuanto falta.* **Negativo si ya paso** -- *y eso es informacion, no un error: «se paso hace 2
        minutos» es lo que hay que decirle a quien cocina.*"""
        return self.acaba_en - (ahora or datetime.now(timezone.utc))

    def ha_terminado(self, ahora: datetime | None = None) -> bool:
        return self.queda(ahora).total_seconds() <= 0


@dataclass
class Cocina:
    """**Una receta, mientras se cocina.** *Lo que hace falta para poder **volver** a ella.*

    *No es la receta: es **por donde ibas**. Y por eso se puede guardar en una linea de texto y releerla.*
    """

    receta_id: int
    version: int
    pasos: list[str] = field(default_factory=list)
    #: **En que paso vas.** *Se guarda un indice, y `None` es «no he empezado» -- que no es el paso 0.*
    paso: int | None = None
    #: *Los ingredientes que ya se han echado.* **Se guardan por lo que la receta dice**, no por indice, para que
    #: sigan significando lo mismo si la receta se reescribe.*
    usados: list[str] = field(default_factory=list)
    temporizadores: list[Temporizador] = field(default_factory=list)

    def empieza(self) -> int:
        """*Ponerse a cocinar.* **El paso 0 existe solo cuando se ha empezado** -- *antes, `paso` es `None`, y esa
        distincion es la que permite decir «sin empezar» en vez de «en el paso 0».*
        """
        if self.paso is None:
            self.paso = 0
        return self.paso

    def avanza(self) -> int | None:
        """**El paso siguiente, y `None` cuando ya no hay.** *No se queda en el ultimo ni vuelve al principio:
        **acabar no es un paso**, y decir `None` es lo que permite enseñar «terminada».*
        """
        if self.paso is None:
            return self.empieza()
        if self.paso + 1 >= len(self.pasos):
            return None
        self.paso += 1
        return self.paso

    def usa(self, texto: str) -> None:
        """**Apunta un ingrediente usado**, y **no dos veces** -- *echar la sal en dos pasos **no es echar el
        doble**, y contarla dos veces haria que la lista de lo que falta mintiera.*
        """
        limpio = str(texto).strip()
        if limpio and limpio not in self.usados:
            self.usados.append(limpio)

    def pon_temporizador(self, minutos: int, ahora: datetime | None = None,
                         paso: int | None = None) -> Temporizador:
        """**Poner un temporizador, y devolverlo.** *Guarda **cuando empezo** -- *que es lo unico que hace falta
        para poder reanudar.*
        """
        t = Temporizador(paso=self.paso if paso is None else paso,
                         minutos=int(minutos), empezo_en=ahora or datetime.now(timezone.utc))
        self.temporizadores.append(t)
        return t

    def lo_que_falta(self, ingredientes: list[str]) -> list[str]:
        """**`R10`: lo que aun no se ha echado.** *«Explicar ingredientes disponibles/faltantes» -- y aqui
        «faltante» quiere decir **lo que queda por usar**, no lo que no hay en casa.*
        """
        return [i for i in ingredientes if i not in self.usados]

    def reanuda(self, ahora: datetime | None = None) -> dict:
        """**Volver a la cocina, sin conexion y sin haber perdido nada.** *Y lo que devuelve es **todo lo que la
        pantalla necesita**, calculado en el momento de leer.*

        *Los temporizadores vienen **con lo que queda ya calculado**, y los terminados **se dicen** en vez de
        desaparecer -- *que un temporizador que se paso **no es un temporizador que no existe**.*
        """
        ahora = ahora or datetime.now(timezone.utc)
        return {
            "paso": self.paso,
            "paso_actual": self.pasos[self.paso] if self.paso is not None and self.paso < len(self.pasos) else None,
            "usados": list(self.usados),
            "hechos": len(self.usados),
            "temporizadores": [
                {"paso": t.paso, "minutos": t.minutos,
                 # **El INSTANTE, para que pueda restar quien lo tiene delante.** *Es el arreglo del §6: se
                 # mandaba el numero ya calculado, y **sin conexion la pantalla no tenia nada que recalcular**
                 # -- el numero se quedaba congelado.* **Con el instante, el reloj lo lleva el aparato.**
                 "acaba_en": t.acaba_en.isoformat(),
                 # *Y se siguen mandando los dos calculados, para quien los quiera ya hechos.*
                 "queda_segundos": int(t.queda(ahora).total_seconds()),
                 "terminado": t.ha_terminado(ahora)}
                for t in self.temporizadores
            ],
        }
