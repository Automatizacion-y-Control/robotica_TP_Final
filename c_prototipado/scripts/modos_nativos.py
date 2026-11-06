"""Construcción de solicitudes nativas de mantenimiento y servicio para v05."""
from robodk.robolink import (ITEM_TYPE_PROGRAM, ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET,
                            ITEM_TYPE_TOOL, INSTRUCTION_INSERT_CODE, INSTRUCTION_CALL_PROGRAM,
                            INSTRUCTION_COMMENT)

INICIALES_MODOS = {
    "MODO_ID": 0, "MODO_ACK": 0, "MODO_SOLICITADO": 0, "MODO_CONFIRMADO": 0,
    "MODO_OBJETIVO": 0, "MODO_EN_TRANSICION": 0, "MODO_RESULTADO": 0,
    "SENSORES_VALIDOS": 0, "PIEZA_SUJETA_SENSOR": 0,
    "IRB_EN_REPOSO": 0, "CRB_EN_REPOSO": 0, "IRB_EN_MANT": 0, "CRB_EN_MANT": 0,
    "CRB_EN_SERVICIO": 0, "CINTA_DETENIDA": 0,
    "IRB_DISPONIBLE": 0, "CRB_DISPONIBLE": 0, "CINTA_DISPONIBLE": 0,
    "CONF_RESTITUCION": 0,
}


