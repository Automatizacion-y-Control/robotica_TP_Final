<div align="center">

**UNIVERSIDAD TECNOLÓGICA NACIONAL**<br>
**Facultad Regional Córdoba**<br>
Licenciatura en Automatización y Control

---

**Cátedra: Robótica Industrial**<br>
Trabajo final: celda robotizada de soldadura

# 09 · Interfaz de operación, usuarios y permisos

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
- [1. Alcance y método de investigación](#1-alcance-y-método-de-investigación)
- [2. Fundamentos y prácticas de fabricantes](#2-fundamentos-y-prácticas-de-fabricantes)
- [3. Identidad, permisos y modo de operación](#3-identidad-permisos-y-modo-de-operación)
- [4. Perfiles y matriz de operaciones](#4-perfiles-y-matriz-de-operaciones)
- [5. Gestión de cuentas y sesiones](#5-gestión-de-cuentas-y-sesiones)
- [6. Implicancias para los modos y el mantenimiento](#6-implicancias-para-los-modos-y-el-mantenimiento)
- [7. Pantallas y navegación](#7-pantallas-y-navegación)
- [8. Contrato con la lógica de la celda](#8-contrato-con-la-lógica-de-la-celda)
- [9. Registros, validación y manual](#9-registros-validación-y-manual)
- [10. Qué hay que definir en nuestra celda](#10-qué-hay-que-definir-en-nuestra-celda)
- [11. Referencias](#11-referencias)

---

## Prólogo

El sistema de control de una célula debe ofrecer una interfaz para conocer su estado y operarla
con restricciones [Barrientos, §9.1.2, p. 261; concepto 01, §5]. Los códigos de acceso al control
y a la modificación de programas forman parte de las medidas reseñadas en la investigación
[Barrientos, §9.3.2, pp. 273–276; concepto 07, §6.1]. Estos fundamentos requieren desarrollar
cómo se identifican los usuarios y se autorizan las operaciones del panel.

Este documento amplía esa investigación mediante documentación primaria de ABB y Siemens y guías
de OWASP sobre autorización y almacenamiento de contraseñas. Luego propone criterios para la celda
del grupo. Los perfiles y decisiones de aplicación se identifican como **propuesta del proyecto**:
no son una clasificación obligatoria del libro ni de los lineamientos.

## 1. Alcance y método de investigación

La jerarquía es **lineamientos → investigación → diseño e implementación → verificación y manual**.
El punto de partida es [00, §§2–6](00_requisitos_y_trazabilidad.md): M5 limita Python, C2 exige
programas ordenados y C4 una simulación repetible. El login y los tres perfiles agregan complejidad
justificada; no constituyen una exigencia explícita nueva de la cátedra.

Se consultaron las fuentes web de §11 el **6 de noviembre de 2026**. Sus versiones se registran
cuando la publicación las identifica. Los manuales de fabricantes se usan como ejemplos de
arquitectura, sin asumir que RoboDK implementa sus funciones ni que un panel propio equivale a
FlexPendant o WinCC. Las referencias HTML carecen de página: se cita el apartado exacto.
Las referencias a Barrientos se apoyan en la investigación ya existente del repositorio.

## 2. Fundamentos y prácticas de fabricantes

| Fuente | Hallazgo documentado | Uso en el proyecto |
|---|---|---|
| Barrientos, §9.1.2, p. 261; §9.3.2, pp. 273–276 | Interfaz con restricciones y acceso controlado al control/programa, según conceptos 01 y 07. | Justificar interfaz y permisos antes de diseñar botones. |
| ABB, *User Authorization System*, apartados Overview, Accessing UAS y Grants and Groups [ABB-UAS] | Identificación individual, grupos con permisos y comprobación de derechos antes de operaciones sensibles; reconexión requiere identificarse de nuevo. | Separar sesión y autorización de cada orden. El UAS del controlador no se reemplaza por ocultar un botón. |
| Siemens, *Unified Basic Panels V20*, Security / User management [Siemens-UM] | Roles con derechos de función, administración de usuarios restringida, usuario activo visible y cierre por inactividad configurable. | Distinguir gestión de cuentas de operación y definir sesiones. |
| OWASP, *Authorization*, apartados Recommendations [OWASP-A] | Privilegios mínimos, rechazo por defecto, validación por solicitud y registros/pruebas de autorización. | Verificar cada orden donde se procesa, incluso si no proviene del botón esperado. |
| OWASP, *Password Storage*, Introduction y Salting [OWASP-P] | Hash específico para contraseñas y salt individual; no almacenar texto plano ni usar un hash rápido genérico como sustituto. | Elegir una biblioteca mantenida para las credenciales del futuro panel. |

Son prácticas de control de acceso. No demuestran seguridad funcional, habilitación física de
movimiento ni cumplimiento de normas ISO. Las ISO del concepto 07 se mantienen **solo como
referencia**, sin acceso a su texto.

## 3. Identidad, permisos y modo de operación

Se distinguen cuatro preguntas:

| Concepto | Pregunta | Ejemplo de aplicación |
|---|---|---|
| Autenticación | ¿Quién solicita? | Cuenta individual activa con sesión válida. |
| Autorización | ¿Tiene permiso para esta operación? | Solicitar preparación del CRB. |
| Modo confirmado | ¿Qué régimen tiene seleccionado la celda? | Automático o mantenimiento. |
| Condiciones de ejecución | ¿Puede realizarse ahora? | Pieza depositada, equipos detenidos y recorrido disponible. |

**Criterio propuesto:** aceptar una orden exige sesión válida, permiso de la operación, modo
compatible, estado conocido y condiciones de ejecución confirmadas. Ninguna de esas condiciones
se infiere de otra. La autenticación no reemplaza selector de modo, consola, dispositivo de
habilitación, enclavamientos ni LOTO.

Un perfil agrupa permisos de trabajo; un modo describe el estado operativo de la máquina.
Entrar como mantenimiento no mueve robots ni cambia de modo. Entrar como administrador no libera
la celda. Mostrar solicitud, aceptación y estado confirmado como datos separados.

## 4. Perfiles y matriz de operaciones

**Propuesta del proyecto:** tres perfiles funcionales, sin herencia automática de todos los
permisos. Una persona puede recibir más de uno por asignación explícita; la sesión tendrá un
perfil activo visible. Cambiarlo exige volver a validar permisos y contexto, sin generar mandos.
No se necesitan cuentas compartidas llamadas simplemente «producción» o «mantenimiento».

| Operación | Producción | Mantenimiento | Administrador |
|---|---|---|---|
| Consultar estado y alarmas de operación | Sí | Sí | Sí |
| Arrancar o continuar producción automática | Sí, si hay condiciones | Solo con perfil de producción adicional activo | Solo con perfil de producción adicional activo |
| Solicitar parada normal | Sí | Sí | Sí |
| Reconocer una alarma | Sí, si corresponde a su operación | Sí | Consulta; no rearme técnico implícito |
| Solicitar rearme | Solo causas operativas definidas | Causas de su intervención, con condiciones confirmadas | Sin permiso técnico implícito |
| Preparar mantenimiento IRB, CRB, ambos o cinta | No | Sí, desde estado permitido | No por ser administrador |
| Servicio de antorcha / recuperación supervisada | No | Sí, con procedimiento específico | No por ser administrador |
| Jog de robots o avance manual desde el panel | No | No en el alcance actual; consola/programas nativos | No |
| Cambiar usuarios, perfiles o política de sesión | No | No | Sí, con registro y protección de la última cuenta administradora |
| Cambiar trayectorias, TCP o parámetros de proceso | No | No por defecto; requiere ingeniería y validación separadas | No por defecto |
| Anular protecciones o declarar energía cero por software | Nunca | Nunca | Nunca |

Reconocer una alarma solo registra su lectura; no elimina la causa ni rearma. La emergencia
física no requiere login ni debe depender de un permiso de software. En la HMI propuesta, una
solicitud de parada normal podrá estar accesible también sin sesión, identificada como no
autenticada en el registro; esto no convierte el botón en una parada de seguridad.

## 5. Gestión de cuentas y sesiones

Las siguientes son **reglas de diseño propuestas**, a concretar y probar al implementar:

1. **Alta:** crear identificador único, nombre, perfil(es), estado y fecha; asignación por
   administrador. Entregar credencial inicial individual y exigir su cambio. No versionar secretos.
2. **Autenticación:** usuario y contraseña; mensaje de fallo sin revelar si una cuenta existe.
   Limitar intentos con espera/bloqueo temporal configurable y registrar los fallos.
3. **Almacenamiento:** hash con biblioteca especializada y salt por cuenta. Propuesta inicial:
   Argon2id si el entorno lo permite; concretar coste y dependencias antes del código [OWASP-P].
   La base de credenciales, copias y permisos de archivos también deben protegerse.
4. **Cambios:** registrar autor y cambio de perfil/estado; reevaluar o revocar sesiones afectadas.
   El usuario podrá cambiar su contraseña, no sus propios privilegios.
5. **Baja:** deshabilitar cuenta, invalidar sesiones y conservar identidad en registros históricos.
   Evitar borrar la referencia que explica quién emitió una orden.
6. **Recuperación:** restablecimiento por procedimiento administrativo; no mostrar contraseñas
   previas ni introducir una cuenta maestra oculta. Proteger la última cuenta administradora activa.
7. **Sesión:** identificar usuario/perfil activos en todas las pantallas; cerrar explícitamente,
   por inactividad o por pérdida de conexión. No restaurar órdenes pendientes al reconectar.
8. **Parámetros:** cerrar antes de implementar los tiempos de inactividad, duración máxima,
   intentos y recuperación administrativa; no atribuir números arbitrarios a una norma.

**Cerrar sesión no debe cortar energía, abrir la pinza, borrar fallas ni reiniciar el lote.**
Propuesta para la celda: revocar nuevas órdenes de arranque; si hay producción, solicitar parada
normal al terminar la pieza y mostrar el estado hasta su confirmación. Una sesión nueva debe
reidentificarse y emitir un arranque explícito. Esta política debe implementarse junto con la
vigencia de señales: hoy la v05 no detecta por sí sola que el panel se cerró o perdió conexión.

## 6. Implicancias para los modos y el mantenimiento

| Situación | Permiso de usuario | Condición y comportamiento propuestos |
|---|---|---|
| Entrar a automático | Producción | Selección aceptada, resguardos/estado conformes y nuevo arranque. Login no inicia ciclo. |
| Cambiar de automático a mantenimiento | Mantenimiento | Solicitar parada; completar/depositar pieza; confirmar reposo; preparar equipo seleccionado. No saltar directamente desde un movimiento. |
| Intervenir un robot | Mantenimiento | Preparación verificada con los demás equipos detenidos; después procedimiento físico de aislamiento. No permitir producción por ser el otro robot el intervenido. |
| Intervenir cinta | Mantenimiento | Definir si basta detenerla, despejar zona o retirar todas las piezas. Con accionamiento averiado no ordenar evacuación. |
| Preventivo programado | Mantenimiento | Usar preparación conocida para tarea/equipo disponible. |
| Correctivo con pieza sostenida o equipo averiado | Mantenimiento | Retener falla y bloquear retorno automático; procedimiento de recuperación según situación. Perfil no prueba que el recorrido sea ejecutable. |
| Programación manual | Habilitación técnica específica | Consola y condiciones del controlador. El login HMI no reemplaza hombre muerto ni velocidad reducida. |
| Volver a producción | Mantenimiento para cerrar intervención; producción para arrancar | Restituir, comprobar, cerrar acceso, rearme y nuevo arranque. Ningún cambio de perfil inicia movimientos. |

La distinción entre preventivo y correctivo pertenece al registro/procedimiento, no a una postura
universal distinta. Tampoco el modo mantenimiento acredita ausencia de tensión o soporte de ejes.
La aplicación detallada se mantiene en `c_prototipado/`, derivada de estos criterios.

## 7. Pantallas y navegación

**Propuesta funcional:** login → inicio según perfil → operación autorizada → confirmación/resultado.

| Pantalla | Contenido y acceso |
|---|---|
| Inicio de sesión | Credenciales, conexión, versión y acceso a estado básico/parada normal; sin mandos de arranque anónimos. |
| Resumen común | Usuario/perfil, modo solicitado/confirmado, estado, pieza/lote y causa de bloqueo. |
| Producción | Preparación, arranque, parada, continuación y alarmas operativas. |
| Mantenimiento | Selección de equipo/tarea, condiciones pendientes, posiciones, diagnóstico, servicio y restitución. |
| Administración | Cuentas, asignaciones, política de sesión y consulta de auditoría; sin mandos técnicos implícitos. |
| Alarmas y diagnóstico | Distinguir activa, reconocida y resuelta; sensores con valor, procedencia y vigencia. |

Una función sin permiso no se ofrece como acción; si el perfil sí tiene permiso pero faltan
condiciones, se muestra deshabilitada con causa concreta. La comprobación efectiva se repite al
recibir la solicitud, para cubrir cambios ocurridos desde que se dibujó la pantalla.
Evitar usar solo colores y pedir confirmación contextual en recuperaciones o cambios sensibles.

## 8. Contrato con la lógica de la celda

**Propuesta de separación:** interfaz → validación de sesión/permiso → solicitud por señal →
coordinador nativo → confirmación → indicación y registro. La interfaz no decide ni ejecuta la
secuencia de robots/cinta. El coordinador mantiene sus condiciones aunque el perfil sea administrador.

Las señales de identidad o perfil no son credenciales confiables por sí solas. En la simulación,
otra aplicación con acceso a la API puede cambiar parámetros de estación: el login de una HMI
propia **no protege todo RoboDK ni implementa el UAS real de ABB**. Deben documentarse los límites
y restringirse los escritores de órdenes dentro de la aplicación. Un identificador de solicitud
evita duplicados, pero no autentica al emisor.

La v05 ya tiene arranque/parada numerados e índice retenido. Usuarios, sesiones y permisos todavía
no existen. La pérdida de permiso se atiende entre subprogramas; no equivale a una interrupción
inmediata. El panel no debe simular que posee una protección que no está implementada.

## 9. Registros, validación y manual

Registrar fecha/hora, cuenta/perfil, operación, equipo, modo y estado previos, identificador de
solicitud, aceptación/rechazo y causa. No registrar contraseñas ni tokens. Conservar sucesión de
sesiones e intervenciones; distinguir la hora de solicitud de la confirmación nativa.

Criterios propuestos para pruebas:

- Probar cada casilla permitida y prohibida de la matriz, también desde el procesador de órdenes.
- Intentar nueva orden tras baja, cambio de perfil, sesión vencida o desconexión.
- Verificar que login, logout, rearme y cambio de usuario no arrancan ni abren la pinza.
- Verificar parada y continuación conservando pieza/lote y registro del usuario que solicitó cada acción.
- Probar administración sin permisos de movimiento; imposibilidad de eliminar la última cuenta
  administradora; recuperación documentada sin secretos fijos en el repositorio.
- Comprobar consistencia entre botón mostrado, autorización, modo confirmado y resultado nativo.

El futuro **`manual.md`** describirá instalación, login, perfiles, pantallas, producción,
mantenimiento, alarmas, recuperación y administración. Seguirá las funciones realmente probadas,
con capturas, versión compatible y limitaciones. Este concepto es investigación y criterio de
diseño; no sustituye ese manual de uso.

## 10. Qué hay que definir en nuestra celda

- ¿Qué permisos exactos corresponde implementar primero y cuáles quedan fuera del alcance?
- ¿Quién asigna perfiles y cómo se habilita la primera cuenta sin credenciales predeterminadas públicas?
- ¿Qué política de sesión y de relevo de operador se probará, incluida desconexión durante un ciclo?
- ¿Qué condiciones habilitan cada transición de modo y cada recuperación por equipo/tarea?
- ¿Cómo se valida una solicitud antes de escribir señales, y qué límites tiene frente a acceso directo a RoboDK?
- ¿Cómo se guardan credenciales/registros y cómo se recupera la administración?
- ¿Qué casos de aceptación respaldan cada sección del manual?

## 11. Referencias

- **[Lineamientos]** Cátedra de Robótica Industrial, UTN FRC, comisión 2LA1, 2026.
  [Lineamientos](../../a_requisitos/Lineamiento_Trabajo_Final_Robotica.pdf), requisitos según
  [00, §§2–6](00_requisitos_y_trazabilidad.md).
- **[Barrientos]** Barrientos, A.; Peñín, L. F.; Balaguer, C.; Aracil, R. *Fundamentos de Robótica*,
  McGraw-Hill, 1.ª ed. §9.1.2, p. 261; §9.3.2, pp. 273–276. Desarrollo previo en
  [01, §5](01_celula_robotizada.md#5-el-sistema-de-control-de-la-célula) y
  [07, §6](07_seguridad_y_normativa.md#6-medidas-de-seguridad).
- **[ABB-UAS]** ABB, FlexPendant Developer Support, *User Authorization System*, apartados
  Overview, Accessing UAS from custom applications y Grants and Groups.
  [Fuente oficial](https://developercenter.robotstudio.com/api/fpsdk/html/6460854b-d939-4bc1-b553-60420e6a227f.htm).
  HTML sin paginación ni edición visible en la página consultada.
- **[Siemens-UM]** Siemens, *Unified Basic Panels*, WinCC Unified V20, publicación 12/2024,
  Operating the Control Panel / Security / User management; apartados Current user y Users.
  [Fuente oficial](https://docs.tia.siemens.cloud/r/unified_basic_panels_enus_20/operating-the-control-panel/security/user-management).
  HTML sin paginación.
- **[OWASP-A]** OWASP Cheat Sheet Series, *Authorization Cheat Sheet*, Recommendations:
  Enforce Least Privileges, Deny by Default, Validate the Permissions on Every Request,
  Implement Appropriate Logging y Create Unit and Integration Test Cases for Authorization Logic.
  [Fuente](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html).
  HTML sin paginación; guía de software, no norma de seguridad funcional.
- **[OWASP-P]** OWASP Cheat Sheet Series, *Password Storage Cheat Sheet*, Introduction y
  Methods for Enhancing Password Storage / Salting.
  [Fuente](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
  HTML sin paginación. Consulta de fuentes web: 2026-11-06.
