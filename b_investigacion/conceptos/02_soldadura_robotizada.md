<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 02 · Soldadura robotizada

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
- [1. Soldadura por puntos y soldadura al arco](#1-soldadura-por-puntos-y-soldadura-al-arco)
- [2. Variables del proceso de soldadura al arco](#2-variables-del-proceso-de-soldadura-al-arco)
- [3. Por qué se robotiza la soldadura al arco](#3-por-qué-se-robotiza-la-soldadura-al-arco)
- [4. La celda de soldadura al arco típica](#4-la-celda-de-soldadura-al-arco-típica)
- [5. Requisitos del robot de soldadura al arco](#5-requisitos-del-robot-de-soldadura-al-arco)
- [6. La pieza: paquetes de chapa magnética](#6-la-pieza-paquetes-de-chapa-magnética)
- [7. Representación del proceso en la simulación](#7-representación-del-proceso-en-la-simulación)
- [8. Qué hay que definir en nuestra celda](#8-qué-hay-que-definir-en-nuestra-celda)
- [9. Referencias](#9-referencias)

---

## Prólogo

La tarea de la celda es una soldadura. Para que la celda sea coherente con el proceso real, y para
poder justificar el robot, la herramienta, el posicionador y las velocidades, hace falta conocer cómo
es una soldadura robotizada y qué exige al equipo.

Este documento resume lo que dicen Groover (sección 8.4.2) y Barrientos (sección 10.2.2) sobre la
soldadura con robots, y lo relaciona con la pieza que se va a soldar, analizada en
[`../despiece_motor_lavarropas.md`](../despiece_motor_lavarropas.md).

---

## 1. Soldadura por puntos y soldadura al arco

Las dos formas de soldadura más robotizadas son [Groover, 8.4.2, pp. 219–220; Barrientos, 10.2.2,
pp. 294–296]:

| | Soldadura por puntos | Soldadura al arco |
|---|---|---|
| **Principio** | Dos piezas se unen en un punto al pasar una corriente muy alta (del orden de 1500 A) por dos electrodos que las aprietan. | Las piezas se unen con un aporte de metal fundido por un arco eléctrico entre la pieza y el electrodo. |
| **Resultado** | Uniones puntuales | **Cordón continuo**, más resistente, apto para uniones estancas |
| **Herramienta** | Pinza de soldadura, pesada | Antorcha con alimentación de alambre, liviana |
| **Robot** | Carga alta (50–100 kg), 5–6 ejes | Carga baja (~10 kg), 5–6 ejes |
| **Control** | **Punto a punto** (PTP) alcanza | **Trayectoria continua** (CP) obligatoria |
| **Aplicación típica** | Carrocerías de automóviles | Recipientes, estructuras, uniones continuas |

La tarea de nuestra celda es un **cordón continuo**, así que corresponde a la soldadura al arco o a un
proceso equivalente de trayectoria continua.

## 2. Variables del proceso de soldadura al arco

La calidad del cordón depende de [Barrientos, 10.2.2, p. 296]:

- la **distancia entre la pieza y el electrodo**;
- la **velocidad de avance** del electrodo a lo largo de la trayectoria;
- la **tensión e intensidad** de la corriente;
- el **ángulo de ataque** del electrodo.

Las dos primeras y la última dependen directamente del robot. Por eso la orientación de la
herramienta (ver [04](04_sistemas_de_referencia_y_tcp.md)) y la velocidad de los movimientos de
soldadura (ver [05](05_tipos_de_movimiento.md)) no son decisiones arbitrarias: definen el cordón.

## 3. Por qué se robotiza la soldadura al arco

- **Ambiente agresivo:** radiación ultravioleta, humo, chispas, alta corriente y temperaturas
  suficientes para fundir el metal [Groover, 8.4.2, p. 220; Barrientos, 10.2.2, p. 296].
- **Exigencia de coordinación:** el soldador necesita mucha coordinación entre la mano y la vista
  para seguir la trayectoria con precisión, lo que produce fatiga [Groover, 8.4.2, p. 220].
- **Bajo tiempo de arco:** por esa fatiga, el soldador manual tiene el arco encendido solo un
  **20–30 % del turno** (*arc-on time*), y suele necesitar un ayudante (*fitter*) que prepare las
  piezas [Groover, 8.4.2, p. 220].
- **Dificultad para mantener constantes las variables** del proceso [Barrientos, 10.2.2, p. 296].

Para uniones largas y repetitivas, rectas o circulares, existen máquinas de soldadura mecanizadas.
El robot se usa cuando hace falta más flexibilidad en la trayectoria [Groover, 8.4.2, p. 220].

## 4. La celda de soldadura al arco típica

Groover describe la celda de soldadura al arco robotizada así [Groover, 8.4.2, pp. 220–221]:

- **el robot;**
- **el equipo de soldadura:** fuente de potencia, controlador, antorcha y alimentador de alambre;
- **un utillaje que sujeta las piezas.** Puede estar **motorizado con uno o dos ejes** para presentar
  al robot distintas partes de la pieza. A este utillaje se lo llama **posicionador**
  (*positioner*).

Para aumentar la productividad, suelen usarse **dos utillajes**: mientras el robot suelda en uno, un
operario (u otro robot) descarga la pieza terminada y carga la siguiente en el otro, protegido por
una **barrera de seguridad** (Figura 8.12 de Groover). Barrientos muestra la misma idea con una
**mesa giratoria** que permite al operario cargar piezas desde afuera del área del robot
(Figura 9.10, una célula de soldadura) [Barrientos, 9.3.2, p. 275].

Barrientos agrega que, cuando hay que acceder a piezas grandes o complejas, se usan **mesas
posicionadoras u orientadoras** sincronizadas con el robot, con un número finito de posiciones
(accionamiento neumático o hidráulico, costo bajo) o infinito (posicionamiento continuo, costo alto)
[Barrientos, 9.2.2, pp. 265–266]. Ver [03](03_seleccion_de_equipos.md).

## 5. Requisitos del robot de soldadura al arco

| Requisito | Valor o característica | Fuente |
|---|---|---|
| Tipo de control | **Trayectoria continua** | Groover, 8.4.2, p. 220; Barrientos, 10.2.2, p. 296; Barrientos, 9.2.6, p. 269 |
| Configuración | Brazo articulado de 6 ejes, el más usado | Groover, 8.4.2, p. 220 |
| Grados de libertad | 5 o 6 (la soldadura al arco es un caso típico de 6) | Barrientos, 9.2.2, p. 265; 10.2.2, p. 296 |
| Carga | Baja, ~10 kg | Barrientos, 10.2.2, p. 296 |
| Alcance | Amplio, ~2 m de radio | Barrientos, 10.2.2, p. 296 |
| Ejes externos | Que muevan el utillaje que sostiene la pieza | Barrientos, 10.2.2, p. 296 |
| Cables | Algunos robots tienen el brazo hueco para llevar los cables de la antorcha por dentro | Groover, 8.4.2, p. 220 |
| Programación | Instrucciones especiales de soldadura con los parámetros del proceso. Trayectoria generada desde el modelo CAD | Barrientos, 10.2.2, p. 296; Groover, 8.4.2, p. 220 |
| Seguimiento del cordón | Algunos robots usan sensores láser para encontrar el inicio y seguir el cordón (0,5 mm a 40 mm/s) | Barrientos, 10.2.2, p. 297 |

## 6. La pieza: paquetes de chapa magnética

El estudio del motor de referencia ([`../despiece_motor_lavarropas.md`](../despiece_motor_lavarropas.md))
mostró que la soldadura une las **chapas del paquete de estator**:

- **Cordones axiales**, paralelos al eje del motor, que cruzan todas las chapas del paquete.
- Ubicados **sobre las aristas** del paquete, dentro de un escalón.
- Con aspecto de **soldadura sin aporte visible** y color de revenido. Es compatible con procesos de
  arco sin aporte (TIG) o láser, aunque falta confirmarlo.
- Un cordón sobre un paquete de chapas tiene que ser **de baja energía**: si deforma las chapas o las
  une eléctricamente más de lo necesario, aumentan las pérdidas del motor.

Esta pieza no es un recipiente ni una estructura, como los ejemplos de los libros, pero cumple las
mismas condiciones: **cordones continuos, cortos y repetitivos**, en distintas caras de una pieza que
hay que orientar frente a la antorcha.

## 7. Representación del proceso en la simulación

RoboDK simula la cinemática y la lógica, no el proceso térmico. Un proceso de soldadura se representa
con:

- la **trayectoria** del TCP de la antorcha sobre la pieza;
- una **velocidad de soldadura** propia, distinta de la de los traslados;
- una **señal digital** que representa el encendido del arco: se activa al comenzar el cordón y se
  desactiva al terminarlo (ver [06](06_estructura_de_programas_y_senales.md)).

En el informe hay que dejar claro ese alcance: no se modelan fenómenos térmicos ni metalúrgicos.

## 8. Qué hay que definir en nuestra celda

- ¿Qué proceso de soldadura representamos (TIG, MIG, láser) y con qué herramienta de RoboDK?
- ¿Cuántos cordones lleva la pieza, de qué largo y en qué posiciones?
- ¿Qué velocidad de soldadura y qué distancia y ángulo de la antorcha usamos, y con qué criterio?
- ¿Usamos un posicionador? ¿De cuántos ejes y de cuántas posiciones (finitas o continuas)?
- ¿Usamos uno o dos utillajes (o una mesa giratoria) para cargar mientras se suelda?
- ¿Qué señal representa el arco y cuándo se activa y desactiva?

## 9. Referencias

- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Sección 8.4.2, pp. 219–221.
- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Secciones 9.2.2, 9.2.6, 9.3.2 y 10.2.2.
- Grupo 4. *Despiece del motor de lavarropas*. `b_investigacion/despiece_motor_lavarropas.md`.
