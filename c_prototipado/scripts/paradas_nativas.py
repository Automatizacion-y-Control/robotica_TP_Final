"""Recuperación nativa después de una parada inmediata, para la v05.

El panel detiene la ejecución; retomar es trabajo de estos programas. Una pieza cortada
durante la soldadura se termina y se deposita corrida, como pieza de revisión o retrabajo.
"""
from robodk.robolink import (ITEM_TYPE_FRAME, ITEM_TYPE_PROGRAM, ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET,
                            ITEM_TYPE_TOOL, INSTRUCTION_CALL_PROGRAM, INSTRUCTION_COMMENT,
                            INSTRUCTION_INSERT_CODE)
from robodk.robomath import transl

from velocidades_v05 import V_ARTICULAR, V_CERCA, V_JUNTO_PIEZA, V_TRASLADO

# Corrimiento hacia el borde derecho de la banda, en sentido de avance. Medido con SolveIK:
# a -70 mm la salida vertical queda en el límite de alcance y a -80 mm no entra.
RETRABAJO_Y = -60.0
RETRABAJO_APROX_Y = -40.0
RETRABAJO_SALIDA_Z = 40.0
SOLDAR = "Sold_Par_Cordones"
# Una señal por paso de Ciclo_Pieza_k, en el orden de sus instrucciones (la 0 es un comentario).
FASES = {1: "Avance de cinta", 2: "Toma", 3: "Presentación lado 1", 4: "Soldadura lado 1",
         5: "Presentación lado 2", 6: "Soldadura lado 2", 7: "Depósito", 8: "Regreso a reposo"}
INICIALES_PARADAS = {
    "FASE_PIEZA": 0, "FASE_CAPTURADA": 0, "PARO_CAUSA": 0, "RECUP_PENDIENTE": 0,
    "RECUPERAR_ID": 0, "RECUPERAR_ACK": 0, "PIEZAS_RETRABAJO": 0, "RETRABAJO_ACTUAL": 0,
    "SUJETA_CAPTURADA": 0, "PIEZA_RESUELTA": 0, "EMERGENCIA_SIM": 0, "CORTINA_ENTRADA_SIM": 0,
    "CORTINA_SALIDA_SIM": 0, "PUERTA_ABIERTA_SIM": 0,
}
# Parado o sin resguardos no se acepta ninguna orden que pueda mover equipos.
RESGUARDOS = ("CORTINA_ENTRADA_SIM", "CORTINA_SALIDA_SIM", "PUERTA_ABIERTA_SIM")


def _marcar_fases(rdk):
    for k in range(1, 5):
        ciclo = rdk.Item(f"Ciclo_Pieza_{k}", ITEM_TYPE_PROGRAM)
        assert ciclo.InstructionCount() == 9
        # De atrás hacia adelante: insertar no corre los índices que faltan.
        for fase in sorted(FASES, reverse=True):
            ciclo.InstructionSelect(fase - 1)
            ciclo.setDO("FASE_PIEZA", fase)
        ciclo.InstructionSelect(ciclo.InstructionCount() - 1)


