<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 06 · Estructura de programas y señales

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
- [1. Métodos de programación](#1-métodos-de-programación)
- [2. Qué tiene que ofrecer un sistema de programación](#2-qué-tiene-que-ofrecer-un-sistema-de-programación)
- [3. Programa principal y subprogramas](#3-programa-principal-y-subprogramas)
- [4. Entradas, salidas e interlocks](#4-entradas-salidas-e-interlocks)
- [5. Interrupciones y monitoreo continuo](#5-interrupciones-y-monitoreo-continuo)
- [6. Sincronización del robot con un eje externo](#6-sincronización-del-robot-con-un-eje-externo)
- [7. El papel de Python](#7-el-papel-de-python)
- [8. Convenciones de nombres](#8-convenciones-de-nombres)
- [9. Qué hay que definir en nuestra celda](#9-qué-hay-que-definir-en-nuestra-celda)
- [10. Referencias](#10-referencias)

---

## Prólogo

El segundo requisito de complejidad mínima pide **un programa principal que llame a subprogramas**
[Lineamientos, requisito C2], y uno de los criterios de evaluación es que los programas estén
**ordenados y con nombres claros**. Además, los movimientos del robot **no pueden hacerse con
Python**: se resuelven con programas e instrucciones de RoboDK, y Python solo puede usarse para
sensores adicionales [Lineamientos, §2].

Este documento define cómo se estructura un programa de robot, cómo se comunica el robot con los
demás equipos de la celda y dónde está el límite de lo que puede hacer Python. Se basa en Barrientos
(capítulo 8 y sección 9.1.2), Groover (sección 8.5) y Craig (capítulos 12 y 13).

---

## 1. Métodos de programación

Barrientos clasifica los métodos en **programación por guiado** y **programación textual**
[Barrientos, 8.1, pp. 220–225]. Craig distingue tres niveles [Craig, 12.2, p. 341]:

1. **Enseñar mostrando:** se lleva el robot a cada punto con un dispositivo de enseñanza y se
   registra la posición.
2. **Lenguajes de programación de robots explícitos**, como RAPID de ABB.
3. **Lenguajes a nivel de tarea**, donde se indica qué hacer y el sistema decide cómo.

La **programación fuera de línea** (OLP) combina ambos: se enseñan puntos sobre un modelo 3D de la
célula y el sistema genera las instrucciones del lenguaje del robot [Craig, 13.2].
RoboDK trabaja así: los targets se definen sobre la estación simulada y los programas pueden
traducirse al lenguaje del controlador real.

## 2. Qué tiene que ofrecer un sistema de programación

Barrientos enumera los requisitos de un sistema de programación de robots [Barrientos, 8.2,
pp. 225–230]:

- **entorno de programación** y **modelado del entorno** (8.2.1 y 8.2.2);
- **tipos de datos** para posiciones y orientaciones (8.2.3);
- **manejo de entradas y salidas** (8.2.4);
- **control del movimiento**: tipo de trayectoria, velocidad, precisión (8.2.5; ver
  [05](05_tipos_de_movimiento.md));
- **control del flujo de ejecución**: bucles, condiciones, subrutinas, tareas en paralelo e
  interrupciones (8.2.6).

Al seleccionar un robot también se evalúa la capacidad de estructurar programas con subrutinas y
bucles, atender interrupciones y modificar trayectorias por señales externas [Barrientos, 9.2.6,
p. 270].

## 3. Programa principal y subprogramas

RAPID, el lenguaje de ABB, es altamente estructurado: un programa se divide en **módulos**, uno de
ellos principal, y cada módulo contiene **rutinas** y datos [Barrientos, 8.4.1, p. 236]. La misma
lógica se aplica en RoboDK: **un programa principal que llama a subprogramas**.

**Criterios para dividir en subprogramas:**

- **Una función por subprograma:** inicio, aproximación, soldadura, retirada, indexado, regreso al
  reposo.
- **Reutilización:** una operación que se repite (un cordón, un indexado) se escribe una sola vez y se
  llama varias veces. Si se combina con frames que se mueven con la pieza (ver
  [04](04_sistemas_de_referencia_y_tcp.md)), el mismo subprograma de soldadura sirve para todos los
  cordones equivalentes.
- **Estado inicial y final conocidos:** cada subprograma tiene que dejar al robot y a las señales en
  un estado definido, para que el siguiente pueda arrancar sin suposiciones.
- **Programa principal legible:** el programa principal tiene que mostrar la secuencia de la tarea
  sin detalles de movimiento.

**Estructura típica de un ciclo:**

```text
Principal
├── Inicio            (herramienta, frame, velocidad, señales en estado seguro, robot en reposo)
├── Repetir por cada posición de trabajo:
│   ├── Indexar       (eje externo a la posición)
│   ├── Esperar       (confirmación de posición)
│   ├── Aproximar
│   ├── Soldar        (arco encendido, cordón, arco apagado)
│   └── Retirar
└── Fin de ciclo      (robot y eje externo a reposo)
```

Para que el ciclo **se repita de forma continua** (requisito C4), el estado final del ciclo tiene que
coincidir con su estado inicial.

## 4. Entradas, salidas e interlocks

La comunicación del robot con las demás máquinas es fundamental para integrarlo y sincronizarlo, y en
el nivel más simple se hace con **señales binarias de entrada y salida** [Barrientos, 8.2.4,
p. 228]:

- Con las **salidas**, el robot activa o desactiva dispositivos (por ejemplo, el arco de soldadura).
- Con las **entradas**, el robot condiciona el flujo del programa: esperas y saltos.

Groover llama **interlocks** a estas señales de coordinación y define dos comandos básicos
[Groover, 8.2, p. 215; 8.5, pp. 231–232]:

| Comando | Tipo de interlock | Uso | Ejemplo en una celda de soldadura |
|---|---|---|---|
| **WAIT** | De entrada | El programa se detiene hasta que una entrada tome un valor. | Esperar que el posicionador confirme que llegó a su posición. |
| **SIGNAL** | De salida | El robot activa una salida hacia otro equipo. | Encender el arco al empezar el cordón; ordenar el indexado. |

En RoboDK, la instrucción equivalente es **fijar o esperar una E/S** (*Set or Wait I/O*).

## 5. Interrupciones y monitoreo continuo

WAIT y SIGNAL actúan en el punto del programa donde aparecen. Para eventos que pueden ocurrir en
cualquier momento hace falta **monitorear una señal todo el tiempo** [Groover, 8.5, p. 232]:

- El comando **REACT** vigila una entrada continuamente. Si cambia, interrumpe el programa y salta a
  una subrutina, por ejemplo **SAFESTOP**, que detiene el robot.
- El ejemplo de Groover es justamente de seguridad: un sensor que detecta a una persona que entra al
  volumen de trabajo del robot.

Barrientos describe lo mismo como **interrupciones**: una señal o combinación de señales se monitorea
de manera automática, y si se cumple la condición, el control ejecuta una rutina especial. La
interrupción puede tomarse **inmediatamente**, **al terminar la instrucción en curso** o **al
terminar el ciclo** [Barrientos, 8.2.4, p. 228]. También hay que poder **activarlas y desactivarlas**
según la fase del programa y fijar **prioridades** entre ellas [Barrientos, 8.2.6, p. 230].

**Movimientos protegidos:** un movimiento que se interrumpe si se cumple una condición externa se
llama movimiento protegido o monitorizado (*guarded motion*) [Barrientos, 8.2.5, p. 230].

Estos mecanismos son la base de la parada de emergencia y de la apertura de puerta (ver
[07](07_seguridad_y_normativa.md)).

## 6. Sincronización del robot con un eje externo

Un posicionador tiene que moverse **sincronizado con el robot** [Barrientos, 9.2.2, p. 266]. Hay dos
formas:

| Forma | Cómo funciona | Cuándo conviene |
|---|---|---|
| **Coordinación por señales** | El robot y el eje externo tienen programas separados. Se coordinan con interlocks: el robot ordena indexar (SIGNAL), espera la confirmación (WAIT) y suelda con el eje quieto. | Cuando el eje externo **solo indexa** entre posiciones fijas y el robot trabaja con la pieza detenida. |
| **Eje externo sincronizado** | El controlador del robot mueve el eje externo como un eje más, en el mismo movimiento. | Cuando la pieza tiene que **girar mientras se suelda** (por ejemplo, un cordón circunferencial). |

Barrientos admite que, en una célula simple, el propio controlador del robot maneje ejes externos
servocontrolados [Barrientos, 9.1.2, p. 261].

**En la simulación**, un posicionador es un **mecanismo** con sus propios programas o targets
articulares. Los lineamientos piden que una cinta se modele como mecanismo y sin Python
[Lineamientos, requisito C3], y el mismo criterio vale para un posicionador.

Craig advierte que, cuando hay varios dispositivos móviles, la simulación de los tiempos sirve para
detectar problemas de sincronización como el **interbloqueo** [Craig, 13.2].

## 7. El papel de Python

**Qué no puede hacer Python** [Lineamientos, §2]:

- mover el robot;
- reemplazar programas o instrucciones de movimiento de RoboDK.

**Qué sí puede hacer:**

- simular **sensores adicionales** (presencia de pieza, puerta, barrera);
- leer y escribir señales que los programas de RoboDK consultan con WAIT o usan como condición.

**Criterio:** la secuencia de movimientos tiene que poder ejecutarse **completa desde el programa
principal de RoboDK**. Python puede agregar condiciones de habilitación, pero si se lo saca, el ciclo
de movimientos tiene que seguir existiendo en la estación.

## 8. Convenciones de nombres

Los programas tienen que tener **nombres claros** (criterio de evaluación). Recomendaciones:

- **Programas:** verbo + objeto. Por ejemplo `Soldar_Cordon`, `Indexar_Posicionador`,
  `Ir_Reposo`.
- **Targets:** prefijo por función y número. Por ejemplo `Aprox_01`, `Inicio_Cordon_01`,
  `Fin_Cordon_01`, `Reposo`.
- **Frames:** por el objeto al que pertenecen. Por ejemplo `Frame_Celda`, `Frame_Pieza`.
- **Señales:** nombre de la función, documentado en una tabla de E/S.
- Un mismo idioma y un mismo formato en toda la estación.

## 9. Qué hay que definir en nuestra celda

- ¿Qué subprogramas tiene la celda, y qué hace cada uno?
- ¿Cuál es el estado inicial y final de cada subprograma?
- ¿Qué señales de entrada y salida hay (arco, posicionador, puerta, presencia de pieza,
  emergencia)? Armar la tabla de E/S.
- ¿El posicionador se coordina por señales o como eje sincronizado?
- ¿Qué eventos se monitorean continuamente, y qué rutina se ejecuta en cada caso?
- ¿Qué hace Python, si lo usamos, y cómo se garantiza que no mueva el robot?
- ¿El programa principal puede correr el ciclo completo sin el panel?

## 10. Referencias

- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Capítulo 8, pp. 219–253; secciones 9.1.2, 9.2.2 y 9.2.6.
- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Secciones 8.2 y 8.5, pp. 214–232.
- **[Craig]** Craig, J. J. *Robótica*, 3.ª ed. Pearson Educación. Capítulos 12 y 13.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
