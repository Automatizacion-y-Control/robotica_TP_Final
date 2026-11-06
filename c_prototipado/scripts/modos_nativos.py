"""Construcción de solicitudes nativas de mantenimiento y servicio para v05."""
from robodk.robolink import (ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET, ITEM_TYPE_TOOL,
                            INSTRUCTION_INSERT_CODE, INSTRUCTION_CALL_PROGRAM,
                            INSTRUCTION_COMMENT)

INICIALES_MODOS = {
    "MODO_ID": 0, "MODO_ACK": 0, "MODO_SOLICITADO": 0, "MODO_CONFIRMADO": 0,
    "MODO_OBJETIVO": 0, "MODO_EN_TRANSICION": 0, "MODO_RESULTADO": 0, "MODO_CAUSA": 0,
    "MODO_ID_CAPTURADO": 0, "MODO_CAPTURADO": 0, "MODO_DESDE_AUTO": 0,
    "MODO_ES_INTERVENCION": 0, "MODO_CONOCIDO": 0,
    "SENSORES_VALIDOS": 0, "PIEZA_SUJETA_SENSOR": 0,
    "IRB_EN_REPOSO": 0, "CRB_EN_REPOSO": 0, "IRB_EN_MANT": 0, "CRB_EN_MANT": 0,
    "CRB_EN_SERVICIO": 0, "CINTA_DETENIDA": 0,
    "IRB_DISPONIBLE": 0, "CRB_DISPONIBLE": 0, "CINTA_DISPONIBLE": 0,
    "CONF_RESTITUCION": 0,
}

# Tabla única para CAUSA_RECHAZO y MODO_CAUSA; el panel la traduce a mensajes.
CAUSAS = {
    0: "Sin causa de rechazo",
    1: "Sin permiso de operación",
    2: "Cambio de modo en curso",
    3: "Sensores no válidos",
    4: "Equipo fuera de la posición requerida",
    5: "Pieza sujeta",
    6: "Cinta en movimiento",
    7: "Equipo no disponible",
    8: "Hay un modo activo",
    9: "No hay modo del cual regresar",
    10: "Falta confirmar la restitución",
    11: "Modo desconocido",
    12: "Producción activa",
}

