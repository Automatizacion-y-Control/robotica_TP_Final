<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 08 · Tiempo de ciclo y validación

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
- [1. Tiempo de ciclo](#1-tiempo-de-ciclo)
- [2. Tasa de producción](#2-tasa-de-producción)
- [3. Costos y justificación económica](#3-costos-y-justificación-económica)
- [4. La simulación como herramienta de validación](#4-la-simulación-como-herramienta-de-validación)
- [5. Qué hay que verificar](#5-qué-hay-que-verificar)
- [6. Prueba progresiva del programa](#6-prueba-progresiva-del-programa)
- [7. Límites de la simulación](#7-límites-de-la-simulación)
- [8. Cómo presentar los resultados](#8-cómo-presentar-los-resultados)
- [9. Qué hay que definir en nuestra celda](#9-qué-hay-que-definir-en-nuestra-celda)
- [10. Referencias](#10-referencias)

---

## Prólogo

El cuarto requisito de complejidad mínima pide una **simulación válida**: un ciclo que se pueda
repetir de forma continua, **sin colisiones y sin puntos fuera de alcance** [Lineamientos, requisito
C4]. El informe tiene que presentar los **resultados**: tiempo de ciclo y verificación de colisiones
y alcance [Lineamientos, §4].

Este documento define cómo se analiza el tiempo de ciclo de una celda (Groover, sección 8.4), qué hay
que verificar en la simulación (Craig, capítulo 13; Barrientos, secciones 9.1 y 9.2) y cómo se
prueba un programa (Barrientos, sección 9.3.2).

---

## 1. Tiempo de ciclo

Groover descompone el tiempo de ciclo de una aplicación robotizada así [Groover, 8.4, p. 224]:

> **Tc = To + Th + Tt**

| Término | Significado | En una celda de soldadura |
|---|---|---|
| **Tc** | Tiempo de ciclo [min/pieza] | Tiempo total de una pieza |
| **To** | Tiempo de la operación (proceso o ensamble) | Tiempo de soldadura (arco encendido) |
| **Th** | Tiempo de manipulación de la pieza | Carga, descarga e **indexado** del posicionador |
| **Tt** | Tiempo de manipulación de la herramienta, si corresponde | Aproximaciones, retiradas, traslados, limpieza de antorcha |

Cuando el robot realiza el proceso, como en la soldadura, **el robot es la máquina principal** y la
manipulación de la pieza queda a cargo de equipos de apoyo (otro robot, un posicionador o un
operario) [Groover, 8.4, p. 225].

Esta descomposición permite ver **cuánto del ciclo es realmente soldadura**. Es el equivalente
automático del *arc-on time* del soldador manual, que es de apenas un 20–30 % del turno
[Groover, 8.4.2, p. 220] (ver [02](02_soldadura_robotizada.md)).

**Sobre la velocidad de catálogo:** en movimientos cortos el robot casi nunca alcanza su velocidad
nominal, así que el tiempo de ciclo no se puede calcular con ella. Por eso algunos fabricantes indican
el tiempo de un movimiento típico [Barrientos, 9.2.4, p. 268]. La simulación da una estimación más
realista.

## 2. Tasa de producción

Para una tirada de Q piezas con un tiempo de preparación Tsu [Groover, 8.4, p. 225]:

> **Tp = (Tsu + Q·Tc) / Q**  y  **Rp = 60 / Tp** [piezas/h]

En tiradas largas, Tsu/Q tiende a cero y la tasa de producción tiende a la **tasa de ciclo**:

> **Rc = 60 / Tc** [piezas/h], con Tc en minutos.

El tiempo de preparación incluye **el tiempo de programar el robot en la planta**
[Groover, 8.4, p. 225]. La programación fuera de línea busca justamente reducirlo, porque permite
programar sin detener el equipo físico [Craig, 13.2].

## 3. Costos y justificación económica

- Costo total anual de la celda: **TC = Cf + Cv·Q**, con costos fijos (equipos) y variables (mano de
  obra, materiales, energía). Un **análisis de punto de equilibrio** compara la celda robotizada con
  una manual [Groover, 8.4, p. 226].
- Barrientos dedica la sección 9.4 a la justificación económica: factores económicos, el robot como
  elemento principal del análisis y métodos de análisis [Barrientos, 9.4, pp. 277–284].

Los lineamientos **no piden** un análisis económico. Puede mencionarse en las conclusiones para
darle contexto industrial al tiempo de ciclo.

## 4. La simulación como herramienta de validación

Barrientos recomienda usar simuladores durante el diseño de la célula: **permiten elegir el robot,
detectar posibles colisiones y verificar el alcance** [Barrientos, 9.1, p. 257; 9.2.1, p. 264].

Craig describe qué tiene que hacer un sistema de programación fuera de línea para que la simulación
sea válida [Craig, 13.2]:

- **Modelado 3D** del robot y de todos los dispositivos, piezas y herramientas de la célula.
- **Detección automática de colisiones:** el sistema advierte e indica dónde ocurre la colisión.
  Tiene que poder aceptar colisiones deseadas (por ejemplo, la herramienta en contacto con la pieza) y
  avisar cuando dos objetos pasan **a menos de una tolerancia**.
- **Emulación cinemática:** la cinemática inversa simulada tiene que comportarse como la del
  controlador real.
- **Emulación de la planificación de trayectorias:** la forma de la trayectoria sirve para detectar
  colisiones, y **su temporización sirve para predecir el tiempo de ciclo**.
- **Simulación de varios procesos:** incluso una célula con un solo robot tiene otros dispositivos
  activos con los que interactúa. Simular los tiempos de todos permite detectar problemas de
  sincronización como el **interbloqueo**.
- **Calibración de la célula:** el modelo nunca coincide con la realidad, así que hay que calibrar
  antes de usar en el robot real los programas hechos fuera de línea.

## 5. Qué hay que verificar

| Verificación | Qué se comprueba | Por qué puede fallar | Referencia |
|---|---|---|---|
| **Alcance** | Todos los targets alcanzables, **con la orientación pedida** | Puntos lejanos o cercanos que solo admiten ciertas orientaciones | Barrientos, 9.2.1, p. 263 |
| **Trayectorias cartesianas** | Cada MoveL y MoveC se ejecuta completo | Puntos intermedios inalcanzables, singularidades, cambio de configuración | Craig, 7.5, pp. 219–222 |
| **Singularidades** | Sin velocidades articulares excesivas | Paso cerca de una configuración singular | Barrientos, 9.2.1, p. 263; Craig, 7.5 |
| **Límites articulares** | Ningún eje fuera de rango | Configuración o giro de muñeca acumulado | Craig, 7.5 |
| **Colisiones** | Sin choques entre robot, herramienta, pieza, utillaje, posicionador y cerramiento | Disposición, trayectorias de traslado, giro del posicionador | Barrientos, 9.2.1, p. 263; Craig, 13.2 |
| **Sincronización** | El robot no se mueve sobre la pieza mientras el eje externo gira | Falta de esperas o señales | Craig, 13.2; ver [06](06_estructura_de_programas_y_senales.md) |
| **Repetibilidad del ciclo** | El estado final del ciclo coincide con el inicial, y el ciclo corre varias veces seguidas | Señales o ejes que no vuelven a su estado inicial | Lineamientos, C4 |

**En RoboDK:**

- La verificación de colisiones se activa en la estación y detiene la simulación al detectar un
  choque. Se configura qué pares de objetos se verifican.
- Los targets inalcanzables y los movimientos que no pueden ejecutarse se informan al actualizar o
  ejecutar el programa.
- Al actualizar un programa se obtienen el **tiempo estimado** y la **longitud de la trayectoria**.

## 6. Prueba progresiva del programa

Barrientos la incluye entre las medidas de seguridad en la instalación [Barrientos, 9.3.2, p. 276]:
el programa del robot, y el de toda la célula, se desarrolla y ejecuta con sumo cuidado:

1. **primero a velocidad lenta y paso a paso;**
2. después **de forma continua**;
3. **aumentando la velocidad** de forma progresiva.

En la simulación conviene seguir el mismo orden: primero cada subprograma por separado, después el
programa principal completo y, por último, varios ciclos seguidos con la verificación de colisiones
activa.

## 7. Límites de la simulación

Conviene declararlos en el informe:

- El **tiempo de ciclo es una estimación** del simulador, no una medición en una instalación real.
- La **verificación de colisiones** se limita a las geometrías y los pares de objetos que se
  configuraron.
- La **emulación dinámica** se puede omitir si el robot sigue bien las trayectorias, pero a alta
  velocidad o con carga pesada los errores dinámicos pueden ser significativos [Craig, 13.2].
- **No se modela el proceso de soldadura** (térmico ni metalúrgico).
- Los **sensores y la seguridad** son representaciones lógicas, no dispositivos certificados.

## 8. Cómo presentar los resultados

Tabla mínima para el informe:

| Indicador | Valor | Cómo se obtuvo |
|---|---|---|
| Tiempo de ciclo Tc | | Estimación de RoboDK del programa principal |
| Tiempo de soldadura To | | Suma de los tramos con el arco encendido |
| Tiempo de manipulación Th | | Indexados del posicionador (y carga y descarga, si se simulan) |
| Tiempo de herramienta Tt | | Aproximaciones, retiradas y traslados |
| Proporción de soldadura To/Tc | | Cálculo |
| Tasa de ciclo Rc | | 60 / Tc |
| Longitud de la trayectoria | | RoboDK |
| Cantidad de cordones | | — |
| Errores de movimiento | | Ejecución con verificación activa |
| Avisos de colisión | | Ejecución con verificación activa |
| Ciclos consecutivos sin error | | Prueba de repetibilidad |

## 9. Qué hay que definir en nuestra celda

- ¿Cómo medimos por separado To, Th y Tt en RoboDK?
- ¿Qué pares de objetos tienen que estar en la verificación de colisiones, y cuáles se aceptan
  (antorcha con pieza)?
- ¿Cuántos ciclos seguidos corremos para demostrar la repetibilidad?
- ¿Simulamos la carga y descarga de la pieza, o solo la soldadura?
- ¿Qué tiempo de ciclo es razonable para la pieza, y cómo lo comparamos con la soldadura manual?

## 10. Referencias

- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Sección 8.4, pp. 224–226; sección 8.4.2.
- **[Craig]** Craig, J. J. *Robótica*, 3.ª ed. Pearson Educación. Sección 7.5, pp. 219–222; capítulo
  13.
- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Secciones 9.1, 9.2.1, 9.2.4, 9.3.2 y 9.4.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
