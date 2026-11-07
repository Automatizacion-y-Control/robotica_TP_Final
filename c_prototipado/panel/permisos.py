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
    EMERGENCIA = "Pulsador de emergencia"
    RESGUARDO = "Cortina o puerta"
    REARME = "Rearme"
    RECUPERAR = "Recuperación"
    REINICIAR = "Reinicio de lote"
    OBJETIVO = "Objetivo de piezas"


MATRIZ = {
    PRODUCCION: {Op.ARRANQUE, Op.PARADA, Op.EMERGENCIA, Op.RESGUARDO, Op.REARME, Op.OBJETIVO},
    MANTENIMIENTO: {Op.PARADA, Op.PREPARAR_MODO, Op.REGRESAR_MODO, Op.ENTRADA_SIMULADA, Op.EMERGENCIA,
                    Op.RESGUARDO, Op.REARME, Op.RECUPERAR, Op.REINICIAR},
    ADMINISTRADOR: {Op.PARADA, Op.ADMINISTRAR, Op.EMERGENCIA, Op.RESGUARDO},
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
RESGUARDOS = {"CORTINA_ENTRADA_SIM": 2, "CORTINA_SALIDA_SIM": 2, "PUERTA_ABIERTA_SIM": 3}
CAUSAS_PARO = {1: "Emergencia", 2: "Cortina de luz", 3: "Puerta abierta"}
OBJETIVO_MAXIMO = 9999


def permitido(perfil, operacion):
    return operacion in MATRIZ.get(perfil, ())
