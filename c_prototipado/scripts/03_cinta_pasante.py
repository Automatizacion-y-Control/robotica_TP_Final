"""Mejora 01: cinta pasante. Genera la v03 de la celda a partir de la v02.

En la v02 el manipulador toma el estator de la cinta y lo deposita en un pallet,
que el operario retira por una ventana del cerramiento. En la v03 la misma cinta
entra y sale de la celda: el manipulador toma el estator en un punto de la banda
y lo devuelve soldado en otro punto, aguas abajo; la cinta lo saca por la cara
este. El operario ya no tiene que alcanzar ningún objeto dentro de la celda.

Se parte de la v02 guardada (y no de 02_construir_celda.py) para conservar los
eventos de simulación cargados a mano:
    - Evento_Tomar_Pieza (adjuntar a TCP_Pinza) se usa sin cambios.
    - Evento_Soltar_Pieza deja la pieza en el frame que era Frame_Pallet. Ese
      frame se cuelga de Frame_Banda con pose nula y se renombra
      Frame_Piezas_Soldadas: el evento lo sigue por referencia y la pieza
      soltada queda sobre la banda, avanzando con ella.

Cambios sobre la v02:
    1. Se quitan el pallet, su soporte, su cortina y el cerramiento v02.
    2. Se agregan el tramo de salida de la cinta, el cerramiento v03 (abertura
       de salida en la cara este) y una cortina de luz en la entrada y otra en la salida.
    3. La toma pasa a V3_TOMA_X y el depósito a V3_DEPOSITO_X, sobre la banda.
    4. Los cuatro programas de depósito en pallet se reemplazan por uno solo,
       Man_Depositar_Cinta, porque el depósito es siempre el mismo punto.
    5. Fin_Lote evacúa las piezas soldadas fuera de la celda.

Uso:  C:\\RoboDK\\Python-Embedded\\python.exe 03_cinta_pasante.py
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, r"C:\RoboDK\Python")

import parametros_celda as P                                               # noqa: E402
from programa_soldadura import pose_ejes                                   # noqa: E402
from robodk.robolink import (Robolink, ITEM_TYPE_STATION, ITEM_TYPE_ROBOT,  # noqa: E402
                             ITEM_TYPE_TOOL, ITEM_TYPE_FRAME, ITEM_TYPE_OBJECT,
                             ITEM_TYPE_TARGET, ITEM_TYPE_PROGRAM, INSTRUCTION_COMMENT,
                             INSTRUCTION_CALL_PROGRAM, COLLISION_OFF)
from robodk.robomath import Mat, transl, rotz, pi                          # noqa: E402

RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
MODELOS = os.path.join(RAIZ, "modelos")
ARCHIVO_V02 = os.path.join(RAIZ, "Celda_Soldadura_Estator_Grupo4_v02.rdk")
ARCHIVO_V03 = os.path.join(RAIZ, "Celda_Soldadura_Estator_Grupo4_v03.rdk")
NOMBRE_V02 = "Celda_Soldadura_Estator_Grupo4"
NOMBRE_V03 = "Celda_Soldadura_Estator_Grupo4_v03"
L = P.ESTATOR_LARGO
BAJO = [0, 0, -1]

RDK = Robolink()


def item(nombre, tipo=None):
    it = RDK.Item(nombre, tipo) if tipo is not None else RDK.Item(nombre)
    if not it.Valid():
        raise RuntimeError(f"No se encontró {nombre} en la estación")
    return it


def borrar(nombre, tipo=None):
    it = RDK.Item(nombre, tipo) if tipo is not None else RDK.Item(nombre)
    if it.Valid():
        it.Delete()


def comentario(prog, texto):
    prog.RunInstruction(texto, INSTRUCTION_COMMENT)


def llamar(prog, nombre):
    prog.RunInstruction(nombre, INSTRUCTION_CALL_PROGRAM)


def vaciar(prog):
    while prog.InstructionCount() > 0:
        prog.InstructionDelete(0)


# ===========================================================================
# 0. Estación v03 a partir del archivo de la v02
# ===========================================================================
# Se cierran las copias abiertas para que los nombres de los ítems sean únicos.
for nombre in (NOMBRE_V02, NOMBRE_V03):
    abierta = RDK.Item(nombre, ITEM_TYPE_STATION)
    while abierta.Valid():
        abierta.Delete()
        abierta = RDK.Item(nombre, ITEM_TYPE_STATION)
estacion = RDK.AddFile(ARCHIVO_V02)
estacion.setName(NOMBRE_V03)
RDK.setActiveStation(estacion)
RDK.Render(False)

f_celda = item("Frame_Celda", ITEM_TYPE_FRAME)
f_cerr = item("Frame_Cerramiento", ITEM_TYPE_FRAME)
f_banda = item("Frame_Banda", ITEM_TYPE_FRAME)
f_toma = item("Frame_Toma_Cinta", ITEM_TYPE_FRAME)
f_sold = item("Frame_Soldadura", ITEM_TYPE_FRAME)
irb = item("ABB IRB 1200-7/0.7", ITEM_TYPE_ROBOT)
tcp_pinza = item("TCP_Pinza", ITEM_TYPE_TOOL)
cinta = item("Cinta_Entrada", ITEM_TYPE_ROBOT)
cinta.setName("Cinta_Pasante")
cinta.Parent().setName("Base_Cinta_Pasante")

x_base_cinta = P.CINTA_TOMA[0] + 250.0 - P.CINTA_LARGO     # base de la cinta, igual que en la v02
y_toma = P.CINTA_TOMA[1]
y_base_cinta = y_toma - P.CINTA_EJE_Y_REL

# ===========================================================================
# 1. Equipos que salen de la celda
# ===========================================================================
for nombre in ("Pallet_Salida", "Soporte_Pallet", "Cortina_Luz_Pallet",
               "Cerramiento_Paneles", "Cerramiento_Estructura"):
    borrar(nombre, ITEM_TYPE_OBJECT)
for prog in [f"Man_Depositar_P{k}" for k in range(1, P.LOTE + 1)] + ["Cinta_Reinicio_Lote"]:
    borrar(prog, ITEM_TYPE_PROGRAM)
for k in range(1, P.LOTE + 1):
    borrar(f"Man_Pallet_P{k}", ITEM_TYPE_TARGET)
    borrar(f"Man_Pallet_P{k}_Aprox", ITEM_TYPE_TARGET)

# El frame del pallet pasa a la banda con pose nula: las piezas que el evento de
# soltar deja en él quedan sobre la banda y avanzan con el eje de la cinta.
f_piezas = item("Frame_Pallet", ITEM_TYPE_FRAME)
f_piezas.setParent(f_banda)
f_piezas.setPose(Mat(transl(0, 0, 0)))
f_piezas.setName("Frame_Piezas_Soldadas")

# ===========================================================================
# 2. Equipos nuevos
# ===========================================================================
def agregar(archivo, padre, nombre, pose=None, color=None):
    it = RDK.AddFile(os.path.join(MODELOS, archivo), padre)
    it.setName(nombre)
    if pose is not None:
        it.setPose(pose)
    if color:
        it.setColor(color)
    return it


agregar("cerramiento_estructura_v03.stl", f_cerr, "Cerramiento_Estructura", color=[0.20, 0.22, 0.25, 1.0])
agregar("cerramiento_paneles_v03.stl", f_cerr, "Cerramiento_Paneles", color=[0.55, 0.70, 0.85, 0.25])
ext_banda = agregar("cinta_extension_banda.stl", f_celda, "Cinta_Salida_Banda", color=[0.20, 0.20, 0.22, 1.0])
ext_estr = agregar("cinta_extension_estructura.stl", f_celda, "Cinta_Salida_Estructura", color=[0.0, 0.55, 0.95, 1.0])
# Cortinas de luz en el paso de la cinta por el cerramiento (entrada oeste y salida este).
cortina_in = agregar("cortina_luz_cinta.stl", f_cerr, "Cortina_Luz_Entrada",
                     transl(P.CERR_X[0] - 30.0, 0, 0), [0.95, 0.90, 0.10, 1.0])
cortina_out = agregar("cortina_luz_cinta.stl", f_cerr, "Cortina_Luz_Salida",
                      transl(P.CERR_X[1] + 30.0, 0, 0), [0.95, 0.90, 0.10, 1.0])

# ===========================================================================
# 3. Toma y depósito sobre la banda
# ===========================================================================
f_toma.setPose(transl(P.V3_TOMA_X, y_toma, P.CINTA_ALTURA_BANDA))
f_dep = RDK.AddFrame("Frame_Deposito_Cinta", f_celda)
f_dep.setPose(transl(P.V3_DEPOSITO_X, y_toma, P.CINTA_ALTURA_BANDA))
item("Sensor_Pieza_En_Toma", ITEM_TYPE_OBJECT).setPose(
    transl(P.V3_TOMA_X, y_base_cinta - 40.0, P.CINTA_ALTURA_BANDA + 30.0) * rotz(pi / 2))

# Estatores del lote: el estator k queda k pasos aguas arriba de la toma.
poses_lote = {}
for k in range(P.LOTE):
    e = item(f"Estator_{k + 1}", ITEM_TYPE_OBJECT)
    e.setParent(f_banda)
    rel = [P.V3_TOMA_X - k * P.CINTA_PASO - x_base_cinta, y_toma - y_base_cinta, 0.0]
    e.setPose(transl(*rel))
    poses_lote[e.Name()] = rel

# Targets de depósito: mismas poses relativas que la toma (pieza apoyada en la banda).
z_agarre = L - P.PINZA_PROF_AGARRE
t_dep_aprox = RDK.AddTarget("Man_Deposito_Aprox", f_dep, irb)
t_dep_aprox.setAsCartesianTarget()
t_dep_aprox.setPose(pose_ejes([0, 0, L + P.DIST_APROX_PINZA], [1, 0, 0], BAJO))
t_dep = RDK.AddTarget("Man_Deposito", f_dep, irb)
t_dep.setAsCartesianTarget()
t_dep.setPose(pose_ejes([0, 0, z_agarre], [1, 0, 0], BAJO))

# Target de evacuación: avance final de la cinta para sacar el lote soldado.
t_evac = RDK.AddTarget("Cinta_Evacuacion", f_celda, cinta)
t_evac.setAsJointTarget()
t_evac.setJoints([P.V3_AVANCE_EVACUACION])
cinta.setJointsHome([0.0])        # "Ajustar las articulaciones al inicio" la lleva al origen

# ===========================================================================
# 4. Programas
# ===========================================================================
dep = RDK.AddProgram("Man_Depositar_Cinta", irb)
comentario(dep, "Devuelve el estator soldado a la banda, aguas abajo de la toma")
dep.setPoseFrame(f_dep)
dep.setPoseTool(tcp_pinza)
dep.waitDI("SOLDADURA_TERMINADA", 1)
dep.setDO("SOLDADURA_TERMINADA", 0)
dep.setSpeed(P.V_APROX, P.V_ARTICULAR)
dep.addMoveJ(item("Man_Presentar_Lado2", ITEM_TYPE_TARGET))    # punto de partida conocido
dep.addMoveL(item("Man_Presentar_Aprox_Lado2", ITEM_TYPE_TARGET))  # salida recta de la zona de soldadura
dep.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
dep.setRounding(5)
dep.addMoveJ(item("Man_Reposo", ITEM_TYPE_TARGET))             # punto de paso alto
dep.addMoveJ(t_dep_aprox)
dep.setRounding(0)
dep.setSpeed(P.V_APROX, P.V_ARTICULAR)
comentario(dep, "Bajada vertical hasta apoyar la pieza en la banda")
dep.addMoveL(t_dep)
llamar(dep, "Pinza_Cerrar")
llamar(dep, "Evento_Soltar_Pieza")                            # la pieza queda en Frame_Piezas_Soldadas
dep.addMoveL(t_dep_aprox)                                     # salida vertical sin la pieza

# El evento de soltar es el de la v02; solo se actualiza el comentario que lo describe.
soltar = item("Evento_Soltar_Pieza", ITEM_TYPE_PROGRAM)
_, tipo, mov, art, pose, juntas = soltar.Instruction(0)
soltar.setInstruction(0, "Libera el estator sobre la banda (Frame_Piezas_Soldadas)", tipo, mov, art, pose, juntas)

evac = RDK.AddProgram("Cinta_Evacuar", cinta)
comentario(evac, "Avance final: saca el lote soldado por la salida de la celda")
evac.addMoveJ(t_evac)

# Ciclo de cada pieza: igual que en la v02, con el depósito sobre la banda.
# El avance de la cinta al comienzo del ciclo k trae el estator k a la toma y
# corre un paso la pieza soldada en el ciclo anterior, liberando el depósito.
for k in range(1, P.LOTE + 1):
    cp = item(f"Ciclo_Pieza_{k}", ITEM_TYPE_PROGRAM)
    vaciar(cp)
    comentario(cp, f"Ciclo completo del estator {k}: tomar, soldar 4 cordones, devolver a la banda")
    for sub in (f"Cinta_Avanzar_{k}", "Man_Tomar_Cinta", "Man_Presentar_Lado1", "Sold_Par_Cordones",
                "Man_Presentar_Lado2", "Sold_Par_Cordones", "Man_Depositar_Cinta", "Man_Ir_Reposo"):
        llamar(cp, sub)

fin = item("Fin_Lote", ITEM_TYPE_PROGRAM)
vaciar(fin)
comentario(fin, "Lote completo: verificación del TCP y evacuación de las piezas soldadas")
llamar(fin, "Sold_Servicio_Antorcha")
llamar(fin, "Cinta_Evacuar")
comentario(fin, "Reposición del lote (simula al operario que carga la entrada y retira la salida, afuera)")
fin.RunInstruction("EVENTO: Ajustar las articulaciones al inicio -> Cinta_Pasante", INSTRUCTION_COMMENT)
for nombre, rel in poses_lote.items():
    fin.RunInstruction(f"EVENTO: Fijar la posición del objeto (relativa) -> {nombre} = "
                       f"[{rel[0]:.1f}, {rel[1]:.1f}, {rel[2]:.1f}, 0, 0, 0]", INSTRUCTION_COMMENT)

# ===========================================================================
# 5. Colisiones de los equipos nuevos
# ===========================================================================
# Los estatores apoyan sobre el tramo de salida; el resto queda verificado.
for k in range(1, P.LOTE + 1):
    e = item(f"Estator_{k}", ITEM_TYPE_OBJECT)
    for obj in (ext_banda, ext_estr):
        RDK.setCollisionActivePair(COLLISION_OFF, e, obj)

# ===========================================================================
# 6. Estado inicial y guardado
# ===========================================================================
for nombre in ("Man_Reposo", "Sold_Reposo", "Pinza_Abierta", "Cinta_Posicion_1"):
    t = item(nombre, ITEM_TYPE_TARGET)
    t.getLink().setJoints(t.Joints())
RDK.setSimulationSpeed(1)
RDK.Render(True)
estacion.Save(ARCHIVO_V03)
print("Estación v03 guardada en", ARCHIVO_V03)
