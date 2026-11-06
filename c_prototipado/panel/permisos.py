"""Matriz de operaciones por perfil (concepto 09, §4). Un perfil no hereda permisos de otro."""
from enum import Enum

PRODUCCION = "produccion"
MANTENIMIENTO = "mantenimiento"
ADMINISTRADOR = "administrador"
PERFILES = (PRODUCCION, MANTENIMIENTO, ADMINISTRADOR)


class Op(Enum):
    ARRANQUE = "Arranque"
    PARADA = "Parada normal"
    PREPARAR_MODO = "Preparar modo"
    REGRESAR_MODO = "Regresar a producción"
    ENTRADA_SIMULADA = "Entrada simulada"
    ADMINISTRAR = "Administrar cuentas"


MATRIZ = {
    PRODUCCION: {Op.ARRANQUE, Op.PARADA},
    MANTENIMIENTO: {Op.PARADA, Op.PREPARAR_MODO, Op.REGRESAR_MODO, Op.ENTRADA_SIMULADA},
    ADMINISTRADOR: {Op.PARADA, Op.ADMINISTRAR},
}

MODOS = {
    1: "IRB 1200 y pinza",
    2: "CRB 1300",
    3: "Ambos robots",
    4: "Cinta",
    5: "Servicio de antorcha",
    6: "Correctivo sin movimiento",
}
TIPOS_INTERVENCION = ("Preventivo", "Correctivo")
ENTRADAS_SIMULADAS = ("PERMISO_OPERACION", "IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE")


def permitido(perfil, operacion):
    return operacion in MATRIZ.get(perfil, ())