def _deposito_retrabajo(rdk):
    irb = rdk.Item("ABB IRB 1200-7/0.7", ITEM_TYPE_ROBOT)
    tcp = rdk.Item("TCP_Pinza", ITEM_TYPE_TOOL)
    celda = rdk.Item("Frame_Celda", ITEM_TYPE_FRAME)
    origen = rdk.Item("Frame_Deposito_Cinta", ITEM_TYPE_FRAME)
    marco = rdk.AddFrame("Frame_Deposito_Retrabajo", celda)
    marco.setPose(transl(0, RETRABAJO_Y, 0) * origen.Pose())
    apoyo_abs = origen.PoseAbs() * rdk.Item("Man_Deposito", ITEM_TYPE_TARGET).Pose()
    aprox_abs = origen.PoseAbs() * rdk.Item("Man_Deposito_Aprox", ITEM_TYPE_TARGET).Pose()

    def target(nombre, pose_abs):
        # SolveIK devuelve [0] si no hay solución: hay que exigir un valor por articulación.
        solucion = irb.SolveIK(irb.PoseAbs().inv() * pose_abs, irb.Joints(), tcp.PoseTool()).list()
        assert len(solucion) == 6, "El IRB no alcanza " + nombre
        t = rdk.AddTarget(nombre, marco, irb)
        t.setAsCartesianTarget()
        t.setPose(marco.PoseAbs().inv() * pose_abs)
        return t

    # La aproximación normal queda fuera de alcance con el corrimiento: se entra en diagonal
    # desde más cerca y solo el último tramo es vertical, lo justo para sacar los dedos.
    aprox = target("Man_Retrabajo_Aprox", transl(0, RETRABAJO_APROX_Y, 0) * aprox_abs)
    salida = target("Man_Retrabajo_Salida", transl(0, RETRABAJO_Y, RETRABAJO_SALIDA_Z) * apoyo_abs)
    apoyo = target("Man_Retrabajo", transl(0, RETRABAJO_Y, 0) * apoyo_abs)
    p = rdk.AddProgram("Man_Depositar_Retrabajo", irb)
    p.RunInstruction("Pieza de revisión o retrabajo: se deposita corrida hacia el borde derecho",
                     INSTRUCTION_COMMENT)
    p.setPoseFrame(marco)
    p.setPoseTool(tcp)
    p.waitDI("SOLDADURA_TERMINADA", 1)
    p.setDO("SOLDADURA_TERMINADA", 0)
    p.setSpeed(V_CERCA, V_ARTICULAR)
    p.addMoveJ(rdk.Item("Man_Presentar_Lado2", ITEM_TYPE_TARGET))
    p.addMoveL(rdk.Item("Man_Presentar_Aprox_Lado2", ITEM_TYPE_TARGET))
    p.setSpeed(V_TRASLADO, V_ARTICULAR)
    p.setRounding(5)
    p.addMoveJ(rdk.Item("Man_Reposo", ITEM_TYPE_TARGET))
    p.addMoveJ(aprox)
    p.setRounding(0)
    p.setSpeed(V_JUNTO_PIEZA, V_ARTICULAR)
    p.addMoveL(salida)
    p.addMoveL(apoyo)
    p.RunInstruction("Pinza_Cerrar", INSTRUCTION_CALL_PROGRAM)
    p.RunInstruction("Evento_Soltar_Pieza", INSTRUCTION_CALL_PROGRAM)
    p.addMoveL(salida)
    p.addMoveL(aprox)


