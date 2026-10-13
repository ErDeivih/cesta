---
seccion: Medidas y agregados
resumen: Lo que se come y lo que se va a comer son dos series distintas, y las dos pueden tener huecos. Aquí está dónde vive cada número, cómo se suma y por qué una suma parcial no se da nunca.
en_una_frase: Un día sin dato no es un día de cero, y una suma parcial no es un total.
---

# 25 — La nutrición, contada sin inventar lo que falta

**Por qué este capítulo existe.** *Los veinticuatro anteriores explican cómo se extrae, se empareja y se
mide. **Este explica lo que este proyecto se niega a hacer con la nutrición** — y por qué negarse es lo que
hace que sus números sirvan para algo.*

## Las dos series, y por qué no son una

| Serie | Qué es | Dónde vive |
|---|---|---|
| **Registrado** | lo que **se comió** | `core/diario.py`, `data/diario.sqlite` |
| **Previsto** | lo que **se va** a comer | la vista de previstos, sobre el plan |
| **Objetivo** | lo que **la persona se ha puesto** | `preferencia`, clave `objetivo:<fecha>` |

*Y el proyecto los separa **en el código y no solo en la cabecera**: `diario.py` **rechaza el tipo `compra`
a propósito** —*«comprar no es comer: si una compra entrara aquí, el diario sumaría»*—, y la prevista vive en
**otra consulta** (`GET /api/recetas/plan/prevision`) que **no escribe nada**.

**Comando, para verlo:**

```
uv run python -c "from core import diario; print(diario.__doc__.splitlines()[2])"
```

*Y la salida empieza igual que este capítulo: **lo que se comió, con lo que se sabe y lo que no.***

## Cómo se suma: nutriente a nutriente, y con cobertura

**La regla, en una línea:** *se suma **lo que hay**, y se dice **de cuántas partes sale**.*

`core/diario.py` tiene la aritmética, y **vive en una sola función**:

```python
def resumen(filas) -> dict:
    # -> {"conocido": {...}, "cobertura": {...}, "completo": bool}
```

**Tres decisiones que están dentro, y las tres importan:**

1. **Se calcula nutriente a nutriente, no en bloque.** `de_ficha` lo dice en su docstring: *«si el producto
   trae kilocalorías pero no proteínas, la entrada lleva las kilocalorías y **deja las proteínas en `None`**»*.
   **Rellenar con ceros sería afirmar que no lleva proteína, y eso no lo sabemos.**
2. **La cobertura es por nutriente.** *«Sin esto, una entrada con proteína y sin energía perdería su proteína
   en el subtotal, o peor: **se leería como que el día está cubierto**.»*
3. **El subtotal se llama `conocido`, y no `total`, a propósito.** *«`completo` significa que todas las filas
   traen energía. **No significa "esto es todo lo que comí"**.»*

**Y la consecuencia, que es la que se ve en pantalla:** un día con dos comidas **se suma solo si las dos traen
su energía**. *Si a una le falta, el día va a `null` y **no a la suma de las otras** — porque una suma parcial
no es «lo previsto»: es **lo previsto menos algo**, y quien la leyera creería que el día está cubierto.*

## El hueco, con la palabra

*Un gráfico que dibuja cero donde no hay dato dice que **se comió nada**, y encima hace parecer que los demás
días están completos.* Por eso los tres sitios donde esto se pinta dicen lo mismo, y con las mismas palabras:

- `paginas/Tendencias.tsx`: *«Sin dato de energía en este día: **no se dibuja, porque un cero no es lo mismo
  que no saber**.»*
- `componentes/LeyendaDeSeries.tsx`: cuando no hay serie **no escribe «0 puntos»**, escribe **«sin serie»**.
- `api/main.py`, en la vista previa de consumir: *«anotar las que se puede y **callar las demás convertiría un
  dato que falta en una comida que parece completa**.»*

## El objetivo, y por qué no hay uno por defecto

*«Objetivo **opcional** por persona y fecha»* — y **opcional quiere decir que puede no haberlo**. Se guarda
como una preferencia más:

```
PUT /api/preferencias   {"clave": "objetivo:2026-10-14", "valor": {"kcal": 2000}}
GET /api/yo             -> {"preferencias": {"objetivo:2026-10-14": {"kcal": 2000}}}
```

**Y el valor lo pone la persona.** *El proyecto no calcula un objetivo por edad, por peso ni por sexo, y no
propone uno «recomendado»*: eso sería inventar un dato de salud, y está fuera de lo que este material hace.

**Y si no lo hay, la gráfica tiene dos series y lo dice** — *no una línea por el cero, y no un 2.000 por
defecto.*

## Lo que este capítulo **no** dice

- **No hay calorías por ingrediente que no esté en el catálogo.** *Un ingrediente sin `producto_id` entra en
  `sin_dato` **con su nombre**, y no se le atribuye la nutrición de otro producto parecido.*
- **No hay densidad.** *`ml` no se convierte a gramos: haría falta la densidad, y no la tenemos.*
- **No hay alérgenos ni equivalencias.** *No están en los datos, y no se deducen.*
- **Y no hay un total de un día incompleto.** *Ni en la gráfica, ni en una media, ni en un porcentaje.*

## Cómo se comprueba

```
uv run pytest -q tests/test_diario.py tests/test_b08_la_prevision_no_inventa.py
```

*Los del diario fijan la aritmética —incluida la cobertura por nutriente—, y los de la prevista fijan que
**no escribe nada** (se comprueba **sobre el árbol sintáctico**: ni `apunta(`, ni `INSERT`, ni `commit(`), que
**solo se convierten unidades de peso**, y que **la suma es la del diario y no una copia**.*

**Y en el frontend:**

```
cd plataforma/web/app && npm test
```

*`tests/puntosDeLasTres.test.mjs` fija la regla que más importa: **dos comidas con 300 y `null` dan `null`, y
no 300.***
