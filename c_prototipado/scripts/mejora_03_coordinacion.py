"""Genera v05 desde v04: coordinador con índice retenido y panel embebido.

Programa_Principal sigue siendo el ciclo nativo, que funciona solo. Coordinador_Panel se
ejecuta desde RoboDK y solo consulta señales; el panel no ejecuta programas ni decide la
secuencia de movimientos. Se entrega solo el .rdk: Panel_Operador va embebido.
Esta etapa no implementa interrupción inmediata ni recuperación desde fallas.
"""
from pathlib import Path
import shutil
import socket
import sys
import tempfile

sys.path.insert(0, r"C:\RoboDK\Python")
from empaquetar_panel import generar
from modos_nativos import instalar, INICIALES_MODOS
from robodk.robolink import (Robolink, ITEM_TYPE_PROGRAM, ITEM_TYPE_PROGRAM_PYTHON, INSTRUCTION_INSERT_CODE,
                            INSTRUCTION_CALL_PROGRAM, INSTRUCTION_COMMENT)

RAIZ = Path(__file__).resolve().parent.parent
INICIALES = {
    "COORDINADOR_ACTIVO": 1, "PERMISO_OPERACION": 0,
    "ARRANQUE_ID": 0, "ARRANQUE_ACK": 0, "PARADA_ID": 0, "PARADA_ACK": 0,
    "AUTO_ACTIVO": 0, "ESTADO_CONTROL": 0, "CAUSA_RECHAZO": 0,
    "PROXIMA_PIEZA": 1, "PIEZA_ACTIVA": 0, "CELDA_INICIALIZADA": 0,
    "PIEZAS_COMPLETADAS": 0, "LOTES_COMPLETADOS": 0,
}

# De menor a mayor prioridad; códigos en modos_nativos.CAUSAS.
CONDICIONES_ARRANQUE = (
    ("CINTA_DISPONIBLE == 0", 7), ("CRB_DISPONIBLE == 0", 7), ("IRB_DISPONIBLE == 0", 7),
    ("CINTA_DETENIDA == 0", 6), ("PIEZA_SUJETA_SENSOR == 1", 5),
    ("CRB_EN_REPOSO == 0", 4), ("IRB_EN_REPOSO == 0", 4), ("SENSORES_VALIDOS == 0", 3),
    ("MODO_CONFIRMADO != 0", 8), ("MODO_EN_TRANSICION == 1", 2),
    ("PERMISO_OPERACION == 0", 1), ("AUTO_ACTIVO == 1", 12),
)


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
    principal = rdk.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
    principal.InstructionSelect(0)
    principal.RunInstruction("Ciclo nativo de un lote de 4 estatores; no necesita el panel", INSTRUCTION_COMMENT)
    principal.InstructionDelete(2)  # Comentario heredado sobre el pallet y el bucle.
    instalar(rdk)
    p = rdk.AddProgram("Coordinador_Panel")

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
    # Prevalece la parada: se descarta el arranque pendiente al detectarla. El que llegue
    # después, durante la parada, es una orden posterior y se atiende en la vuelta siguiente.
    codigo("IF ARRANQUE_ID != ARRANQUE_ACK")
    salida("CAUSA_RECHAZO", 13)
    codigo("ARRANQUE_ACK = ARRANQUE_ID")
    codigo("END")
    codigo("IF AUTO_ACTIVO == 1")
    llamar("Parada_Entre_Piezas")
    codigo("END")
    salida("AUTO_ACTIVO", 0)
    salida("ESTADO_CONTROL", 2)
    codigo("PARADA_ACK = PARADA_ID")
    codigo("END")

    llamar("Atender_Solicitud_Modo")
    llamar("Confirmar_Posicion_Modo")

    # Una vuelta dura ~0,3 s: un arranque llegado junto a una parada espera a la siguiente.
    codigo("IF PEDIDO_PARADA == 0")
    codigo("IF ARRANQUE_ID != ARRANQUE_ACK")
    salida("CAUSA_RECHAZO", 0)
    # Sin ELSE validado: cada condición escribe su causa y la última escrita prevalece.
    for condicion, causa in CONDICIONES_ARRANQUE:
        codigo("IF " + condicion)
        salida("CAUSA_RECHAZO", causa)
        codigo("END")
    # El acuse va después de la causa: quien lo lee debe encontrar el resultado ya escrito.
    codigo("ARRANQUE_ACK = ARRANQUE_ID")
    codigo("IF CAUSA_RECHAZO == 0")
    codigo("IF CELDA_INICIALIZADA == 0")
    llamar("Inicio_Celda")
    salida("CELDA_INICIALIZADA", 1)
    codigo("END")
    salida("AUTO_ACTIVO", 1)
    salida("ESTADO_CONTROL", 1)
    codigo("END")
    codigo("END")
    codigo("END")

    # La pérdida de permiso se retiene al volver de la pieza, sin autoarranque al recuperarlo.
    codigo("IF AUTO_ACTIVO == 1")
    codigo("IF PERMISO_OPERACION == 0")
    llamar("Parada_Entre_Piezas")
    salida("AUTO_ACTIVO", 0)
    salida("ESTADO_CONTROL", 3)
    codigo("END")
    codigo("END")

    for condicion in ("SENSORES_VALIDOS == 0", "IRB_DISPONIBLE == 0",
                      "CRB_DISPONIBLE == 0", "CINTA_DISPONIBLE == 0"):
        codigo("IF AUTO_ACTIVO == 1")
        codigo("IF " + condicion)
        llamar("Parada_Entre_Piezas")
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
    for nombre, valor in {**INICIALES, **INICIALES_MODOS}.items():
        rdk.setParam(nombre, valor)
    panel = rdk.AddFile(str(generar(carpeta_temporal / "Panel_Operador.py")), estacion)
    assert panel.Valid() and panel.Type() == ITEM_TYPE_PROGRAM_PYTHON
    ruta = RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"
    estacion.Save(str(ruta))
    shutil.rmtree(carpeta_temporal)
    print("Guardada", ruta, flush=True)
    return rdk, estacion


if __name__ == "__main__":
    construir()
