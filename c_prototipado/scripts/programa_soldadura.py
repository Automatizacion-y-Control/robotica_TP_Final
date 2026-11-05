"""Targets y programa del par de cordones (Sold_Par_Cordones).

Módulo compartido por construir_celda.py (construcción completa) y
actualizar_soldadura.py (actualización de una estación ya existente sin
perder los eventos de simulación cargados a mano).

Geometría, en Frame_Soldadura (centro del estator, eje de la pieza en +Y):
    - Punto de soldadura: vértice interior del escalón de cada arista, a
      CORDON_XY del eje en X y en Z.
    - El TCP se ubica sobre la bisectriz exterior de la arista, a DIST_ARCO
      del vértice, con el eje Z de la antorcha apuntando al vértice y el eje X
      en el sentido del avance (+Y).
    - Cordón A: arista (+X, +Z), avance en +Y.
      Transición: salida radial hasta R_TRANSICION, arco con centro en el eje
      del estator (MoveC) hasta la arista B, entrada radial.
      Cordón B: arista (-X, +Z), avance en -Y.
"""
import math

import parametros_celda as P
from robodk.robolink import INSTRUCTION_COMMENT, INSTRUCTION_CALL_PROGRAM, ITEM_TYPE_TARGET
from robodk.robomath import Mat

NOMBRE_PROGRAMA = "Sold_Par_Cordones"
S2 = 1.0 / math.sqrt(2.0)
U_A = [S2, 0.0, S2]               # bisectriz exterior de la arista A (+X, +Z)
U_B = [-S2, 0.0, S2]              # bisectriz exterior de la arista B (-X, +Z)
BAJO = [0.0, 0.0, -1.0]


def pose_ejes(pos, x, z):
    """Pose con origen en pos, eje X en x y eje Z en z; Y = Z x X."""
    def norm(v):
        m = math.sqrt(sum(c * c for c in v))
        return [c / m for c in v]
    z = norm(z)
    d = sum(x[i] * z[i] for i in range(3))
    x = norm([x[i] - d * z[i] for i in range(3)])
    y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]]
    return Mat([[x[0], y[0], z[0], pos[0]], [x[1], y[1], z[1], pos[1]],
                [x[2], y[2], z[2], pos[2]], [0, 0, 0, 1]])


def tcp_en_arista(u, y, separacion):
    """TCP frente a la arista de bisectriz u, a 'separacion' del vértice del escalón."""
    c = P.CORDON_XY
    base = [c * math.copysign(1, u[0]), y, c]
    pos = [base[i] + separacion * u[i] for i in range(3)]
    return pose_ejes(pos, [0, 1, 0], [-u[0], -u[1], -u[2]])


def _target(RDK, nombre, frame_ref, robot, pose):
    """Crea el target o, si ya existe, actualiza su pose (los programas lo siguen referenciando)."""
    t = RDK.Item(nombre, ITEM_TYPE_TARGET)
    if not t.Valid() or t.Parent().Name() != frame_ref.Name():
        t = RDK.AddTarget(nombre, frame_ref, robot)
    t.setAsCartesianTarget()
    t.setPose(pose)
    return t