CORRECTIVO = 6
# "equipos" lista solo lo que el modo mueve: un equipo ajeno averiado no impide la tarea.
MODOS = {
    1: {"ida": ["Man_Ir_Mantenimiento"], "vuelta": ["Man_Ir_Reposo"],
        "posicion": ["IRB_EN_MANT", "CRB_EN_REPOSO"], "equipos": ["IRB_DISPONIBLE"]},
    2: {"ida": ["Sold_Ir_Mantenimiento"], "vuelta": ["Sold_Ir_Reposo"],
        "posicion": ["IRB_EN_REPOSO", "CRB_EN_MANT"], "equipos": ["CRB_DISPONIBLE"]},
    3: {"ida": ["Man_Ir_Mantenimiento", "Sold_Ir_Mantenimiento"],
        "vuelta": ["Sold_Ir_Reposo", "Man_Ir_Reposo"],
        "posicion": ["IRB_EN_MANT", "CRB_EN_MANT"],
        "equipos": ["IRB_DISPONIBLE", "CRB_DISPONIBLE"]},
    # Preparar cinta no la mueve: admite diagnóstico con accionamiento averiado.
    4: {"ida": [], "vuelta": [], "posicion": ["IRB_EN_REPOSO", "CRB_EN_REPOSO"], "equipos": []},
    5: {"ida": ["Preparar_Servicio_Antorcha"], "vuelta": ["Sold_Servicio_Antorcha"],
        "posicion": ["IRB_EN_REPOSO", "CRB_EN_SERVICIO"], "equipos": ["CRB_DISPONIBLE"]},
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

    # Reemplaza a Parada_Ciclo en el coordinador: nunca ordena mover un equipo no disponible.
    p = programa("Parada_Entre_Piezas")
    p.setDO("ARCO_TIG", 0)
    dentro(p, ["CRB_DISPONIBLE == 1"], lambda: call(p, "Sold_Ir_Reposo"))
    dentro(p, ["IRB_DISPONIBLE == 1"], lambda: call(p, "Man_Ir_Reposo"))

    p = programa("Atender_Solicitud_Modo")

    def rechazar(condiciones, causa):
        dentro(p, ["MODO_DESDE_AUTO == 0"] + condiciones, lambda: p.setDO("MODO_CAUSA", causa))

    def fijar_si(condicion, senal):
        dentro(p, [condicion], lambda: p.setDO(senal, 1))

    code(p, "IF MODO_ID != MODO_ACK")
    code(p, "MODO_ID_CAPTURADO = MODO_ID")
    code(p, "MODO_CAPTURADO = MODO_SOLICITADO")
    p.setDO("MODO_RESULTADO", 2)  # rechazo salvo que una rama lo acepte
    p.setDO("MODO_CAUSA", 0)
    p.setDO("MODO_DESDE_AUTO", 0)
    p.setDO("MODO_ES_INTERVENCION", 0)
    p.setDO("MODO_CONOCIDO", 0)
    fijar_si("MODO_CAPTURADO == 0", "MODO_CONOCIDO")
    for modo in (*MODOS, CORRECTIVO):
        fijar_si(f"MODO_CAPTURADO == {modo}", "MODO_CONOCIDO")
        fijar_si(f"MODO_CAPTURADO == {modo}", "MODO_ES_INTERVENCION")

    # Solo una intervención válida detiene la producción; lo demás se rechaza sin afectarla.
    def detener():
        call(p, "Parada_Entre_Piezas")
        p.setDO("AUTO_ACTIVO", 0)
        p.setDO("ESTADO_CONTROL", 2)
        p.setDO("MODO_DESDE_AUTO", 1)
        p.setDO("MODO_RESULTADO", 3)  # parada realizada: reenviar desde reposo confirmado
    dentro(p, ["AUTO_ACTIVO == 1", "MODO_ES_INTERVENCION == 1"], detener)

    # Sin ELSE validado: cada condición escribe su causa y la última escrita prevalece,
    # por eso se recorren de menor a mayor prioridad.
    for modo, datos in MODOS.items():
        for equipo in datos["equipos"]:
            rechazar(["MODO_CONFIRMADO == 0", f"MODO_CAPTURADO == {modo}", f"{equipo} == 0"], 7)
    entrada = ["MODO_ES_INTERVENCION == 1", "MODO_CONFIRMADO == 0", f"MODO_CAPTURADO != {CORRECTIVO}"]
    rechazar(entrada + ["IRB_EN_REPOSO == 0"], 4)
    rechazar(entrada + ["CRB_EN_REPOSO == 0"], 4)
    rechazar(entrada + ["PIEZA_SUJETA_SENSOR == 1"], 5)
    rechazar(entrada + ["PERMISO_OPERACION == 0"], 1)

    # No se transita directamente de una postura de mantenimiento a otra.
    regreso = ["MODO_CAPTURADO == 0"]
    for modo, datos in MODOS.items():
        for equipo in datos["equipos"]:
            rechazar(regreso + [f"MODO_CONFIRMADO == {modo}", f"{equipo} == 0"], 7)
        for posicion in datos["posicion"]:
            rechazar(regreso + [f"MODO_CONFIRMADO == {modo}", f"{posicion} == 0"], 4)
    # El correctivo no movió nada: se cierra con todo reparado y la celda ya en reposo.
    for equipo in ("IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
        rechazar(regreso + [f"MODO_CONFIRMADO == {CORRECTIVO}", f"{equipo} == 0"], 7)
    for posicion in ("IRB_EN_REPOSO", "CRB_EN_REPOSO"):
        rechazar(regreso + [f"MODO_CONFIRMADO == {CORRECTIVO}", f"{posicion} == 0"], 4)
    rechazar(regreso + ["MODO_CONFIRMADO != 0", "PIEZA_SUJETA_SENSOR == 1"], 5)
    rechazar(regreso + ["MODO_CONFIRMADO != 0", "PERMISO_OPERACION == 0"], 1)
    rechazar(regreso + ["MODO_CONFIRMADO != 0", "CONF_RESTITUCION == 0"], 10)
    rechazar(regreso + ["MODO_CONFIRMADO == 0"], 9)
    rechazar(["MODO_ES_INTERVENCION == 1", "MODO_CONFIRMADO != 0"], 8)
    rechazar(["MODO_CONOCIDO == 1", "CINTA_DETENIDA == 0"], 6)
    rechazar(["MODO_CONOCIDO == 1", "SENSORES_VALIDOS == 0"], 3)
    rechazar(["MODO_CONOCIDO == 1", "MODO_EN_TRANSICION == 1"], 2)
    rechazar(["MODO_CONOCIDO == 0"], 11)

    aceptada = ["MODO_DESDE_AUTO == 0", "MODO_CONOCIDO == 1", "MODO_CAUSA == 0"]
    for modo, llamadas in [*((m, d["ida"]) for m, d in MODOS.items()), (CORRECTIVO, [])]:
        def preparar(modo=modo, llamadas=llamadas):
            p.setDO("ARCO_TIG", 0)
            p.setDO("MODO_EN_TRANSICION", 1)
            p.setDO("ESTADO_CONTROL", 4)
            for n in llamadas:
                call(p, n)
            p.setDO("MODO_OBJETIVO", modo)
            p.setDO("MODO_RESULTADO", 1)
        dentro(p, aceptada + ["MODO_CONFIRMADO == 0", f"MODO_CAPTURADO == {modo}"], preparar)

    # Retorno solo desde posturas conocidas y después de restitución explícita.
    for modo, llamadas in [*((m, d["vuelta"]) for m, d in MODOS.items()), (CORRECTIVO, [])]:
        def regresar(llamadas=llamadas):
            p.setDO("MODO_EN_TRANSICION", 1)
            p.setDO("ESTADO_CONTROL", 5)
            for n in llamadas:
                call(p, n)
            p.setDO("MODO_OBJETIVO", 0)
            p.setDO("MODO_RESULTADO", 1)
            p.setDO("CONF_RESTITUCION", 0)
        dentro(p, aceptada + ["MODO_CAPTURADO == 0", f"MODO_CONFIRMADO == {modo}"], regresar)
    code(p, "MODO_ACK = MODO_ID_CAPTURADO")
    code(p, "END")

    p = programa("Confirmar_Posicion_Modo")
    comunes = ["MODO_EN_TRANSICION == 1", "SENSORES_VALIDOS == 1", "CINTA_DETENIDA == 1"]
    posturas = {0: ["IRB_EN_REPOSO", "CRB_EN_REPOSO"],
                **{m: d["posicion"] for m, d in MODOS.items()}}
    for modo, posiciones in posturas.items():
        def confirmar(modo=modo):
            p.setDO("MODO_CONFIRMADO", modo)
            p.setDO("MODO_EN_TRANSICION", 0)
            p.setDO("ESTADO_CONTROL", 2 if modo == 0 else 6)
        dentro(p, comunes + ["PIEZA_SUJETA_SENSOR == 0", f"MODO_OBJETIVO == {modo}"] +
               [f"{n} == 1" for n in posiciones], confirmar)

    # El correctivo no exige postura: el equipo puede haber quedado donde falló.
    def confirmar_correctivo():
        p.setDO("MODO_CONFIRMADO", CORRECTIVO)
        p.setDO("MODO_EN_TRANSICION", 0)
        p.setDO("ESTADO_CONTROL", 6)
    dentro(p, comunes + [f"MODO_OBJETIVO == {CORRECTIVO}"], confirmar_correctivo)
