"""Actualiza el programa Sold_Par_Cordones y sus targets en la estación abierta.

Se usa cuando la estación ya tiene cargados a mano los eventos de simulación
(Evento_Tomar_Pieza, Evento_Soltar_Pieza): volver a correr construir_celda.py
los borraría. Este script solo:
    - crea o actualiza los targets de soldadura (programa_soldadura.crear_targets);
    - vacía y vuelve a cargar las instrucciones de Sold_Par_Cordones.
Los programas que llaman a Sold_Par_Cordones lo hacen por nombre, así que no
hace falta tocarlos.

Con --reiniciar-lote, además deja la simulación en el estado de inicio de lote:
estatores sobre la banda, cinta en el origen, robots y pinza en reposo. Es una
herramienta de desarrollo para repetir pruebas; no forma parte del ciclo.

Uso:  C:\\RoboDK\\Python-Embedded\\python.exe actualizar_soldadura.py [--reiniciar-lote]
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, r"C:\RoboDK\Python")

import parametros_celda as P                                            # noqa: E402
import programa_soldadura                                               # noqa: E402
from robodk.robolink import (Robolink, ITEM_TYPE_STATION, ITEM_TYPE_ROBOT,  # noqa: E402
                             ITEM_TYPE_TOOL, ITEM_TYPE_FRAME, ITEM_TYPE_PROGRAM,
                             ITEM_TYPE_OBJECT, ITEM_TYPE_TARGET)
from robodk.robomath import transl                                      # noqa: E402

NOMBRE_ESTACION = "Celda_Soldadura_Estator_Grupo4"
ARCHIVO_RDK = os.path.normpath(os.path.join(AQUI, "..", "Celda_Soldadura_Estator_Grupo4_v02.rdk"))

RDK = Robolink()
estacion = RDK.Item(NOMBRE_ESTACION, ITEM_TYPE_STATION)
if not estacion.Valid():
    sys.exit(f"No está abierta la estación {NOMBRE_ESTACION}")
RDK.setActiveStation(estacion)

crb = RDK.Item("ABB CRB 1300-10/1.15", ITEM_TYPE_ROBOT)
antorcha = RDK.Item("Antorcha_TIG", ITEM_TYPE_TOOL)
f_sold = RDK.Item("Frame_Soldadura", ITEM_TYPE_FRAME)
prog = RDK.Item(programa_soldadura.NOMBRE_PROGRAMA, ITEM_TYPE_PROGRAM)

# --- Programa de soldadura -----------------------------------------------------
targets = programa_soldadura.crear_targets(RDK, crb, f_sold)
while prog.InstructionCount() > 0:
    prog.InstructionDelete(0)
programa_soldadura.cargar_programa(prog, targets, antorcha, f_sold, "Sold_Ir_Reposo")
print(f"{prog.Name()}: {prog.InstructionCount()} instrucciones")

# --- Reinicio del lote (opcional) ------------------------------------------------
if "--reiniciar-lote" in sys.argv:
    # Los estatores vuelven a Frame_Banda con la misma pose relativa que les da
    # construir_celda.py: el estator k queda k pasos antes de la toma.
    f_banda = RDK.Item("Frame_Banda", ITEM_TYPE_FRAME)
    x_toma, y_toma = P.CINTA_TOMA
    x_base = x_toma + 250.0 - P.CINTA_LARGO
    y_base = y_toma - P.CINTA_EJE_Y_REL
    for k in range(P.LOTE):
        e = RDK.Item(f"Estator_{k + 1}", ITEM_TYPE_OBJECT)
        e.setParent(f_banda)
        e.setPose(transl(x_toma - k * P.CINTA_PASO - x_base, y_toma - y_base, 0))
    for nombre in ("Man_Reposo", "Sold_Reposo", "Pinza_Abierta", "Cinta_Posicion_1"):
        t = RDK.Item(nombre, ITEM_TYPE_TARGET)
        t.getLink().setJoints(t.Joints())
    print("Lote reiniciado: estatores en la banda, equipos en reposo")

RDK.setSimulationSpeed(1)
estacion.Save(ARCHIVO_RDK)
print("Estación guardada en", ARCHIVO_RDK)
