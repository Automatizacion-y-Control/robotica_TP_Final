"""Banco de integración del coordinador nativo v05: inyecta señales y observa.

Las ejecuciones API son exclusivas del banco, no del panel de operación.
Reabre el archivo nominal al terminar; nunca guarda el estado de los ensayos.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM, COLLISION_ON
from sensores_modos import SensoresModos


def main():
    puerto = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else 20500
    r = Robolink(port=puerto)
    raiz = Path(__file__).resolve().parent.parent
    estacion = r.ActiveStation()
    assert estacion.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    p = r.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
    sensores = SensoresModos(r)
    pruebas = []
    inicio = time.monotonic()

    def valor(n):
        return float(r.getParam(n))

    def esperar(condicion, limite=40):
        t = time.monotonic()
        while time.monotonic() - t < limite:
            sensores.actualizar()
            if r.Collisions():
                raise AssertionError("Colisión en prueba de coordinación")
            if condicion():
                return
            time.sleep(.025)
        raise AssertionError("Tiempo máximo de espera")

    def registrar(nombre, **datos):
        fila = {"prueba": nombre, **datos}
        pruebas.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)

    try:
        r.setCollisionActive(COLLISION_ON)
        r.setSimulationSpeed(10)
        for n in ("IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
            r.setParam(n, 1)
        esperar(lambda: valor("CINTA_DETENIDA") == 1)
        p.RunProgram()
        time.sleep(.2)
        r.setParam("ARRANQUE_ID", 1)
        esperar(lambda: valor("ARRANQUE_ACK") == 1)
        assert valor("AUTO_ACTIVO") == 0 and valor("CAUSA_RECHAZO") == 1
        registrar("Arranque sin permiso rechazado", siguiente=valor("PROXIMA_PIEZA"))
        r.setParam("PERMISO_OPERACION", 1)
        time.sleep(.3)
        assert valor("AUTO_ACTIVO") == 0
        registrar("Restaurar permiso no arranca", auto=valor("AUTO_ACTIVO"))

        # Parar durante soldadura, toma de la siguiente pieza y cuarta pieza.
        for orden, pieza, fase in ((2, 1, "soldadura"), (3, 2, "toma"), (4, 4, "soldadura"),
                                   (5, 4, "segundo lote")):
            r.setParam("ARRANQUE_ID", orden)
            esperar(lambda: valor("PIEZA_ACTIVA") == pieza and
                    (valor("ARCO_TIG") == 1 if fase != "toma" else
                     r.Item("Estator_2").Parent().Name() == "TCP_Pinza"), limite=70)
            if fase == "segundo lote":
                r.setParam("MODO_SOLICITADO", 1)
                r.setParam("MODO_ID", 1)
                esperar(lambda: valor("MODO_ACK") == 1 and valor("AUTO_ACTIVO") == 0)
                assert valor("MODO_RESULTADO") == 3
            else:
                r.setParam("PARADA_ID", orden)
                esperar(lambda: valor("PARADA_ACK") == orden and valor("AUTO_ACTIVO") == 0)
            assert valor("PROXIMA_PIEZA") == pieza + 1
            assert valor("PIEZA_ACTIVA") == 0 and valor("ARCO_TIG") == 0
            assert all(r.Item("Estator_" + str(k)).Parent().Name() != "TCP_Pinza" for k in range(1,5))
            registrar("Parada durante " + fase, pieza=pieza, siguiente=valor("PROXIMA_PIEZA"),
                      completadas=valor("PIEZAS_COMPLETADAS"), lotes=valor("LOTES_COMPLETADOS"))
            antes = valor("PIEZAS_COMPLETADAS")
            time.sleep(.25)
            assert valor("PIEZAS_COMPLETADAS") == antes
        assert valor("PIEZAS_COMPLETADAS") == 8
        assert valor("LOTES_COMPLETADOS") == 1
        registrar("Dos lotes soldados sin repetir piezas", completadas=8,
                  fin_segundo_lote_diferido=True, colisiones=0)
        r.setParam("MODO_ID", 2)
        esperar(lambda: valor("MODO_CONFIRMADO") == 1)
        assert valor("PROXIMA_PIEZA") == 5 and valor("PIEZAS_COMPLETADAS") == 8
        r.setParam("CONF_RESTITUCION", 1)
        r.setParam("MODO_SOLICITADO", 0)
        r.setParam("MODO_ID", 3)
        esperar(lambda: valor("MODO_CONFIRMADO") == 0 and valor("MODO_ACK") == 3)
        assert valor("PROXIMA_PIEZA") == 5 and valor("AUTO_ACTIVO") == 0
        registrar("Mantenimiento y retorno conservan lote parcial", siguiente=5, completadas=8,
                  solicitud_desde_auto_requiere_repeticion=True)
    finally:
        r.setParam("COORDINADOR_ACTIVO", 0)
        r.setParam("SENSORES_VALIDOS", 0)
        time.sleep(.25)
        if p.Busy():
            p.Stop()
        for sub in r.ItemList(ITEM_TYPE_PROGRAM):
            if sub.Busy():
                sub.Stop()
        resultado = {"version": r.Version(), "segundos_reales": time.monotonic()-inicio,
                     "pruebas": pruebas}
        with (raiz / "verificaciones" / "coordinacion_v05.json").open("w", encoding="utf-8", newline="\n") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
            f.write("\n")
        estacion.Delete()
        s = r.AddFile(str(raiz / "Celda_Soldadura_Estator_Grupo4_v05.rdk"))
        r.setActiveStation(s)
        r.setSimulationSpeed(1)


if __name__ == "__main__":
    main()
