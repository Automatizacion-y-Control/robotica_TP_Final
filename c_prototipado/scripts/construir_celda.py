"""Construye en RoboDK la estación de la celda de soldadura de estatores.

Arma la estación completa a partir de parametros_celda.py y de los modelos de
c_prototipado/modelos/: equipos, frames, herramientas, targets y programas.
El resultado se guarda en c_prototipado/Celda_Soldadura_Estator_Grupo4_v02.rdk
(versión con pallet de salida; la v03 se obtiene con mejora_01_cinta_pasante.py).

Alcance del script:
    - Solo CONSTRUYE la estación. No ejecuta ni mueve los robots durante el
      ciclo: todos los movimientos quedan como instrucciones nativas de RoboDK
      (MoveJ, MoveL, MoveC) dentro de los programas.
    - Los eventos de simulación (tomar y soltar la pieza, reponer el lote) no
      pueden crearse desde la API; en cada lugar donde van se deja una
      instrucción de comentario que empieza con "EVENTO:" para agregarlos
      desde el menú de RoboDK.

Requisitos: RoboDK abierto (API en el puerto 20500) y los modelos generados
con generar_modelos.py.

Uso:  C:\\RoboDK\\Python-Embedded\\python.exe construir_celda.py
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, r"C:\RoboDK\Python")

import parametros_celda as P                                   # noqa: E402
import programa_soldadura                                       # noqa: E402
from robodk.robolink import (Robolink, ITEM_TYPE_STATION, ITEM_TYPE_ROBOT,  # noqa: E402
                             ITEM_TYPE_TOOL, INSTRUCTION_COMMENT,
                             INSTRUCTION_CALL_PROGRAM, COLLISION_ON, COLLISION_OFF)
from robodk.robomath import Mat, transl, rotz, roty, rotx, pi  # noqa: E402

RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
MODELOS = os.path.join(RAIZ, "modelos")
BIBLIO = os.path.join(MODELOS, "biblioteca")
ARCHIVO_RDK = os.path.join(RAIZ, "Celda_Soldadura_Estator_Grupo4_v02.rdk")
NOMBRE_ESTACION = "Celda_Soldadura_Estator_Grupo4"

RDK = Robolink()


# ===========================================================================
# Utilidades
# ===========================================================================
def rad(g):
    return g * pi / 180.0


def pose_ejes(pos, x, z):
    """Pose homogénea con origen en pos, eje X en x y eje Z en z (se ortonormaliza).

    Y se obtiene como Z x X, de modo que la terna queda dextrógira.
    """
    def norm(v):
        m = math.sqrt(sum(c * c for c in v))
        return [c / m for c in v]
    z = norm(z)
    # Quita la componente de x sobre z para asegurar ortogonalidad.
    d = sum(x[i] * z[i] for i in range(3))
    x = norm([x[i] - d * z[i] for i in range(3)])
    y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]]
    return Mat([[x[0], y[0], z[0], pos[0]],
                [x[1], y[1], z[1], pos[1]],
                [x[2], y[2], z[2], pos[2]],
                [0, 0, 0, 1]])


def agregar(archivo, padre, nombre=None, pose=None, color=None):
    """Carga un archivo (robot, herramienta u objeto) bajo un padre."""
    it = RDK.AddFile(archivo, padre)
    if nombre:
        it.setName(nombre)
    if pose is not None:
        it.setPose(pose)
    if color:
        it.setColor(color)
    return it


def frame(nombre, padre, pose):
    f = RDK.AddFrame(nombre, padre)
    f.setPose(pose)
    return f


def target_cart(nombre, frame_ref, robot, pose):
    """Target cartesiano (pose del TCP) referido a frame_ref."""
    t = RDK.AddTarget(nombre, frame_ref, robot)
    t.setAsCartesianTarget()
    t.setPose(pose)
    return t


def target_art(nombre, padre, robot, juntas):
    """Target articular (valores de eje), usado para reposos, pinza y cinta."""
    t = RDK.AddTarget(nombre, padre, robot)
    t.setAsJointTarget()
    t.setJoints(juntas)
    return t


class Programa:
    """Envoltorio de un programa de RoboDK con comentarios y llamadas legibles."""

    def __init__(self, nombre, robot):
        self.p = RDK.AddProgram(nombre, robot)
        self.nombre = nombre

    def comentario(self, texto):
        self.p.RunInstruction(texto, INSTRUCTION_COMMENT)

    def evento(self, texto):
        """Marca un evento de simulación pendiente de agregar desde la GUI."""
        self.p.RunInstruction("EVENTO: " + texto, INSTRUCTION_COMMENT)

    def llamar(self, otro):
        self.p.RunInstruction(otro.nombre if isinstance(otro, Programa) else otro,
                              INSTRUCTION_CALL_PROGRAM)

    def __getattr__(self, atributo):
        # Delega en el Item de RoboDK: addMoveJ, addMoveL, addMoveC, setSpeed, ...
        return getattr(self.p, atributo)


# ===========================================================================
# 1. Estación
# ===========================================================================
anterior = RDK.Item(NOMBRE_ESTACION, ITEM_TYPE_STATION)
if anterior.Valid():
    anterior.Delete()              # se reconstruye desde cero para que sea reproducible
estacion = RDK.AddStation(NOMBRE_ESTACION)
RDK.setActiveStation(estacion)
RDK.Render(False)                  # acelera la construcción

# Referencia de la celda: origen en el piso, bajo la base del manipulador.
f_celda = frame("Frame_Celda", estacion, Mat(transl(0, 0, 0)))


# ===========================================================================
# 2. Equipos
# ===========================================================================
# --- Robot manipulador IRB 1200 con pinza Robotiq 2F-85 ---------------------
irb = agregar(os.path.join(BIBLIO, "ABB-IRB-1200-7-0-7.robot"), f_celda)
irb.Parent().setName("Base_Manipulador_IRB1200")
x, y, z, g = P.IRB_BASE
irb.Parent().setPose(transl(x, y, z) * rotz(rad(g)))

pinza = agregar(os.path.join(BIBLIO, "RobotiQ-2F-85-Gripper-Mechanism.robot"), irb)
pinza.setName("Pinza_2F85")
pinza.Parent().setPose(Mat(transl(0, 0, 0)))   # la base de la pinza coincide con la brida
# El modelo de la pinza es un mecanismo sin TCP: se define una herramienta
# sin geometría en el centro de las almohadillas, sobre el eje de la brida.
tcp_pinza = irb.AddTool(transl(0, 0, P.PINZA_TCP_Z), "TCP_Pinza")

# --- Robot soldador CRB 1300 con antorcha TIG ---------------------------------
crb = agregar(os.path.join(BIBLIO, "ABB-CRB-1300-10-1-15.robot"), f_celda)
crb.Parent().setName("Base_Soldador_CRB1300")
x, y, z, g = P.CRB_BASE
crb.Parent().setPose(transl(x, y, z) * rotz(rad(g)))

antorcha = RDK.AddFile(os.path.join(MODELOS, "antorcha_tig.stl"), crb)   # al cargarse sobre un robot queda como herramienta
antorcha.setName("Antorcha_TIG")
antorcha.setPoseTool(transl(0, 0, P.TIG_TCP_Z))                          # TCP en la punta del tungsteno
antorcha.setColor([0.75, 0.20, 0.15, 1.0])

# --- Cinta de entrada (mecanismo lineal, ejemplo 17 de RoboDK) ----------------
cinta = agregar(os.path.join(BIBLIO, "Conveyor.robot"), f_celda)
cinta.setName("Cinta_Entrada")
cinta.Parent().setName("Base_Cinta_Entrada")
x_toma, y_toma = P.CINTA_TOMA
x_base_cinta = x_toma + 250.0 - P.CINTA_LARGO        # la toma queda a 250 mm del final de la banda
y_base_cinta = y_toma - P.CINTA_EJE_Y_REL
cinta.Parent().setPose(transl(x_base_cinta, y_base_cinta, 0))
cinta.setJoints([0])

# Frame solidario a la banda: cuelga del mecanismo y avanza con su eje.
# (Un objeto cargado directamente sobre un robot o mecanismo se convierte en
# herramienta; por eso las piezas cuelgan de este frame y no de la cinta.)
f_banda = RDK.AddFrame("Frame_Banda", cinta)
f_banda.setPose(Mat(transl(0, 0, 0)))       # AddFrame no garantiza pose nula: se fija en la brida
# Con el eje en 0, la brida del mecanismo está sobre la base, a la altura de la
# banda; avanza en +X con el eje. Las piezas se ubican con su pose RELATIVA a
# Frame_Banda (setPoseAbs no es confiable sobre un frame recién creado).
# Estatores del lote apoyados sobre la banda. El estator k llega a la toma
# cuando la cinta avanza k pasos.
estatores = []
for k in range(P.LOTE):
    e = RDK.AddFile(os.path.join(MODELOS, "paquete_estator.stl"), f_banda)
    e.setName(f"Estator_{k + 1}")
    e.setPose(transl(x_toma - k * P.CINTA_PASO - x_base_cinta, y_toma - y_base_cinta, 0))
    e.setColor([0.62, 0.64, 0.68, 1.0])
    estatores.append(e)

# Sensor láser al final de la banda: detecta el estátor en la posición de toma.
sensor = agregar(os.path.join(BIBLIO, "Laser-Sensor.stl"), f_celda, "Sensor_Pieza_En_Toma",
                 transl(x_toma, y_base_cinta - 40.0, P.CINTA_ALTURA_BANDA + 30.0) * rotz(rad(90)))

# --- Pallet de salida sobre su soporte ----------------------------------------
cx, cy = P.PALLET_CENTRO
agregar(os.path.join(MODELOS, "soporte_pallet.stl"), f_celda, "Soporte_Pallet",
        transl(cx, cy, 0), [0.30, 0.35, 0.45, 1.0])
z_pallet = P.SOPORTE_PALLET_ALTURA + P.PALLET_ESPESOR       # cara superior del pallet
agregar(os.path.join(MODELOS, "pallet_4_posiciones.stl"), f_celda, "Pallet_Salida",
        transl(cx - P.PALLET_LADO / 2, cy - P.PALLET_LADO / 2, P.SOPORTE_PALLET_ALTURA),
        [0.55, 0.40, 0.25, 1.0])

# --- Estación de servicio de la antorcha ---------------------------------------
sx, sy = P.SERVICIO_BASE
agregar(os.path.join(MODELOS, "estacion_servicio_antorcha.stl"), f_celda,
        "Estacion_Servicio_Antorcha", transl(sx, sy, 0), [0.95, 0.75, 0.10, 1.0])

# --- Cerramiento, puerta y cortina de luz --------------------------------------
f_cerr = frame("Frame_Cerramiento", f_celda, Mat(transl(0, 0, 0)))
agregar(os.path.join(MODELOS, "cerramiento_estructura.stl"), f_cerr, "Cerramiento_Estructura",
        color=[0.20, 0.22, 0.25, 1.0])
agregar(os.path.join(MODELOS, "cerramiento_paneles.stl"), f_cerr, "Cerramiento_Paneles",
        color=[0.55, 0.70, 0.85, 0.25])                       # paneles translúcidos
f_bisagra = frame("Bisagra_Puerta", f_cerr, transl(P.CERR_X[1], P.CERR_PUERTA_Y[0], 0))
agregar(os.path.join(MODELOS, "puerta.stl"), f_bisagra, "Puerta", color=[0.95, 0.65, 0.10, 0.6])
agregar(os.path.join(MODELOS, "cortina_luz.stl"), f_cerr, "Cortina_Luz_Pallet",
        transl(P.CERR_X[1], 0, 0), [0.95, 0.90, 0.10, 1.0])


# ===========================================================================
# 3. Frames de trabajo
# ===========================================================================
# Zona de soldadura: centro del estátor presentado, ejes alineados con la celda.
# El eje del estátor queda en +Y, hacia el soldador.
f_sold = frame("Frame_Soldadura", f_celda, transl(*P.SOLD_CENTRO))
# Toma en la cinta: centro de la cara inferior del estátor apoyado en la banda.
f_toma = frame("Frame_Toma_Cinta", f_celda, transl(x_toma, y_toma, P.CINTA_ALTURA_BANDA))
# Pallet: centro de la cara superior del pallet.
f_pallet = frame("Frame_Pallet", f_celda, transl(cx, cy, z_pallet))
# Servicio: centro de la base del pedestal.
f_serv = frame("Frame_Servicio", f_celda, transl(sx, sy, 0))


# ===========================================================================
# 4. Targets
# ===========================================================================
L = P.ESTATOR_LARGO
BAJO = [0, 0, -1]            # herramienta apuntando hacia abajo

# --- Reposos --------------------------------------------------------------------
t_irb_reposo = target_art("Man_Reposo", f_celda, irb, P.IRB_REPOSO)
t_crb_reposo = target_art("Sold_Reposo", f_celda, crb, P.CRB_REPOSO)

# --- Pinza (valores del eje del mecanismo, apertura en mm) ----------------------
t_pz_abierta = target_art("Pinza_Abierta", f_celda, pinza, [P.PINZA_ABIERTA])
t_pz_cerrada = target_art("Pinza_Cerrada", f_celda, pinza, [P.PINZA_CERRADA])
t_pz_sujeta = target_art("Pinza_Sujeta", f_celda, pinza, [P.PINZA_SUJETA])

# --- Cinta (avance acumulado del eje lineal) -------------------------------------
t_cinta = [target_art(f"Cinta_Posicion_{k + 1}", f_celda, cinta, [k * P.CINTA_PASO])
           for k in range(P.LOTE)]

# --- Manipulador: toma en la cinta ------------------------------------------------
# TCP dentro del agujero, a PINZA_PROF_AGARRE de la cara superior.
z_agarre = L - P.PINZA_PROF_AGARRE
t_toma_aprox = target_cart("Man_Toma_Aprox", f_toma, irb,
                           pose_ejes([0, 0, L + P.DIST_APROX_PINZA], [1, 0, 0], BAJO))
t_toma = target_cart("Man_Toma", f_toma, irb, pose_ejes([0, 0, z_agarre], [1, 0, 0], BAJO))

# --- Manipulador: presentación al soldador ------------------------------------------
# Eje de la pinza = eje del estátor = +Y. La cara del lado de la pinza está en
# y = -L/2 y el TCP queda PINZA_PROF_AGARRE adentro.
y_tcp_pres = -L / 2 + P.PINZA_PROF_AGARRE
t_pres_aprox = target_cart("Man_Presentar_Aprox", f_sold, irb,
                           pose_ejes([0, y_tcp_pres - 150.0, 0], [1, 0, 0], [0, 1, 0]))
t_pres_1 = target_cart("Man_Presentar_Lado1", f_sold, irb,
                       pose_ejes([0, y_tcp_pres, 0], [1, 0, 0], [0, 1, 0]))
# Lado 2: mismo punto, girado 180° sobre el eje de la pinza para llevar arriba
# las dos aristas que estaban abajo. Se define como target ARTICULAR (J6 + 180°)
# porque la misma pose también se alcanza volteando la muñeca (J4 y J5), un
# movimiento mayor y que barre la zona de soldadura.
def juntas_ik(robot, frame_ref, pose_local, herramienta, referencia):
    """Cinemática inversa de una pose expresada en frame_ref.

    Se calcula con la pose del frame (y no con la del target recién creado,
    que puede no estar actualizada todavía) y se valida el resultado.
    """
    pose_base = robot.Parent().PoseAbs().inv() * frame_ref.PoseAbs() * pose_local
    q = robot.SolveIK(pose_base, referencia, herramienta.PoseTool()).list()
    if len(q) < 6 or all(abs(v) < 1e-6 for v in q):
        raise RuntimeError(f"Sin solución de IK para {robot.Name()} en {frame_ref.Name()}")
    return q


q_pres_1 = juntas_ik(irb, f_sold, t_pres_1.Pose(), tcp_pinza, P.IRB_REPOSO)
q_pres_aprox_1 = juntas_ik(irb, f_sold, t_pres_aprox.Pose(), tcp_pinza, q_pres_1)


def girar_j6(q):
    q = list(q)
    q[5] = q[5] + 180.0 if q[5] <= 180.0 else q[5] - 180.0    # J6 admite ±360°
    return q


t_pres_2 = target_art("Man_Presentar_Lado2", f_sold, irb, girar_j6(q_pres_1))
# Salida de la zona de soldadura con la orientación del lado 2, para que el
# retiro recto no incluya un giro de 180°.
t_pres_aprox_2 = target_art("Man_Presentar_Aprox_Lado2", f_sold, irb, girar_j6(q_pres_aprox_1))

# --- Manipulador: depósito en el pallet ---------------------------------------------
d = P.PALLET_PASO / 2
posiciones_pallet = [(-d, -d), (d, -d), (-d, d), (d, d)]
t_dep, t_dep_aprox = [], []
for k, (px, py) in enumerate(posiciones_pallet):
    t_dep_aprox.append(target_cart(f"Man_Pallet_P{k + 1}_Aprox", f_pallet, irb,
                                   pose_ejes([px, py, L + P.DIST_APROX_PINZA], [1, 0, 0], BAJO)))
    t_dep.append(target_cart(f"Man_Pallet_P{k + 1}", f_pallet, irb,
                             pose_ejes([px, py, z_agarre], [1, 0, 0], BAJO)))

# --- Soldador: par de cordones de las dos aristas superiores ---------------------------
# La geometría de los cordones y de la transición está en programa_soldadura.py,
# compartida con actualizar_soldadura.py.
t_sold = programa_soldadura.crear_targets(RDK, crb, f_sold)

# --- Soldador: servicio de la antorcha --------------------------------------------------
xp, yp, zp = P.SERVICIO_PUNTO
t_serv_aprox = target_cart("Serv_Aprox", f_serv, crb, pose_ejes([xp, yp, zp + 80.0], [1, 0, 0], BAJO))
# La punta se detiene 3 mm sobre el cruce de los haces (modelados como barras
# de 2 mm): el dispositivo real mide la posición de la punta al cortar los haces.
t_serv_tcp = target_cart("Serv_Verificacion_TCP", f_serv, crb, pose_ejes([xp, yp, zp + 3.0], [1, 0, 0], BAJO))
t_serv_cambio = target_cart("Serv_Cambio_Tungsteno", f_serv, crb,
                            pose_ejes([0, -65.0, 900.0 + 15.0 + 120.0], [1, 0, 0], BAJO))


# ===========================================================================
# 5. Programas
# ===========================================================================
# --- Pinza ---------------------------------------------------------------------------
pz_abrir = Programa("Pinza_Abrir", pinza)
pz_abrir.comentario("Apertura máxima: reposo de la pinza")
pz_abrir.addMoveJ(t_pz_abierta)

pz_cerrar = Programa("Pinza_Cerrar", pinza)
pz_cerrar.comentario("Dedos juntos para entrar o salir del agujero del estator")
pz_cerrar.addMoveJ(t_pz_cerrada)

pz_sujetar = Programa("Pinza_Sujetar", pinza)
pz_sujetar.comentario("Agarre interior: los dedos se abren contra el agujero de Ø55")
pz_sujetar.addMoveJ(t_pz_sujeta)

# --- Cinta ---------------------------------------------------------------------------
prog_cinta = []
for k in range(P.LOTE):
    pc = Programa(f"Cinta_Avanzar_{k + 1}", cinta)
    pc.comentario(f"Lleva el estator {k + 1} del lote a la posición de toma")
    pc.addMoveJ(t_cinta[k])
    pc.comentario("Señal del sensor láser: hay pieza en la toma")
    pc.setDO("PIEZA_EN_TOMA", 1)
    prog_cinta.append(pc)

cinta_reinicio = Programa("Cinta_Reinicio_Lote", cinta)
cinta_reinicio.comentario("Vuelve el eje de la cinta al origen para el lote siguiente")
cinta_reinicio.addMoveJ(t_cinta[0])

# --- Eventos de simulación de la pinza -------------------------------------------------
# Cada evento vive en un subprograma propio para que se cargue una sola vez
# desde la GUI y lo reutilicen la toma y los cuatro depósitos.
evt_tomar = Programa("Evento_Tomar_Pieza", irb)
evt_tomar.comentario("Engancha a TCP_Pinza el estator que la pinza acaba de sujetar")
evt_tomar.evento("Adjuntar objeto -> herramienta TCP_Pinza")

evt_soltar = Programa("Evento_Soltar_Pieza", irb)
evt_soltar.comentario("Libera el estator sobre el pallet")
evt_soltar.evento("Desacoplar objeto de TCP_Pinza -> dejar en Frame_Pallet")

# --- Manipulador ---------------------------------------------------------------------
man_reposo = Programa("Man_Ir_Reposo", irb)
man_reposo.comentario("Posición de reposo fuera de la zona de soldadura")
man_reposo.setPoseTool(tcp_pinza)
man_reposo.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
man_reposo.addMoveJ(t_irb_reposo)

man_tomar = Programa("Man_Tomar_Cinta", irb)
man_tomar.comentario("Toma el estator de la cinta con agarre interior")
man_tomar.setPoseFrame(f_toma)
man_tomar.setPoseTool(tcp_pinza)
man_tomar.waitDI("PIEZA_EN_TOMA", 1)
man_tomar.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
man_tomar.setRounding(5)
man_tomar.addMoveJ(t_toma_aprox)                  # traslado libre sobre la pieza
man_tomar.llamar(pz_cerrar)
man_tomar.setRounding(0)
man_tomar.setSpeed(P.V_APROX, P.V_ARTICULAR)
man_tomar.comentario("Entrada vertical en el agujero: MoveL para no rozar la pieza")
man_tomar.addMoveL(t_toma)
man_tomar.llamar(pz_sujetar)
man_tomar.llamar(evt_tomar)                       # la pieza pasa a moverse con la pinza
man_tomar.setDO("PIEZA_EN_TOMA", 0)
man_tomar.addMoveL(t_toma_aprox)                  # salida vertical con la pieza

man_presentar_1 = Programa("Man_Presentar_Lado1", irb)
man_presentar_1.comentario("Presenta las aristas A y B arriba, con el eje del estator hacia el soldador")
man_presentar_1.setPoseFrame(f_sold)
man_presentar_1.setPoseTool(tcp_pinza)
man_presentar_1.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
man_presentar_1.addMoveJ(t_pres_aprox)            # reorientación de vertical a horizontal
man_presentar_1.setSpeed(P.V_APROX, P.V_ARTICULAR)
man_presentar_1.addMoveL(t_pres_1)                # entrada recta a la posición de soldadura
man_presentar_1.setDO("PIEZA_PRESENTADA", 1)

man_presentar_2 = Programa("Man_Presentar_Lado2", irb)
man_presentar_2.comentario("Gira 180° sobre el eje de la pinza (J6) para subir las aristas C y D")
man_presentar_2.setPoseFrame(f_sold)
man_presentar_2.setPoseTool(tcp_pinza)
man_presentar_2.waitDI("SOLDADURA_TERMINADA", 1)
man_presentar_2.setDO("SOLDADURA_TERMINADA", 0)
man_presentar_2.setSpeed(P.V_APROX, P.V_ARTICULAR)
man_presentar_2.addMoveJ(t_pres_2)                # giro en el lugar; el soldador ya se retiró
man_presentar_2.setDO("PIEZA_PRESENTADA", 1)

man_depositar = []
for k in range(P.LOTE):
    pd = Programa(f"Man_Depositar_P{k + 1}", irb)
    pd.comentario(f"Deposita el estator soldado en la posición {k + 1} del pallet")
    pd.setPoseFrame(f_pallet)
    pd.setPoseTool(tcp_pinza)
    pd.waitDI("SOLDADURA_TERMINADA", 1)
    pd.setDO("SOLDADURA_TERMINADA", 0)
    pd.setSpeed(P.V_APROX, P.V_ARTICULAR)
    pd.addMoveJ(t_pres_2)                         # punto de partida conocido (sin movimiento en el ciclo)
    pd.addMoveL(t_pres_aprox_2)                   # salida recta de la zona de soldadura
    pd.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
    pd.setRounding(5)
    pd.addMoveJ(t_irb_reposo)                     # punto de paso alto (reposo), sin barrer el pallet
    pd.addMoveJ(t_dep_aprox[k])
    pd.setRounding(0)
    pd.setSpeed(P.V_APROX, P.V_ARTICULAR)
    pd.addMoveL(t_dep[k])                         # bajada vertical a la posición
    pd.llamar(pz_cerrar)
    pd.llamar(evt_soltar)                         # la pieza queda en el pallet
    pd.addMoveL(t_dep_aprox[k])                   # salida vertical sin la pieza
    man_depositar.append(pd)

# --- Soldador ------------------------------------------------------------------------
sold_reposo = Programa("Sold_Ir_Reposo", crb)
sold_reposo.comentario("Reposo del soldador fuera del volumen de giro de la pieza")
sold_reposo.setPoseTool(antorcha)
sold_reposo.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
sold_reposo.addMoveJ(t_crb_reposo)

sold_par = Programa(programa_soldadura.NOMBRE_PROGRAMA, crb)
programa_soldadura.cargar_programa(sold_par.p, t_sold, antorcha, f_sold, sold_reposo.nombre)

sold_servicio = Programa("Sold_Servicio_Antorcha", crb)
sold_servicio.comentario("Verificación del TCP al final de cada lote")
sold_servicio.setPoseFrame(f_serv)
sold_servicio.setPoseTool(antorcha)
sold_servicio.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
sold_servicio.addMoveJ(t_serv_aprox)
sold_servicio.setSpeed(P.V_APROX, P.V_ARTICULAR)
sold_servicio.comentario("Bajada vertical hasta el cruce de los haces")
sold_servicio.addMoveL(t_serv_tcp)
sold_servicio.addMoveL(t_serv_aprox)
sold_servicio.llamar(sold_reposo)

sold_cambio = Programa("Sold_Cambio_Tungsteno", crb)
sold_cambio.comentario("Cambio o reafilado del tungsteno. Se ejecuta a pedido, con la celda detenida")
sold_cambio.setPoseFrame(f_serv)
sold_cambio.setPoseTool(antorcha)
sold_cambio.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
sold_cambio.addMoveJ(t_serv_cambio)
sold_cambio.comentario("Pausa para el operario: abrir puerta, cambiar electrodo, ajustar saliente")
sold_cambio.Pause(-1)
sold_cambio.llamar(sold_servicio)                # tras el cambio, siempre se verifica el TCP

# --- Secuencia --------------------------------------------------------------------------
inicio = Programa("Inicio_Celda", irb)
inicio.comentario("Estado inicial conocido: robots en reposo, pinza abierta, arco apagado")
inicio.setDO("ARCO_TIG", 0)
inicio.setDO("PIEZA_EN_TOMA", 0)
inicio.setDO("PIEZA_PRESENTADA", 0)
inicio.setDO("SOLDADURA_TERMINADA", 0)
inicio.llamar(sold_reposo)
inicio.llamar(man_reposo)
inicio.llamar(pz_abrir)

ciclos = []
for k in range(P.LOTE):
    cp = Programa(f"Ciclo_Pieza_{k + 1}", irb)
    cp.comentario(f"Ciclo completo del estator {k + 1}: tomar, soldar 4 cordones, depositar")
    cp.llamar(prog_cinta[k])
    cp.llamar(man_tomar)
    cp.llamar(man_presentar_1)
    cp.llamar(sold_par)                          # aristas A y B
    cp.llamar(man_presentar_2)
    cp.llamar(sold_par)                          # aristas C y D (mismo programa, pieza girada)
    cp.llamar(man_depositar[k])
    cp.llamar(man_reposo)
    ciclos.append(cp)

fin_lote = Programa("Fin_Lote", irb)
fin_lote.comentario("Pallet completo: verificación del TCP y reposición del lote")
fin_lote.llamar(sold_servicio)
fin_lote.llamar(cinta_reinicio)
fin_lote.evento("Reposicion del lote: estatores del pallet a la cinta (simula al operario)")

principal = Programa("Programa_Principal", irb)
principal.comentario("Celda de soldadura TIG de paquetes de estator - Grupo 4")
principal.comentario("Un lote = 4 estatores = un pallet. El programa se repite en bucle")
principal.llamar(inicio)
for cp in ciclos:
    principal.llamar(cp)
principal.llamar(fin_lote)


# ===========================================================================
# 6. Colisiones
# ===========================================================================
# Se desactivan solo los contactos que existen por diseño:
#   - herramientas montadas sobre la brida (pinza e IRB, antorcha y CRB);
#   - eslabones de la pinza entre sí (mecanismo articulado);
#   - estator apoyado en la banda o en el pallet, y dedos dentro del agujero.
# Todo lo demás (robots entre sí, con la pieza, el cerramiento, la cinta,
# el pallet y la estación de servicio) queda verificado.
RDK.setCollisionActive(COLLISION_ON)
N_ESLABONES_PINZA = 7
for i in range(N_ESLABONES_PINZA):
    for j in range(i + 1, N_ESLABONES_PINZA):
        RDK.setCollisionActivePair(COLLISION_OFF, pinza, pinza, i, j)
    for k in (5, 6):
        RDK.setCollisionActivePair(COLLISION_OFF, irb, pinza, k, i)
for k in (5, 6):
    RDK.setCollisionActivePair(COLLISION_OFF, crb, antorcha, k, 0)
# El modelo del sensor láser incluye el haz como geometría; el haz es luz y no
# debe contar como colisión, así que el sensor se excluye de la verificación.
for otro in (irb, crb, pinza, cinta, antorcha):
    for i in range(8):
        RDK.setCollisionActivePair(COLLISION_OFF, sensor, otro, 0, i)
pallet_item = RDK.Item("Pallet_Salida")
for e in estatores:
    RDK.setCollisionActivePair(COLLISION_OFF, e, sensor)
    RDK.setCollisionActivePair(COLLISION_OFF, e, cinta)
    RDK.setCollisionActivePair(COLLISION_OFF, e, pallet_item)
    for i in range(N_ESLABONES_PINZA):
        RDK.setCollisionActivePair(COLLISION_OFF, e, pinza, 0, i)

# Simulación en tiempo real (1x) para que la ejecución se vea a velocidad real.
RDK.setSimulationSpeed(1)
RDK.Render(True)
estacion.Save(ARCHIVO_RDK)
print("Estación guardada en", ARCHIVO_RDK)
