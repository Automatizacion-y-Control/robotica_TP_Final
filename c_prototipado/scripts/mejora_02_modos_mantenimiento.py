"""Mejora 02: modos de operación y mantenimiento. Genera la v04 a partir de la v03.

Aplica los requisitos de c_prototipado/modos_y_mantenimiento.md (§10):
    1. Pasillo de mantenimiento del lado sur, afuera: la cara sur del cerramiento
       se acerca a la cinta y se arma con paneles desmontables, para sacar la
       banda por ese costado.
    2. Accionamiento de la cinta en el extremo oeste, fuera de la celda, con su
       resguardo.
    3. Puntos de aislamiento con candado fuera de la celda (tablero LOTO).
    4. Panel de operador y pulsadores de emergencia (panel, puerta, entrada y
       salida de la cinta).
    5. Gabinetes de los controladores, fuente TIG y argón, fuera de la celda.
    6. Posiciones de mantenimiento de cada robot y programa de parada de ciclo.

Se parte de la v03 guardada para conservar los eventos de simulación cargados
a mano (tomar, soltar y reposición del lote). El ciclo de producción no cambia.

Uso:  C:\\RoboDK\\Python-Embedded\\python.exe mejora_02_modos_mantenimiento.py
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, r"C:\RoboDK\Python")

import parametros_celda as P                                               # noqa: E402
from robodk.robolink import (Robolink, ITEM_TYPE_STATION, ITEM_TYPE_ROBOT,  # noqa: E402
                             ITEM_TYPE_FRAME, ITEM_TYPE_OBJECT, ITEM_TYPE_TARGET,
                             ITEM_TYPE_PROGRAM, ITEM_TYPE_TOOL, INSTRUCTION_COMMENT,
                             INSTRUCTION_CALL_PROGRAM)
from robodk.robomath import transl, rotz, pi                               # noqa: E402

RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
MODELOS = os.path.join(RAIZ, "modelos")
ARCHIVO_V03 = os.path.join(RAIZ, "Celda_Soldadura_Estator_Grupo4_v03.rdk")
ARCHIVO_V04 = os.path.join(RAIZ, "Celda_Soldadura_Estator_Grupo4_v04.rdk")
NOMBRE_V03 = "Celda_Soldadura_Estator_Grupo4_v03"
NOMBRE_V04 = "Celda_Soldadura_Estator_Grupo4_v04"

# Colores RGBA por función: seguridad en amarillo/naranja/rojo, servicios en gris.
AMARILLO = [0.95, 0.85, 0.10, 1.0]
AMARILLO_PISO = [0.95, 0.85, 0.10, 0.45]
NARANJA_PANEL = [0.95, 0.55, 0.10, 0.35]
ROJO = [0.85, 0.10, 0.10, 1.0]
GRIS = [0.55, 0.57, 0.60, 1.0]
GRIS_OSCURO = [0.25, 0.27, 0.30, 1.0]

RDK = Robolink()


def item(nombre, tipo=None):
    it = RDK.Item(nombre, tipo) if tipo is not None else RDK.Item(nombre)
    if not it.Valid():
        raise RuntimeError(f"No se encontró {nombre} en la estación")
    return it


def borrar(nombre, tipo=None):
    it = RDK.Item(nombre, tipo) if tipo is not None else RDK.Item(nombre)
    if it.Valid():
        it.Delete()


def agregar(archivo, padre, nombre, pose=None, color=None):
    it = RDK.AddFile(os.path.join(MODELOS, archivo), padre)
    it.setName(nombre)
    if pose is not None:
        it.setPose(pose)
    if color:
        it.setColor(color)
    return it


def comentario(prog, texto):
    prog.RunInstruction(texto, INSTRUCTION_COMMENT)


def llamar(prog, nombre):
    prog.RunInstruction(nombre, INSTRUCTION_CALL_PROGRAM)


# ===========================================================================
# 0. Estación v04 a partir del archivo de la v03
# ===========================================================================
for nombre in (NOMBRE_V03, NOMBRE_V04):
    abierta = RDK.Item(nombre, ITEM_TYPE_STATION)
    while abierta.Valid():
        abierta.Delete()
        abierta = RDK.Item(nombre, ITEM_TYPE_STATION)
estacion = RDK.AddFile(ARCHIVO_V03)
estacion.setName(NOMBRE_V04)
RDK.setActiveStation(estacion)
RDK.Render(False)

f_celda = item("Frame_Celda", ITEM_TYPE_FRAME)
f_cerr = item("Frame_Cerramiento", ITEM_TYPE_FRAME)
irb = item("ABB IRB 1200-7/0.7", ITEM_TYPE_ROBOT)
crb = item("ABB CRB 1300-10/1.15", ITEM_TYPE_ROBOT)

# ===========================================================================
# 1. Cerramiento: cara sur desmontable y pasillo de mantenimiento
# ===========================================================================
for nombre in ("Cerramiento_Estructura", "Cerramiento_Paneles", "Cortina_Luz_Entrada", "Cortina_Luz_Salida"):
    borrar(nombre, ITEM_TYPE_OBJECT)

agregar("cerramiento_estructura_v04.stl", f_cerr, "Cerramiento_Estructura", color=[0.20, 0.22, 0.25, 1.0])
agregar("cerramiento_paneles_v04.stl", f_cerr, "Cerramiento_Paneles", color=[0.55, 0.70, 0.85, 0.25])
agregar("paneles_desmontables_sur.stl", f_cerr, "Paneles_Desmontables_Sur", color=NARANJA_PANEL)
agregar("paneles_desmontables_manijas.stl", f_cerr, "Paneles_Desmontables_Manijas", color=GRIS_OSCURO)
agregar("pasillo_mantenimiento.stl", f_celda, "Pasillo_Mantenimiento", color=AMARILLO_PISO)
# Cortinas de luz en los túneles de la cinta, con la cara sur nueva.
agregar("cortina_luz_cinta_v04.stl", f_cerr, "Cortina_Luz_Entrada", transl(P.CERR_X[0] - 30.0, 0, 0), AMARILLO)
agregar("cortina_luz_cinta_v04.stl", f_cerr, "Cortina_Luz_Salida", transl(P.CERR_X[1] + 30.0, 0, 0), AMARILLO)

# ===========================================================================
# 2. Accionamiento de la cinta, afuera
# ===========================================================================
ax, ay = P.V4_ACCIONAMIENTO
agregar("accionamiento_cinta.stl", f_celda, "Accionamiento_Cinta", transl(ax, ay, 0), GRIS)
agregar("accionamiento_cinta_resguardo.stl", f_celda, "Accionamiento_Cinta_Resguardo",
        transl(ax, ay, 0), [0.95, 0.85, 0.10, 0.40])

# ===========================================================================
# 3 y 4. Aislamiento, panel de operador y paradas de emergencia
# ===========================================================================
lx, ly = P.V4_TABLERO_LOTO
agregar("tablero_loto.stl", f_celda, "Tablero_LOTO", transl(lx, ly, 0), GRIS)
agregar("tablero_loto_manijas.stl", f_celda, "Tablero_LOTO_Seccionadores", transl(lx, ly, 0), ROJO)

px, py = P.V4_PANEL_OPERADOR
agregar("panel_operador.stl", f_celda, "Panel_Operador", transl(px, py, 0), GRIS_OSCURO)
agregar("parada_emergencia_hongo.stl", f_celda, "Parada_Emergencia_Panel",
        transl(px, py - 120.0, 0), ROJO)                    # hongo sobre la consola del panel

for nombre, (ex, ey) in P.V4_PARADAS_EMERGENCIA.items():
    agregar("parada_emergencia_poste.stl", f_celda, nombre + "_Poste", transl(ex, ey, 0), AMARILLO)
    agregar("parada_emergencia_hongo.stl", f_celda, nombre, transl(ex, ey, 0), ROJO)

# ===========================================================================
# 5. Equipos auxiliares, afuera de la cara norte
# ===========================================================================
gy = P.V4_GABINETES_Y
agregar("gabinete_controlador.stl", f_celda, "Controlador_IRB1200", transl(-800.0, gy, 0), GRIS)
agregar("gabinete_controlador.stl", f_celda, "Controlador_CRB1300", transl(-100.0, gy, 0), GRIS)
agregar("fuente_tig.stl", f_celda, "Fuente_TIG", transl(500.0, gy, 0), [0.15, 0.35, 0.70, 1.0])
agregar("cilindro_argon.stl", f_celda, "Cilindro_Argon", transl(850.0, gy + 200.0, 0), [0.10, 0.55, 0.25, 1.0])

# ===========================================================================
# 6. Posiciones de mantenimiento y parada de ciclo
# ===========================================================================
def target_articular(nombre, robot, juntas):
    t = RDK.AddTarget(nombre, f_celda, robot)
    t.setAsJointTarget()
    t.setJoints(juntas)
    return t


t_man_mant = target_articular("Man_Mantenimiento", irb, P.IRB_MANTENIMIENTO)
t_sold_mant = target_articular("Sold_Mantenimiento", crb, P.CRB_MANTENIMIENTO)

for nombre, robot, herramienta, reposo, t_mant, equipo in (
        ("Man_Ir_Mantenimiento", irb, "TCP_Pinza", "Man_Reposo", t_man_mant, "IRB 1200"),
        ("Sold_Ir_Mantenimiento", crb, "Antorcha_TIG", "Sold_Reposo", t_sold_mant, "CRB 1300")):
    prog = RDK.AddProgram(nombre, robot)
    comentario(prog, f"Lleva el {equipo} a su posición de mantenimiento: brazo plegado, herramienta hacia la puerta")
    comentario(prog, "Se ejecuta en modo manual, con la celda detenida y nadie dentro")
    prog.setPoseTool(item(herramienta, ITEM_TYPE_TOOL))
    prog.setSpeed(P.V_APROX, P.V_ARTICULAR / 2)               # traslado lento: el modo es manual
    prog.addMoveJ(item(reposo, ITEM_TYPE_TARGET))
    prog.addMoveJ(t_mant)
    comentario(prog, f"A continuación: bloqueo y etiquetado (LOTO) del {equipo}, ver modos_y_mantenimiento.md §7")

parada = RDK.AddProgram("Parada_Ciclo", irb)
comentario(parada, "Parada de ciclo: se llama al terminar una pieza; deja la celda en un estado conocido")
parada.setDO("ARCO_TIG", 0)
llamar(parada, "Sold_Ir_Reposo")
llamar(parada, "Man_Ir_Reposo")
comentario(parada, "La cinta queda detenida en su posición; desde acá se puede elegir otro modo")

# ===========================================================================
# 7. Estado inicial y guardado
# ===========================================================================
for nombre in ("Man_Reposo", "Sold_Reposo", "Pinza_Abierta", "Cinta_Posicion_1"):
    t = item(nombre, ITEM_TYPE_TARGET)
    t.getLink().setJoints(t.Joints())
RDK.setSimulationSpeed(1)
RDK.Render(True)
estacion.Save(ARCHIVO_V04)
print("Estación v04 guardada en", ARCHIVO_V04)
