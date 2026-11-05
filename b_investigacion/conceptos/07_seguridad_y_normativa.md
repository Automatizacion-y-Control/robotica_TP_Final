<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 07 · Seguridad y normativa

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
- [1. Por qué la seguridad es crítica en una célula robotizada](#1-por-qué-la-seguridad-es-crítica-en-una-célula-robotizada)
- [2. Tipos de accidentes y riesgos](#2-tipos-de-accidentes-y-riesgos)
- [3. Causas de los accidentes](#3-causas-de-los-accidentes)
- [4. Responsabilidades](#4-responsabilidades)
- [5. Niveles de protección](#5-niveles-de-protección)
- [6. Medidas de seguridad](#6-medidas-de-seguridad)
- [7. El PLC de seguridad y la habilitación del robot](#7-el-plc-de-seguridad-y-la-habilitación-del-robot)
- [8. Riesgos propios de la soldadura al arco](#8-riesgos-propios-de-la-soldadura-al-arco)
- [9. Normativa](#9-normativa)
- [10. Representación en la simulación](#10-representación-en-la-simulación)
- [11. Qué hay que definir en nuestra celda](#11-qué-hay-que-definir-en-nuestra-celda)
- [12. Referencias](#12-referencias)

---

## Prólogo

Los lineamientos no piden explícitamente elementos de seguridad, pero sí que la complejidad que se
agrega esté **justificada** y que la simulación sea **válida** [Lineamientos]. La seguridad es una de
las razones más sólidas para agregar elementos a una celda: un cerramiento, una puerta enclavada o
una parada de emergencia tienen una función clara y una base normativa.

Este documento reúne los conceptos de seguridad de la clase 2, de Barrientos (sección 9.3) y de
Groover (sección 14.2.1), y las normas aplicables a una celda robotizada de soldadura.

---

## 1. Por qué la seguridad es crítica en una célula robotizada

Barrientos señala que la seguridad suele tratarse de manera marginal en los textos de robótica, pero
que es un aspecto crítico en el desarrollo y la explotación de una célula, por dos razones
[Barrientos, 9.3, p. 271]:

- el robot tiene **mayor índice de riesgo** que otras máquinas parecidas;
- la **aceptación social** del robot en la fábrica.

La Tabla 9.4 de Barrientos compara el robot con una máquina de control numérico [Barrientos, 9.3.2,
p. 272]:

| Robot industrial | Máquina de control numérico |
|---|---|
| Mueve simultáneamente varios ejes (seis o más) | Normalmente mueve uno o dos ejes a la vez |
| Movimientos independientes de cada eje; trayectorias complejas | Movimientos limitados y trayectorias simples |
| Campo de acción **fuera del volumen de la propia máquina**; espacio de trabajo difícil de reconocer | Campo de acción dentro del volumen de la máquina |
| Campo de acción solapado con otras máquinas | Normalmente sin solapamiento |

## 2. Tipos de accidentes y riesgos

Barrientos y la clase 2 coinciden en tres tipos principales [Barrientos, 9.3.1, p. 272; Clase 2]:

| Riesgo | Descripción |
|---|---|
| **Colisión** | El robot en movimiento, o la herramienta que lleva, golpea al operador. |
| **Aplastamiento** | El operador queda atrapado entre el robot y un objeto fijo (un transportador, una mesa, un cerramiento). |
| **Proyección** | El robot despide una pieza o material (metal fundido, piezas mal sujetas). |

A estos se suman los **riesgos propios de la aplicación**: choque eléctrico, **arco de soldadura**,
quemaduras, sustancias tóxicas y ruido [Clase 2]. La gran velocidad y la elevada energía estática y
dinámica del robot agravan todos estos riesgos [Barrientos, 9.3.1, p. 272].

## 3. Causas de los accidentes

Los accidentes con robots se deben normalmente a [Barrientos, 9.3.1, p. 272]:

- mal funcionamiento del sistema de control (software, hardware, potencia);
- **acceso indebido de personal a la zona de trabajo** del robot;
- errores humanos en mantenimiento, programación o ajuste;
- rotura de partes mecánicas por corrosión o fatiga;
- liberación de energía almacenada (eléctrica, hidráulica, potencial);
- sobrecarga del robot;
- medio ambiente o herramienta peligrosa (láser, chorro de agua, oxicorte).

**Dato clave:** según el Instituto de Investigaciones de Seguridad en el Trabajo de Tokio, **el 90 %
de los accidentes en líneas robotizadas ocurre durante el mantenimiento, ajuste o programación**, y
solo el 10 % durante el funcionamiento normal. Por eso es tan importante **impedir el acceso de
operarios al campo de acción del robot mientras está en funcionamiento** [Barrientos, 9.3.2,
pp. 272–273].

## 4. Responsabilidades

La seguridad de un sistema robotizado tiene dos partes [Barrientos, 9.3.2, p. 273]:

- **La seguridad intrínseca del robot**, que es responsabilidad del **fabricante**.
- **El diseño e implantación de la célula**, y su uso, programación y mantenimiento, que son
  responsabilidad **del usuario o integrador**.

La estrategia de trabajo para definir las medidas de seguridad comprende [Barrientos, 9.3.2,
p. 273]:

1. Determinar los **límites del sistema**: uso previsto, espacio y tiempos de trabajo.
2. **Identificar todos los peligros** en todas las fases de trabajo, incluidos el trabajo conjunto con
   el operador y el mal uso.
3. **Definir el riesgo** de que ocurra cada accidente en función del daño que pueda producir.
4. **Comprobar** que las medidas de seguridad son adecuadas.

## 5. Niveles de protección

La clase 2 organiza la protección en tres niveles [Clase 2]:

| Nivel | Método | Tecnología | Interacción con el operador |
|---|---|---|---|
| **1. Protección mecánica** | Aislamiento físico total de la celda | Barreras, cercas metálicas, **puertas enclavadas** (*interlocks*) | Nula durante la operación |
| **2. Protección optoelectrónica** | Detección de presencia sin contacto | Cortinas láser, escáneres, alfombras sensibles | El robot se detiene si se vulnera el perímetro virtual |
| **3. Robótica colaborativa** | Espacio compartido entre humano y robot | Sensores de fuerza y par, piel táctil, monitoreo de velocidad | Directa, segura e intencional (ISO 10218-1/2) |

### 5.1 Nivel 1: protección mecánica

- **Barreras y cercas:** impiden físicamente el ingreso. El color advierte al personal no informado.
- **Protección contra proyecciones:** contienen objetos o piezas que puedan salir despedidos.
- **Prevención de tráfico:** protegen la celda contra el impacto de vehículos de la planta.
- **Puertas rápidas con interlock:** el operador solo ingresa tras solicitar acceso desde un panel
  exterior. Si la puerta se abre a la fuerza, **el interlock corta inmediatamente la energía de los
  actuadores del robot**. Es la aplicación ideal para **procesos con proyección de partículas, como
  la soldadura**, o donde el robot se mueve a máxima velocidad [Clase 2].

### 5.2 Nivel 2: protección optoelectrónica

Reemplaza los muros por percepción cuando hace falta acceso frecuente [Clase 2]:

| Dispositivo | Principio | Aplicación ideal |
|---|---|---|
| **Cortina láser** | Haces infrarrojos entre emisor y receptor. Si un cuerpo interrumpe un haz, se envía una parada. | Estaciones de carga y descarga manual donde el operador introduce las manos repetidamente. |
| **Escáner láser (LiDAR 2D)** | Mide distancias por tiempo de vuelo. Permite zonas de advertencia (reduce la velocidad) y de paro. | Áreas irregulares o puntos ciegos. |
| **Alfombra sensible** | Placas conductoras que se tocan al ser pisadas. | Ambientes con polvo, humo o virutas donde los sensores ópticos fallan. |
| **Finales de carrera y *bumpers*** | Interruptores que cortan la energía si se excede un límite o hay contacto. | Prevención de sobrecarrera. |

### 5.3 Nivel 3: robótica colaborativa

El robot comparte el espacio con la persona y limita su energía para no lastimarla, con sensores de
fuerza y par en las articulaciones [Clase 2]. **No es compatible con un arco de soldadura abierto**,
por la radiación y las proyecciones.

## 6. Medidas de seguridad

Barrientos agrupa las medidas según la fase [Barrientos, 9.3.2, pp. 273–276].

### 6.1 En el diseño del robot (responsabilidad del fabricante)

- **Supervisión del sistema de control**, incluso de sí mismo (*watch-dog*).
- **Paradas de emergencia** que desenergicen completamente al robot.
- **Velocidad máxima limitada** cuando hay una persona cerca (programación): como referencia, menor a
  **0,3 m/s**.
- **Detectores de sobreesfuerzo** en los accionamientos (colisión o atrapamiento).
- **Pulsador de hombre muerto** en la consola de programación.
- **Códigos de acceso** al control y a la modificación del programa.
- **Frenos mecánicos** adicionales y **autodiagnóstico** al arrancar.

### 6.2 En el diseño de la célula (responsabilidad del integrador)

- **Barreras de acceso** alrededor de la célula, con **parada inmediata** al entrar en la zona de
  trabajo (Figura 9.9).
- **Dispositivos de intercambio de piezas:** si el operador tiene que poner o retirar piezas en el
  área de trabajo del robot, se usan dispositivos que permitan hacerlo **a distancia**, por ejemplo
  **mesas giratorias**. La Figura 9.10 es un operario cargando una **célula de soldadura** con mesa
  giratoria.
- **Movimientos condicionados:** si el operador tiene que entrar en algún momento, el robot se
  programa para no moverse en esos instantes.
- **Zonas de reparación** dentro del campo de acción pero fuera de la zona de trabajo, donde se
  asegura que el robot no se mueva automáticamente.
- **Instalación auxiliar adecuada:** sistema eléctrico con protecciones y aislamientos, neumática e
  hidráulica correctas.

### 6.3 En la instalación y explotación

- **No entrar en la zona de trabajo** durante la programación. El robot se mueve a velocidad lenta, y
  hay que salir antes de pasar a modo automático. Conviene programar de a dos: uno observa y está
  listo para accionar la emergencia.
- **Señalización adecuada:** señales luminosas y acústicas del estado del robot; aviso con sirena o
  luz **antes de arrancar** el ciclo tras una parada.
- **Prueba progresiva del programa:** primero a velocidad lenta y paso a paso, después continuo y
  aumentando la velocidad.
- **Formación** del personal.

### 6.4 Protecciones incorporadas en celdas automatizadas

Groover exige que una celda que funciona sin operador tenga protecciones contra condiciones
(1) peligrosas para las personas, (2) destructivas para el equipo y (3) destructivas para la pieza,
con **detección y recuperación de errores** [Groover, 14.2.1, p. 369].

## 7. El PLC de seguridad y la habilitación del robot

Ningún sensor funciona aislado: todos reportan a un **PLC de seguridad** que asegura la
sincronización y la redundancia [Clase 2]. La secuencia de habilitación (*handshake*) es:

| Paso | Quién | Qué hace |
|---|---|---|
| 1. Petición | Robot → PLC | *Request to Move*: el robot pide permiso para iniciar un movimiento. |
| 2. Verificación | PLC | Revisa todos los periféricos: puertas cerradas, cortinas libres. |
| 3. Habilitación | PLC → Robot | *Safety Clear / Enable Power*: si el entorno es seguro, envía la señal de habilitación. |
| 4. Ejecución | Robot | Energiza los actuadores y ejecuta la trayectoria. |
| 5. Interrupción | PLC → Robot | *Emergency Stop*: si un sensor cambia de estado durante el movimiento, el PLC **retira la habilitación inmediatamente**. |

En el programa del robot, esto corresponde a las esperas por señales (WAIT) antes del movimiento y a
la **interrupción con monitoreo continuo** (REACT con SAFESTOP) durante el movimiento
[Groover, 8.5, p. 232] (ver [06](06_estructura_de_programas_y_senales.md)).

**Arquitectura de una celda totalmente segura** [Clase 2]:

1. Nivel 1: cerramiento físico y puerta rápida.
2. Nivel 2: cortinas láser en la ventana de carga.
3. Nivel 2: escáner monitoreando los puntos ciegos.
4. Nivel 3: brazo colaborativo con sensores de par (cuando aplica).
5. Control: PLC procesando las señales en milisegundos.

> *La seguridad no es un obstáculo para la producción; es la infraestructura que hace posible la
> automatización confiable.* [Clase 2]

## 8. Riesgos propios de la soldadura al arco

| Riesgo | Origen | Medida típica |
|---|---|---|
| Radiación ultravioleta | Arco eléctrico | Paneles o cortinas opacas al arco en el cerramiento |
| Proyecciones y chispas | Metal fundido | Cerramiento cerrado; puerta enclavada |
| Humos | Fusión del metal | Extracción de humos |
| Choque eléctrico | Alta corriente de soldadura | Instalación eléctrica con protecciones |
| Quemaduras | Pieza y antorcha calientes | Descarga a distancia; tiempo de enfriamiento |

Fuentes de los riesgos: [Groover, 8.4.2, p. 220; Barrientos, 10.2.2, p. 296; Clase 2].

## 9. Normativa

### 9.1 Normas citadas en la bibliografía

Barrientos cita las normas vigentes en su época [Barrientos, 9.3.3, pp. 276–277]:

- **ISO 10218:1992**: análisis de seguridad, definición de riesgos, identificación de peligros y
  diseño de sistemas robotizados.
- **ANSI/RIA R15.06-1992** (Estados Unidos): incluye la estimación del riesgo según la experiencia
  del operador y la frecuencia con que está en la zona de peligro.
- **EN 775 / UNE-EN 775** (Europa, España): adaptación de la ISO 10218, combinada con la
  **EN 292** (*Safety of machinery – Basic concepts, general principles for design*).

Estas versiones están **reemplazadas**.

### 9.2 Normas vigentes aplicables

| Norma | Tema | Aplicación a una celda de soldadura |
|---|---|---|
| ISO 10218-1 | Seguridad del robot industrial | La cumple el fabricante del robot |
| **ISO 10218-2** | **Seguridad de sistemas y células robotizadas**: integración, cerramiento, modos de operación | **Norma principal para el diseño de la celda** (la cita la clase 2) |
| ISO 12100 | Principios generales de diseño; evaluación y reducción del riesgo (reemplazó a la EN 292) | Método para identificar y evaluar los riesgos |
| ISO 13849-1 | Partes de los sistemas de mando relativas a la seguridad (nivel de desempeño PL) | Circuito de puerta y parada de emergencia |
| ISO 13850 | Función de parada de emergencia | Pulsador de emergencia |
| ISO 14119 | Dispositivos de enclavamiento asociados a resguardos | Puerta de la celda |
| ISO 14120 | Resguardos fijos y móviles | Cerramiento |
| ISO 13857 | Distancias de seguridad para impedir alcanzar zonas peligrosas | Altura y abertura del cerramiento |
| ISO 13855 | Posicionamiento de los dispositivos de protección según la velocidad de aproximación | Ubicación de una cortina láser, si se usa |
| IEC 60204-1 | Equipo eléctrico de las máquinas | Tablero y circuito de mando |
| ISO 25980 | Cortinas, tiras y pantallas transparentes para procesos de soldadura al arco | Protección contra el arco en el cerramiento |
| Ley 19.587 y Decreto 351/79 | Higiene y seguridad en el trabajo (Argentina) | Marco legal local |

> **Alcance de las citas normativas:** el grupo no tuvo acceso al texto de estas normas. Se incluyen
> **como referencia**, con su título y su campo de aplicación general, para indicar el marco
> normativo de la celda. No se citan requisitos concretos (distancias, velocidades, niveles de
> desempeño). La única base normativa consultada es la de la bibliografía (sección 9.1) y la
> mención de la ISO 10218-1/2 en la clase 2.
>
> Por prioridad para el diseño de la celda: **ISO 10218-2** (principal), **ISO 10218-1** e
> **ISO 12100**. Las demás se nombran como normas complementarias.

## 10. Representación en la simulación

RoboDK simula cinemática y lógica, no sensores certificados. Los elementos de seguridad se
representan como:

- **geometría** (cerramiento, puerta, paneles), para mostrar la disposición y verificar colisiones;
- **señales** (puerta cerrada, emergencia, presencia), que los programas consultan;
- **lógica de habilitación**, en los programas o en un script Python que simule los sensores (ver
  [06](06_estructura_de_programas_y_senales.md)).

En el informe hay que aclarar ese alcance: son recursos de simulación académica, no dispositivos
certificados.

## 11. Qué hay que definir en nuestra celda

- ¿Qué peligros tiene nuestra celda, en cada fase (operación, carga, programación, mantenimiento)?
- ¿Qué nivel de protección usamos y por qué?
- ¿Cómo carga y descarga el operador la pieza sin entrar al área del robot?
- ¿Qué condiciones habilitan el ciclo (puerta, emergencia, pieza presente)?
- ¿Qué pasa si una condición cambia durante el movimiento? ¿Cómo se recupera la celda?
- ¿Cómo se protege del arco a quien está afuera de la celda?
- ¿Qué señalización tiene la celda antes de arrancar y durante el ciclo?
- ¿Qué parte de esto se modela en RoboDK y qué parte se describe solo en el informe?

## 12. Referencias

- **[Clase 2]** Luque, J. *Islas robotizadas y seguridad industrial*. UTN FRC, 2026.
- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, Madrid, 1.ª ed. Sección 9.3, pp. 271–277; sección 10.2.2.
- **[Groover]** Groover, M. P. *Automation, Production Systems, and Computer-Integrated
  Manufacturing*, 4.ª ed. Pearson, 2015. Secciones 8.4.2, 8.5 y 14.2.1.
- **[Lineamientos]** Cátedra de Robótica, UTN FRC. *Trabajo de fin de curso*, 2026.
**Normas (citadas como referencia, no consultadas):**

- ISO 10218-1. *Robótica – Requisitos de seguridad – Parte 1: Robots industriales*. ISO, Ginebra.
- ISO 10218-2. *Robótica – Requisitos de seguridad – Parte 2: Sistemas robotizados industriales,
  aplicaciones y células*. ISO, Ginebra.
- ISO 12100. *Seguridad de las máquinas – Principios generales para el diseño – Evaluación del riesgo
  y reducción del riesgo*. ISO, Ginebra.
- ISO 13849-1. *Seguridad de las máquinas – Partes de los sistemas de mando relativas a la
  seguridad – Parte 1: Principios generales para el diseño*. ISO, Ginebra.
- ISO 13850. *Seguridad de las máquinas – Función de parada de emergencia – Principios para el
  diseño*. ISO, Ginebra.
- ISO 13855. *Seguridad de las máquinas – Posicionamiento de los equipos de protección en función de
  la velocidad de aproximación de partes del cuerpo humano*. ISO, Ginebra.
- ISO 13857. *Seguridad de las máquinas – Distancias de seguridad para impedir que se alcancen zonas
  peligrosas con los miembros superiores e inferiores*. ISO, Ginebra.
- ISO 14119. *Seguridad de las máquinas – Dispositivos de enclavamiento asociados a resguardos –
  Principios para el diseño y la selección*. ISO, Ginebra.
- ISO 14120. *Seguridad de las máquinas – Resguardos – Requisitos generales para el diseño y
  construcción de resguardos fijos y móviles*. ISO, Ginebra.
- ISO 25980. *Salud y seguridad en soldadura y procesos afines – Cortinas, tiras y pantallas
  transparentes para procesos de soldadura al arco*. ISO, Ginebra.
- IEC 60204-1. *Seguridad de las máquinas – Equipo eléctrico de las máquinas – Parte 1: Requisitos
  generales*. IEC, Ginebra.
- Ley N.º 19.587 de Higiene y Seguridad en el Trabajo y Decreto Reglamentario 351/79. República
  Argentina.
