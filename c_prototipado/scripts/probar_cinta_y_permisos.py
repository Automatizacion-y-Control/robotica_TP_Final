"""Ensaya preparación de cinta y permiso puntual en una copia descartable de v04.

El banco ejecuta exclusivamente programas nativos; las señales se inyectan
desde Python. No se modifica ni guarda la estación de producción.
"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

sys.path.insert(0, r"C:\RoboDK\Python")
import parametros_celda as P
from robodk.robolink import (Robolink, ITEM_TYPE_PROGRAM, ITEM_TYPE_TARGET,
                            ITEM_TYPE_ROBOT, COLLISION_ON, INSTRUCTION_INSERT_CODE)


def main():
    raiz = Path(__file__).resolve().parent.parent
    rdk = Robolink(port=20500)
    anterior = rdk.ActiveStation()
    velocidad = rdk.SimulationSpeed()
    evidencia = {"version": rdk.Version(), "pruebas": []}
    temporal = Path(tempfile.mkdtemp(prefix="ensayo_cinta_")) / "ensayo.rdk"
    shutil.copy2(raiz / "Celda_Soldadura_Estator_Grupo4_v04.rdk", temporal)
    estacion = rdk.AddFile(str(temporal))
    estacion.setName("Ensayo_Cinta_Permisos_Descartable")

    def eventos():
        return {p.Name(): [p.setParam(i)["Name"] for i in range(p.InstructionCount())
                           if p.setParam(i)["Type"] == 7]
                for p in rdk.ItemList(ITEM_TYPE_PROGRAM)
                if any(p.setParam(i)["Type"] == 7 for i in range(p.InstructionCount()))}

    originales = eventos()
    respuesta = estacion.setParam("FlowControl", "1")
    if respuesta != "OK":
        raise RuntimeError("No se pudo habilitar FlowControl")
    estacion.Save(str(temporal))
    estacion.Delete()
    estacion = rdk.AddFile(str(temporal))
    recuperados = eventos()
    prueba_flujo = rdk.AddProgram("Ensayo_Persistencia_Flujo")
    prueba_flujo.RunInstruction("IF ENS_COND == 1", INSTRUCTION_INSERT_CODE)
    prueba_flujo.setDO("ENS_RAMA", 1)
    prueba_flujo.RunInstruction("END", INSTRUCTION_INSERT_CODE)
    rdk.setParam("ENS_COND", 0)
    rdk.setParam("ENS_RAMA", 0)
    prueba_flujo.RunProgram()
    time.sleep(.25)
    persistencia = rdk.getParam("ENS_RAMA")
    prueba_flujo.Delete()
    evidencia["persistencia_flujo"] = {"rama_con_condicion_falsa": persistencia,
                                      "eventos_antes": originales,
                                      "eventos_despues": recuperados}
    assert originales == recuperados and originales, "Eventos no conservados"
    assert float(persistencia) == 0, "FlowControl no persistió"
    cinta = rdk.Item("Cinta_Pasante", ITEM_TYPE_ROBOT)
    target = rdk.AddTarget("Ensayo_Cinta_Final", estacion, cinta)
    target.setAsJointTarget()

    def registrar(nombre, **datos):
        fila = {"prueba": nombre, **datos}
        evidencia["pruebas"].append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)

    def piezas():
        return [{"nombre": "Estator_" + str(k),
                 "x": rdk.Item("Estator_" + str(k)).PoseAbs().Pos()[0]}
                for k in range(1, P.LOTE + 1)]

    def extremos():
        xs = [fila["x"] for fila in piezas()]
        return {"fuera_de_zona": min(xs) - P.ESTATOR_LADO / 2 > P.CERR_X[1],
                "dentro_del_apoyo_salida": max(xs) + P.ESTATOR_LADO / 2 <= P.CINTA_EXT_FIN_X}

    programa = rdk.AddProgram("Ensayo_Permiso_Cinta", cinta)
    programa.waitDI("ENS_PERMISO", 1)
    programa.setSpeed(250, 250)
    programa.addMoveJ(target)
    programa.setDO("ENS_FIN_MOVIMIENTO", 1)
    try:
        for nombre in ("Man_Reposo", "Sold_Reposo", "Pinza_Abierta", "Cinta_Posicion_1"):
            t = rdk.Item(nombre, ITEM_TYPE_TARGET)
            t.getLink().setJoints(t.Joints())
        registrar("Preparación sin vaciado", eje=cinta.Joints().list(),
                  piezas=piezas(), colisiones=rdk.Collisions(),
                  criterio="Mantener posición; no declarar banda vacía")
        for destino in (P.V3_AVANCE_EVACUACION, 2050):
            cinta.setJoints([0])
            target.setJoints([destino])
            resultado = programa.Update(COLLISION_ON, 3600, 1, 1)
            registrar("Evacuación desde lote inicial", destino=destino,
                      resultado=resultado, piezas=piezas(), **extremos())

        cinta.setJoints([0])
        target.setJoints([2050])
        rdk.setParam("ENS_PERMISO", 1)
        rdk.setParam("ENS_FIN_MOVIMIENTO", 0)
        rdk.setCollisionActive(COLLISION_ON)
        rdk.setSimulationSpeed(1)
        programa.RunProgram()
        inicio = time.monotonic()
        retiro = None
        max_colisiones = 0
        while time.monotonic() - inicio < 25:
            q = cinta.Joints().list()[0]
            if retiro is None and q > 150 and q < 1900:
                rdk.setParam("ENS_PERMISO", 0)
                retiro = q
            max_colisiones = max(max_colisiones, rdk.Collisions())
            if float(rdk.getParam("ENS_FIN_MOVIMIENTO")) == 1:
                break
            time.sleep(.02)
        if programa.Busy():
            programa.Stop()
            raise RuntimeError("Tiempo máximo de ensayo de cinta")
        registrar("Retirada de permiso durante movimiento nativo", eje_al_retirar=retiro,
                  eje_final=cinta.Joints().list(), fin=rdk.getParam("ENS_FIN_MOVIMIENTO"),
                  permiso=rdk.getParam("ENS_PERMISO"), colisiones=max_colisiones,
                  segundos_reales=time.monotonic() - inicio)
    finally:
        if programa.Busy():
            programa.Stop()
        estacion.Delete()
        rdk.setActiveStation(anterior)
        rdk.setSimulationSpeed(velocidad)
        temporal.unlink()
        temporal.parent.rmdir()
        salida = raiz / "verificaciones" / "cinta_y_permisos_v04.json"
        with salida.open("w", encoding="utf-8", newline="\n") as archivo:
            json.dump(evidencia, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")


if __name__ == "__main__":
    main()
