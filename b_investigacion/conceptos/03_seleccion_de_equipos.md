<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 03 · Selección de equipos

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
- [1. Criterio general](#1-criterio-general)
- [2. Características a considerar en el robot](#2-características-a-considerar-en-el-robot)
- [3. Características deseables según la aplicación](#3-características-deseables-según-la-aplicación)
- [4. Selección de la herramienta](#4-selección-de-la-herramienta)
- [5. Selección del posicionador](#5-selección-del-posicionador)
- [6. Otras consideraciones](#6-otras-consideraciones)
- [7. Matriz de selección](#7-matriz-de-selección)
- [8. Qué hay que definir en nuestra celda](#8-qué-hay-que-definir-en-nuestra-celda)
- [9. Referencias](#9-referencias)

---

## Prólogo

El informe técnico tiene que presentar el robot y la herramienta **con su justificación**
[Lineamientos]. Elegir un robot porque estaba en el ejemplo de RoboDK no es una justificación: hay
que mostrar que sus características responden a lo que pide la tarea.

Este documento reúne los criterios de selección de Barrientos (sección 9.2) y los requisitos
específicos de la soldadura (ver [02](02_soldadura_robotizada.md)). Cierra con una matriz que se va a
completar cuando se proponga la celda.

---

## 1. Criterio general

La selección la hace el equipo técnico con su experiencia y buen criterio, buscando en el mercado el
robot que mejor responda a las características necesarias, con **un compromiso adecuado entre precio
y prestaciones** [Barrientos, 9.2, p. 262].

Los valores de catálogo están medidos en condiciones óptimas, distintas de las reales, pero sirven
para comparar entre robots [Barrientos, 9.2, p. 263].

## 2. Características a considerar en el robot

Barrientos las resume en la Tabla 9.1 y las desarrolla en la sección 9.2 [Barrientos, 9.2,
pp. 262–270]:

### 2.1 Área de trabajo (9.2.1)

- Es el volumen al que llega el extremo del robot. Depende de los eslabones y de los límites de las
  articulaciones.
- **Se mide sin la herramienta**: si cambia el efector, el área se recalcula.
- Tiene que incluir **todos** los puntos de la tarea: alimentadores, mesa de trabajo, puntos de
  salida de piezas.
- Que un punto esté dentro del área **no significa que se pueda alcanzar con cualquier orientación**:
  los puntos más alejados y los más cercanos solo admiten ciertas orientaciones.
- Hay que considerar los **puntos singulares**, donde no se puede hacer, por ejemplo, una trayectoria
  rectilínea.
- Además de alcanzar los puntos, el robot **no tiene que colisionar** con los demás componentes. Para
  verificarlo se usan simuladores gráficos.

### 2.2 Grados de libertad (9.2.2)

- Determinan la accesibilidad y la capacidad de orientar la herramienta.
- Manipulación sobre planos horizontales: 3 GDL más uno de orientación alcanzan.
- **Pintura, soldadura al arco y aplicación de sellantes necesitan 6 GDL** o más.
- Más GDL implica más costo. A veces se reemplazan con un **utillaje apropiado o con mesas
  posicionadoras u orientadoras** sincronizadas con el robot.

### 2.3 Precisión, repetibilidad y resolución (9.2.3)

| Concepto | Definición |
|---|---|
| **Resolución** | Mínimo incremento que acepta la unidad de control. |
| **Precisión** | Distancia entre el punto programado y el valor medio de los puntos alcanzados. Depende de la calibración, deformaciones y errores de cálculo. |
| **Repetibilidad** | Radio de la esfera que abarca los puntos alcanzados al repetir el mismo movimiento. Depende de la transmisión (rozamientos, holguras). |

- El dato que suelen dar los fabricantes es la **repetibilidad**, entre ±2 mm y ±0,01 mm en robots
  comerciales.
- En una trayectoria programada (una línea recta) también influyen el **interpolador** y el control
  dinámico: más puntos interpolados y menos velocidad dan más precisión.

### 2.4 Velocidad (9.2.4)

- La velocidad y la carga están **inversamente relacionadas**.
- La velocidad nominal se da en régimen permanente. En movimientos cortos casi nunca se alcanza, así
  que **no sirve sola para estimar el tiempo de ciclo**.
- Valores habituales: **1 a 4 m/s** en el extremo con carga máxima.

### 2.5 Capacidad de carga (9.2.5)

- Hay que sumar **el peso de la pieza y el de la herramienta**, que a menudo es mayor.
- También importa el **momento**: la carga admisible baja cuando el centro de gravedad se aleja de la
  muñeca.
- Valores frecuentes: **5 a 50 kg**.

### 2.6 Sistema de control (9.2.6)

- **Cinemática:** para *pick & place* alcanza con control punto a punto (PTP). Para **soldadura al
  arco**, la **trayectoria continua (CP)** es fundamental. Casi todos los robots tienen interpolación
  en línea recta y circular.
- **Dinámica:** estabilidad y velocidad de respuesta. Sobrepasar el destino (*overshoot*) por inercia
  puede causar colisiones.
- **Programación:** manejo de entradas y salidas, subrutinas, interrupciones y modificación de la
  trayectoria por señales externas. Se desarrolla en [06](06_estructura_de_programas_y_senales.md).

## 3. Características deseables según la aplicación

La Tabla 9.2 de Barrientos agrupa las aplicaciones [Barrientos, 9.2, p. 269]. La soldadura al arco
entra en **procesado**:

| Procesado (incluye soldadura al arco) |
|---|
| Sistema de programación potente |
| 5–6 grados de libertad |
| Campo de acción similar al humano |
| Control de trayectoria continua |

Como referencia, la Tabla 9.3 de Barrientos incluye un robot específico de soldadura al arco: 6 GDL,
1605 mm de alcance, 12 kg de carga, 0,1 mm de repetibilidad y control PTP/CP
[Barrientos, 9.2, p. 270]. Es un ejemplo histórico, pero muestra el orden de magnitud: **alcance
medio, carga baja, buena repetibilidad**.

## 4. Selección de la herramienta

La herramienta (efector final) es la interfaz con la tarea [Clase 1]. Para una antorcha de soldadura
hay que considerar:

- **Peso**, que se suma a la carga del robot (ver 2.5).
- **Geometría:** el largo y el ángulo del cuello definen dónde queda el TCP y qué accesos permite
  (ver [04](04_sistemas_de_referencia_y_tcp.md)).
- **Cables y mangueras:** pueden limitar el giro de la muñeca. Algunos robots los llevan por dentro
  del brazo [Groover, 8.4.2, p. 220].
- **Proceso:** el tipo de antorcha tiene que corresponder al proceso de soldadura elegido (ver
  [02](02_soldadura_robotizada.md)).

## 5. Selección del posicionador

El posicionador es el utillaje motorizado que orienta la pieza frente al robot [Groover, 8.4.2,
p. 220]. Criterios:

- **Cantidad de ejes:** uno o dos, según cuántas caras de la pieza haya que presentar y con qué
  orientación [Groover, 8.4.2, p. 220].
- **Posiciones finitas o continuas:** con un número finito de posiciones (indexado), el accionamiento
  puede ser neumático o hidráulico y el costo es bajo. Con posicionamiento continuo, el costo es alto
  [Barrientos, 9.2.2, p. 266].
- **Sincronización:** el posicionador tiene que estar **controlado de manera sincronizada con el
  robot** [Barrientos, 9.2.2, p. 266], por el controlador del robot como eje externo o por un control
  central [Barrientos, 9.1.2, p. 261].
- **Capacidad de carga:** tiene que corresponder al peso de la pieza y el utillaje. Un posicionador
  muy sobredimensionado ocupa espacio, cuesta más y es difícil de justificar.
- **Reemplazo de GDL:** un posicionador puede evitar la necesidad de un robot con más grados de
  libertad [Barrientos, 9.2.2, p. 265].

## 6. Otras consideraciones

Además de las técnicas, Barrientos menciona [Barrientos, 9.2, p. 271]:

- el **servicio técnico** del fabricante (postventa, mantenimiento, formación, actualización), que
  depende de su presencia en la zona;
- el **costo y la amortización**: un robot más barato y con menos prestaciones puede resolver bien la
  tarea, aunque sea menos adaptable a usos futuros.

## 7. Matriz de selección

Plantilla para completar en la propuesta de la celda:

| Criterio | Qué pide la tarea | Robot elegido | ¿Cumple? |
|---|---|---|---|
| Área de trabajo | Todos los puntos de soldadura y de espera, con la orientación necesaria | | |
| Grados de libertad | 6 (soldadura al arco) | | |
| Repetibilidad | Del orden de las décimas de milímetro | | |
| Velocidad | Traslados rápidos; soldadura lenta | | |
| Carga | Antorcha + cables (la pieza la lleva el posicionador) | | |
| Control | Trayectoria continua, interpolación lineal y circular | | |
| Ejes externos | Posicionador sincronizado | | |
| Programación | E/S, subprogramas, interrupciones | | |

## 8. Qué hay que definir en nuestra celda

- ¿Qué robot usamos? ¿Cumple todos los criterios de la matriz?
- ¿Qué antorcha usamos, cuánto pesa y dónde queda su TCP?
- ¿Usamos posicionador? ¿De cuántos ejes, de qué capacidad y con posiciones finitas o continuas?
- ¿El posicionador elegido está bien dimensionado para la pieza, o hay que justificar por qué se usa
  uno más grande?
- ¿Cómo se sincroniza el posicionador con el robot?

## 9. Referencias

- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Sección 9.2, pp. 262–271.
- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Sección 8.4.2.
- **[Clase 1]** Perassi, S. *Robótica Industrial – Clase 1*. UTN FRC, 2026.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
