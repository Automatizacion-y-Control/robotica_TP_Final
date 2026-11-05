"""Verifica la estación de la celda: alcance de targets, programas y colisiones.

Para cada target cartesiano calcula la cinemática inversa con la herramienta
del robot dueño. Para cada programa ejecuta Update() de RoboDK, que recorre
la trayectoria completa (con verificación de colisiones si se pide) y
devuelve la cantidad de instrucciones válidas, el tiempo estimado y la
distancia recorrida.

No modifica la estación ni ejecuta el ciclo: solo consulta y reporta.

Con --con-pieza, cuelga temporalmente un estator de prueba del TCP de la pinza
para verificar también los choques de la pieza transportada y la holgura entre
la antorcha y el estator en la zona de soldadura. La pieza de prueba se borra
al terminar; los programas no se modifican.

Uso:  C:\\RoboDK\\Python-Embedded\\python.exe verificar_celda.py [--colisiones] [--con-pieza]
"""
import io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, r"C:\RoboDK\Python")
import parametros_celda as P                                                # noqa: E402
from robodk.robolink import (Robolink, ITEM_TYPE_STATION, ITEM_TYPE_TARGET,  # noqa: E402
                             ITEM_TYPE_PROGRAM, ITEM_TYPE_TOOL, ITEM_TYPE_ROBOT,
                             ITEM_TYPE_OBJECT, COLLISION_ON, COLLISION_OFF)
from robodk.robomath import transl, rotx, pi                                 # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NOMBRE_ESTACION = "Celda_Soldadura_Estator_Grupo4"
if "--estacion" in sys.argv:
    NOMBRE_ESTACION = sys.argv[sys.argv.index("--estacion") + 1]
CON_COLISIONES = "--colisiones" in sys.argv
CON_PIEZA = "--con-pieza" in sys.argv
MODELO_ESTATOR = os.path.normpath(os.path.join(AQUI, "..", "modelos", "paquete_estator.stl"))

RDK = Robolink()
estacion = RDK.Item(NOMBRE_ESTACION, ITEM_TYPE_STATION)
if not estacion.Valid():
    sys.exit(f"No está abierta la estación {NOMBRE_ESTACION}")
RDK.setActiveStation(estacion)

# Herramienta con la que se programa cada robot (los targets se resuelven con ella).
HERRAMIENTA = {"ABB IRB 1200-7/0.7": "TCP_Pinza", "ABB CRB 1300-10/1.15": "Antorcha_TIG"}

print("=== Alcance de targets cartesianos ===")
sin_alcance = 0
for t in RDK.ItemList(ITEM_TYPE_TARGET):
    if t.isJointTarget():
        continue
    robot = t.getLink()               # robot asociado al target
    if not robot.Valid() or robot.Name() not in HERRAMIENTA:
        continue
    tool = RDK.Item(HERRAMIENTA[robot.Name()], ITEM_TYPE_TOOL)
    # Pose del TCP respecto de la base del robot: base^-1 * pose absoluta del target.
    pose_base = robot.Parent().PoseAbs().inv() * t.PoseAbs()
    juntas = robot.SolveIK(pose_base, None, tool.PoseTool())
    ok = len(juntas.list()) >= 6
    sin_alcance += 0 if ok else 1
    print(f"  {'OK ' if ok else 'NO '} {robot.Name():22s} {t.Name():28s}"
          + (f" {[round(j, 1) for j in juntas.list()[:6]]}" if ok else ""))
print(f"  Targets fuera de alcance: {sin_alcance}")

def estado_inicial():
    """Lleva robots, pinza y cinta al estado que deja Inicio_Celda.

    Update() simula desde la posición actual de cada mecanismo, así que sin
    este paso cada programa se evaluaría desde donde terminó el anterior.
    """
    for nombre_target in ("Man_Reposo", "Sold_Reposo", "Pinza_Abierta", "Cinta_Posicion_1"):
        t = RDK.Item(nombre_target, ITEM_TYPE_TARGET)
        t.getLink().setJoints(t.Joints())


# Programas que se evalúan solos desde el estado inicial. Los subprogramas que
# dependen de un estado previo (por ejemplo, depositar después de soldar) se
# verifican dentro de su secuencia, en Ciclo_Pieza_k y Programa_Principal.
INDEPENDIENTES = ["Inicio_Celda", "Sold_Servicio_Antorcha", "Sold_Cambio_Tungsteno",
                  "Ciclo_Pieza_1", "Programa_Principal"]

pieza_prueba = None
if CON_PIEZA:
    # Pose del estator respecto del TCP de la pinza: el TCP está
    # PINZA_PROF_AGARRE debajo de la cara superior, con Z de la herramienta
    # entrando en la pieza; el origen del modelo está en la cara inferior.
    tcp = RDK.Item("TCP_Pinza", ITEM_TYPE_TOOL)
    pieza_prueba = RDK.AddFile(MODELO_ESTATOR, tcp)
    if pieza_prueba.Type() != ITEM_TYPE_OBJECT:
        sys.exit("No se pudo colgar la pieza de prueba del TCP")
    pieza_prueba.setName("Estator_Prueba_Verificacion")
    pieza_prueba.setPose(transl(0, 0, P.ESTATOR_LARGO - P.PINZA_PROF_AGARRE) * rotx(pi))
    # Contactos previstos de la pieza transportada: los dedos dentro del
    # agujero y, en la toma, el estator 1 que ocupa el mismo lugar en la cinta.
    pinza = RDK.Item("Pinza_2F85", ITEM_TYPE_ROBOT)
    for i in range(8):
        RDK.setCollisionActivePair(COLLISION_OFF, pieza_prueba, pinza, 0, i)
    for k in range(1, P.LOTE + 1):
        RDK.setCollisionActivePair(COLLISION_OFF, pieza_prueba, RDK.Item(f"Estator_{k}", ITEM_TYPE_OBJECT))
    # Apoyos de la pieza según la versión: banda, tramo de salida, pallet y sensor.
    for nombre in ("Cinta_Entrada", "Cinta_Pasante", "Cinta_Salida_Banda", "Cinta_Salida_Estructura",
                   "Pallet_Salida", "Sensor_Pieza_En_Toma"):
        otro = RDK.Item(nombre)
        if otro.Valid():
            RDK.setCollisionActivePair(COLLISION_OFF, pieza_prueba, otro)
    print("\nPieza de prueba colgada del TCP de la pinza")

print("\n=== Programas (Update desde el estado inicial) ===")
modo = COLLISION_ON if CON_COLISIONES else COLLISION_OFF
resultados = {}
for nombre in INDEPENDIENTES:
    prog = RDK.Item(nombre, ITEM_TYPE_PROGRAM)
    estado_inicial()
    # Paso de muestreo fino (1 mm, 1°): con el paso por defecto se pierden
    # contactos cortos, como el roce de la punta con el escalón de la arista.
    validas, tiempo, distancia, ratio, mensaje = prog.Update(modo, 3600, 1.0, 1.0)
    resultados[nombre] = (tiempo, distancia, ratio)
    estado = "OK " if ratio >= 1.0 else "ERR"
    print(f"  {estado} {nombre:26s} instr. válidas {validas:3.0f}  t={tiempo:7.1f} s"
          f"  d={distancia:8.1f} mm  {mensaje if ratio < 1.0 else ''}")
estado_inicial()

if pieza_prueba is not None:
    pieza_prueba.Delete()            # la estación queda como estaba
    print("Pieza de prueba eliminada")