def instalar(rdk):
    crb = rdk.Item("ABB CRB 1300-10/1.15", ITEM_TYPE_ROBOT)
    servicio = rdk.AddProgram("Preparar_Servicio_Antorcha", crb)
    servicio.RunInstruction("Preparación sin pausa: acceso y aislamiento se tramitan después de posicionar", INSTRUCTION_COMMENT)
    servicio.setPoseTool(rdk.Item("Antorcha_TIG", ITEM_TYPE_TOOL))
    servicio.setSpeed(100, 30)
    servicio.addMoveJ(rdk.Item("Sold_Reposo", ITEM_TYPE_TARGET))
    servicio.addMoveJ(rdk.Item("Serv_Cambio_Tungsteno", ITEM_TYPE_TARGET))

    def programa(nombre):
        return rdk.AddProgram(nombre)

    def code(p, s):
        p.RunInstruction(s, INSTRUCTION_INSERT_CODE)

    def call(p, s):
        p.RunInstruction(s, INSTRUCTION_CALL_PROGRAM)

    def dentro(p, condiciones, acciones):
        for c in condiciones:
            code(p, "IF " + c)
        acciones()
        for _ in condiciones:
            code(p, "END")

    p = programa("Atender_Solicitud_Modo")
    code(p, "IF MODO_ID != MODO_ACK")
    code(p, "MODO_ID_CAPTURADO = MODO_ID")
    code(p, "MODO_CAPTURADO = MODO_SOLICITADO")
    p.setDO("MODO_RESULTADO", 2)  # rechazo por condiciones o selección desconocida
    p.setDO("MODO_DESDE_AUTO", 0)
    # Pedir mantenimiento durante producción solicita primero la parada normal.
    code(p, "IF AUTO_ACTIVO == 1")
    call(p, "Parada_Ciclo")
    p.setDO("AUTO_ACTIVO", 0)
    p.setDO("ESTADO_CONTROL", 2)
    p.setDO("MODO_DESDE_AUTO", 1)
    p.setDO("MODO_RESULTADO", 3)  # parada realizada: reenviar desde reposo confirmado
    code(p, "END")

    comunes = ["MODO_DESDE_AUTO == 0", "PERMISO_OPERACION == 1", "SENSORES_VALIDOS == 1",
               "PIEZA_SUJETA_SENSOR == 0", "CINTA_DETENIDA == 1",
               "IRB_DISPONIBLE == 1", "CRB_DISPONIBLE == 1",
               "MODO_EN_TRANSICION == 0"]
    # No se transita directamente de una postura de mantenimiento a otra.
    for modo, llamadas in ((1, ["Man_Ir_Mantenimiento"]), (2, ["Sold_Ir_Mantenimiento"]),
                           (3, ["Man_Ir_Mantenimiento", "Sold_Ir_Mantenimiento"]),
                           (4, []), (5, ["Preparar_Servicio_Antorcha"])):
        condiciones = comunes + ["MODO_CONFIRMADO == 0", "IRB_EN_REPOSO == 1",
                                  "CRB_EN_REPOSO == 1", f"MODO_CAPTURADO == {modo}"]
        # Preparar cinta no la mueve: admite diagnóstico con accionamiento averiado.
        def preparar(modo=modo, llamadas=llamadas):
            p.setDO("ARCO_TIG", 0)
            p.setDO("MODO_EN_TRANSICION", 1)
            p.setDO("ESTADO_CONTROL", 4)
            for n in llamadas:
                call(p, n)
            p.setDO("MODO_OBJETIVO", modo)
            p.setDO("MODO_RESULTADO", 1)
        dentro(p, condiciones, preparar)

    # Retorno solo desde posturas conocidas y después de restitución explícita.
    for modo, posiciones, llamadas in (
        (1, ["IRB_EN_MANT == 1", "CRB_EN_REPOSO == 1"], ["Man_Ir_Reposo"]),
        (2, ["IRB_EN_REPOSO == 1", "CRB_EN_MANT == 1"], ["Sold_Ir_Reposo"]),
        (3, ["IRB_EN_MANT == 1", "CRB_EN_MANT == 1"], ["Sold_Ir_Reposo", "Man_Ir_Reposo"]),
        (4, ["IRB_EN_REPOSO == 1", "CRB_EN_REPOSO == 1"], []),
        (5, ["IRB_EN_REPOSO == 1", "CRB_EN_SERVICIO == 1"], ["Sold_Servicio_Antorcha"]),
    ):
        def regresar(llamadas=llamadas):
            p.setDO("MODO_EN_TRANSICION", 1)
            p.setDO("ESTADO_CONTROL", 5)
            for n in llamadas:
                call(p, n)
            p.setDO("MODO_OBJETIVO", 0)
            p.setDO("MODO_RESULTADO", 1)
            p.setDO("CONF_RESTITUCION", 0)
        dentro(p, comunes + ["MODO_CAPTURADO == 0", f"MODO_CONFIRMADO == {modo}",
                              "CONF_RESTITUCION == 1"] + posiciones, regresar)
    code(p, "MODO_ACK = MODO_ID_CAPTURADO")
    code(p, "END")

    p = programa("Confirmar_Posicion_Modo")
    for modo, posiciones in (
        (0, ["IRB_EN_REPOSO == 1", "CRB_EN_REPOSO == 1"]),
        (1, ["IRB_EN_MANT == 1", "CRB_EN_REPOSO == 1"]),
        (2, ["IRB_EN_REPOSO == 1", "CRB_EN_MANT == 1"]),
        (3, ["IRB_EN_MANT == 1", "CRB_EN_MANT == 1"]),
        (4, ["IRB_EN_REPOSO == 1", "CRB_EN_REPOSO == 1"]),
        (5, ["IRB_EN_REPOSO == 1", "CRB_EN_SERVICIO == 1"]),
    ):
        def confirmar(modo=modo):
            p.setDO("MODO_CONFIRMADO", modo)
            p.setDO("MODO_EN_TRANSICION", 0)
            p.setDO("ESTADO_CONTROL", 2 if modo == 0 else 6)
        dentro(p, ["MODO_EN_TRANSICION == 1", "SENSORES_VALIDOS == 1",
                    "CINTA_DETENIDA == 1", "PIEZA_SUJETA_SENSOR == 0",
                    f"MODO_OBJETIVO == {modo}"] + posiciones, confirmar)
