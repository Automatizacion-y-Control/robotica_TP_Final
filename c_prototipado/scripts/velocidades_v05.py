"""Perfil de velocidades de la v05: cada tramo va a la velocidad que necesita.

Solo el cordón y los últimos milímetros junto a la pieza van lentos. Los programas vienen de
versiones anteriores, así que se reemplazan sus instrucciones de velocidad por índice.
"""
from robodk.robolink import ITEM_TYPE_PROGRAM

V_CORDON = 5.0        # mm/s; dato de referencia a confirmar con ensayos de soldadura
V_JUNTO_PIEZA = 100.0  # entrada al agujero, apoyo y último tramo antes del cordón
V_CERCA = 200.0       # salidas y rodeos cerca de la pieza
V_ACERCAMIENTO = 300.0  # desde la zona libre hasta el punto de aproximación
V_TRASLADO = 1000.0   # traslados libres
V_ARTICULAR = 150.0   # °/s, movimientos MoveJ

# (programa, índice, velocidad lineal): reemplazos de instrucciones de velocidad existentes.
REEMPLAZOS = (
    ("Man_Ir_Reposo", 2, V_TRASLADO),
    ("Man_Tomar_Cinta", 4, V_TRASLADO),
    ("Man_Tomar_Cinta", 9, V_JUNTO_PIEZA),
    ("Man_Presentar_Lado1", 3, V_TRASLADO),
    ("Man_Presentar_Lado1", 5, V_JUNTO_PIEZA),
    ("Man_Presentar_Lado2", 5, V_JUNTO_PIEZA),
    ("Man_Depositar_Cinta", 5, V_CERCA),
    ("Man_Depositar_Cinta", 8, V_TRASLADO),
    ("Man_Depositar_Cinta", 13, V_JUNTO_PIEZA),
    ("Sold_Ir_Reposo", 2, V_TRASLADO),
    ("Sold_Par_Cordones", 4, V_TRASLADO),
    ("Sold_Par_Cordones", 8, V_ACERCAMIENTO),
    ("Sold_Par_Cordones", 14, V_CORDON),
    ("Sold_Par_Cordones", 17, V_JUNTO_PIEZA),
    ("Sold_Par_Cordones", 25, V_CORDON),
    ("Sold_Par_Cordones", 28, V_CERCA),
)
# (índice de la instrucción antes de la cual se inserta, velocidad), de atrás hacia adelante.
INSERCIONES_SOLDADURA = (
    (30, V_ACERCAMIENTO),  # retiro libre hasta la zona de aproximación
    (22, V_JUNTO_PIEZA),   # entrada al cordón B
    (20, V_CERCA),         # rodeo en arco a radio constante
    (11, V_JUNTO_PIEZA),   # entrada al cordón A
)


def _reemplazar(programa, indice, lineal):
    assert programa.Instruction(indice)[1] == 2, (programa.Name(), indice)
    programa.InstructionDelete(indice)
    programa.InstructionSelect(indice - 1)
    programa.setSpeed(lineal, V_ARTICULAR)


def ajustar_velocidades(rdk):
    for nombre, indice, lineal in REEMPLAZOS:
        _reemplazar(rdk.Item(nombre, ITEM_TYPE_PROGRAM), indice, lineal)
    soldadura = rdk.Item("Sold_Par_Cordones", ITEM_TYPE_PROGRAM)
    for indice, lineal in INSERCIONES_SOLDADURA:
        soldadura.InstructionSelect(indice - 1)
        soldadura.setSpeed(lineal, V_ARTICULAR)
    soldadura.InstructionSelect(soldadura.InstructionCount() - 1)
