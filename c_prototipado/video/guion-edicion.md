# Guion de edición del video

Fecha: 2026-11-07. Método de los videos de los TP: transcripción local con Whisper, cortes en los silencios
medidos con FFmpeg, placas con PIL y render con FFmpeg. **Estado: aprobado por el usuario el 2026-11-07 (punto de control 1), con las decisiones registradas abajo.**

Criterios acordados: se cortan las fallas, los arranques repetidos y las pausas de más de 5 s; las pausas cortas
quedan. Se corta el final después de la última palabra. Pantalla dividida con los **programas reales de RoboDK**
cuando se habla de ellos. Portada y placa final sobrias, sin música. Salida H.264 1080p, lo más chica posible.

## Crudo

| Archivo | Duración | Formato | Voz |
|---|---|---|---|
| `crudo_2026-11-07.mp4` (antes `d_presentacion/2026-11-07_15-13-01_pantalla.mp4`; no se versiona) | 9:04,9 | 1920×1080, 30 fps, H.264/AAC, 123 MB | −25,8 LUFS |

Grabación de pantalla: el informe en PDF, la celda en RoboDK, el panel y la soldadura en primer plano.

Transcripción local con Whisper large-v3-turbo en `trabajo/transcripcion.*` (172 s en CPU). Es auxiliar: tiene
errores de reconocimiento conocidos, como «TIP» por TIG, «Casal» por Casali, «Vera González» por Vera Gonzalo,
«Robe de K» por RoboDK, «TIC/MIC» por TIG/MIG y «realme» por «rearme». «Un movimiento que se obcede» (6:18) no se
entiende: probablemente nombra el movimiento circular. El «¡Gracias!» de
8:55 es una alucinación sobre el silencio final.

No hay pausas de más de 5 s: la más larga es de 3,9 s, en 7:05,2 (`silencedetect`, −25 dB).

## Registro de cortes

| N.º | Crudo | Tipo | Qué pasa | Acción |
|---|---|---|---|---|
| 1 | 0:00,0–0:01,2 | Pausa | Silencio inicial | Cortar |
| 2 | 4:40,1–4:47,0 | Falla | «después uno lo puede… y acá puse mal,»: se equivoca al tipear la clave y la vuelve a escribir | **Queda** (decisión 2) |
| 3 | 8:51,6–9:04,9 | Pausa | Silencio final, después de «nos estamos viendo» | Cortar |

## Propuesta

| Tramo del crudo | Contenido | Imagen |
|---|---|---|
| — | Portada, 5 s | Placa: UTN FRC, Robótica Industrial, título, Grupo 4, integrantes, docentes, 2LA1 · 2026 |
| 0:01,2–0:22,2 | Presentación del grupo y del trabajo | Grabación completa (portada del informe) |
| 0:22,2–0:58,4 | Qué se fabrica: el motor, el paquete de estator antes del bobinado, 4 cordones | Grabación completa (figura del motor en el informe) |
| 0:58,4–1:20,9 | Cómo evolucionó: de una celda sencilla a la definitiva | Grabación completa |
| 1:20,9–2:37,3 | Equipos, seguridad y mantenimiento | Grabación completa |
| 2:37,3–3:14,9 | Modos, lotes de 4, programa principal y coordinador | **Dividida:** `Programa_Principal` |
| 3:14,9–4:08,9 | El ciclo de una pieza: fases, señales, cinta, manipulador, soldador | **Dividida:** `Ciclo_Pieza_1` |
| 4:08,9–5:37,6 | Panel: inicio de sesión (con la clave mal tipeada), entradas simuladas, producción, pedido de 12 piezas, arranque | Grabación completa |
| 5:37,6–6:22,8 | Soldadura: 4 cordones, 5 mm/s, TIG, MoveL y MoveC | **Dividida:** `Sold_Par_Cordones` |
| 6:22,8–6:46,3 | Depósito: posición de pieza correcta o de retrabajo; avanza el estator 2 | **Dividida:** `Man_Depositar_Cinta` y `Man_Depositar_Retrabajo` |
| 6:46,3–7:56,4 | Secuencia acelerada: reposo, cordón, giro; después el paquete pasa al bobinado; el panel contando | Grabación completa |
| 7:56,4–8:13,8 | Emergencia, rearme y pieza a revisar por calidad | **Dividida:** `Recuperar_Pieza` (extracto) |
| 8:13,8–8:51,6 | Fin del lote y cierre | Grabación completa |
| — | Placa final, 3 s | Grupo 4 · Robótica Industrial · UTN FRC · 2026 |

Duración estimada: **unos 8:58** (8:50,4 del crudo y 8 s de placas).

**Pantalla dividida:** la grabación a 1280×720, a la izquierda; a la derecha, una tarjeta de 560 px de ancho con las
instrucciones del programa, tal como están en la v05 (comentarios, `MoveJ`, `MoveL`, `MoveC`, velocidades y señales).
En los programas largos se muestra el tramo del que se habla y se marca con «…» lo que se omite. Se resalta la línea
que se nombra; por ejemplo, `Establecer velocidad (5.0 mm/s)` y el `MoveC` en la soldadura.

## Decisiones del usuario (2026-11-07)

1. **«Somos el grupo 10» (0:04):** es un error de Whisper; se dice «Grupo 4». Queda como está.
2. **Clave mal tipeada (4:40–4:47):** no se corta, porque muestra que el panel rechaza una clave incorrecta.
3. **Coordinador y Python (3:00):** la tarjeta de `Programa_Principal` lleva la nota «El panel (Python) solo envía
   solicitudes; Coordinador_Panel, nativo de RoboDK, decide y llama a los programas».

## Salida

`d_presentacion/Video_Celda_Soldadura_Grupo4.mp4`: H.264 1080p, 30 fps, `-tune animation`, CRF a ajustar sobre la vista previa,
AAC 96 kb/s y voz normalizada a −16 LUFS. Primero se arma una vista previa a 540p para revisar.