def crear_targets(RDK, crb, f_sold):
    """Crea o actualiza los targets del par de cordones y devuelve un dict por función."""
    L = P.ESTATOR_LARGO
    y_ini, y_fin = -L / 2 + 1.0, L / 2 - 1.0              # 1 mm de margen en cada cara
    r_sold = P.CORDON_XY * math.sqrt(2.0)                  # radio del vértice del escalón
    sep_trans = P.R_TRANSICION - r_sold                    # separación del vértice en la transición
    t = {}
    t["zona"] = _target(RDK, "Sold_Zona_Aprox", f_sold, crb, pose_ejes([0, y_ini, 250.0], [0, 1, 0], BAJO))
    t["a_aprox"] = _target(RDK, "Sold_A_Aprox", f_sold, crb, tcp_en_arista(U_A, y_ini, P.DIST_ARCO + P.DIST_APROX_SOLD))
    t["a_ini"] = _target(RDK, "Sold_A_Inicio", f_sold, crb, tcp_en_arista(U_A, y_ini, P.DIST_ARCO))
    t["a_fin"] = _target(RDK, "Sold_A_Fin", f_sold, crb, tcp_en_arista(U_A, y_fin, P.DIST_ARCO))
    t["a_salida"] = _target(RDK, "Sold_A_Salida", f_sold, crb, tcp_en_arista(U_A, y_fin, sep_trans))
    t["medio"] = _target(RDK, "Sold_Transicion_Medio", f_sold, crb,
                         pose_ejes([0, y_fin, P.R_TRANSICION], [0, 1, 0], BAJO))
    t["b_entrada"] = _target(RDK, "Sold_B_Entrada", f_sold, crb, tcp_en_arista(U_B, y_fin, sep_trans))
    t["b_ini"] = _target(RDK, "Sold_B_Inicio", f_sold, crb, tcp_en_arista(U_B, y_fin, P.DIST_ARCO))
    t["b_fin"] = _target(RDK, "Sold_B_Fin", f_sold, crb, tcp_en_arista(U_B, y_ini, P.DIST_ARCO))
    t["b_ret"] = _target(RDK, "Sold_B_Retiro", f_sold, crb, tcp_en_arista(U_B, y_ini, P.DIST_ARCO + P.DIST_APROX_SOLD))
    return t


def cargar_programa(prog, t, antorcha, f_sold, nombre_reposo):
    """Agrega las instrucciones del par de cordones a un programa vacío."""
    def comentario(texto):
        prog.RunInstruction(texto, INSTRUCTION_COMMENT)

    comentario("Suelda las dos aristas superiores del estator presentado")
    prog.setPoseFrame(f_sold)
    prog.setPoseTool(antorcha)
    prog.waitDI("PIEZA_PRESENTADA", 1)
    prog.setSpeed(P.V_TRASLADO_LIN, P.V_ARTICULAR)
    prog.setRounding(5)
    prog.addMoveJ(t["zona"])                               # traslado libre sobre la zona
    prog.setRounding(0)
    prog.setSpeed(P.V_APROX, P.V_ARTICULAR)
    comentario("Aproximación radial a la arista A")
    prog.addMoveL(t["a_aprox"])
    prog.addMoveL(t["a_ini"])
    comentario("Cordón A: arco encendido, avance recto a velocidad de soldadura")
    prog.setDO("ARCO_TIG", 1)
    prog.setSpeed(P.V_SOLDADURA, P.V_ARTICULAR)
    prog.addMoveL(t["a_fin"])
    prog.setDO("ARCO_TIG", 0)
    prog.setSpeed(P.V_APROX, P.V_ARTICULAR)
    comentario("Separación radial: la punta sale del escalón antes de rodear la pieza")
    prog.addMoveL(t["a_salida"])
    comentario("Transición en arco alrededor del eje del estator, a radio constante")
    prog.addMoveC(t["medio"], t["b_entrada"])
    prog.addMoveL(t["b_ini"])                              # entrada radial a la arista B
    comentario("Cordón B: avance recto en sentido contrario al A")
    prog.setDO("ARCO_TIG", 1)
    prog.setSpeed(P.V_SOLDADURA, P.V_ARTICULAR)
    prog.addMoveL(t["b_fin"])
    prog.setDO("ARCO_TIG", 0)
    prog.setSpeed(P.V_APROX, P.V_ARTICULAR)
    prog.addMoveL(t["b_ret"])                              # retiro radial
    prog.addMoveL(t["zona"])
    prog.setDO("PIEZA_PRESENTADA", 0)
    prog.setDO("SOLDADURA_TERMINADA", 1)
    prog.RunInstruction(nombre_reposo, INSTRUCTION_CALL_PROGRAM)
