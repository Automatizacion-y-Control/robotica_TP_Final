<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

**Cátedra: Robótica Industrial**

# Panel de operador y sensores

Propuesta de implementación y registro de decisiones

**Grupo 4**<br>
Casali Emiliano · Ferrero Facundo · Vera Gonzalo

**Docentes**<br>
Ing. Julián Luque · Lic. Sergio Perassi

Comisión 2LA1 · Año 2026

</div>

## Índice

- [Prólogo](#prólogo)
- [1. Documentos rectores y trazabilidad](#1-documentos-rectores-y-trazabilidad)
- [2. Estado comprobado de la v04](#2-estado-comprobado-de-la-v04)
- [3. Antecedente del panel v01](#3-antecedente-del-panel-v01)
- [4. Arquitectura propuesta](#4-arquitectura-propuesta)
- [5. Modos y transiciones](#5-modos-y-transiciones)
- [6. Preparación para mantenimiento](#6-preparación-para-mantenimiento)
- [7. Señales y sensores](#7-señales-y-sensores)
- [8. Organización del panel](#8-organización-del-panel)
- [9. Implementación y pruebas pendientes](#9-implementación-y-pruebas-pendientes)
- [10. Registro de decisiones](#10-registro-de-decisiones)
- [Ensayos de control nativo](#ensayos-de-control-nativo)
- [11. Referencias](#11-referencias)

## Prólogo

Este documento registra la preparación del panel y los sensores de la celda de soldadura TIG de
paquetes de estator de motor de lavarropas. Distingue resultados comprobados de propuestas todavía
pendientes de implementación. Fecha de revisión: **2026-11-06**.

La guía del trabajo es `a_requisitos/`; su interpretación y fundamento se desarrollan en
`b_investigacion/`. El diseño de `c_prototipado/` deriva de ambos. Las versiones anteriores sirven
para explicar la progresión de las mejoras; no sustituyen a los requisitos.

## 1. Documentos rectores y trazabilidad

Fuente primaria: [lineamientos de la cátedra](../a_requisitos/Lineamiento_Trabajo_Final_Robotica.pdf).
Los identificadores siguientes corresponden a la
[matriz de investigación, §§2–6](../b_investigacion/conceptos/00_requisitos_y_trazabilidad.md),
que desarrolla los lineamientos. No se atribuye al PDF una paginación no verificada.

| Requisito o criterio | Fundamento de investigación | Decisión y evidencia prevista |
|---|---|---|
| M5: movimientos sin Python | [06, §7](../b_investigacion/conceptos/06_estructura_de_programas_y_senales.md#7-el-papel-de-python) | Panel y sensores intercambian señales; movimientos y secuencia en programas nativos. Revisar código y ejecutar desde RoboDK. |
| C2: principal y subprogramas | [06, §§3–5](../b_investigacion/conceptos/06_estructura_de_programas_y_senales.md#3-programa-principal-y-subprogramas) | Coordinación con estados iniciales/finales definidos y confirmaciones de E/S. |
| C3: cinta como mecanismo | [06, §6](../b_investigacion/conceptos/06_estructura_de_programas_y_senales.md#6-sincronización-del-robot-con-un-eje-externo) | Avance y evacuación mediante programas nativos de cinta. |
| C4: repetibilidad, alcance y colisiones | [08, §§4–7](../b_investigacion/conceptos/08_tiempo_de_ciclo_y_validacion.md#4-la-simulación-como-herramienta-de-validación) | Probar producción y nuevas secuencias de mantenimiento, incluidos sus estados intermedios. |
| Complejidad agregada justificada | [07, §§6–7 y 10](../b_investigacion/conceptos/07_seguridad_y_normativa.md) | Modos, permisos, causas de bloqueo y recuperación como representación académica. |
| Coherencia entre informe y estación | [00, §§4–6](../b_investigacion/conceptos/00_requisitos_y_trazabilidad.md) | Registrar qué está propuesto, implementado y verificado. |

El detalle de aplicación a esta celda está en
[modos y mantenimiento, §§4–11](modos_y_mantenimiento.md). El panel es una mejora de diseño:
no se presenta como una exigencia explícita adicional de la cátedra.

## 2. Estado comprobado de la v04

Resultados de la sesión del 2026-11-06, RoboDK **6.1.1.26991**:

| Comprobación | Resultado y alcance |
|---|---|
| Targets cartesianos | 19 alcanzables con las herramientas correspondientes. |
| Verificador con pieza transportada | `Inicio_Celda`, `Sold_Servicio_Antorcha`, `Sold_Cambio_Tungsteno`, `Ciclo_Pieza_1` y `Programa_Principal`: ratio 1 con colisiones y muestreo de 1 mm/1°. |
| Ejecución de producción | Dos ejecuciones consecutivas del principal, un lote por ejecución, a ×10; sin colisiones detectadas. Monitoreo por consultas, no prueba exhaustiva de eventos entre muestras. |
| Fin de los dos lotes | Los cuatro estatores quedaron bajo `Frame_Banda`. |
| Mantenimiento IRB y parada | `Man_Ir_Mantenimiento` y `Parada_Ciclo`: ratio 1 desde reposo. |
| Corrección CRB | La antorcha chocaba con la estación de servicio al 84 % de la ida; la postura final también presentaba contactos del robot. |
| Postura CRB corregida | `[100, -30, 50, 0, 60, 0]` grados; ida y vuelta a reposo verificadas con muestreo de 1 mm/1°. Parámetro y target actualizados. Archivo guardado y reabierto para confirmar persistencia. |
| Estado final | Robots en reposo, pinza abierta, cinta en posición inicial; cero colisiones; velocidad ×1. |

Estas pruebas **no validan todavía los modos desde el panel** ni la postura simultánea de ambos
robots en mantenimiento. Tampoco acreditan soporte mecánico de ejes para desmontajes.

La inspección de instrucciones nativas confirmó:

- `Parada_Ciclo` apaga `ARCO_TIG` y llama al reposo del soldador y del manipulador. No espera por
  sí mismo que termine una pieza: debe ser invocado en el límite entre piezas.
- `Programa_Principal` llama a inicio, cuatro ciclos y fin de lote. Todavía no consulta solicitudes
  de cambio de modo o parada entre piezas. Conserva un comentario antiguo sobre salida por pallet.
- Los programas de mantenimiento pasan por reposo y luego al target de mantenimiento; no comprueban
  por sí mismos puerta, pieza sostenida, disponibilidad del equipo ni solicitudes del panel.
- `Inicio_Celda` abre la pinza y mueve robots: no debe usarse como recuperación general de una falla.
- Existen señales `ARCO_TIG`, `PIEZA_EN_TOMA`, `PIEZA_PRESENTADA` y `SOLDADURA_TERMINADA`.
  Su presencia no demuestra que sean sensores independientes: hoy hay escrituras desde programas.

## 3. Antecedente del panel v01

Se exportó, sin ejecutarlo, el programa Python embebido
`Panel_Operador_RoboDK_Con_Sensor_Pieza_CORREGIDO` de la v01. Se conserva como
[referencia de código](referencias/panel_v01_referencia.py.txt), con extensión de texto para no
confundirlo con una implementación vigente. El archivo `.rdk` original no se modificó.

| Elemento observado | Evaluación para la nueva celda |
|---|---|
| Tkinter, estado general, puerta, presencia, avance y mensajes | Reutilizar ideas de presentación; decidir tecnología después de definir el contrato de señales. |
| Secuencia de seis cordones y posicionador MTD 250 | Corresponde al antecedente; la celda actual tiene dos robots, cuatro cordones y cinta pasante. |
| `RunProgram`, `Stop` y consulta de `Busy` desde Python | El panel decide la secuencia y las recuperaciones. Rehacer esa responsabilidad en los programas nativos conforme a M5 y al concepto 06, §7. |
| Creación de un programa con `addMoveJ` durante el uso | Excluir del panel de operación. Los scripts de construcción y verificación tienen otra finalidad. |
| Presencia mediante `Visible()` | No reutilizar como sensor de toma: visibilidad no demuestra ubicación ni agarre. |
| Botón HOME y repetición del subprograma interrumpido | No reutilizar como recuperación universal ante falla o pieza sostenida. |
| Puerta movida desde Python y salida directa DO5 | Reemplazar por entradas simuladas y contrato de señales; conservar `ARCO_TIG` como denominación de la celda actual. |

**Decisión propuesta:** construir lógica propia para la celda actual y conservar la v01 como
antecedente visual e histórico. Reutilizar código solo cuando respete el contrato de señales y no
dependa del posicionador ni de la secuencia anterior.

## 4. Arquitectura propuesta

1. **Programas nativos:** ejecutan la secuencia, los movimientos, las esperas y las confirmaciones
   de estado. Un coordinador nativo acepta o rechaza solicitudes según el modo y las condiciones.
2. **Sensores Python:** consultan poses, articulaciones o pertenencia de las piezas; calculan
   detecciones y escriben sus señales. No mueven objetos, robots ni cinta para producir una detección.
3. **Panel:** muestra estados confirmados y escribe solicitudes o entradas de simulación. No llama
   subprogramas para encadenar movimientos ni crea instrucciones durante la operación.
4. **Construcción y verificación:** scripts separados, fuera del funcionamiento del panel.

Antes de implementar el coordinador se debe comprobar qué condiciones, saltos e interrupciones
ejecuta realmente RoboDK 6.1.1. Una instrucción insertada como código del controlador no garantiza
que el simulador la interprete. Si una función no puede representarse de forma nativa, registrar
el límite y resolver el diseño sin trasladar la secuencia a Python.

El arranque inicial del coordinador será desde RoboDK. El panel solicitará el arranque del ciclo
por señal. El ciclo de movimientos debe seguir definido íntegramente en la estación.

## 5. Modos y transiciones

**Propuesta pendiente de implementación.** Separar modo solicitado, modo confirmado y estado de
ejecución: seleccionar mantenimiento no significa que el equipo ya esté posicionado o aislado.

| Modo | Entrada y comportamiento esperado | Salida |
|---|---|---|
| Arranque / recuperación | Diagnóstico inicial; comprobar posición, pieza y disponibilidad. Recuperación supervisada si el estado es desconocido. | Listo, después de las comprobaciones. |
| Automático | Resguardos simulados conformes, sin fallas ni mantenimiento activo, equipos disponibles y preparación del lote confirmada. | Pedido normal de parada al terminar la pieza, o interrupción por falla/protección. |
| Parada de ciclo | Retener el pedido; completar y depositar la pieza actual; ejecutar `Parada_Ciclo`; no iniciar la siguiente. | Reposo confirmado, manteniendo el índice y estado real del lote. |
| Manual / programación | Un equipo por vez; arco inhibido; movimientos mediante consola o programas nativos previamente autorizados. | Detención confirmada antes de cambiar de modo. |
| Servicio de antorcha | Celda parada, IRB en reposo, cinta detenida; CRB a servicio antes del acceso. | Retirada y regreso verificados, cierre, rearme y nuevo pedido de arranque. |
| Mantenimiento | Selección de equipo; preparación confirmada; etapa separada de aislamiento y acceso. | Fin de intervención, restitución, comprobaciones y prueba antes de automático. |

Prioridad propuesta: emergencia/protección y fallas bloqueantes antes que solicitudes de operación.
El rearme borra una condición retenida solo si su causa desapareció; **no arranca ni mueve equipos**.
El cierre de la puerta y el retorno de comunicación tampoco deben producir arranque.

## 6. Preparación para mantenimiento

Para una parada programada: terminar y depositar la pieza antes de mover a mantenimiento.
Durante la preparación no debe haber personas dentro de la zona de robots. Los demás equipos
permanecen detenidos y el arco inhibido. No se autoriza producción con personas interviniendo.

| Equipo seleccionado | Preparación propuesta | Estado pendiente de comprobar |
|---|---|---|
| IRB y pinza | CRB en reposo; IRB vacío a `Man_Mantenimiento`; cinta detenida. | Retorno del IRB y permisos integrados. |
| CRB | IRB vacío en reposo; CRB a `Sold_Mantenimiento`; cinta detenida. | Permisos integrados; ida/vuelta geométrica ya comprobada. |
| Ambos robots | Desde reposo, posicionar uno y después el otro. Determinar el orden mediante prueba conjunta. | Ambos órdenes, posturas simultáneas y retorno; no asumir validez por pruebas individuales. |
| Cinta | Robots en reposo; banda detenida en la posición actual. Vaciar solo si la tarea lo requiere y el mecanismo está disponible. | Secuencia de vaciado sin reposición automática; no utilizar directamente `Fin_Lote`, que repone piezas mediante eventos. |
| Antorcha | IRB en reposo y CRB a la posición específica de servicio; banda detenida. | Distinguir verificación de TCP de preparación para cambio de tungsteno. |

**Preventivo y correctivo:** registrar tipo de intervención y tarea. La postura depende de la tarea,
no solo de esa clasificación. Un correctivo con equipo averiado no debe intentar mover ese equipo
para satisfacer una condición de mantenimiento. Con pieza sostenida o posición desconocida, bloquear
la preparación automática y registrar recuperación requerida. No abrir automáticamente la pinza.

Separar los estados **solicitado → preparando → posicionado → aislamiento por procedimiento →
intervención → restitución → comprobación**. Una confirmación ingresada en la simulación no es una
medición de energía cero. Para desmontar motores/ejes se necesita una preparación y sujeción
específica; una postura articular libre de colisiones no garantiza estabilidad al desmontar.

## 7. Señales y sensores

Tabla inicial propuesta; falta fijar canales concretos y tolerancias. Cada señal tendrá un único
escritor. No mezclar parámetros de estación con E/S sin comprobar experimentalmente su correspondencia.

| Señal o grupo | Escritor | Lectores y significado |
|---|---|---|
| `MODO_SOLICITADO`, `EQUIPO_MANT_SOLICITADO` | Panel | Coordinador nativo; valores enumerados todavía por fijar. |
| `SOL_ARRANQUE`, `SOL_PARADA_CICLO`, `SOL_REARME`, `SOL_PREPARAR_MANT` | Panel | Solicitudes con identificador y confirmación para impedir repetición por un botón retenido. |
| `MODO_ACTIVO`, `ESTADO_CELDA`, `ORDEN_CONFIRMADA`, `CAUSA_BLOQUEO` | Coordinador nativo | Panel; no se deducen de la selección visual. |
| `PIEZA_EN_TOMA_SENSOR` | Sensores Python | Presencia calculada por volumen de detección alrededor de la toma y pose de la pieza, con tolerancias pendientes. |
| `PIEZA_SUJETA_SENSOR` | Sensores Python | Pertenencia al TCP y coherencia geométrica; representa agarre en simulación, no fuerza real. |
| `IRB_EN_REPOSO`, `CRB_EN_REPOSO`, `IRB_EN_MANT`, `CRB_EN_MANT` | Sensores Python | Comparación articular con targets y tolerancia definida; no basta la finalización del programa. |
| `CINTA_DETENIDA`, `CINTA_POSICION`, `PINZA_ABIERTA_SENSOR` | Sensores Python | Lectura articular y estabilidad temporal; distinguir posición de ausencia de movimiento. |
| `PUERTA_CERRADA_SIM`, `CORTINA_ENTRADA_LIBRE_SIM`, `CORTINA_SALIDA_LIBRE_SIM`, `RESGUARDO_CINTA_CERRADO_SIM`, `EMERGENCIA_SIM` | Entradas de simulación | Cada entrada se identifica como simulada; valores desconocidos al iniciar bloquean la habilitación. |
| `PANEL_VIGENTE`, `SENSORES_VALIDOS` | Panel / sensores, respectivamente | Vigencia temporal a comprobar; ante desconexión no conservar permisos indefinidamente. |
| `ARCO_TIG`, `PIEZA_PRESENTADA`, `SOLDADURA_TERMINADA` | Programas nativos existentes | Mantener significado y revisar reinicio por pieza y por par de cordones. |
| `PIEZA_EN_TOMA` existente | Programas nativos existentes | Auditar sus escrituras antes de migrar a la nueva detección; no permitir dos escritores. |

Para cada sensor calculado se registrarán: objeto/frame de referencia, magnitud observada,
umbral, tolerancia, frecuencia, tratamiento de ruido, demora máxima y reacción ante pérdida de datos.
No usar la visibilidad para demostrar presencia o agarre. No confundir `ARCO_TIG=1` con confirmación
física de arco establecido ni `SOLDADURA_TERMINADA=1` con calidad metalúrgica.

## 8. Organización del panel

- **Estado general:** conexión, modo confirmado, estado de ejecución, pieza/lote y causa de bloqueo.
- **Operación:** solicitudes de arranque, parada de ciclo y rearme con acuse de recepción.
- **Mantenimiento:** equipo, preventivo/correctivo, tarea, condiciones pendientes y preparación.
- **Sensores:** valor, procedencia calculada/simulada y vigencia; separar entradas modificables de
  indicadores de solo lectura.
- **Alarmas y registro:** orden solicitada, aceptación/rechazo, transición, falla y recuperación,
  con fecha y hora. No depender solo de colores para explicar el estado.

Las entradas de ensayo de puerta, cortinas y emergencia estarán identificadas como simulación.
El panel no acredita seguridad industrial ni sustituye los puntos físicos de aislamiento descritos
en [modos y mantenimiento, §§6–7 y 11](modos_y_mantenimiento.md).

## 9. Implementación y pruebas pendientes

| Paso | Producto / criterio para completarlo | Estado |
|---|---|---|
| 1 | Trazabilidad e inventario de v04 y antecedente v01 | Documentados en esta revisión. |
| 2 | Cerrar estados, transiciones y disponibilidad por equipo | Propuesta; falta validar capacidades nativas. |
| 3 | Comprobar condiciones/saltos y monitoreo durante movimiento en RoboDK 6.1.1 | IF, WHILE, E/S y ejecución paralela probados; ELSE no validado. Retirar permiso durante MoveJ de cinta no detiene el movimiento. Interrupción inmediata nativa no demostrada. |
| 4 | Verificar preparación/retorno individual, conjunta y de cinta | IRB de regreso y ambos órdenes conjuntos pasan. Ensayada cinta sin evacuación y evacuación del lote inicial; banda vacía y lotes parciales requieren procedimiento específico. |
| 5 | Fijar contrato de E/S, escritor único, acuses, tolerancias y tiempos máximos | Propuesta de señales; pendiente de cerrar. |
| 6 | Implementar coordinación nativa sin perder eventos de la estación anterior | Pendiente. |
| 7 | Implementar sensores y comprobar detecciones antes/durante/después de toma y depósito | Pendiente. |
| 8 | Construir panel propio con solicitudes e indicadores | Pendiente; antecedente revisado. |
| 9 | Ensayos integrados y documentación de resultados | Pendiente. |

Ensayos de aceptación que deben quedar registrados:

1. Dos lotes consecutivos, señales reiniciadas correctamente, sin colisiones ni bloqueos de espera.
2. Parada solicitada durante avance, toma, soldadura y depósito: completar la pieza cuando sea una
   parada normal; no comenzar la siguiente. Si el pedido llega en reposo, no iniciar una pieza.
3. Mantenimiento de cada equipo y de ambos: permisos, secuencia, posturas finales y retorno.
4. Cinta: tarea con/sin vaciado y fallo del accionamiento; ningún movimiento del equipo averiado.
5. Fallas con pieza sostenida y soldadura incompleta: sin apertura de pinza, HOME ni repetición
   automática del cordón; recuperación supervisada.
6. Puerta, cortinas y emergencia durante movimiento: comprobar la reacción realmente representable,
   su latencia y sus límites. Un WAIT antes de un movimiento no representa monitoreo continuo.
7. Orden incompatible, solicitud repetida, pérdida de conexión y datos vencidos: rechazo o estado
   de bloqueo definido; el retorno de señal o el rearme no arrancan producción.

## 10. Registro de decisiones

| Fecha | Decisión / evidencia |
|---|---|
| 2026-11-06 | Requisitos → investigación → diseño es la jerarquía rectora. La v01 es antecedente. |
| 2026-11-06 | Revisado código del panel v01 sin ejecutarlo; conservarlo como texto de referencia y rehacer la coordinación para cumplir M5. |
| 2026-11-06 | Corregida postura CRB de mantenimiento; guardado confirmado al reabrir el archivo. |
| 2026-11-06 | Modos todavía no integrados: las pruebas geométricas no equivalen a validación funcional del panel. |
| 2026-11-06 | Control de flujo probado en estación aislada basada en ejemplo oficial: habilitar la opción por estación es imprescindible. Usar IF/END y WHILE/END comprobados; no adoptar ELSE todavía. |
| 2026-11-06 | IRB ida/vuelta y mantenimiento conjunto en ambos órdenes: ratio 1 sin colisiones con muestreo 1 mm/1°. Orden propuesto: IRB, CRB; regreso CRB, IRB. |
| 2026-11-06 | Ensayo sobre copia descartable de v04: retirar permiso con eje a 155 mm no detiene el avance a 2050 mm. No atribuir función de protección inmediata a WAIT ni al panel. |
| 2026-11-06 | Separar cinta detenida, zona de robots sin piezas y banda vacía. Evacuación a 1750 mm no despeja el lote inicial; 2050 mm sí despeja ese caso, pero no representa retirada de piezas. |

Cada implementación posterior debe actualizar la tabla de pasos, señales definitivas y pruebas,
indicando versión de estación y resultado. No marcar como implementado un requisito por disponer
solamente de geometría o de una descripción.

## Ensayos de control nativo

Banco reproducible: [probar_control_nativo.py](scripts/probar_control_nativo.py). Construye una
estación temporal sin robots, inyecta entradas y observa salidas; elimina la estación de ensayo
y restaura la estación activa y la velocidad. No guarda ni altera el ciclo de la v04.
Las llamadas de ejecución desde Python pertenecen exclusivamente al banco de prueba.

```text
C:\RoboDK\Python-Embedded\python.exe c_prototipado/scripts/probar_control_nativo.py
C:\RoboDK\Python-Embedded\python.exe c_prototipado/scripts/probar_control_nativo.py --con-flujo
C:\RoboDK\Python-Embedded\python.exe c_prototipado/scripts/probar_control_nativo.py --con-flujo-api
```

Para la segunda variante se usa la configuración de
[FlowControlTest_oficial.rdk](referencias/FlowControlTest_oficial.rdk), descargado del
[ejemplo del soporte de RoboDK](https://robodk.com/forum/Thread-Conditional-call-to-a-program-from-custom-code-instruction?pid=16753).
Se eliminan sus programas antes del ensayo; no se ejecuta código del adjunto.
El soporte indica habilitar **Station Parameters → Enable flow control statements** y usar
instrucciones de llamada separadas de las líneas insertadas de control de flujo.

| Prueba en 6.1.1.26991 | Resultado observado | Consecuencia |
|---|---|---|
| Set nativo | La salida 17 se lee como parámetro 17. | Existe comunicación programa → parámetros. |
| WAIT con entrada externa | Con entrada 0 permanece ocupado y no escribe fin; con entrada 1 termina y escribe fin. | Parámetros → espera nativa funciona. |
| Llamada nativa | El subprograma escribe su salida. | La secuencia puede permanecer en la estación. |
| IF/END sin habilitación de flujo | La rama se ejecuta tanto con entrada 0 como con 1. | No asumir que insertar texto activa condiciones. |
| IF/END con flujo habilitado | Rama y llamada se omiten con 0 y se ejecutan con 1. | Bifurcación demostrada sin coordinador Python. |
| WHILE/END y asignaciones | El contador termina en 3. | Bucle nativo simulado disponible con la configuración ensayada. |
| IF/ELSE/END insertado | Con entrada 0 queda 0; con 1 termina en 20, en vez de 20 y 10 respectivamente. | Esta forma no está validada. Diseñar inicialmente con IF separados sobre una selección capturada. |
| Start Thread | El padre termina mientras el hijo espera; una señal libera al hijo. | Posible separar coordinador y tareas, con confirmaciones explícitas. |
| Retirar permiso después de WAIT | La pausa posterior termina y se alcanza etapa 2 aun con permiso 0. | WAIT es puntual. Esto no demuestra interrupción durante movimiento ni función de seguridad. |

Evidencia: [sin flujo](verificaciones/control_nativo_6_1_1_sin_flujo.json),
[con flujo](verificaciones/control_nativo_6_1_1_con_flujo.json).
El [primer ensayo](verificaciones/control_nativo_6_1_1.json) conserva el resultado de código RAPID
insertado sin habilitar el flujo; no debe interpretarse como ausencia general de bifurcaciones.
La correspondencia de E/S con parámetros también está descrita en la
[documentación oficial Set/Wait IO](https://robodk.com/doc/en/Robot-Programs-SetWait-IO.html).

Alcance pendiente: no se probó el vencimiento del timeout nativo ni combinaciones arbitrarias de
sintaxis RAPID. Los ensayos sin robots usan pausas,
no trayectorias. Todavía no se ha cambiado la configuración de flujo de la v04 ni creado la v05.

La comprobación posterior sobre un movimiento real del mecanismo se registra en el apartado siguiente;
no se logró una interrupción nativa inmediata.

### Verificación geométrica complementaria

[Resultados](verificaciones/mantenimiento_conjunto_v04.json), obtenidos con programas temporales
de llamadas nativas y `Update(COLLISION_ON, 3600, 1, 1)` desde reposo:

- IRB a mantenimiento y regreso: ratio 1.
- IRB a mantenimiento, luego CRB; regreso CRB y luego IRB: ratio 1.
- CRB a mantenimiento, luego IRB; regreso IRB y luego CRB: ratio 1.

Se proponen movimientos secuenciales, no simultáneos. Estas pruebas incluyen las posturas combinadas
durante las trayectorias pero no validan disponibilidad de equipos, accesibilidad física para una
tarea particular, soporte de ejes ni aislamiento. Los programas temporales se eliminaron y se
restableció el reposo; la v04 no se guardó con cambios de este ensayo.

### Cinta y retirada de permiso durante movimiento

Banco: [probar_cinta_y_permisos.py](scripts/probar_cinta_y_permisos.py).
Evidencia: [cinta_y_permisos_v04.json](verificaciones/cinta_y_permisos_v04.json).
Se abrió una copia descartable del archivo v04, conservando eventos y geometría. Se eliminó al
terminar y se restauró la estación activa y la velocidad. Los movimientos de ensayo fueron
instrucciones MoveJ nativas, no órdenes de movimiento desde el sensor o el panel.

| Caso | Resultado observado | Interpretación |
|---|---|---|
| Preparar sin evacuar | Robots en reposo, cinta en 0, cuatro piezas sobre banda, cero colisiones. | Para una tarea que no requiere quitar piezas, mantener la posición; no ordenar origen por defecto. Falta integrar permisos y confirmación temporal de detención. |
| Evacuar lote inicial hasta eje 1750 | Centros en X = 1600, 1300, 1000 y 700 mm; ratio 1 sin colisiones. | El último estator sigue dentro: cara este del cerramiento en X = 850 mm. El target productivo no es un vaciado universal. |
| Evacuar lote inicial hasta eje 2050 | Centros en X = 1900, 1600, 1300 y 1000 mm; ratio 1 sin colisiones. | Todas las piezas quedan fuera de la zona y dentro del apoyo de salida, que termina en X = 2100 mm. Solo probado para la distribución inicial. |
| Permiso retirado durante MoveJ | Se retiró con eje a 155 mm; el eje llegó a 2050 mm y el programa escribió fin, con permiso en 0. Cero colisiones detectadas por monitoreo. | WAIT previo no cancela el movimiento en curso. La reacción inmediata a una intrusión no está implementada por ese mecanismo. |

Para determinar salida completa se comprobó `min(X_centros) - ESTATOR_LADO/2 > CERR_X[1]`;
para el apoyo, `max(X_centros) + ESTATOR_LADO/2 <= CINTA_EXT_FIN_X`. Se aplica a las piezas
verticales de este ensayo; no es un algoritmo general para cualquier orientación o distribución.

**Decisiones para cerrar la lógica de cinta:**

1. **Sin evacuación:** detener y conservar eje; no declarar vacía ni reiniciar el lote.
2. **Despejar zona de robots:** solo permitir una evacuación cuya distribución de piezas y apoyo
   final estén comprobados. No reutilizar 2050 mm para cualquier lote parcial.
3. **Banda vacía para recambio:** exige retirada efectiva de las piezas y confirmación independiente;
   desplazarlas a la salida no vacía la banda. La retirada se representará por un procedimiento
   supervisado y los eventos nativos necesarios; el panel no reubicará ni ocultará piezas.
4. **Accionamiento averiado:** rechazar evacuación automática; mantener estado e indicar recuperación
   e intervención. No intentar mover la cinta para satisfacer el permiso de mantenimiento.
5. **Reinicio:** preservar estado del lote; después de intervención no ejecutar automáticamente
   `Fin_Lote`, porque también repone piezas. Requiere confirmación de restitución y nuevo arranque.

**Decisión de alcance para la v05:** se puede implementar coordinación de producción, paradas al
final de pieza y preparación programada. La emergencia y las protecciones se deben mostrar como
entradas de simulación con su alcance explícito. No dar por validada una parada inmediata por
señales hasta demostrar un mecanismo nativo que cancele el movimiento. La parada manual del
simulador es distinta de esa función. No añadir `Stop()` al panel Python para ocultar esta diferencia.

### Persistencia del control de flujo sobre la base v04

Se comprobó `estacion.setParam("FlowControl", "1")`, con respuesta `OK`, mediante el banco
`--con-flujo-api`. La [evidencia](verificaciones/control_nativo_6_1_1_flujo_api.json) reproduce
IF, WHILE, llamadas y ejecución paralela sin depender del ejemplo externo. Es una capacidad
comprobada experimentalmente en esta versión, no una garantía para otras versiones.

El banco de cinta habilita esa opción en su copia descartable de v04, guarda y reabre el archivo,
compara los nombres de las instrucciones de evento por programa y ejecuta una condición falsa.
El resultado se registra en `persistencia_flujo` del JSON de cinta. Esto permite derivar la futura
v05 del archivo v04 conservando los eventos originales, en vez de reconstruirla desde el ejemplo.

Siguientes tareas: cerrar estados/órdenes y recuperación para lotes parciales; elegir la
representación de las interrupciones dentro de las capacidades demostradas. La v05 y el panel
todavía no están implementados.

## 11. Referencias

- **[Lineamientos]** Cátedra de Robótica Industrial, UTN FRC, comisión 2LA1, 2026.
  [Documento rector](../a_requisitos/Lineamiento_Trabajo_Final_Robotica.pdf). Identificadores M5,
  C2–C4 según la [síntesis de investigación, §§2–6](../b_investigacion/conceptos/00_requisitos_y_trazabilidad.md).
- **[Investigación 06]** [Estructura de programas y señales](../b_investigacion/conceptos/06_estructura_de_programas_y_senales.md),
  §§3–7: estructura, E/S y límite de Python. Allí se desarrolla Barrientos, §8.2.4, p. 228;
  §8.2.6, p. 230; Groover, §8.5, pp. 231–232. Referencias tomadas de la investigación del repositorio.
- **[Investigación 07]** [Seguridad y normativa](../b_investigacion/conceptos/07_seguridad_y_normativa.md),
  §§4, 6–7 y 10. Fundamento citado allí: Barrientos, §9.3, pp. 271–277. Las normas ISO se
  mantienen solo como referencia; no se consultó su texto ni se afirma cumplimiento.
- **[Investigación 08]** [Tiempo de ciclo y validación](../b_investigacion/conceptos/08_tiempo_de_ciclo_y_validacion.md),
  §§4–7. Prueba progresiva: Barrientos, §9.3.2, p. 276, según la investigación del repositorio.
- **[Aplicación]** [Modos y mantenimiento](modos_y_mantenimiento.md), §§4–11; documento interno sin paginación.
- **[Antecedente]** Panel Python exportado de la estación v01, apartado 3 de este documento;
  evidencia histórica de implementación, no fuente de requisitos.
