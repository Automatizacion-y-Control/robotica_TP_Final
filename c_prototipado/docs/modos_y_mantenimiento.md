<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# Modos de operación y mantenimiento

*Base para la mejora 02 (v04) y para el panel de operador*

**Grupo 4**<br>
Casali Emiliano · Ferrero Facundo · Vera Gonzalo

**Docentes**<br>
Ing. Julián Luque · Lic. Sergio Perassi

Comisión 2LA1 · Año 2026

</div>

---

## Índice

- [Prólogo](#prólogo)
- [1. Conceptos: paradas, aislamiento y modos](#1-conceptos-paradas-aislamiento-y-modos)
- [2. Energías peligrosas de la celda](#2-energías-peligrosas-de-la-celda)
- [3. Zonas y accesos](#3-zonas-y-accesos)
- [4. Modos de la celda](#4-modos-de-la-celda)
- [5. Matriz de modos por equipo](#5-matriz-de-modos-por-equipo)
- [6. Paradas](#6-paradas)
- [7. Procedimiento de bloqueo y etiquetado (LOTO)](#7-procedimiento-de-bloqueo-y-etiquetado-loto)
- [8. Tareas de mantenimiento](#8-tareas-de-mantenimiento)
- [9. Problemas de la disposición actual (v03)](#9-problemas-de-la-disposición-actual-v03)
- [10. Requisitos para la v04 y para el panel](#10-requisitos-para-la-v04-y-para-el-panel)
- [11. Qué se representa en la simulación](#11-qué-se-representa-en-la-simulación)
- [12. Referencias](#12-referencias)

---

## Prólogo

La v03 se diseñó para que el ciclo de producción funcione. Este documento la mira desde el otro
lado: **cómo se opera y cómo se mantiene**. Es el paso previo a dos cosas:

- la **mejora 02 (v04)**, que ajusta la disposición para que el mantenimiento sea posible y seguro;
- el **panel de operador**, que tiene que reflejar los modos y las zonas definidos acá.

La razón para hacerlo primero es la misma que da la bibliografía: según Barrientos, **el 90 % de
los accidentes en líneas robotizadas ocurre durante el mantenimiento, el ajuste o la
programación**, y solo el 10 % en funcionamiento normal [Barrientos, 9.3.2, p. 272]. Una celda que
no prevé cómo se interviene empuja a intervenirla de manera insegura.

Las normas citadas (ISO 10218-1/2, ISO 13850, ISO 14119 y otras) se usan **como referencia**: el
grupo no tuvo acceso a su texto (ver [07](../../b_investigacion/conceptos/07_seguridad_y_normativa.md)).

---

## 1. Conceptos: paradas, aislamiento y modos

Son tres cosas distintas, y en el diseño no deben confundirse.

| | Parada de protección | Parada de emergencia | Bloqueo y etiquetado (LOTO) |
|---|---|---|---|
| **Qué es** | Función de seguridad automática | Función de seguridad manual | **Procedimiento** de trabajo |
| **Cuándo actúa** | Se abre una puerta o se interrumpe una cortina | Una persona ve un peligro | Antes de un mantenimiento planificado |
| **Quién la acciona** | El dispositivo de protección | Cualquier persona | El técnico que va a intervenir |
| **Qué hace** | Detiene los movimientos peligrosos | Detiene los movimientos peligrosos lo antes posible | Aísla **todas** las energías peligrosas del equipo, las bloquea con candado y tarjeta, disipa las residuales y verifica energía cero |
| **Cómo se vuelve** | Rearme cuando desaparece la condición | Desenclavar el pulsador y rearmar | Retiro del candado por quien lo puso, tras cerrar la intervención |
| **¿Habilita trabajar adentro?** | No | **No**: el equipo detenido sigue teniendo energía | **Sí**: es la condición para intervenir |

**La parada de emergencia no es un medio de aislamiento.** Responde a una exposición imprevista a
energías peligrosas que pone en riesgo a las personas o a la instalación. El LOTO, en cambio, es
el procedimiento que se sigue **para** hacer un mantenimiento seguro, y el bloqueo de las energías
es una de sus etapas.

Los **modos** (§4) definen qué puede hacer cada equipo y quién puede estar dentro de la celda. Las
**paradas** (§6) actúan en cualquier modo. El **LOTO** (§7) se aplica solo en el modo de
mantenimiento.

## 2. Energías peligrosas de la celda

El LOTO tiene que cubrir **todas** las energías, no solo la eléctrica.

| Energía | Dónde está | Cómo se aísla | Energía residual a disipar o controlar |
|---|---|---|---|
| **Eléctrica** de los robots | Controladores del IRB 1200 y del CRB 1300 | Seccionador de cada controlador, con candado | Condensadores del controlador: esperar el tiempo de descarga indicado por el fabricante |
| **Eléctrica** de la cinta | Motorreductor y su tablero | Seccionador de la cinta, con candado | — |
| **Eléctrica** de la fuente TIG | Fuente de soldadura y su generador de alta frecuencia para el cebado | Seccionador de la fuente, con candado | Condensadores de la fuente |
| **Potencial (gravedad)** | Brazos de los robots | Los frenos retienen los ejes sin energía | Un eje puede caer si se desmonta su motor o su freno: hay que apoyar o sujetar el brazo **antes** |
| **Mecánica almacenada** | Banda de la cinta tensada | — | Destensar la banda antes de tocar rodillos o tensores |
| **Gas a presión** | Cilindro y manguera de argón | Válvula del cilindro, cerrada y bloqueada | Purgar la manguera |
| **Hidráulica** (refrigerante) | Circuito de refrigeración de la antorcha, si tiene | Bomba sin energía, válvulas cerradas | Despresurizar el circuito |
| **Térmica** | Antorcha, electrodo y pieza recién soldada | — | Esperar el enfriamiento |
| **Radiación** | Arco de soldadura | Se elimina al aislar la fuente TIG | — |

La pinza Robotiq 2F-85 es **eléctrica**: no hay energía neumática en la celda.

## 3. Zonas y accesos

Se propone dividir la celda en **dos zonas**, para poder intervenir la cinta sin entrar a la zona de
los robots:

| Zona | Contiene | Acceso | Protección |
|---|---|---|---|
| **Z1 · Cinta** | Cinta, túneles de entrada y salida, sensor de pieza | Por fuera del cerramiento de robots, a lo largo de la cinta | Cortinas de luz en los túneles; resguardos del accionamiento de la cinta |
| **Z2 · Robots** | Manipulador, soldador, zona de soldadura, estación de servicio | Puerta enclavada | Cerramiento, puerta con enclavamiento, cortinas en los túneles |

Las dos zonas comparten la cinta: la toma y el depósito están **dentro** de Z2. Por eso, intervenir
Z1 exige que Z2 esté detenida en un estado seguro, y viceversa para las tareas que tocan la cinta
desde adentro.

## 4. Modos de la celda

El operador elige el modo con un **selector de llave**: la llave la tiene quien está habilitado para
ese modo, y no se puede pasar a automático con alguien adentro.

| Modo | Qué ocurre | Personas dentro de Z2 | Velocidad de los robots |
|---|---|---|---|
| **Automático** | Ciclo continuo de producción | Nadie | Programada |
| **Parada de ciclo** | Termina la pieza en curso y deja todo en reposo, en un estado conocido | Nadie | Programada, hasta el reposo |
| **Manual / programación** | Se mueve **un equipo por vez**, con la consola y el pulsador de hombre muerto; los demás quedan detenidos | El operador con la consola | **Reducida** |
| **Servicio de antorcha** | El soldador va a la posición de servicio; el resto queda detenido; se habilita la puerta | El operador, en la zona de servicio | Robots detenidos |
| **Mantenimiento** | El equipo a intervenir está aislado con LOTO (§7) | El técnico | Equipo sin energía |
| **Arranque / vaciado** | Lleva todo al origen, saca las piezas a medio procesar y repone el lote | Según la tarea | Reducida o programada, según la tarea |

**Transiciones permitidas** (todas pasan por un estado seguro):

```text
              ┌──────────── Parada de ciclo ◄──────────┐
              ▼                                         │
  Arranque ──► Automático ─────────────────────────────┘
     ▲            │
     │            ▼ (parada de ciclo terminada, robots en reposo)
     │       Seleccionar modo con llave
     │      ┌──────────┬─────────────────┬──────────────┐
     │      ▼          ▼                 ▼              │
     │   Manual    Servicio de       Mantenimiento      │
     │             antorcha          (con LOTO)         │
     │      │          │                 │              │
     └──────┴──────────┴─────────────────┘ (puerta cerrada, nadie adentro, rearme)
```

**La parada de emergencia y las paradas de protección pueden ocurrir en cualquier modo** y no son
un modo en sí: ver §6.

## 5. Matriz de modos por equipo

| Equipo | Automático | Parada de ciclo | Manual | Servicio de antorcha | Mantenimiento |
|---|---|---|---|---|---|
| **IRB 1200** (manipulador) | Ciclo | Termina y va a reposo | Movimiento con consola, velocidad reducida | Detenido | Aislado si es el equipo intervenido |
| **CRB 1300** (soldador) | Ciclo | Termina y va a reposo | Movimiento con consola, velocidad reducida | Va a la posición de servicio y se detiene | Aislado si es el equipo intervenido |
| **Pinza** | Ciclo | Abierta | Abrir y cerrar desde la consola | Detenida | Aislada con el IRB |
| **Cinta** | Avance por ciclo | Detenida | Avance manual por pulsadores locales, a baja velocidad | Detenida | Aislada si es el equipo intervenido |
| **Fuente TIG** | Arco según el programa | Arco apagado | **Arco inhibido** | **Aislada** (cambio de tungsteno) | Aislada |
| **Torre de servicio** | Verificación de TCP por lote | — | Prueba del verificador | Cambio de tungsteno y verificación | Calibración del verificador |

En **manual**, el arco de soldadura queda **inhibido** aunque el programa lo pida: se programa en
seco y se suelda solo en automático, con la celda cerrada.

## 6. Paradas

| Parada | La dispara | Detiene | Cómo se rearma |
|---|---|---|---|
| **Emergencia** | Pulsadores en el panel, junto a la puerta, en la entrada y en la salida de la cinta, y en cada consola | Robots, cinta y fuente TIG, lo antes posible | Desenclavar el pulsador, verificar la causa y rearmar desde el panel |
| **Protección, Z2** | Apertura de la puerta o interrupción de una cortina en automático | Robots, cinta y arco | Cerrar la puerta o despejar la cortina y rearmar |
| **Protección, Z1** | Resguardo del accionamiento de la cinta abierto | Cinta | Cerrar el resguardo y rearmar |
| **Fin de ciclo** (no es de seguridad) | Pedido del operador | Lo que corresponda, al terminar la pieza | Arranque |

Ninguna parada habilita a intervenir un equipo: para eso está el LOTO.

## 7. Procedimiento de bloqueo y etiquetado (LOTO)

Procedimiento general, a seguir antes de cualquier mantenimiento:

1. **Preparar:** identificar el equipo y **todas** sus energías (§2), y avisar al personal afectado.
2. **Detener** el equipo en forma normal, con una parada de ciclo y los robots en su posición de
   mantenimiento (§8).
3. **Aislar:** abrir los seccionadores y cerrar las válvulas de cada energía.
4. **Bloquear y etiquetar:** cada persona que interviene pone **su propio candado** y su tarjeta en
   cada punto de aislamiento.
5. **Disipar las energías residuales:** descargar condensadores, destensar la banda, purgar el gas,
   sujetar los brazos que podrían caer, esperar el enfriamiento.
6. **Verificar energía cero:** intentar arrancar el equipo y medir la ausencia de tensión. Recién
   entonces se interviene.
7. **Intervenir.**
8. **Restituir:** retirar herramientas, reponer resguardos, verificar que no queden personas
   adentro. Cada persona retira **su** candado. Rearmar y probar en manual antes de pasar a
   automático.

## 8. Tareas de mantenimiento

| Tarea | Zona | Energías a aislar | Qué necesita de la disposición |
|---|---|---|---|
| **Cambio de la banda de la cinta** | Z1 | Eléctrica de la cinta; tensión de la banda | La banda sin fin sale **por un costado**: un lateral libre de obstáculos en todo el largo, o paneles desmontables |
| **Cambio de rodillos o del motorreductor** | Z1 | Eléctrica de la cinta; tensión de la banda | Acceso a los **dos extremos**, con el accionamiento fuera de la zona de robots |
| **Cambio de un motor de un robot** | Z2 | Eléctrica del robot; **gravedad del eje afectado** | Espacio libre alrededor del robot para una persona con herramientas; camino para entrar y sacar componentes pesados; posición de mantenimiento con el eje afectado apoyado |
| **Cambio de baterías del encoder, lubricación** | Z2 | Eléctrica del robot | Acceso al robot |
| **Cambio de tungsteno y boquilla** | Z2, zona de servicio | Eléctrica de la fuente TIG; temperatura | Ya previsto: estación de servicio frente a la puerta |
| **Cambio de dedos de la pinza** | Z2 | Eléctrica del IRB | Posición de mantenimiento del IRB con la pinza accesible desde la puerta |
| **Prueba de cortinas y enclavamientos** | Z1 y Z2 | — | Acceso desde afuera |

**Posiciones de mantenimiento:** cada robot necesita una posición articular conocida para el
mantenimiento, con el brazo plegado, la herramienta accesible desde la puerta y los ejes en una
posición que no caigan al desmontar un motor. Son programas de movimiento normales, que se ejecutan
antes de aplicar el LOTO.

## 9. Problemas de la disposición actual (v03)

| Problema | Consecuencia |
|---|---|
| Entre la cinta y la pared sur quedan **~250 mm** | No entra una persona; la banda no se puede sacar por ese costado |
| Del otro costado, la cinta queda **junto al manipulador** | Tampoco hay lateral libre para la banda |
| El extremo de entrada de la cinta, con su rodillo y accionamiento, queda **dentro** del cerramiento | Intervenirlo obliga a entrar a la zona de robots |
| Hay **una sola puerta**, en la cara este | Para llegar a la cinta o al lado oeste hay que cruzar la celda |
| No hay **posiciones de mantenimiento** definidas | Los robots se intervienen en cualquier postura |
| No hay **puntos de aislamiento** representados | El LOTO no tiene dónde aplicarse |

## 10. Requisitos para la v04 y para el panel

> **Estado:** la disposición está implementada en la v04 ([mejora 02](mejora_02_modos_mantenimiento.md)).
> Los modos, las paradas, el rearme y el panel están implementados en la v05 ([manual](manual.md)).
> La emergencia y las cortinas representan la función en simulación; no son un circuito de seguridad.

**Disposición (mejora 02):**

1. Un **pasillo de mantenimiento** a lo largo de la cinta, del lado sur, **fuera** del cerramiento
   de robots: el cerramiento se separa de la cinta y la cinta queda en Z1. El ancho del pasillo se
   fija en la v04, con el criterio de que entren una persona y la banda a retirar.
2. El **accionamiento de la cinta**, fuera de Z2, accesible desde el pasillo.
3. **Espacio libre alrededor de cada robot** y un camino hasta la puerta para retirar componentes.
4. **Puntos de aislamiento con candado** fuera del cerramiento: seccionadores de cada robot, de la
   cinta y de la fuente TIG, y válvula del argón, agrupados junto al panel.
5. **Pulsadores de emergencia** en el panel, junto a la puerta y en la entrada y la salida de la
   cinta.
6. **Posiciones de mantenimiento** de cada robot.

**Panel de operador:**

La propuesta y el seguimiento de implementación se registran en
[Panel de operador y sensores](panel_y_sensores.md). Se derivan de los lineamientos de
`a_requisitos/` y los conceptos de `b_investigacion/`; el panel v01 se conserva como antecedente.
El detalle de lo implementado y de lo pendiente está en ese documento.

- selector de modo (§4) y estado de cada zona y equipo;
- arranque, parada de ciclo y rearme;
- indicación de las paradas de emergencia y de protección, y de su causa;
- **no reemplaza** a los pulsadores de emergencia ni a los puntos de aislamiento físicos;
- **solo lee y escribe señales**: nunca mueve los robots ni la cinta.

## 11. Qué se representa en la simulación

| Elemento | En RoboDK | Solo en el informe |
|---|---|---|
| Zonas, pasillo, puerta, resguardos | Geometría | — |
| Puntos de aislamiento y pulsadores de emergencia | Geometría (marcadores) | Su función real |
| Selector de modo, paradas, rearme | Señales que leen los programas | Circuito de seguridad |
| Posiciones de mantenimiento | Programas con MoveJ a targets articulares | — |
| Parada de ciclo | Programa que termina la pieza y lleva todo a reposo | — |
| LOTO | — | Procedimiento completo (§7) |
| Velocidad reducida en manual | — | Es una función del controlador del robot |

## 12. Referencias

- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*.
  McGraw-Hill, 1.ª ed. Sección 9.3, pp. 271–277: causas de accidentes, medidas de seguridad, zonas
  de reparación y movimientos condicionados.
- **[Clase 2]** Luque, J. *Islas robotizadas y seguridad industrial*. UTN FRC, 2026: niveles de
  protección, puertas con enclavamiento, cortinas, PLC de seguridad.
- **Normas de referencia** (no consultadas): ISO 10218-1 y 10218-2 (modos de operación y seguridad
  de celdas robotizadas), ISO 12100 (evaluación del riesgo), ISO 13850 (parada de emergencia),
  ISO 14119 (dispositivos de enclavamiento). Para el procedimiento de bloqueo y etiquetado, la
  referencia habitual es la norma OSHA 29 CFR 1910.147 (*Control of hazardous energy*). En
  Argentina, el marco general es la Ley 19.587 de Higiene y Seguridad en el Trabajo y su Decreto
  351/79.
- Grupo 4. [`definicion_celda.md`](definicion_celda.md),
  [`mejora_01_cinta_pasante.md`](mejora_01_cinta_pasante.md) y
  [07 · Seguridad y normativa](../../b_investigacion/conceptos/07_seguridad_y_normativa.md).
