<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 04 · Sistemas de referencia y TCP

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
- [1. Localización espacial](#1-localización-espacial)
- [2. Sistemas de referencia de una celda](#2-sistemas-de-referencia-de-una-celda)
- [3. El TCP](#3-el-tcp)
- [4. Por qué referir los targets a un frame de pieza](#4-por-qué-referir-los-targets-a-un-frame-de-pieza)
- [5. Frames sobre un eje externo](#5-frames-sobre-un-eje-externo)
- [6. Implementación en RoboDK](#6-implementación-en-robodk)
- [7. Qué hay que definir en nuestra celda](#7-qué-hay-que-definir-en-nuestra-celda)
- [8. Referencias](#8-referencias)

---

## Prólogo

El primer requisito de complejidad mínima pide **al menos un frame de referencia propio** (mesa,
pallet, pieza o cinta) y **una herramienta con su TCP definido y justificado**, no el predeterminado
[Lineamientos, requisito C1]. En el informe hay que presentar los frames con su justificación.

Este documento define qué es cada sistema de referencia de una celda, qué es el TCP y por qué
conviene organizar los puntos de la tarea respecto de un frame de la pieza. Se basa en la clase 1, en
Craig (sección 3.8) y en Barrientos (capítulo 3).

---

## 1. Localización espacial

Para que el robot trabaje sobre una pieza hay que describir **posiciones y orientaciones** en el
espacio. Una posición se da con coordenadas cartesianas respecto de un sistema de referencia. Una
orientación se puede dar con matrices de rotación, ángulos de Euler, par de rotación o cuaterniones
[Barrientos, 3.1 y 3.2, pp. 50–61].

Las dos cosas juntas se representan con una **matriz de transformación homogénea**, que también
permite pasar una descripción de un sistema de referencia a otro y encadenar transformaciones
[Barrientos, 3.3, pp. 62–80; Craig, 2.2 a 2.7].

Los lenguajes comerciales usan distintas representaciones. Por ejemplo, RAPID (ABB) da la posición
con coordenadas cartesianas y la orientación con un cuaternión [Barrientos, 8.2.3, p. 228].

## 2. Sistemas de referencia de una celda

Craig propone cinco **tramas estándar** con nombre propio, para que todos los movimientos del robot
se describan de una manera general y comprensible [Craig, 3.8, pp. 89–91]. La clase 1 presenta la
misma idea con la nomenclatura industrial [Clase 1]:

| Clase 1 | Craig | Dónde está | Respecto de qué se define |
|---|---|---|---|
| **Mundo / World** | Estación {S} (también "universal" o "de tarea") | Fija en la planta o en la tarea. | — (referencia absoluta). La estación se define respecto de la base. |
| **Base** | Base {B} | En la base del robot (eslabón 0). Frecuentemente coincide con el mundo, salvo en montajes sobre rieles. | Mundo |
| — | Muñeca {W} | En la brida del último eslabón. Se mueve con él. | Base |
| **Herramienta / Tool** | Herramienta {T} | En el extremo de la herramienta (el TCP). Sigue la orientación del efector final. | Muñeca |
| **Objeto de trabajo / WorkObject** | — | Atado a la pieza o al utillaje. | Mundo |
| *Target* | Objetivo {G} | Ubicación a la que el robot lleva la herramienta. Al final del movimiento, {T} coincide con {G}. | Estación u objeto de trabajo |

Según la clase 1, el sistema **Mundo** sirve cuando varios robots colaboran en una misma línea, y el
**objeto de trabajo** es un referencial dinámico atado a la pieza [Clase 1].

## 3. El TCP

El **TCP** (*Tool Center Point*) es el origen del sistema de la herramienta: el punto que el robot
lleva a cada target y cuya trayectoria se controla en los movimientos cartesianos.

- Se define **respecto de la brida** del robot (sistema muñeca), con una traslación y una rotación
  [Craig, 3.8, p. 90].
- **Posición:** en una antorcha de soldadura se ubica en el punto de trabajo del proceso, a la
  distancia de trabajo del extremo del electrodo o la boquilla.
- **Orientación:** el eje Z suele alinearse con el eje de la antorcha. Así, la orientación de los
  targets expresa directamente el ángulo de ataque del electrodo, una de las variables del cordón
  (ver [02](02_soldadura_robotizada.md)).

**Por qué no sirve el predeterminado:** si el TCP queda en la brida, el robot lleva la brida a los
targets y no la punta de la antorcha. Las trayectorias rectas y la velocidad de soldadura pasarían a
estar definidas en un punto que no es el que suelda.

**Cómo se justifica:** con la geometría de la antorcha (largo y ángulo del cuello) y con el punto del
proceso que se quiere controlar.

## 4. Por qué referir los targets a un frame de pieza

La clase 1 lo explica con un ejemplo: si la matriz física se mueve 5 cm, **solo se recalibra el
objeto de trabajo y el controlador desplaza toda la trayectoria** [Clase 1].

Ventajas de definir los targets respecto de un frame de la pieza y no respecto de la base del robot:

- **Reubicación:** si la pieza o el utillaje se mueven, se corrige un solo frame y no cada target.
- **Variantes:** dos piezas o dos posiciones de un pallet pueden compartir los mismos targets
  relativos, cambiando solo el frame. Esto ayuda a cumplir el requisito C3.
- **Calibración:** al pasar de la simulación al robot real, se calibra el frame de la pieza. Craig
  señala que la calibración de la célula es una parte necesaria de cualquier programación fuera de
  línea, porque el modelo nunca coincide exactamente con la realidad [Craig, 13.2].
- **Claridad:** los targets quedan expresados en las coordenadas de la pieza, que son las del plano
  de la pieza.

## 5. Frames sobre un eje externo

Cuando la pieza está montada sobre un **posicionador**, el frame de la pieza tiene que **moverse con
el eje del posicionador**. Así, al girar el posicionador:

- los targets atados a la pieza giran con ella;
- un mismo cordón, definido una sola vez, puede repetirse en otra cara de la pieza girando el
  posicionador, sin definir targets nuevos.

En cambio, los targets que no dependen de la pieza (posición de reposo, puntos de espera fuera de la
zona de trabajo) conviene definirlos respecto de un frame fijo.

## 6. Implementación en RoboDK

- **Frame de referencia** (*reference frame*): se crea en el árbol de la estación y se puede colgar
  de otro frame o de un mecanismo. Todo lo que cuelga de él (objetos, targets) se mueve con él.
- **Herramienta**: se asocia al robot. Su TCP se define con una traslación X, Y, Z y una rotación
  respecto de la brida.
- **Targets**: cada uno pertenece a un frame. Hay targets cartesianos (posición y orientación del TCP)
  y articulares (valores de cada eje).
- **Instrucciones de programa** que fijan el frame y la herramienta activos antes de los
  movimientos.

## 7. Qué hay que definir en nuestra celda

- ¿Qué frames propios tiene la celda (celda, posicionador, pieza) y de quién cuelga cada uno?
- ¿Dónde queda el TCP de la antorcha (traslación y rotación), y con qué geometría se justifica?
- ¿Qué orientación del TCP corresponde al ángulo de ataque elegido?
- ¿Qué targets dependen de la pieza y cuáles de un frame fijo?
- ¿El frame de la pieza cuelga del eje del posicionador?
- Si hay variantes de pieza, ¿comparten targets cambiando solo el frame?

## 8. Referencias

- **[Clase 1]** Perassi, S. *Robótica Industrial – Clase 1: Introducción, morfología y sistemas de
  coordenadas*. UTN FRC, 2026. Diapositiva "Sistemas de coordenadas anidados en celda".
- **[Craig]** Craig, J. J. *Robótica*, 3.ª ed. Pearson Educación. Capítulo 2 y sección 3.8,
  pp. 89–91; sección 13.2.
- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Capítulo 3, pp. 49–92; sección 8.2.3, p. 228.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
