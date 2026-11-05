<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 00 · Requisitos y trazabilidad

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
- [1. Consigna](#1-consigna)
- [2. Requisitos de programación del movimiento](#2-requisitos-de-programación-del-movimiento)
- [3. Requisitos de complejidad mínima](#3-requisitos-de-complejidad-mínima)
- [4. Entregables](#4-entregables)
- [5. Criterios de evaluación](#5-criterios-de-evaluación)
- [6. Matriz de trazabilidad](#6-matriz-de-trazabilidad)
- [7. Documentos de conceptos](#7-documentos-de-conceptos)
- [8. Referencias](#8-referencias)

---

## Prólogo

Este documento abre la serie de documentos de conceptos de implementación del trabajo final. Reúne
los requisitos que fija la cátedra en los lineamientos del trabajo [Lineamientos] y los vincula con
el documento de la serie que desarrolla los conceptos necesarios para cumplir cada uno.

La serie no describe todavía la celda del grupo. Su objetivo es fijar, a partir de la bibliografía
de la cátedra, los conceptos y criterios con los que después se va a diseñar, programar y justificar
la celda. Cada documento termina con una sección de preguntas abiertas que la propuesta de la celda
tendrá que responder.

Este documento funciona también como lista de control: antes de entregar, cada fila de la matriz de
la sección 6 tiene que tener su evidencia en la estación (`.rdk`) y en el informe técnico.

---

## 1. Consigna

> Diseñar, programar y simular en RoboDK una celda robotizada que cumpla una tarea concreta.

- Se puede partir de un ejemplo de RoboDK. En ese caso hay que **indicar cuál se usó y
  profundizarlo**, agregando complejidad a conciencia: cada elemento que se suma tiene que tener una
  razón, y no se trata de llenar la celda de elementos.
- Tarea del grupo: **soldadura de paquetes de chapa de estator** de motores de lavarropas (ver
  [`../despiece_motor_lavarropas.md`](../despiece_motor_lavarropas.md)).

## 2. Requisitos de programación del movimiento

| Id | Requisito |
|---|---|
| M1 | Los movimientos se programan con **MoveJ, MoveL y MoveC**, y hay que entender cuándo conviene cada uno. |
| M2 | **MoveJ:** traslados libres entre zonas, donde no importa la trayectoria de la herramienta. |
| M3 | **MoveL:** recorridos en línea recta (aproximaciones, retiradas y trabajo sobre la pieza). |
| M4 | **MoveC:** trayectorias en arco o circulares que la herramienta debe seguir. |
| M5 | **Python no se usa para los movimientos del robot.** Se resuelven con programas e instrucciones de RoboDK. Python solo puede usarse para sensores adicionales. |

## 3. Requisitos de complejidad mínima

| Id | Requisito |
|---|---|
| C1 | **Frames y TCP propios:** al menos un frame de referencia propio (mesa, pallet, pieza o cinta) y una herramienta con su TCP definido y justificado, no el predeterminado. |
| C2 | **Programas ordenados:** un programa principal que llame a subprogramas (por ejemplo: inicio, tomar, depositar, trabajar). |
| C3 | **Al menos uno de estos elementos:** una cinta transportadora, un segundo robot o variantes de pieza o de patrón (dos tipos de pieza, o un pallet con varias posiciones). Una cinta se modela como mecanismo, sin Python. |
| C4 | **Simulación válida:** un ciclo que se pueda repetir de forma continua, sin colisiones y sin puntos fuera de alcance. |

## 4. Entregables

| Id | Entregable | Contenido exigido |
|---|---|---|
| E1 | Archivo de la estación (`.rdk`) | Simulación completa y programas listos para ejecutar. |
| E2 | Informe técnico (máximo 8 páginas) | a) Tarea que resuelve la celda. b) Ejemplo de RoboDK de partida, si se usó, y qué se le agregó. c) Robot, herramienta y frames, con su justificación. d) Estructura de programas y por qué se eligió cada tipo de movimiento. e) Resultados: tiempo de ciclo y verificación de colisiones y alcance. f) Conclusiones y dificultades. |

## 5. Criterios de evaluación

| Criterio | Qué se observa |
|---|---|
| Movimientos | Uso de MoveJ, MoveL y MoveC con la elección correcta de cada uno. Sin Python en los movimientos. |
| Complejidad agregada | Cumplimiento de los requisitos mínimos y ampliaciones claras y justificadas. |
| Calidad de la simulación | Ciclo continuo, sin colisiones ni puntos fuera de alcance, programas ordenados y con nombres claros. |
| Informe | Completo, claro y coherente con lo que muestra la estación. |

## 6. Matriz de trazabilidad

| Requisito | Documento que lo fundamenta | Evidencia esperada en la estación | Sección del informe |
|---|---|---|---|
| Consigna (tarea concreta) | [01](01_celula_robotizada.md), [02](02_soldadura_robotizada.md) | Celda que suelda la pieza | E2-a |
| Ejemplo de partida | [01](01_celula_robotizada.md) | — | E2-b |
| M1 a M4 | [05](05_tipos_de_movimiento.md) | MoveJ, MoveL y MoveC en los programas, cada uno donde corresponde | E2-d |
| M5 | [06](06_estructura_de_programas_y_senales.md) | Ningún script Python que mueva el robot | E2-d |
| C1 | [04](04_sistemas_de_referencia_y_tcp.md) | Frame de pieza o posicionador y TCP de antorcha definidos | E2-c |
| C2 | [06](06_estructura_de_programas_y_senales.md) | Programa principal que llama a subprogramas con nombres claros | E2-d |
| C3 | [01](01_celula_robotizada.md), [03](03_seleccion_de_equipos.md) | Variante de pieza o patrón (a definir en la propuesta) | E2-b, E2-c |
| C4 | [08](08_tiempo_de_ciclo_y_validacion.md) | Ciclo repetible, verificación de colisiones activa, todos los targets alcanzables | E2-e |
| Justificación del robot y la herramienta | [03](03_seleccion_de_equipos.md), [02](02_soldadura_robotizada.md) | — | E2-c |
| Seguridad de la celda (complejidad justificada) | [07](07_seguridad_y_normativa.md) | Cerramiento, puerta, parada de emergencia y habilitaciones | E2-b, E2-f |
| Tiempo de ciclo | [08](08_tiempo_de_ciclo_y_validacion.md) | Tiempo estimado del programa principal | E2-e |

## 7. Documentos de conceptos

| # | Documento | Tema |
|---|---|---|
| 00 | [00_requisitos_y_trazabilidad.md](00_requisitos_y_trazabilidad.md) | Este documento |
| 01 | [01_celula_robotizada.md](01_celula_robotizada.md) | Qué es una célula robotizada, componentes, disposición y control |
| 02 | [02_soldadura_robotizada.md](02_soldadura_robotizada.md) | Soldadura al arco robotizada y la celda de soldadura típica |
| 03 | [03_seleccion_de_equipos.md](03_seleccion_de_equipos.md) | Criterios para elegir el robot, la herramienta y el posicionador |
| 04 | [04_sistemas_de_referencia_y_tcp.md](04_sistemas_de_referencia_y_tcp.md) | Sistemas de referencia y TCP |
| 05 | [05_tipos_de_movimiento.md](05_tipos_de_movimiento.md) | Trayectorias, interpolación y MoveJ, MoveL y MoveC |
| 06 | [06_estructura_de_programas_y_senales.md](06_estructura_de_programas_y_senales.md) | Programa principal, subprogramas, señales y sincronización |
| 07 | [07_seguridad_y_normativa.md](07_seguridad_y_normativa.md) | Riesgos, medidas de seguridad y normas |
| 08 | [08_tiempo_de_ciclo_y_validacion.md](08_tiempo_de_ciclo_y_validacion.md) | Tiempo de ciclo, producción y validación de la simulación |

## 8. Referencias

- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso: simulación de una celda
  robotizada*. Comisión 2LA1, 2026. (`a_requisitos/Lineamiento_Trabajo_Final_Robotica.pdf`)
- La bibliografía completa de la serie está en [`../bibliografia.md`](../bibliografia.md).
