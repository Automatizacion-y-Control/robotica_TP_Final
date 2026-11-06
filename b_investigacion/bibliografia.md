<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL · Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control<br>
**Cátedra: Robótica Industrial**

# Bibliografía: celdas robotizadas y normativa

**Grupo 4**<br>
Casali Emiliano · Ferrero Facundo · Vera Gonzalo<br>
**Docentes:** Ing. Julián Luque · Lic. Sergio Perassi<br>
Comisión 2LA1 · Año 2026

</div>

## Índice

- [Prólogo](#prólogo)
- [Material de la cátedra](#material-catedra)
- [Barrientos](#barrientos)
- [Groover](#groover)
- [Otros libros](#otros-libros)
- [Normas aplicables](#normas-aplicables)
- [Fuentes complementarias de interfaz y usuarios](#fuentes-interfaz)

## Prólogo

Se reúne la bibliografía que fundamenta la investigación, indicando apartados y páginas cuando
corresponden. Las fuentes complementarias de fabricantes y software permiten desarrollar el panel
sin atribuir a los libros decisiones particulares del proyecto. Las normas ISO se incluyen solo
como referencia: no se tuvo acceso a su texto.

Los PDF de la cátedra y los libros están en `biblio/`, que no se versiona (material con derechos
de autor).

<a id="material-catedra"></a>

## 1. Material de la cátedra (en `biblio/`)

| Archivo | Qué aporta para la celda |
|---|---|
| Clase 1: Robótica Industrial (Perassi) | Morfología del brazo y sistemas de coordenadas anidados (World, Base, Tool, WorkObject). Sirve para justificar los frames y el TCP. |
| Clase 2: Islas Robotizadas y Seguridad Industrial (Luque) | Riesgos (colisión, aplastamiento, arco de soldadura), los 3 niveles de protección, el PLC de seguridad y el *handshake* PLC–robot. Es la base de la parte de seguridad. Cita "Cap. 11.1" sin decir de qué libro, y las ISO 10218-1/2. |
| Craig, *Robótica*, 3.ª ed. | Cinemática, trayectorias y programación. **No trata seguridad ni normativa.** Su capítulo 11.1 es la introducción al control de fuerza, así que la cita de la clase 2 no viene de este libro. |

### Resumen de la clase 2 aplicado a la celda de soldadura

- **Nivel 1, protección mecánica:** cerramiento con puerta enclavada (*interlock*). Si la puerta se
  abre, se corta la energía del robot. La clase lo recomienda para procesos con proyección de
  partículas, **como la soldadura**. La estación ya tiene cerramiento y puerta.
- **Nivel 2, optoelectrónico:** cortina láser en la ventana de carga si el operador carga la pieza a
  mano, o escáner láser para los puntos ciegos.
- **Nivel 3, colaborativo:** no aplica. Con arco de soldadura no se comparte el espacio con el
  operador.
- **Integración:** todos los sensores reportan a un PLC de seguridad. El robot pide permiso para
  moverse (*Request to Move*), el PLC verifica puertas y cortinas y devuelve *Enable*. Si algo cambia
  durante el movimiento, retira la habilitación según la función de protección correspondiente.
  El panel Python no sustituye ese circuito; en RoboDK las señales deben declarar el alcance
  de la reacción realmente implementada.

<a id="barrientos"></a>

## 2. Barrientos, *Fundamentos de Robótica* (en `biblio/`)

**Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*. McGraw-Hill,
Madrid.** El PDF es la 1.ª edición (10 capítulos, 316 páginas). Lo que nos sirve está en el
**capítulo 9, Criterios de implantación de un robot industrial** (pp. 255–290), y en la **sección
10.2.2, Soldadura** (pp. 294–297).

### 9.1 Diseño y control de una célula robotizada (pp. 256–261)

- **Proceso de diseño:** elegir el robot, definir los periféricos pasivos (mesas, alimentadores,
  utillajes) y activos (manipuladores, máquinas CN), y armar el *lay-out*. Es un proceso iterativo,
  y **los simuladores permiten elegir el robot, detectar colisiones y verificar el alcance**
  (p. 257). Esto justifica el uso de RoboDK.
- **Disposición del robot (9.1.1):** hay cuatro casos: en el centro, en línea, móvil sobre rail y
  suspendido. **La disposición en el centro es la típica de la soldadura al arco**, cuando el robot
  tiene que alcanzar puntos fijos dentro de su área de trabajo (p. 258). Es nuestro caso.
- **Sistema de control de la célula (9.1.2, p. 261):** control individual de cada equipo,
  sincronización entre ellos, detección y recuperación de situaciones anómalas, optimización,
  interfaz con el usuario, con otras células y con un control superior. Si la célula es simple,
  **el propio controlador del robot puede mandar los ejes externos** (el posicionador) con sus
  E/S. Si es más compleja, hace falta un elemento central (PLC u ordenador). Esto justifica tanto
  el posicionador como eje externo como el panel de supervisión.

### 9.2 Selección del robot (pp. 262–271)

La Tabla 9.1 lista qué evaluar: área de trabajo, grados de libertad, precisión y repetibilidad,
velocidad, carga, tipo de movimiento (punto a punto o trayectoria continua), programación,
accionamiento y comunicaciones. Sirve para justificar el ABB CRB 1300 en el informe.

### 9.3 Seguridad en instalaciones robotizadas (pp. 271–277)

- **Tipos de accidente (9.3.1):** colisión entre robot y persona, aplastamiento contra un elemento
  fijo y proyección de piezas o material. Coinciden con las categorías de la clase 2, así que es
  probable que "Cap. 11.1" sea una cita de la 2.ª edición de este libro.
- **Causas:** fallas del sistema de control, acceso indebido a la zona de trabajo, errores humanos
  en mantenimiento y programación, rotura mecánica, energía almacenada, sobrecarga y herramienta
  peligrosa.
- **Dato clave (p. 272):** según el Instituto de Investigaciones de Seguridad en el Trabajo de
  Tokio, **el 90 % de los accidentes ocurre en mantenimiento, ajuste y programación**, y solo el
  10 % en funcionamiento normal. De ahí la importancia de impedir el acceso mientras el robot
  trabaja.
- **Responsabilidades:** la seguridad intrínseca del robot es del fabricante. **El diseño, la
  implantación y el uso de la célula son responsabilidad del usuario**, es decir, nuestra.
- **Medidas en el diseño del robot:** supervisión del control (*watch-dog*), paradas de emergencia,
  **velocidad limitada a menos de 0,3 m/s con personas cerca** (programación), detectores de
  sobreesfuerzo, pulsador de hombre muerto en la consola, códigos de acceso, frenos y
  autodiagnóstico.
- **Medidas en el diseño de la célula (pp. 274–275):**
  - **barreras de acceso** con parada inmediata al entrar;
  - **dispositivos de intercambio de piezas**: si el operador carga y descarga piezas dentro del
    área del robot, conviene usar una **mesa giratoria** para hacerlo a distancia. La Figura 9.10
    es justamente **una célula de soldadura con mesa giratoria**;
  - movimientos condicionados mientras el operador está dentro;
  - zonas de reparación fuera de la zona de trabajo;
  - instalación eléctrica y neumática adecuada.
- **Medidas en la instalación y explotación:** no entrar a la zona de trabajo (programar desde
  afuera y a velocidad lenta), señalización luminosa y acústica antes de arrancar, **prueba
  progresiva del programa (primero lento y paso a paso)** y formación del personal.

### 9.3.3 Normativa legal (pp. 276–277)

El libro cita las normas vigentes en esa época:

- **ISO 10218:1992**: análisis de seguridad, riesgos y diseño de sistemas robotizados.
- **ANSI/RIA R15.06-1992** (EE. UU.): agrega la estimación del riesgo según la experiencia del
  operador y la frecuencia de exposición.
- **EN 775 / UNE-EN 775** (Europa y España, 1992/1996): adaptación de la ISO 10218, combinada con
  la EN 292 (seguridad de máquinas).

Estas versiones ya están reemplazadas. Las vigentes son la **ISO 10218-1/2** (las que cita la clase
2) y la **ISO 12100**, que reemplazó a la EN 292. Ver la sección 5 de este documento.

### 10.2.2 Soldadura (pp. 294–297)

- **Soldadura al arco:** la calidad depende de la distancia entre pieza y electrodo, la velocidad
  de avance, la tensión y corriente y el ángulo de ataque. El ambiente es agresivo (radiación UV,
  humo, chispas), lo que justifica reemplazar al operario por un robot.
- **Requisitos del robot:** trayectoria continua, poca carga (~10 kg), alcance de ~2 m, 5 o 6
  grados de libertad, y **ejes externos que mueven el utillaje que sostiene la pieza** (es decir, un
  posicionador, como el de nuestra celda).
- Algunos robots usan sensores láser para encontrar el comienzo del cordón y seguirlo, con
  precisiones de 0,5 mm a 40 mm/s.

<a id="groover"></a>

## 3. Groover, *Automation, Production Systems, and CIM* (en `biblio/`)

**Groover, M. P. *Automation, Production Systems, and Computer-Integrated Manufacturing*, 4.ª ed.
Pearson, 2015.** Está en inglés. Las páginas citadas son las del libro; en el PDF hay que sumarles 18.
Tiene un enfoque de ingeniería de producción y **no trata la normativa de seguridad**. Aporta la
justificación del proceso, la composición de la celda y el cálculo del ciclo.

### 8.4.2 Arc Welding (pp. 219–221)

- **Por qué robotizar:** el soldador trabaja con radiación UV, alta corriente y altas temperaturas, y
  la tarea exige mucha coordinación entre la mano y la vista. Por la fatiga, **el arco está
  encendido solo un 20–30 % del turno** (*arc-on time*), y hace falta un ayudante (*fitter*) que
  prepare las piezas.
- **Composición de la celda:** robot + equipo de soldadura (fuente, controlador, antorcha y
  alimentador de alambre) + **un utillaje motorizado de 1 o 2 ejes que presenta distintas partes de
  la pieza al robot. A ese utillaje se lo llama posicionador** (*positioner*). Describe exactamente
  nuestra celda y sirve para justificar el MTD 250.
- **Dos utillajes para más productividad:** mientras el robot suelda en uno, el operador descarga y
  carga el otro, detrás de una barrera de seguridad (Figura 8.12). Es la misma idea que la mesa
  giratoria de Barrientos.
- **Robot:** tiene que tener **control de trayectoria continua**. Lo más común es un brazo articulado
  de 6 ejes, a veces con el brazo hueco para llevar los cables de la antorcha por dentro.
- **Programación:** la trayectoria del cordón se puede generar a partir del modelo CAD, que es lo que
  hacemos en RoboDK.

### 8.4 Características de las aplicaciones robotizadas (p. 224)

Groover da seis condiciones que favorecen el uso de un robot. Nuestra celda cumple varias:

1. **Trabajo peligroso para personas:** la soldadura al arco es uno de los ejemplos que da.
2. **Ciclo repetitivo:** son los mismos cordones en cada paquete de estator.
3. Manipulación difícil para personas (no aplica: la pieza es liviana).
4. **Operación en varios turnos:** típica de una línea de electrodomésticos.
5. **Pocos cambios de preparación:** son tiradas largas de un mismo motor.
6. **Pieza en posición y orientación conocidas:** el posicionador la fija en el mismo lugar en cada
   ciclo.

### 8.4 Tiempo de ciclo y producción (pp. 224–226)

- **Tiempo de ciclo:** Tc = To + Th + Tt, donde To es el tiempo de proceso (soldadura), Th el de
  manipulación de la pieza y Tt el de manipulación de la herramienta. Cuando el robot hace el
  proceso, como en la soldadura, es la máquina principal, y la carga de la pieza queda a cargo de
  equipos de apoyo o de un operario.
- **Tasa de producción:** Rc = 60 / Tc [piezas/h] en tiradas largas.
- **Costos:** TC = Cf + Cv·Q, con un análisis de punto de equilibrio contra la soldadura manual.

Con esto el informe puede presentar el tiempo de ciclo de RoboDK (32,4 s en la versión actual) como
una tasa de producción y separar el tiempo de soldadura del de indexación.

### 8.2 y 8.5 Control y programación (pp. 214–232)

- **Interpolación:** el controlador calcula la trayectoria entre puntos con interpolación lineal y
  circular. Un robot articulado necesita interpolar para moverse en línea recta (p. 228). Esto
  respalda la elección entre MoveJ, MoveL y MoveC.
- **Interlocks:** sirven para coordinar el robot con el resto de los equipos de la celda (p. 215).
  Hay dos comandos básicos: **WAIT** (espera una entrada, por ejemplo "posicionador en posición") y
  **SIGNAL** (activa una salida, por ejemplo el arco, que en la estación es DO5) (pp. 231–232).
- **Monitoreo de seguridad:** el comando **REACT** vigila una entrada todo el tiempo, por ejemplo un
  sensor de presencia de personas, y si cambia salta a una subrutina **SAFESTOP** que detiene el
  robot (p. 232). Es el mismo concepto que la parada por puerta abierta del panel.

### 14.2.1 Condiciones para que la celda funcione sin operador (pp. 369–370)

Una celda automatizada de una estación necesita:

- un ciclo programado que haga todos los pasos solo;
- almacenamiento de piezas y transferencia automática entre el almacén y la estación;
- atención periódica de un operario (cargar piezas, retirar terminadas);
- **protecciones incorporadas** contra condiciones (1) peligrosas para las personas,
  (2) destructivas para el equipo o (3) destructivas para la pieza, con **detección y recuperación
  de errores**.

Si la celda produce **piezas distintas**, además necesita identificar cada pieza, cargar el programa
que le corresponde y cambiar rápido de utillaje. Esto aplica si agregamos dos variantes de paquete
de estator.

<a id="otros-libros"></a>

## 4. Otros libros

1. **Barrientos et al., *Fundamentos de Robótica*, 2.ª ed. (McGraw-Hill, 2007).** Es la versión
   ampliada del que tenemos. Probablemente sea la que cita la clase 2 ("Cap. 11.1"), porque tiene
   más capítulos que la 1.ª edición.
2. **Sánchez Jiménez, J. L. *Fundamentos de robótica*. Ecoe Ediciones, Bogotá, 2021.** Tiene
   apartados de **seguridad en instalaciones robotizadas** y justificación económica. Es una
   alternativa más nueva si no se consigue el de Barrientos.

> Para confirmar de qué libro es la cita "Cap. 11.1" de la clase 2, conviene preguntarle al docente.

<a id="normas-aplicables"></a>

## 5. Normas aplicables

Las fuentes específicas para la interfaz se incorporan en §6 y se desarrollan en el concepto 09.

| Norma | Tema | Uso en la celda |
|---|---|---|
| ISO 10218-1 | Seguridad del robot industrial (el robot en sí) | Lo cumple el fabricante (ABB) |
| **ISO 10218-2** | **Seguridad de sistemas y celdas robotizadas** (integración, cerramiento, modos de operación) | **Norma principal para el diseño de la celda** |
| ISO 12100 | Evaluación y reducción de riesgos en máquinas | Método para identificar los riesgos de la celda |
| ISO 13849-1 | Partes de los sistemas de mando relativas a la seguridad (nivel de desempeño PL) | Diseño del circuito de seguridad (puerta, parada de emergencia) |
| ISO 13850 | Función de parada de emergencia | Pulsador de emergencia del panel |
| ISO 14119 | Dispositivos de enclavamiento (*interlocks*) | Puerta de la celda |
| ISO 14120 | Resguardos fijos y móviles | Cerramiento |
| ISO 13857 | Distancias de seguridad (alcance de extremidades) | Altura y malla del cerramiento |
| ISO 13855 | Posicionamiento de dispositivos de protección según la velocidad de aproximación | Ubicación de una cortina láser, si se usa |
| IEC 60204-1 | Equipo eléctrico de las máquinas | Tablero y circuito de mando |
| ISO 25980 | Cortinas y pantallas para soldadura (protección contra el arco) | Paneles opacos frente a la zona de arco |
| Ley 19.587 y Decreto 351/79 (Argentina) | Higiene y seguridad en el trabajo | Marco legal local |

<a id="fuentes-interfaz"></a>

## 6. Fuentes complementarias de interfaz y usuarios

Investigación desarrollada en [09 · Interfaz de operación, usuarios y permisos](conceptos/09_interfaz_de_operacion_usuarios_y_permisos.md).
Consulta: 2026-11-06. Fuentes HTML sin paginación; se identifican apartados en lugar de páginas.

| Fuente primaria | Apartados consultados | Aporte |
|---|---|---|
| [ABB, FlexPendant Developer Support: User Authorization System](https://developercenter.robotstudio.com/api/fpsdk/html/6460854b-d939-4bc1-b553-60420e6a227f.htm) | Overview; Accessing UAS from custom applications; Grants and Groups | Usuarios, grupos y permisos del controlador; comprobación por operación. |
| [Siemens, Unified Basic Panels V20, publicación 12/2024: User management](https://docs.tia.siemens.cloud/r/unified_basic_panels_enus_20/operating-the-control-panel/security/user-management) | Security / User management; Current user; Users | Roles, derechos de función y sesiones de la HMI. |
| [OWASP, Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) | Recommendations: mínimos privilegios, rechazo por defecto, comprobación por solicitud, registro y pruebas | Criterios de autorización del software. |
| [OWASP, Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) | Introduction; Methods for Enhancing Password Storage / Salting | Protección de credenciales; no constituye seguridad funcional. |

Las funciones particulares de esas plataformas no se atribuyen a RoboDK. La matriz de perfiles
producción/mantenimiento/administración es una propuesta del proyecto fundamentada en la investigación.
