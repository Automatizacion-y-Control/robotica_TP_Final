# Prototipado

Diseño, construcción y verificación de la celda en RoboDK 6.1.1.

## Versiones de la celda

| Versión | Cambio principal |
|---|---|
| v01 | Antecedente: posicionador MTD 250 y cilindro de 6 cordones |
| v02 | Manipulador y soldador sobre el paquete de estator; salida por pallet |
| v03 | Cinta pasante: la misma cinta trae y saca las piezas |
| v04 | Disposición y posiciones para mantenimiento |
| **v05** | **Versión actual:** coordinador, modos, paradas, recuperación, sensores y panel embebido |

Cada versión se genera a partir del archivo de la anterior, porque los eventos de simulación no se pueden
crear desde la API. `Componentes_Grupo4.rdk` es la estación de trabajo con los componentes.

## Carpetas

| Carpeta | Contenido |
|---|---|
| [docs/](docs/) | Definición de la celda, mejoras, modos y mantenimiento, panel y sensores, manual e informe |
| [docs/informe/](docs/informe/) | Fuentes del informe técnico: texto, diseño e imágenes |
| [docs/antecedentes/](docs/antecedentes/) | Informe de la entrega anterior |
| [panel/](panel/) | Código del panel de operador, que se embebe en la v05 al generarla |
| [scripts/](scripts/) | Parámetros, construcción de cada versión, ensayos y mediciones |
| [verificaciones/](verificaciones/) | Resultados de los ensayos |
| [modelos/](modelos/) | Modelos 3D propios y de la biblioteca de RoboDK |
| [imagenes/](imagenes/) | Capturas de la celda y del panel |
| [referencias/](referencias/) | Panel de la v01 y ejemplo oficial de control de flujo |

## Cómo usar la v05

- **Sin panel:** doble clic en `Programa_Principal`.
- **Con panel:** doble clic en `Coordinador_Panel` y después en `Abrir_Panel_Operador`. Ver el
  [manual](docs/manual.md).

Al cerrar RoboDK, no guardar: se conservaría el estado de la simulación.

## Regenerar y ensayar

Con RoboDK abierto como administrador y una sola estación abierta, desde `scripts/`:

```text
C:\RoboDK\Python-Embedded\python.exe mejora_03_coordinacion.py --puerto 20500
C:\RoboDK\Python-Embedded\python.exe verificar_celda.py --colisiones --con-pieza --estacion Celda_Soldadura_Estator_Grupo4_v05
C:\RoboDK\Python-Embedded\python.exe verificar_modos_v05.py --puerto 20500
C:\RoboDK\Python-Embedded\python.exe verificar_coordinacion_v05.py --puerto 20500
C:\RoboDK\Python-Embedded\python.exe verificar_paradas_v05.py --puerto 20500
C:\RoboDK\Python-Embedded\python.exe verificar_panel.py --puerto 20500
C:\RoboDK\Python-Embedded\python.exe medir_ciclo_v05.py --puerto 20500
```

Los bancos trabajan sobre la estación o una copia y no guardan cambios; se corren de a uno, con el panel cerrado.
Después de regenerar, hay que copiar la estación a [d_presentacion](../d_presentacion/).

## Pendiente

- Detención intermitente en el `MoveC` entre cordones, sin causa identificada.
- Repetir la batería completa sobre la versión final.
- Forzado de sensores.
