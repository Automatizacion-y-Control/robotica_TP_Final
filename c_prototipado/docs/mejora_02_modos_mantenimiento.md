<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

**Cátedra: Robótica Industrial**

# Mejora 02 · Modos de operación y mantenimiento

De la v03 a la v04

**Grupo 4**<br>
Casali Emiliano · Ferrero Facundo · Vera Gonzalo

**Docentes**<br>
Ing. Julián Luque · Lic. Sergio Perassi

Comisión 2LA1 · Año 2026

</div>

## Índice

- [Prólogo](#prólogo)
- [1. Motivo del cambio](#1-motivo-del-cambio)
- [2. Cambios en la disposición](#2-cambios-en-la-disposición)
- [3. Posiciones y programas de mantenimiento](#3-posiciones-y-programas-de-mantenimiento)
- [4. Generación de la estación](#4-generación-de-la-estación)
- [5. Verificación](#5-verificación)
- [6. Alcance y continuidad](#6-alcance-y-continuidad)
- [7. Referencias](#7-referencias)

## Prólogo

Este documento describe el paso de la v03 a la v04: los cambios de disposición que hacen posible
el mantenimiento y las posiciones para realizarlo. El ciclo de producción no cambia. La lógica de
modos, los sensores y el panel se agregan en la v05 y se describen en
[panel y sensores](panel_y_sensores.md). Fecha de revisión: **2026-11-06**.

## 1. Motivo del cambio

El análisis de [modos y mantenimiento, §9](modos_y_mantenimiento.md#9-problemas-de-la-disposición-actual-v03)
mostró que la disposición de la v03 no permitía intervenir la cinta ni aislar los equipos desde
afuera. La mejora 02 aplica los requisitos de
[§10 de ese documento](modos_y_mantenimiento.md#10-requisitos-para-la-v04-y-para-el-panel).

## 2. Cambios en la disposición

| Elemento | Cambio | Valor |
|---|---|---|
| Cara sur del cerramiento | Se acerca a la cinta y se arma con paneles desmontables, para sacar la banda por ese costado. | Y = −960 mm; paneles de 700 mm nominales |
| Pasillo de mantenimiento | Del lado sur, afuera del cerramiento. | 800 mm de ancho; X de −1950 a 1500 mm |
| Túneles de la cinta | Entrada y salida se adaptan a la nueva cara sur. | Y de −960 a −120 mm |
| Accionamiento de la cinta | Se representa en el extremo oeste, afuera, con su resguardo. | Centro en (−1760, −80) mm |
| Tablero de aislamiento (LOTO) | Afuera, adosado a la cara este, junto a la puerta. | Centro en (1010, 700) mm |
| Panel de operador | Afuera del cerramiento. | Centro en (1150, 250) mm |
| Pulsadores de emergencia | Junto a la puerta y en la entrada y la salida de la cinta, además del panel. | (930, 920), (−1420, −1060) y (970, −1060) mm |
| Gabinetes, fuente TIG y argón | Detrás de la cara norte, afuera. | Y = 1950 mm |

Todos los valores están en [parametros_celda.py](../scripts/parametros_celda.py), sección «Mejora 02».

**Aclaración sobre el accionamiento.** El modelo de cinta de la biblioteca de RoboDK dibuja el rodillo
motriz en el extremo este, dentro de la celda. En la v04 el accionamiento se representa con un modelo
propio en el extremo oeste, afuera, y el rodillo del este se considera de retorno.

## 3. Posiciones y programas de mantenimiento

| Robot | Target | Valores articulares (°) |
|---|---|---|
| IRB 1200 | `Man_Mantenimiento` | 45, −30, 50, 0, 60, 0 |
| CRB 1300 | `Sold_Mantenimiento` | 100, −30, 50, 0, 60, 0 |

La postura del CRB se corrigió durante la verificación: la versión inicial chocaba con la estación de
servicio al 84 % de la ida y presentaba contactos del robot en la postura final.

Programas agregados:

| Programa | Función |
|---|---|
| `Man_Ir_Mantenimiento` | Lleva el IRB de reposo a su posición de mantenimiento. |
| `Sold_Ir_Mantenimiento` | Lleva el CRB de reposo a su posición de mantenimiento. |
| `Parada_Ciclo` | Apaga el arco y lleva ambos robots a reposo. En la v05 el coordinador usa `Parada_Entre_Piezas`. |

## 4. Generación de la estación

La v04 se genera con [04_modos_mantenimiento.py](../scripts/04_modos_mantenimiento.py) a
partir de la v03 guardada, para conservar los eventos de simulación cargados desde la interfaz.

## 5. Verificación

Resultados de RoboDK 6.1.1.26991, detallados en
[panel y sensores, §2](panel_y_sensores.md#2-estado-comprobado-de-la-v04):

| Comprobación | Resultado |
|---|---|
| Targets cartesianos | 19 alcanzables con sus herramientas. |
| Verificador con pieza transportada | Sin colisiones, con muestreo de 1 mm/1°. |
| Producción | Dos ejecuciones consecutivas de un lote, a ×10, sin colisiones detectadas. |
| Mantenimiento individual | Ida y vuelta de cada robot sin colisiones. |
| Mantenimiento conjunto | Ambos órdenes sin colisiones ([evidencia](../verificaciones/mantenimiento_conjunto_v04.json)). Orden adoptado: IRB y CRB; regreso CRB e IRB. |

## 6. Alcance y continuidad

Las posiciones se verificaron geométricamente. Eso no acredita accesibilidad física para una tarea
particular, soporte de ejes ni aislamiento. Los puntos de aislamiento y los pulsadores son modelos
de la disposición, no funciones simuladas.

La v05 parte de esta estación y agrega el coordinador, los modos, los sensores y el panel.

## 7. Referencias

- [Modos y mantenimiento](modos_y_mantenimiento.md).
- [Panel y sensores](panel_y_sensores.md).
- [Definición de la celda](definicion_celda.md).
- [Catálogo de componentes, §16](../../b_investigacion/componentesRDK.md#16-cambios-en-la-v04-mejora-02).
