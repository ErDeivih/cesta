# Calorías y pautas de salud — decisiones y fuentes

**Cerrado el 2026-11-06.** Encargo: gasto energético, macros, pautas de salud con fuente y
enlace, objetivo con su «por qué» y aviso discreto. Fuentes consultadas y leídas ese mismo día;
lo que no se ha podido leer se dice.

## 1. Gasto energético: Mifflin-St Jeor, y por qué

Se usa **Mifflin-St Jeor (1990)** para el gasto en reposo:

- hombres: `10 × peso(kg) + 6,25 × altura(cm) − 5 × edad + 5`
- mujeres: `10 × peso(kg) + 6,25 × altura(cm) − 5 × edad − 161`

Fuente: [Mifflin et al., 1990 (resumen indexado en Europe PMC)](https://europepmc.org/article/MED/2305711),
leído el 2026-11-06. El mismo trabajo señala que Harris-Benedict sobreestimaba el gasto en torno
al 5 %; por eso no se usa Harris-Benedict.

Al reposo se le aplica un **factor de actividad** (PAL) de la referencia FAO/WHO/UNU:
[Human energy requirements, 2004](https://www.fao.org/4/y5686e/y5686e00.htm) (leído el índice y la
estructura; anexo de ecuaciones y niveles de actividad). Factores usados, redondeados a los
estilos habituales: sedentario 1,2 · ligero 1,375 · moderado 1,55 · alto 1,725 · muy alto 1,9.
El resultado se enseña como **estimación con rango ±10 %**, nunca como «tu gasto real».

**Ajuste por objetivo** (elección de la persona, no automática):

| Objetivo | Ajuste diario | Fundamento |
|---|---:|---|
| Mantener | 0 kcal | Equilibrio entre ingesta y gasto (WHO, «Healthy diet») |
| Perder | −300 a −500 kcal | Ritmo gradual de 1–2 lb/semana y déficit moderado; [CDC, «Steps for Losing Weight» (17/01/2025)](https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html) |
| Ganar | +300 a +500 kcal | Espejo del ajuste moderado; la referencia de equilibrio energético es la misma de WHO |

**Matiz honesto:** la CDC ancla el ritmo (1–2 lb/semana) pero **no escribe literalmente «300–500
kcal/día»**; esa horquilla es la traducción conservadora que se ha decidido para esta app, y así
se cuenta en el documento y en el código. El punto que se aplica es el centro (−400 / +400).

**Suelo de seguridad.** Si con «Perder» el objetivo queda por debajo de **1.200 kcal/día en
mujeres** o **1.500 kcal/día en hombres**, la app **no enseña ni guarda esa cifra**: dice que el
resultado queda por debajo y que se hable con un profesional. No es una pauta de salud ni una
recomendación: es un límite de seguridad de la app para no presentar como «objetivo» una cifra que
puede ser peligrosa. En ese caso el gasto estimado sí se puede consultar; lo que no se da es el
objetivo de pérdida.

El déficit **no se aplica solo**: la app no fija objetivo al abrir ni propone adelgazar. Se elige
en la pantalla y se guarda solo al pulsar «Usar como objetivo». No hay dietas, IMC como juicio ni
«deberías».

## 2. Reparto de macros

Se enseña en % de la energía y en gramos para el objetivo central:

| Macro | Rango | Fuente |
|---|---|---|
| Proteína | 10–15 % | [WHO, «Healthy diet» (26/01/2026)](https://www.who.int/news-room/fact-sheets/detail/healthy-diet) |
| Grasas | 15–30 % (saturadas <10 %) | WHO, «Healthy diet»; [EFSA DRV (26/03/2010)](https://www.efsa.europa.eu/en/press/news/nda100326) da 20–35 % |
| Hidratos | 45–60 % | EFSA DRV (45–60 %); WHO admite 45–75 % |
| Fibra | ≥25 g/día | EFSA DRV y WHO |

Decisión: se usa el **rango estrecho de EFSA para hidratos (45–60 %)** y el de WHO para proteína y
grasa, porque son los que la app puede explicar sin mezclar referencias. La pantalla dice el rango
y la fuente, no una fórmula.

## 3. Pautas de salud (cifra, fuente y enlace)

| Pauta | Cifra | Fuente y fecha |
|---|---|---|
| Fibra | ≥25 g/día | [EFSA DRV (26/03/2010)](https://www.efsa.europa.eu/en/press/news/nda100326); [WHO (26/01/2026)](https://www.who.int/news-room/fact-sheets/detail/healthy-diet) |
| Azúcar libre | <10 % de la energía; mejor <5 % | WHO, «Healthy diet» (26/01/2026) |
| Sal | <5 g/día (<2.000 mg sodio) | [WHO, sodio (11/05/2026)](https://www.who.int/news-room/fact-sheets/detail/sodium-reduction) |
| Agua | 2,0 L/día mujeres; 2,5 L/día hombres (agua total, incluida la de los alimentos) | EFSA DRV (26/03/2010) |
| Fruta y verdura | ≥400 g/día (mayores de 10 años) | WHO, «Healthy diet» (26/01/2026) |
| Alcohol | Ningún nivel de consumo es sin riesgo | [WHO, alcohol (28/06/2024)](https://www.who.int/news-room/fact-sheets/detail/alcohol) |

Contexto español: [AESAN, recomendaciones dietéticas y de actividad física
(2022)](https://www.aesan.gob.es/nutricion/recomendaciones-dieteticas). No se le atribuye una cifra
concreta que no se haya leído en su informe; las cifras de la tabla salen de las fuentes citadas.

## 4. Interfaz y aviso

- El objetivo se enseña con su **por qué** en lenguaje de usuario: «partimos de tu gasto estimado
  (2.590 kcal) y ajustamos −400 para perder». Sin fórmulas, sin «Mifflin», «PAL» ni «TDEE» en
  pantalla; los nombres de las fuentes sí aparecen, con su enlace.
- Macros en gramos y % con sus rangos; nada de objetivos impuestos.
- Aviso **claro y discreto**, no alarmista: «No es consejo médico. Si tienes una condición de
  salud, consulta con un profesional.» No diagnostica, no llama enfermo a nadie.
- Si faltan datos, no calcula. Si el usuario no elige objetivo, no se guarda nada.

## 5. Límites

- Es una **estimación**, no una medición: el gasto real varía por composición corporal, genética,
  sueño, medicación o enfermedad. El rango ±10 % lo dice sin dramatizar.
- No se usa para diagnosticar ni para tratar ninguna condición.
- No hay datos de composición corporal ni de salud en la app: solo los que la persona escriba en
  el formulario, y no se envían a ningún sitio (se calculan en el aparato).
- El agua de la referencia EFSA es **agua total** (bebida + alimentos); la pantalla lo dice.
- El alcohol se enseña como riesgo, no como cantidad permitida.

## 6. Lo que NO se hace

- Fijar un objetivo calórico al abrir la app o al registrar el peso.
- Déficit automático, planes de adelgazamiento, dietas, «quema esto», IMC como juicio.
- Presentar Mifflin como «tu gasto real» o dar una cifra única sin rango.
- Inventar kcal de alimentos que no las tienen (la app ya dice «sin dato»).


## 7. Verificación de las fuentes (08/11/2026)

Se han vuelto a abrir las páginas oficiales y se ha comprobado que responden (HTTP 200) y que la
fecha que enseña la pantalla es la del documento:

| Fuente | URL comprobada | Fecha que se muestra |
|---|---|---|
| WHO, *Healthy diet* | https://www.who.int/news-room/fact-sheets/detail/healthy-diet | 26/01/2026 |
| WHO, *Sodium reduction* | https://www.who.int/news-room/fact-sheets/detail/sodium-reduction | 11/05/2026 |
| WHO, *Alcohol* | https://www.who.int/news-room/fact-sheets/detail/alcohol | 28/06/2024 |
| EFSA, valores dietéticos de referencia | https://www.efsa.europa.eu/en/press/news/nda100326 | 26/03/2010 |
| FAO/WHO/UNU, *Human energy requirements* | https://www.fao.org/4/y5686e/y5686e00.htm | 2004 |
| CDC, *Steps for Losing Weight* | https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html | 17/01/2025 |
| AESAN, recomendaciones dietéticas | https://www.aesan.gob.es/nutricion/recomendaciones-dieteticas | 2022 |
| Mifflin-St Jeor (Europe PMC) | https://europepmc.org/article/MED/2305711 | 1990 |

No hay cambios de cifras ni de enlaces: la pantalla ya citaba estas fuentes. La verificación se deja
aquí para que la próxima persona no tenga que repetirla. Las 17 pruebas de `Pautas.test.tsx` siguen
verdes: seis pautas con su cifra y su fuente enlazada, ocho fuentes externas, el «por qué» del
objetivo, el suelo de seguridad y los 44 px de todo lo que se pulsa.
