"""Ensayo aislado de E/S y flujo nativo, sin robots ni movimientos.

Construye programas temporales en otra estación y exporta evidencia JSON.
Python actúa como banco de prueba: inyecta entradas y observa resultados.
No es el coordinador ni el panel de producción.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import (Robolink, INSTRUCTION_CALL_PROGRAM, INSTRUCTION_START_THREAD,
                            INSTRUCTION_INSERT_CODE)


def main():
    rdk = Robolink(port=20500)
    anterior = rdk.ActiveStation()
    velocidad = rdk.SimulationSpeed()
    por_api = "--con-flujo-api" in sys.argv
    con_flujo = "--con-flujo" in sys.argv or por_api
    if con_flujo and not por_api:
        referencia = Path(__file__).resolve().parent.parent / "referencias" / "FlowControlTest_oficial.rdk"
        estacion = rdk.AddFile(str(referencia))
        # Solo se conserva la configuración del ejemplo; no se ejecuta su código.
        for hijo in estacion.Childs():
            hijo.Delete()
        estacion.setName("Ensayo_Control_Nativo_Con_Flujo")
    else:
        estacion = rdk.AddStation("Ensayo_Control_Nativo_Sin_Movimientos")
        if por_api:
            respuesta = estacion.setParam("FlowControl", "1")
            if respuesta != "OK":
                raise RuntimeError("No se pudo habilitar FlowControl: " + respuesta)
    programas = []
    resultados = {"version": rdk.Version(), "fecha": "2026-11-06",
                  "base_con_flujo_oficial": con_flujo and not por_api,
                  "flujo_habilitado_por_api": por_api, "pruebas": []}

    def programa(nombre):
        p = rdk.AddProgram(nombre)
        programas.append(p)
        return p

    def valor(nombre):
        return rdk.getParam(nombre)

    def terminar(p, limite=4):
        inicio = time.monotonic()
        while time.monotonic() - inicio < limite:
            if not p.Busy():
                return
            time.sleep(.02)
        p.Stop()
        raise RuntimeError("Tiempo máximo en " + p.Name())

    def ejecutar(p):
        p.RunProgram()
        time.sleep(.15)
        terminar(p)

    def registrar(nombre, **datos):
        entrada = {"prueba": nombre, **datos}
        resultados["pruebas"].append(entrada)
        print(json.dumps(entrada, ensure_ascii=False), flush=True)

    try:
        rdk.setSimulationSpeed(1)
        rdk.setParam("ENS_SALIDA", 0)
        p = programa("Ensayo_Escritura")
        p.setDO("ENS_SALIDA", 17)
        ejecutar(p)
        registrar("Set nativo visible como parámetro", observado=valor("ENS_SALIDA"), esperado=17)

        rdk.setParam("ENS_ENTRADA", 0)
        rdk.setParam("ENS_FIN", 0)
        p = programa("Ensayo_Espera")
        p.waitDI("ENS_ENTRADA", 1)
        p.setDO("ENS_FIN", 1)
        p.RunProgram()
        time.sleep(.4)
        bloqueado = bool(p.Busy()) and float(valor("ENS_FIN")) == 0
        rdk.setParam("ENS_ENTRADA", 1)
        terminar(p)
        registrar("WAIT y entrada desde parámetro", bloqueado_antes=bloqueado,
                  fin_despues=valor("ENS_FIN"))

        sub = programa("Ensayo_Subprograma")
        sub.setDO("ENS_SUB", 1)
        p = programa("Ensayo_Llamada")
        p.RunInstruction(sub.Name(), INSTRUCTION_CALL_PROGRAM)
        rdk.setParam("ENS_SUB", 0)
        ejecutar(p)
        registrar("Llamada nativa", observado=valor("ENS_SUB"), esperado=1)

        # Sintaxis del ejemplo oficial para contrastar configuración habilitada y predeterminada.
        for entrada in (0, 1):
            rdk.setParam("ENS_COND", entrada)
            rdk.setParam("ENS_RAMA", 0)
            p = programa("Ensayo_IF_" + str(entrada))
            p.RunInstruction("IF ENS_COND == 1", INSTRUCTION_INSERT_CODE)
            p.RunInstruction(sub.Name(), INSTRUCTION_CALL_PROGRAM)
            p.setDO("ENS_RAMA", 1)
            p.RunInstruction("END", INSTRUCTION_INSERT_CODE)
            rdk.setParam("ENS_SUB", 0)
            ejecutar(p)
            registrar("IF con llamada nativa", entrada=entrada,
                      observado=valor("ENS_RAMA"), subprograma=valor("ENS_SUB"), esperado=entrada)

        if con_flujo:
            for entrada in (0, 1):
                rdk.setParam("ENS_COND", entrada)
                rdk.setParam("ENS_ELSE", 0)
                p = programa("Ensayo_ELSE_" + str(entrada))
                p.RunInstruction("IF ENS_COND == 1", INSTRUCTION_INSERT_CODE)
                p.setDO("ENS_ELSE", 10)
                p.RunInstruction("ELSE", INSTRUCTION_INSERT_CODE)
                p.setDO("ENS_ELSE", 20)
                p.RunInstruction("END", INSTRUCTION_INSERT_CODE)
                ejecutar(p)
                registrar("IF ELSE", entrada=entrada, observado=valor("ENS_ELSE"),
                          esperado=10 if entrada else 20)
            p = programa("Ensayo_WHILE")
            p.RunInstruction("ENS_CONTADOR = 0", INSTRUCTION_INSERT_CODE)
            p.RunInstruction("WHILE ENS_CONTADOR < 3", INSTRUCTION_INSERT_CODE)
            p.RunInstruction("ENS_CONTADOR = ENS_CONTADOR + 1", INSTRUCTION_INSERT_CODE)
            p.RunInstruction("END", INSTRUCTION_INSERT_CODE)
            ejecutar(p)
            registrar("WHILE y asignación", observado=valor("ENS_CONTADOR"), esperado=3)

            rdk.setParam("ENS_HILO", 0)
            hilo = programa("Ensayo_Hilo")
            hilo.waitDI("ENS_LIBERAR_HILO", 1)
            hilo.setDO("ENS_HILO", 1)
            rdk.setParam("ENS_LIBERAR_HILO", 0)
            p = programa("Ensayo_Paralelo")
            p.RunInstruction(hilo.Name(), INSTRUCTION_START_THREAD)
            p.setDO("ENS_PADRE", 1)
            ejecutar(p)
            registrar("Start Thread no bloqueante", padre=valor("ENS_PADRE"),
                      hijo_esperando=bool(hilo.Busy()), hijo=valor("ENS_HILO"))
            rdk.setParam("ENS_LIBERAR_HILO", 1)
            terminar(hilo)
            registrar("Hilo liberado por señal", observado=valor("ENS_HILO"), esperado=1)

        # WAIT comprueba al alcanzarse; retirar la entrada no supervisa la pausa posterior.
        rdk.setParam("ENS_PERMISO", 1)
        rdk.setParam("ENS_ETAPA", 0)
        p = programa("Ensayo_Permiso_Puntual")
        p.waitDI("ENS_PERMISO", 1)
        p.setDO("ENS_ETAPA", 1)
        p.Pause(1200)
        p.setDO("ENS_ETAPA", 2)
        p.RunProgram()
        inicio = time.monotonic()
        while float(valor("ENS_ETAPA")) != 1 and time.monotonic() - inicio < 3:
            time.sleep(.02)
        etapa = valor("ENS_ETAPA")
        rdk.setParam("ENS_PERMISO", 0)
        terminar(p)
        registrar("Retirada de permiso después del WAIT", etapa_al_retirar=etapa,
                  etapa_final=valor("ENS_ETAPA"), permiso_final=valor("ENS_PERMISO"))
    finally:
        for p in programas:
            if p.Valid() and p.Busy():
                p.Stop()
        carpeta = Path(__file__).resolve().parent.parent / "verificaciones"
        carpeta.mkdir(exist_ok=True)
        sufijo = "flujo_api" if por_api else "con_flujo" if con_flujo else "sin_flujo"
        ruta = carpeta / ("control_nativo_6_1_1_" + sufijo + ".json")
        with ruta.open("w", encoding="utf-8", newline="\n") as archivo:
            json.dump(resultados, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
        estacion.Delete()
        rdk.setActiveStation(anterior)
        rdk.setSimulationSpeed(velocidad)
        print("Evidencia:", ruta, flush=True)


if __name__ == "__main__":
    main()
