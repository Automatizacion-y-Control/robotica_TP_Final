"""Prueba modos nativos con sensores geométricos y entradas simuladas explícitas."""
import argparse
import json
from pathlib import Path
import time
from sensores_modos import SensoresModos
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM, COLLISION_ON


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    args = parser.parse_args()
    r = Robolink(port=args.puerto)
    raiz = Path(__file__).resolve().parent.parent
    s = r.ActiveStation()
    assert s.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    sensores = SensoresModos(r)
    p = r.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
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

    contador = 0
    def pedir(modo):
        nonlocal contador
        contador += 1
        r.setParam("MODO_SOLICITADO", modo)
        r.setParam("MODO_ID", contador)
        esperar(lambda: val("MODO_ACK") == contador)

    try:
        # Comprueba la trayectoria de servicio con los nuevos programas, sin bucle principal.
        ensayo = r.AddProgram("_Ensayo_Servicio_Ida_Vuelta")
        from robodk.robolink import INSTRUCTION_CALL_PROGRAM
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
        p.RunProgram()
        r.setParam("IRB_DISPONIBLE", 0)
        pedir(1)
        assert val("MODO_RESULTADO") == 2 and val("MODO_CONFIRMADO") == 0
        registrar("Equipo averiado rechaza preparación", resultado=2)
        r.setParam("IRB_DISPONIBLE", 1)

        for modo in (1,2,3,4,5):
            pedir(modo)
            esperar(lambda: val("MODO_CONFIRMADO") == modo and val("MODO_EN_TRANSICION") == 0)
            assert val("AUTO_ACTIVO") == 0
            registrar("Modo confirmado", modo=modo, sensores=sensores.actualizar())
            r.setParam("ARRANQUE_ID", modo)
            esperar(lambda: val("ARRANQUE_ACK") == modo)
            assert val("AUTO_ACTIVO") == 0 and val("CAUSA_RECHAZO") == 1
            pedir(0)
            assert val("MODO_RESULTADO") == 2 and val("MODO_CONFIRMADO") == modo
            r.setParam("CONF_RESTITUCION", 1)
            pedir(0)
            esperar(lambda: val("MODO_CONFIRMADO") == 0 and val("MODO_EN_TRANSICION") == 0)
            assert val("AUTO_ACTIVO") == 0 and val("CONF_RESTITUCION") == 0
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
