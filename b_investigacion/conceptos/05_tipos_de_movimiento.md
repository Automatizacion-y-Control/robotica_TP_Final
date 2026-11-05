<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 05 · Tipos de movimiento

*Documento de conceptos de implementación*

**Grupo 4**<br>
Casali Emiliano · Ferrero Facundo · Vera Gonzalo

**Docentes**<br>
Ing. Julián Luque · Lic. Sergio Perassi

Comisión 2LA1 · Año 2026

</div>

---

## Índice

- [Prólogo](#prólogo)
- [1. Tipos de trayectoria](#1-tipos-de-trayectoria)
- [2. Interpolación en el espacio cartesiano](#2-interpolación-en-el-espacio-cartesiano)
- [3. Problemas de las trayectorias cartesianas](#3-problemas-de-las-trayectorias-cartesianas)
- [4. MoveJ, MoveL y MoveC](#4-movej-movel-y-movec)
- [5. Puntos de paso y zonas de precisión](#5-puntos-de-paso-y-zonas-de-precisión)
- [6. Velocidad](#6-velocidad)
- [7. Estructura de movimientos de una operación de soldadura](#7-estructura-de-movimientos-de-una-operación-de-soldadura)
- [8. Qué hay que definir en nuestra celda](#8-qué-hay-que-definir-en-nuestra-celda)
- [9. Referencias](#9-referencias)

---

## Prólogo

Los lineamientos piden programar los movimientos con **MoveJ, MoveL y MoveC**, y entender cuándo
conviene cada uno [Lineamientos, §2]. Es el primer criterio de evaluación: *uso de MoveJ, MoveL y
MoveC, con la elección correcta de cada uno*.

Este documento explica qué hay detrás de cada instrucción: los tipos de trayectoria que genera el
control del robot, cómo se interpola una trayectoria cartesiana y qué problemas puede tener. De ahí
salen los criterios para elegir cada movimiento. Se basa en Barrientos (capítulo 6 y sección 8.2.5),
Craig (capítulo 7) y Groover (secciones 8.2 y 8.5).

---

## 1. Tipos de trayectoria

Para ir de un punto inicial a uno final, el robot puede seguir infinitas trayectorias. Los robots
comerciales implementan tres tipos [Barrientos, 6.2, pp. 172–174]:

| Tipo | Cómo se mueven las articulaciones | Trayectoria del extremo |
|---|---|---|
| **Punto a punto** | Cada articulación va a su destino sin coordinarse con las demás, eje a eje o todas a la vez. | Impredecible. Solo se usa en robots muy simples. |
| **Coordinada o isócrona** | Todas las articulaciones empiezan y terminan a la vez, adaptándose a la más lenta. Es el menor tiempo posible sin forzar los actuadores. | **No es significativa para el usuario** (no es una recta). |
| **Continua** | Se calcula de forma continua la evolución de cada articulación para que el extremo siga una trayectoria conocida, típicamente **una recta o un arco de círculo**. | La que se programó. |

Groover lo plantea igual: la diferencia entre punto a punto y trayectoria continua es la misma que en
el control numérico, y el controlador calcula la trayectoria entre puntos con rutinas de
**interpolación lineal y circular** [Groover, 8.2, pp. 215–216].

## 2. Interpolación en el espacio cartesiano

Cuando el usuario pide una recta, los puntos que programa están demasiado separados. El control tiene
que **generar puntos intermedios** suficientemente cercanos para que el extremo siga la trayectoria
indicada [Barrientos, 6.3, p. 175]:

- La **interpolación lineal** hace que cada coordenada cartesiana evolucione a velocidad constante
  desde su valor inicial hasta el final.
- Un robot articulado necesita esta interpolación para moverse en recta, porque sus articulaciones
  son rotativas [Groover, 8.5, p. 228].
- Cada punto interpolado exige resolver la cinemática inversa. La cantidad de puntos está limitada
  por el tiempo de cálculo y por la velocidad: **a menor velocidad, más puntos y más precisión**
  [Barrientos, 9.2.3, p. 267].
- La **orientación** también se interpola. Hacerlo con matrices de rotación da resultados
  inconsistentes, por eso se usan otras representaciones, como los cuaterniones [Barrientos, 6.3.1,
  p. 175].

## 3. Problemas de las trayectorias cartesianas

Como una trayectoria cartesiana impone una correspondencia continua entre la forma de la ruta y las
posiciones de las articulaciones, puede fallar aunque los puntos inicial y final sean alcanzables.
Craig describe tres problemas [Craig, 7.5, pp. 219–222]:

| Tipo | Problema | Ejemplo |
|---|---|---|
| 1 | **Puntos intermedios inalcanzables** | La recta pasa por una zona fuera del espacio de trabajo, aunque los extremos estén dentro. Un movimiento articular sí podría hacerse. |
| 2 | **Velocidades articulares muy altas cerca de una singularidad** | Al acercarse a una configuración singular, una articulación tendería a velocidad infinita. El robot se desvía o hay que bajar la velocidad. |
| 3 | **Inicio y destino en distintas soluciones** | El robot llega a todos los puntos, pero no con la misma configuración (por ejemplo, codo arriba y codo abajo). |

**La conclusión de Craig es la regla de uso:** debido a estas dificultades, se usan por defecto
trayectorias en el espacio articular, y **las trayectorias cartesianas se usan solo cuando la
aplicación realmente lo necesita** [Craig, 7.5, p. 222].

## 4. MoveJ, MoveL y MoveC

| Instrucción | Tipo de trayectoria | Cuándo usarla [Lineamientos, §2] | Por qué |
|---|---|---|---|
| **MoveJ** | Coordinada en el espacio articular | **Traslados libres entre zonas**, donde no importa la trayectoria de la herramienta. | Es la más rápida y la que menos exige a los actuadores. No tiene los problemas de las trayectorias cartesianas (sección 3). |
| **MoveL** | Continua, interpolación lineal | **Aproximaciones, retiradas y trabajo sobre la pieza** en línea recta. | El TCP sigue una recta conocida: la herramienta entra y sale sin arrastrarse sobre la pieza, y el cordón recto sigue la junta. |
| **MoveC** | Continua, interpolación circular | **Arcos o círculos** que la herramienta tiene que seguir. | El TCP sigue un arco definido por tres puntos: el actual, uno intermedio y el final. |

**Criterio de elección:**

1. ¿Importa por dónde pasa la herramienta? Si **no**, MoveJ.
2. Si **sí**, ¿la trayectoria es una recta? Entonces MoveL.
3. ¿Es un arco? Entonces MoveC.

Aplicado a la soldadura: los cordones rectos se hacen con MoveL, los cordones o transiciones en arco
con MoveC, y los traslados entre zonas y el regreso al reposo con MoveJ.

**Atención:** MoveL y MoveC pueden fallar por las causas de la sección 3. Si un movimiento cartesiano
no se puede ejecutar en la simulación, hay que revisar el alcance, las singularidades y la
configuración del robot, y no reemplazarlo por un MoveJ cuando la trayectoria importa.

## 5. Puntos de paso y zonas de precisión

- Cuando hay obstáculos, en vez de una sola recta se pueden programar **puntos de paso** (*via
  points*). Si un punto de paso se define con **precisión baja**, el robot va hacia el siguiente sin
  llegar exactamente al anterior y sin frenar: **gana continuidad y velocidad a costa de una
  precisión innecesaria en ese punto** (Figura 8.6, "zona de precisión") [Barrientos, 8.2.5,
  pp. 229–230].
- Craig trata el mismo tema como el paso por **puntos vía** de una trayectoria, sin detenerse en
  ellos [Craig, 7.2 y 7.3].
- RAPID permite elegir qué tipo de interpolación usar al pasar cerca de puntos singulares
  [Barrientos, 8.2.5, p. 229].

En RoboDK esto se configura con el **redondeo** (*rounding*) de los movimientos. En los puntos donde
la precisión importa (inicio y fin de cordón) el redondeo tiene que ser nulo. En los traslados puede
ser mayor.

## 6. Velocidad

- La velocidad suele indicarse **en la propia instrucción de movimiento o como un porcentaje** de una
  velocidad base definida aparte, lo que permite cambiar la velocidad de todo un programa con una sola
  instrucción [Barrientos, 8.2.5, p. 229; Groover, 8.5, p. 231].
- La **velocidad de soldadura** es una variable del proceso (ver [02](02_soldadura_robotizada.md)) y
  tiene que ser distinta de la de los traslados.
- Cerca de una singularidad puede hacer falta bajar la velocidad para no exceder los límites de las
  articulaciones [Craig, 7.5, p. 221].
- En la puesta en marcha, el programa se prueba primero a velocidad lenta (ver
  [08](08_tiempo_de_ciclo_y_validacion.md)) [Barrientos, 9.3.2, p. 276].

## 7. Estructura de movimientos de una operación de soldadura

Patrón general de un cordón, a partir de los criterios anteriores:

| Paso | Movimiento | Tipo | Velocidad | Precisión |
|---|---|---|---|---|
| 1. Traslado a la zona de la pieza | Hasta un punto de aproximación, lejos de la pieza | MoveJ | Alta | Redondeo permitido |
| 2. Aproximación | Hasta el inicio del cordón | MoveL | Media | Exacta |
| 3. Arco encendido | — | Señal | — | — |
| 4. Cordón | Del inicio al fin del cordón | MoveL o MoveC | **De soldadura** | Exacta |
| 5. Arco apagado | — | Señal | — | — |
| 6. Retirada | Hasta un punto seguro sobre la pieza | MoveL | Media | Exacta en el inicio |
| 7. Traslado | A la espera o al reposo | MoveJ | Alta | Redondeo permitido |

## 8. Qué hay que definir en nuestra celda

- ¿Qué movimientos de la celda son traslados libres (MoveJ), cuáles son rectas (MoveL) y cuáles son
  arcos (MoveC)?
- **¿Dónde hay un arco real que justifique MoveC?** Es un requisito de evaluación, así que tiene que
  surgir de la tarea y no agregarse artificialmente.
- ¿Qué velocidades usamos para traslados, aproximación y soldadura?
- ¿Dónde usamos redondeo y dónde precisión exacta?
- ¿Hay tramos cartesianos cerca de singularidades o con cambios de configuración?

## 9. Referencias

- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Secciones 6.2–6.4, pp. 172–185; 8.2.5, pp. 229–230; 9.2.3, p. 267;
  9.3.2, p. 276.
- **[Craig]** Craig, J. J. *Robótica*, 3.ª ed. Pearson Educación. Capítulo 7, en especial la sección
  7.5, pp. 219–222.
- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Secciones 8.2 y 8.5.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026. Sección 2.
