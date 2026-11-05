<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 01 · La célula robotizada

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
- [1. Qué es una célula robotizada](#1-qué-es-una-célula-robotizada)
- [2. Componentes de la célula](#2-componentes-de-la-célula)
- [3. El proceso de diseño y el papel de la simulación](#3-el-proceso-de-diseño-y-el-papel-de-la-simulación)
- [4. Disposición del robot en la célula](#4-disposición-del-robot-en-la-célula)
- [5. El sistema de control de la célula](#5-el-sistema-de-control-de-la-célula)
- [6. Células que operan sin operador](#6-células-que-operan-sin-operador)
- [7. Cuándo conviene robotizar](#7-cuándo-conviene-robotizar)
- [8. Qué hay que definir en nuestra celda](#8-qué-hay-que-definir-en-nuestra-celda)
- [9. Referencias](#9-referencias)

---

## Prólogo

La consigna del trabajo pide diseñar una celda robotizada que cumpla una tarea concreta, y agregarle
complejidad sabiendo por qué se suma cada elemento [Lineamientos]. Para eso primero hay que tener
claro qué es una célula, qué elementos la forman y qué tiene que resolver su sistema de control.

Este documento reúne esos conceptos generales a partir de Barrientos (capítulo 9, *Criterios de
implantación de un robot industrial*) y de Groover (capítulos 8 y 14). Es la base de los documentos
que siguen: la soldadura como proceso ([02](02_soldadura_robotizada.md)), la selección de los equipos
([03](03_seleccion_de_equipos.md)) y la seguridad ([07](07_seguridad_y_normativa.md)).

---

## 1. Qué es una célula robotizada

Una **célula (o celda) robotizada** es el conjunto formado por uno o más robots y los elementos que
trabajan con ellos para realizar una tarea, dispuestos físicamente en la planta y coordinados por un
sistema de control [Barrientos, 9.1, p. 256].

Groover la ubica dentro de las **células de manufactura de una sola estación** (*single-station
manufacturing cells*) y distingue dos tipos [Groover, 14.1 y 14.2, pp. 367–369]:

- **Célula atendida** (*manned*): un operario realiza o asiste la operación.
- **Célula automatizada** (*automated*): la estación realiza el ciclo sola. El operario solo la
  atiende periódicamente.

En una célula automatizada con robot, el robot puede ser **la máquina principal** (cuando él realiza
el proceso, como en la soldadura) o **un equipo de apoyo** (cuando carga y descarga otra máquina)
[Groover, 8.4, p. 225].

## 2. Componentes de la célula

Barrientos clasifica los elementos que acompañan al robot en dos grupos [Barrientos, 9.1, p. 256]:

| Tipo | Qué son | Ejemplos |
|---|---|---|
| **Periféricos pasivos** | No tienen movimiento propio controlado | Mesas, alimentadores, utillajes (*fixtures*) |
| **Periféricos activos** | Tienen movimiento o control propio | Otros manipuladores, máquinas CN, posicionadores, transportadores |

A eso se suman:

- **El efector final o herramienta:** la interfaz entre el robot y la tarea (pinzas, antorchas de
  soldadura, pistolas de pintura) [Clase 1].
- **El sistema de control de la célula:** coordina todos los equipos (sección 5).
- **Los elementos de seguridad:** cerramiento, puertas, sensores y paradas de emergencia (ver
  [07](07_seguridad_y_normativa.md)).

## 3. El proceso de diseño y el papel de la simulación

El proyecto de una célula implica muchas decisiones, desde un posible rediseño del producto hasta el
plano detallado de la implantación (*lay-out*) [Barrientos, 9.1, p. 256]:

1. Elegir el robot más adecuado para la aplicación.
2. Definir, e incluso diseñar, los periféricos pasivos y activos.
3. Ubicarlos físicamente en la célula.
4. Definir la arquitectura de control, en hardware y software.

La definición del *lay-out* es un **proceso iterativo**. Para iterar rápido, Barrientos recomienda
usar herramientas informáticas: **un simulador de sistemas robotizados permite evaluar alternativas
de robot y de disposición, detectar posibles colisiones y verificar el alcance** [Barrientos, 9.1,
p. 257]. Vuelve sobre esto al tratar el área de trabajo: no alcanza con que todos los puntos queden
dentro del campo de acción, también hay que verificar que el robot no choque con los demás
componentes, y para eso se usan programas de simulación gráfica [Barrientos, 9.2.1, pp. 263–264].

Craig llama a estas herramientas **sistemas de programación fuera de línea** (OLP): modelan en 3D el
robot, los dispositivos fijos, las piezas y las herramientas de la célula, y permiten programar sin
usar el robot real [Craig, 13.2]. RoboDK es una herramienta de este tipo.

## 4. Disposición del robot en la célula

Barrientos plantea cuatro situaciones básicas [Barrientos, 9.1.1, pp. 257–260]:

| Disposición | Descripción | Aplicaciones típicas |
|---|---|---|
| **Robot en el centro** | El robot queda rodeado por los demás elementos y aprovecha al máximo su campo de acción, que tiene forma aproximadamente esférica. | Carga y descarga de máquinas, **soldadura al arco**, paletizado, ensamblado: tareas en las que el robot alcanza puntos fijos dentro de su área. |
| **Robot en línea** | Uno o varios robots trabajan sobre piezas que llegan por un transporte, que puede ser intermitente o continuo. | Líneas de soldadura de carrocerías. |
| **Robot móvil** | El robot se desplaza sobre una vía para seguir a la pieza o ampliar su campo de acción. | Pintura de carrocerías, atención de varias máquinas. |
| **Robot suspendido** | El robot queda sobre el área de trabajo (pórtico o robot articulado invertido). | Adhesivos, pintura, corte, soldadura al arco. |

## 5. El sistema de control de la célula

Una vez fijados los equipos y su disposición, el segundo factor crítico es el sistema de control
[Barrientos, 9.1.2, p. 261]. Tiene que cumplir, en mayor o menor medida, estas funciones:

- **Control individual** de cada máquina, transporte y dispositivo, incluidos los robots.
- **Sincronización** del funcionamiento de los dispositivos entre sí.
- **Detección, tratamiento y recuperación** de situaciones anómalas.
- **Optimización** del funcionamiento conjunto, para evitar esperas innecesarias.
- **Interfaz con el usuario**, que muestre el estado del sistema y permita operarlo con las
  restricciones que correspondan.
- **Interfaz con otras células** y con un **sistema de control superior**.

Sobre el hardware que implementa esas funciones, Barrientos distingue dos casos [Barrientos, 9.1.2,
p. 261]:

- **Célula simple:** el propio controlador del robot puede manejar el resto de los dispositivos con
  sus entradas y salidas, e incluso **ejes externos servocontrolados**.
- **Célula compleja:** con muchos dispositivos que tienen su propio controlador, hace falta una
  **estructura jerárquica** con un elemento central (PLC u ordenador) que se comunique con todos.

La clase 2 lleva esta idea a la seguridad: todos los sensores reportan a un **PLC de seguridad**, que
habilita o no el movimiento del robot (ver [07](07_seguridad_y_normativa.md)) [Clase 2].

## 6. Células que operan sin operador

Groover enumera lo que necesita una célula automatizada para funcionar sin atención durante períodos
largos [Groover, 14.2.1, pp. 369–370].

**Si produce piezas iguales:**

- un **ciclo programado** que haga solo todos los pasos del proceso;
- un **almacenamiento de piezas** (en bruto y terminadas) que permita seguir más allá de un ciclo;
- **transferencia automática** de piezas entre el almacenamiento y la estación;
- **atención periódica** de un operario que reponga piezas y retire las terminadas;
- **protecciones incorporadas** contra condiciones (1) peligrosas para las personas,
  (2) destructivas para el equipo o (3) destructivas para la pieza. Pueden ser una alta confiabilidad
  del proceso o una capacidad de **detección y recuperación de errores**.

**Si produce piezas distintas**, además necesita:

- un **sistema de identificación** de la pieza que entra, para aplicar la secuencia correcta;
- **carga del programa** que corresponde a cada pieza;
- **cambio rápido** de utillajes y herramientas.

Groover también relaciona la capacidad del almacenamiento con el tiempo de operación sin atención:
UT = n·Tc, donde n es la cantidad de piezas almacenadas y Tc el tiempo de ciclo
[Groover, 14.2.2, p. 370].

## 7. Cuándo conviene robotizar

Groover da seis características de una tarea que favorecen el uso de un robot [Groover, 8.4, p. 224]:

1. **Trabajo peligroso** o insalubre para las personas (fundición, pintura, soldadura).
2. **Ciclo repetitivo**, que el robot hace con más consistencia que una persona.
3. **Manipulación difícil** de piezas o herramientas pesadas.
4. **Operación en varios turnos**, que acelera el retorno de la inversión.
5. **Pocos cambios de preparación**, típicos de tiradas largas.
6. **Pieza en posición y orientación conocidas** en cada ciclo.

Estos criterios sirven para justificar, en el informe, por qué la tarea elegida se presta a una celda
robotizada.

## 8. Qué hay que definir en nuestra celda

- ¿Partimos de un ejemplo de RoboDK? ¿De cuál, y qué le agregamos? (requisito de la consigna)
- ¿Es una célula atendida o automatizada? ¿Qué hace el operario y cuándo?
- ¿Qué periféricos pasivos y activos tiene la celda, y por qué hace falta cada uno?
- ¿Qué disposición del robot usamos, y por qué?
- ¿Quién controla la celda: el controlador del robot (con el posicionador como eje externo) o un
  elemento central? ¿Cómo se representa eso en la simulación?
- ¿Qué situaciones anómalas detecta la celda y cómo se recupera de cada una?
- ¿Qué variante de pieza o de patrón incorporamos para cumplir el requisito C3, y qué exige eso al
  control (identificación, programa por pieza)?
- ¿Cuáles de las seis características de Groover cumple nuestra tarea?

## 9. Referencias

- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Capítulo 9, pp. 255–290.
- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Capítulos 8 y 14.
- **[Craig]** Craig, J. J. *Robótica*, 3.ª ed. Pearson Educación. Capítulo 13.
- **[Clase 1]** Perassi, S. *Robótica Industrial – Clase 1: Introducción, morfología y sistemas de
  coordenadas*. UTN FRC, 2026.
- **[Clase 2]** Luque, J. *Islas robotizadas y seguridad industrial*. UTN FRC, 2026.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
