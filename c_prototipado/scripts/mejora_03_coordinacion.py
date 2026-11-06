"""Genera v05 desde v04: arranque y parada entre piezas con índice retenido.

El coordinador se ejecuta desde RoboDK y solo consulta señales. El panel
posterior no debe ejecutar programas ni decidir la secuencia de movimientos.
Esta etapa no implementa interrupción inmediata ni recuperación desde fallas.
"""
from pathlib import Path
import shutil
import socket
import sys
import tempfile

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import (Robolink, ITEM_TYPE_PROGRAM, INSTRUCTION_INSERT_CODE,
                            INSTRUCTION_CALL_PROGRAM, INSTRUCTION_COMMENT)

RAIZ = Path(__file__).resolve().parent.parent
INICIALES = {
    "COORDINADOR_ACTIVO": 1, "PERMISO_OPERACION": 0,
    "ARRANQUE_ID": 0, "ARRANQUE_ACK": 0, "PARADA_ID": 0, "PARADA_ACK": 0,
    "AUTO_ACTIVO": 0, "ESTADO_CONTROL": 0, "CAUSA_RECHAZO": 0,
    "PROXIMA_PIEZA": 1, "PIEZA_ACTIVA": 0, "CELDA_INICIALIZADA": 0,
    "PIEZAS_COMPLETADAS": 0, "LOTES_COMPLETADOS": 0,
}


def construir():
    puerto = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else 20500
    # Evita que Robolink arranque una instancia sin elevación al no encontrar servidor.
    with socket.create_connection(("localhost", puerto), timeout=3):
        pass
    rdk = Robolink(port=puerto)
    licencia, _ = rdk.License()
    es_prueba = "trial" in licencia.casefold() or "prueba" in licencia.casefold()
    if not es_prueba and any(nombre in licencia.casefold() for nombre in ("free", "gratis", "expired", "caducad")):
        raise RuntimeError("RoboDK no tiene licencia validada. Abrir como administrador antes de generar v05.")
    carpeta_temporal = Path(tempfile.mkdtemp(prefix="construccion_v05_"))
    base = carpeta_temporal / "base_v04.rdk"
    shutil.copy2(RAIZ / "Celda_Soldadura_Estator_Grupo4_v04.rdk", base)
    estacion = rdk.AddFile(str(base))
    estacion.setName("Celda_Soldadura_Estator_Grupo4_v05")
    assert estacion.setParam("FlowControl", "1") == "OK"
    anterior = rdk.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
    anterior.setName("Produccion_Lote_Completo_Antecedente")
    p = rdk.AddProgram("Programa_Principal")

    def codigo(texto):
        p.RunInstruction(texto, INSTRUCTION_INSERT_CODE)

    def llamar(nombre):
        p.RunInstruction(nombre, INSTRUCTION_CALL_PROGRAM)

    def salida(nombre, valor):
        p.setDO(nombre, valor)

    p.RunInstruction("Coordinador v05: iniciar desde RoboDK; mandos por señales. "
                     "PERMISO_OPERACION no es una parada inmediata de protección.", INSTRUCTION_COMMENT)
    codigo("WHILE COORDINADOR_ACTIVO == 1")
    # Se capturan solicitudes: dos IF separados no deben modificar su selección entre ramas.
    salida("PEDIDO_PARADA", 0)
    codigo("IF PARADA_ID != PARADA_ACK")
    salida("PEDIDO_PARADA", 1)
    codigo("END")
    codigo("IF PEDIDO_PARADA == 1")
    codigo("IF AUTO_ACTIVO == 1")
    llamar("Parada_Ciclo")
    codigo("END")
    salida("AUTO_ACTIVO", 0)
    salida("ESTADO_CONTROL", 2)
    codigo("PARADA_ACK = PARADA_ID")
    codigo("END")

    codigo("IF ARRANQUE_ID != ARRANQUE_ACK")
    codigo("ARRANQUE_ACK = ARRANQUE_ID")
    salida("CAUSA_RECHAZO", 1)
    codigo("IF PEDIDO_PARADA == 0")
    codigo("IF AUTO_ACTIVO == 0")
    codigo("IF PERMISO_OPERACION == 1")
    salida("CAUSA_RECHAZO", 0)
    codigo("IF CELDA_INICIALIZADA == 0")
    llamar("Inicio_Celda")
    salida("CELDA_INICIALIZADA", 1)
    codigo("END")
    salida("AUTO_ACTIVO", 1)
    salida("ESTADO_CONTROL", 1)
    codigo("END")
    codigo("END")
    codigo("END")
    codigo("END")

    # La pérdida de permiso se retiene al volver de la pieza, sin autoarranque al recuperarlo.
    codigo("IF AUTO_ACTIVO == 1")
    codigo("IF PERMISO_OPERACION == 0")
    llamar("Parada_Ciclo")
    salida("AUTO_ACTIVO", 0)
    salida("ESTADO_CONTROL", 3)
    codigo("END")
    codigo("END")

    codigo("IF AUTO_ACTIVO == 1")
    codigo("INDICE_CAPTURADO = PROXIMA_PIEZA")
    for k in range(1, 5):
        codigo(f"IF INDICE_CAPTURADO == {k}")
        salida("PIEZA_ACTIVA", k)
        llamar(f"Ciclo_Pieza_{k}")
        salida("PIEZA_ACTIVA", 0)
        salida("PROXIMA_PIEZA", k + 1)
        codigo("PIEZAS_COMPLETADAS = PIEZAS_COMPLETADAS + 1")
        codigo("END")
    codigo("IF INDICE_CAPTURADO == 5")
    llamar("Fin_Lote")
    codigo("LOTES_COMPLETADOS = LOTES_COMPLETADOS + 1")
    salida("PROXIMA_PIEZA", 1)
    codigo("END")
    codigo("END")
    p.Pause(100)
    codigo("END")
    # Salir del coordinador no ejecuta una recuperación ni abre la pinza.
    salida("AUTO_ACTIVO", 0)
    for nombre, valor in INICIALES.items():
        rdk.setParam(nombre, valor)
    ruta = RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"
    estacion.Save(str(ruta))
    base.unlink()
    carpeta_temporal.rmdir()
    print("Guardada", ruta, flush=True)
    return rdk, estacion


if __name__ == "__main__":
    construir()
