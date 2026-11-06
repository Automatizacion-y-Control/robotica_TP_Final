"""Prueba modos nativos con sensores geométricos y entradas simuladas explícitas."""
import argparse
import json
from pathlib import Path
import time
from sensores_modos import SensoresModos
from robodk.robolink import (Robolink, ITEM_TYPE_PROGRAM, COLLISION_ON,
                            INSTRUCTION_CALL_PROGRAM)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    args = parser.parse_args()
    r = Robolink(port=args.puerto)
    raiz = Path(__file__).resolve().parent.parent
    s = r.ActiveStation()
    assert s.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    sensores = SensoresModos(r)
    p = r.Item("Coordinador_Panel", ITEM_TYPE_PROGRAM)
    resultados = []
    exito = False

    def val(n):
        return float(r.getParam(n))

    def esperar(predicado, limite=15):
        inicio = time.monotonic()
        while time.monotonic()-inicio < limite:
            sensores.actualizar()
            if r.Collisions():
                raise AssertionError("Colisión: " + str([(a.Name(),b.Name()) for a,b,i,j in r.CollisionPairs()]))
            if predicado():
                return
            time.sleep(.04)
        raise AssertionError("Tiempo máximo; modo="+str(val("MODO_CONFIRMADO")))

    def registrar(nombre, **datos):
        fila = {"prueba": nombre, **datos}
        resultados.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)

    def correr(nombre):
        programa = r.Item(nombre, ITEM_TYPE_PROGRAM)
        programa.RunProgram()
        time.sleep(.2)
        esperar(lambda: not programa.Busy())

    contador = 0
    def pedir(modo):
        nonlocal contador
        contador += 1
        r.setParam("MODO_SOLICITADO", modo)
        r.setParam("MODO_ID", contador)
        esperar(lambda: val("MODO_ACK") == contador)

    def rechazado(modo, causa):
        confirmado = val("MODO_CONFIRMADO")
        pedir(modo)
        assert val("MODO_RESULTADO") == 2 and val("MODO_CAUSA") == causa, val("MODO_CAUSA")
        assert val("MODO_CONFIRMADO") == confirmado

    def confirmado(modo):
        pedir(modo)
        esperar(lambda: val("MODO_CONFIRMADO") == modo and val("MODO_EN_TRANSICION") == 0)
        assert val("AUTO_ACTIVO") == 0

    def regresar():
        r.setParam("CONF_RESTITUCION", 1)
        confirmado(0)
        assert val("CONF_RESTITUCION") == 0

    arranques = 0
    def arranque_rechazado(causa):
        nonlocal arranques
        arranques += 1
        r.setParam("ARRANQUE_ID", arranques)
        esperar(lambda: val("ARRANQUE_ACK") == arranques)
        assert val("AUTO_ACTIVO") == 0 and val("CAUSA_RECHAZO") == causa, val("CAUSA_RECHAZO")

    try:
        # Comprueba la trayectoria de servicio con los nuevos programas, sin bucle principal.
        ensayo = r.AddProgram("_Ensayo_Servicio_Ida_Vuelta")
        ensayo.RunInstruction("Preparar_Servicio_Antorcha", INSTRUCTION_CALL_PROGRAM)
        ensayo.RunInstruction("Sold_Servicio_Antorcha", INSTRUCTION_CALL_PROGRAM)
        try:
            comprobacion = ensayo.Update(COLLISION_ON, 3600, 1, 1)
            assert comprobacion[3] == 1, comprobacion
            registrar("Servicio ida y regreso", resultado=comprobacion)
        finally:
            ensayo.Delete()
        r.setSimulationSpeed(10)
        r.setCollisionActive(COLLISION_ON)
        r.setParam("PERMISO_OPERACION", 1)
        for n in ("IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
            r.setParam(n, 1)
        esperar(lambda: val("CINTA_DETENIDA") == 1)

        # Fuera de reposo se distingue si la parada ordena o no el regreso del robot.
        correr("Sold_Ir_Mantenimiento")
        r.setParam("CRB_DISPONIBLE", 0)
        correr("Parada_Entre_Piezas")
        assert sensores.actualizar()["CRB_EN_MANT"]
        registrar("Parada no mueve el equipo no disponible", crb_en_mantenimiento=True)
        r.setParam("CRB_DISPONIBLE", 1)
        correr("Parada_Entre_Piezas")
        assert sensores.actualizar()["CRB_EN_REPOSO"]
        registrar("Parada mueve a reposo el equipo disponible", crb_en_reposo=True)

        p.RunProgram()
        r.setParam("IRB_DISPONIBLE", 0)
        rechazado(1, 7)
        rechazado(3, 7)
        registrar("Equipo averiado rechaza preparación que lo mueve", causa=7)
        arranque_rechazado(7)
        registrar("Equipo averiado rechaza arranque", causa=7)

        articulaciones = sensores.irb.Joints().list()
        confirmado(6)
        assert sensores.irb.Joints().list() == articulaciones
        r.setParam("CONF_RESTITUCION", 1)
        rechazado(0, 7)
        registrar("Correctivo sin movimiento con equipo averiado", modo=6, regreso_causa=7)
        r.setParam("IRB_DISPONIBLE", 1)
        regresar()
        registrar("Regreso del correctivo con equipo reparado", modo=0)

        r.setParam("CRB_DISPONIBLE", 0)
        confirmado(1)
        regresar()
        r.setParam("CRB_DISPONIBLE", 1)
        registrar("Equipo ajeno averiado no impide la tarea", modo=1)

        r.setParam("CINTA_DISPONIBLE", 0)
        confirmado(4)
        regresar()
        arranque_rechazado(7)
        r.setParam("CINTA_DISPONIBLE", 1)
        registrar("Cinta averiada admite diagnóstico y rechaza arranque", modo=4)

        rechazado(99, 11)
        rechazado(0, 9)
        registrar("Solicitudes inválidas en reposo", desconocido=11, sin_modo=9)

        r.setParam("PERMISO_OPERACION", 0)
        rechazado(1, 1)
        arranque_rechazado(1)
        confirmado(6)
        r.setParam("CONF_RESTITUCION", 1)
        rechazado(0, 1)
        r.setParam("PERMISO_OPERACION", 1)
        regresar()
        registrar("Sin permiso se rechaza lo que mueve; el correctivo se admite", causa=1)

        for modo in (1,2,3,4,5):
            confirmado(modo)
            registrar("Modo confirmado", modo=modo, sensores=sensores.actualizar())
            arranque_rechazado(8)
            rechazado(6 if modo != 4 else 1, 8)
            rechazado(0, 10)
            regresar()
            assert val("AUTO_ACTIVO") == 0
            registrar("Retorno sin autoarranque", desde=modo, siguiente=val("PROXIMA_PIEZA"))
        exito = True
    finally:
        r.setParam("COORDINADOR_ACTIVO", 0)
        time.sleep(.3)
        for prog in r.ItemList(ITEM_TYPE_PROGRAM):
            if prog.Busy():
                prog.Stop()
        r.setParam("SENSORES_VALIDOS", 0)
        with (raiz / "verificaciones" / "modos_v05.json").open("w", encoding="utf-8", newline="\n") as f:
            json.dump({"version": r.Version(), "exito": exito, "pruebas": resultados},f,ensure_ascii=False,indent=2)
            f.write("\n")
        s.Delete()
        r.AddFile(str(raiz / "Celda_Soldadura_Estator_Grupo4_v05.rdk"))
        r.setSimulationSpeed(1)


if __name__ == "__main__":
    main()