def _recuperacion(rdk):
    def code(p, s):
        p.RunInstruction(s, INSTRUCTION_INSERT_CODE)

    def call(p, *nombres):
        for n in nombres:
            p.RunInstruction(n, INSTRUCTION_CALL_PROGRAM)

    def si(p, condiciones, acciones):
        for c in condiciones:
            code(p, "IF " + c)
        acciones()
        for _ in condiciones:
            code(p, "END")

    def limpiar(p):
        p.setDO("ARCO_TIG", 0)
        p.setDO("PIEZA_PRESENTADA", 0)
        p.setDO("SOLDADURA_TERMINADA", 0)
        call(p, "Sold_Ir_Reposo")

    def depositar(p):
        si(p, ["RETRABAJO_ACTUAL == 1"], lambda: call(p, "Man_Depositar_Retrabajo"))
        si(p, ["RETRABAJO_ACTUAL == 0"], lambda: call(p, "Man_Depositar_Cinta"))
        call(p, "Man_Ir_Reposo")

    p = rdk.AddProgram("Recuperar_Desde_Lado1")
    limpiar(p)
    call(p, "Man_Presentar_Lado1", SOLDAR, "Man_Presentar_Lado2", SOLDAR)
    depositar(p)

    p = rdk.AddProgram("Recuperar_Desde_Lado2")
    limpiar(p)
    p.setDO("SOLDADURA_TERMINADA", 1)
    call(p, "Man_Presentar_Lado2", SOLDAR)
    depositar(p)

    p = rdk.AddProgram("Recuperar_Deposito")
    limpiar(p)
    p.setDO("SOLDADURA_TERMINADA", 1)
    depositar(p)

    p = rdk.AddProgram("Recuperar_Pieza")
    p.RunInstruction("Retoma la pieza interrumpida; la soldadura se repite desde el par de cordones",
                     INSTRUCTION_COMMENT)
    code(p, "FASE_CAPTURADA = FASE_PIEZA")
    p.setDO("RETRABAJO_ACTUAL", 0)
    p.setDO("PIEZA_RESUELTA", 0)
    p.setDO("SUJETA_CAPTURADA", 0)
    si(p, ["PIEZA_SUJETA_SENSOR == 1"], lambda: p.setDO("SUJETA_CAPTURADA", 1))
    for fase in (4, 6):
        si(p, [f"FASE_CAPTURADA == {fase}"], lambda: p.setDO("RETRABAJO_ACTUAL", 1))

    # Sin pieza en la pinza no hay nada que terminar: solo se llevan los equipos a reposo.
    def sin_pieza():
        limpiar(p)
        call(p, "Man_Ir_Reposo", "Pinza_Abrir")
        for fase in (7, 8):
            si(p, [f"FASE_CAPTURADA == {fase}"], lambda: p.setDO("PIEZA_RESUELTA", 1))
    si(p, ["SUJETA_CAPTURADA == 0"], sin_pieza)

    for fases, programa in (((1, 2, 3, 4), "Recuperar_Desde_Lado1"), ((5, 6), "Recuperar_Desde_Lado2"),
                            ((7, 8), "Recuperar_Deposito")):
        for fase in fases:
            def terminar(programa=programa):
                call(p, programa)
                p.setDO("PIEZA_RESUELTA", 1)
            si(p, ["SUJETA_CAPTURADA == 1", f"FASE_CAPTURADA == {fase}"], terminar)

    def contar():
        code(p, "PROXIMA_PIEZA = PROXIMA_PIEZA + 1")
        code(p, "PIEZAS_COMPLETADAS = PIEZAS_COMPLETADAS + 1")
    si(p, ["PIEZA_RESUELTA == 1", "PIEZA_ACTIVA != 0"], contar)
    si(p, ["RETRABAJO_ACTUAL == 1", "PIEZA_RESUELTA == 1"],
       lambda: code(p, "PIEZAS_RETRABAJO = PIEZAS_RETRABAJO + 1"))
    p.setDO("PIEZA_ACTIVA", 0)
    p.setDO("FASE_PIEZA", 0)
    p.setDO("MODO_EN_TRANSICION", 0)
    p.setDO("MODO_OBJETIVO", 0)


def _fijar_postura(rdk):
    """RoboDK marca estos targets cartesianos como no alcanzables aunque tienen solución:
    fijarlos como articulares define la postura exacta y quita la advertencia."""
    irb = rdk.Item("ABB IRB 1200-7/0.7", ITEM_TYPE_ROBOT)
    tcp = rdk.Item("TCP_Pinza", ITEM_TYPE_TOOL)
    reposo = rdk.Item("Man_Reposo", ITEM_TYPE_TARGET).Joints()
    for nombre in ("Man_Presentar_Aprox", "Man_Presentar_Lado1", "Man_Toma_Aprox", "Man_Toma"):
        t = rdk.Item(nombre, ITEM_TYPE_TARGET)
        pose_abs = t.Parent().PoseAbs() * t.Pose()
        solucion = irb.SolveIK(irb.PoseAbs().inv() * pose_abs, reposo, tcp.PoseTool())
        assert len(solucion.list()) == 6, "El IRB no alcanza " + nombre
        t.setAsJointTarget()
        t.setJoints(solucion)


def instalar_paradas(rdk):
    _fijar_postura(rdk)
    _marcar_fases(rdk)
    _deposito_retrabajo(rdk)
    _recuperacion(rdk)
