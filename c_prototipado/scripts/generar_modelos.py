"""Genera los modelos 3D (STL ASCII) de los componentes propios de la celda.

Salida: c_prototipado/modelos/
    paquete_estator.stl             pieza a soldar
    pallet_4_posiciones.stl         pallet de salida 2 x 2
    soporte_pallet.stl              soporte bajo del pallet
    antorcha_tig.stl                antorcha TIG recta, TCP en la punta del tungsteno
    estacion_servicio_antorcha.stl  pedestal con horquilla de verificación de TCP
    cerramiento.stl                 postes, largueros y paneles con aberturas
    puerta.stl                      hoja de la puerta de acceso
    cortina_luz.stl                 emisor y receptor de la cortina de la ventana del pallet

El script no se conecta con RoboDK: solo escribe geometría. Las cotas salen de
parametros_celda.py para que la geometría y la disposición no se desfasen.

Uso:  python generar_modelos.py
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)          # permite importar parametros_celda aun con python -I
import parametros_celda as P      # noqa: E402
SALIDA = os.path.join(AQUI, "..", "modelos")

N_ARCO = 96                       # divisiones angulares del agujero del estator
DENSIDAD_ACERO_SI = 7.65e-6       # kg/mm3, acero al silicio


# ---------------------------------------------------------------------------
# Utilidades de malla
# ---------------------------------------------------------------------------
def escribir_stl(nombre, triangulos):
    """Escribe una lista de triángulos ((x,y,z) x 3) como STL ASCII."""
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, nombre)
    # newline="\n": LF también en Windows, para que el archivo sea idéntico en
    # cualquier sistema (el .gitattributes trata los STL como binarios).
    with open(ruta, "w", encoding="ascii", newline="\n") as f:
        f.write(f"solid {nombre}\n")
        for a, b, c in triangulos:
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            m = math.sqrt(sum(x * x for x in n)) or 1.0
            n = [x / m for x in n]
            f.write(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n    outer loop\n")
            for p in (a, b, c):
                f.write(f"      vertex {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")
            f.write("    endloop\n  endfacet\n")
        f.write(f"endsolid {nombre}\n")
    print("escrito", os.path.normpath(ruta), len(triangulos), "triangulos")


def tri_caja(x0, y0, z0, lx, ly, lz):
    """Prisma rectangular con un vértice en (x0, y0, z0) y lados lx, ly, lz."""
    v = [(x, y, z) for x in (x0, x0 + lx) for y in (y0, y0 + ly) for z in (z0, z0 + lz)]
    caras = [(0, 2, 6, 4), (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6), (0, 1, 3, 2), (4, 6, 7, 5)]
    tri = []
    for a, b, c, d in caras:
        tri += [(v[a], v[b], v[c]), (v[a], v[c], v[d])]
    return tri


def tri_caja_ext(xa, xb, ya, yb, za, zb):
    """Prisma definido por sus extremos en cada eje (cómodo para paneles)."""
    return tri_caja(min(xa, xb), min(ya, yb), min(za, zb), abs(xb - xa), abs(yb - ya), abs(zb - za))


def tri_tronco(z0, z1, r0, r1, n=48):
    """Tronco de cono sobre el eje Z, con tapas. Con r0 == r1 es un cilindro."""
    tri = []
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0a = (r0 * math.cos(a), r0 * math.sin(a), z0); p0b = (r0 * math.cos(b), r0 * math.sin(b), z0)
        p1a = (r1 * math.cos(a), r1 * math.sin(a), z1); p1b = (r1 * math.cos(b), r1 * math.sin(b), z1)
        tri += [(p0a, p0b, p1b), (p0a, p1b, p1a)]
        tri += [((0, 0, z0), p0b, p0a), ((0, 0, z1), p1a, p1b)]
    return tri


# ---------------------------------------------------------------------------
# Paquete de estator
# ---------------------------------------------------------------------------
def contorno_exterior(theta):
    """Intersección del rayo de ángulo theta con el contorno exterior.

    El contorno es un cuadrado con un escalón en cada arista. Es estrellado
    respecto del centro, así que cada rayo lo corta una sola vez.
    """
    h = P.ESTATOR_LADO / 2.0
    e = h - P.ESTATOR_ESCALON
    c, s = math.cos(theta), math.sin(theta)
    mejor = None
    # Segmentos del primer cuadrante; el resto se obtiene rotando 90°.
    segs = [((h, 0.0), (h, e)), ((h, e), (e, e)), ((e, e), (e, h)), ((e, h), (0.0, h))]
    for k in range(4):
        ca, sa = math.cos(k * math.pi / 2), math.sin(k * math.pi / 2)
        for (x1, y1), (x2, y2) in segs:
            p1 = (x1 * ca - y1 * sa, x1 * sa + y1 * ca)
            p2 = (x2 * ca - y2 * sa, x2 * sa + y2 * ca)
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            den = c * dy - s * dx
            if abs(den) < 1e-12:
                continue
            t = (p1[0] * dy - p1[1] * dx) / den      # distancia sobre el rayo
            u = (p1[0] * s - p1[1] * c) / den        # parámetro sobre el segmento
            if t > 0 and -1e-9 <= u <= 1 + 1e-9 and (mejor is None or t < mejor):
                mejor = t
    return (mejor * c, mejor * s)


def paquete_estator():
    """Paquete con origen en el centro de la cara inferior y Z sobre el eje."""
    h, e = P.ESTATOR_LADO / 2.0, P.ESTATOR_LADO / 2.0 - P.ESTATOR_ESCALON
    # Ángulos regulares más los vértices del contorno, para que aristas y
    # escalones queden exactos en la malla.
    angs = {2 * math.pi * i / N_ARCO for i in range(N_ARCO)}
    for k in range(4):
        for x, y in [(h, e), (e, e), (e, h)]:
            angs.add((k * math.pi / 2 + math.atan2(y, x)) % (2 * math.pi))
    angs = sorted(angs)
    r = P.ESTATOR_D_AGUJERO / 2.0
    ext = [contorno_exterior(a) for a in angs]
    inn = [(r * math.cos(a), r * math.sin(a)) for a in angs]
    z0, z1 = 0.0, P.ESTATOR_LARGO
    tri = []
    for i in range(len(angs)):
        j = (i + 1) % len(angs)
        eo, eo2, io, io2 = ext[i], ext[j], inn[i], inn[j]
        tri += [((io[0], io[1], z1), (eo[0], eo[1], z1), (eo2[0], eo2[1], z1)),    # cara superior
                ((io[0], io[1], z1), (eo2[0], eo2[1], z1), (io2[0], io2[1], z1))]
        tri += [((io[0], io[1], z0), (eo2[0], eo2[1], z0), (eo[0], eo[1], z0)),    # cara inferior
                ((io[0], io[1], z0), (io2[0], io2[1], z0), (eo2[0], eo2[1], z0))]
        tri += [((eo[0], eo[1], z0), (eo2[0], eo2[1], z0), (eo2[0], eo2[1], z1)),  # pared exterior
                ((eo[0], eo[1], z0), (eo2[0], eo2[1], z1), (eo[0], eo[1], z1))]
        tri += [((io[0], io[1], z0), (io2[0], io2[1], z1), (io2[0], io2[1], z0)),  # pared del agujero
                ((io[0], io[1], z0), (io[0], io[1], z1), (io2[0], io2[1], z1))]
    escribir_stl("paquete_estator.stl", tri)
    area = P.ESTATOR_LADO ** 2 - 4 * P.ESTATOR_ESCALON ** 2 - math.pi * r ** 2
    print(f"  seccion {area:.0f} mm2, masa estimada {area * P.ESTATOR_LARGO * DENSIDAD_ACERO_SI:.2f} kg")


# ---------------------------------------------------------------------------
# Pallet y soporte
# ---------------------------------------------------------------------------
def pallet():
    """Placa con origen en una esquina inferior; las posiciones se definen como targets."""
    escribir_stl("pallet_4_posiciones.stl",
                 tri_caja(0, 0, 0, P.PALLET_LADO, P.PALLET_LADO, P.PALLET_ESPESOR))


def soporte_pallet():
    """Soporte con origen en el centro de la base; el pallet apoya en la cara superior."""
    l = P.PALLET_LADO
    escribir_stl("soporte_pallet.stl", tri_caja(-l / 2, -l / 2, 0, l, l, P.SOPORTE_PALLET_ALTURA))


# ---------------------------------------------------------------------------
# Antorcha TIG recta
# ---------------------------------------------------------------------------
# Tramos sobre el eje Z, desde la brida: (z0, z1, r0, r1).
TIG_TRAMOS = {
    "placa":    (0.0, 12.0, 40.0, 40.0),     # placa de montaje Ø80 x 12
    "cuerpo":   (12.0, 172.0, 22.5, 22.5),   # cuerpo refrigerado Ø45 x 160
    "boquilla": (172.0, 202.0, 11.0, 6.5),   # boquilla cerámica cónica de 30 mm
}
TUNGSTENO_D = 2.4                 # diámetro típico del electrodo


def antorcha_tig():
    tri = []
    for z0, z1, r0, r1 in TIG_TRAMOS.values():
        tri += tri_tronco(z0, z1, r0, r1)
    z_boq = TIG_TRAMOS["boquilla"][1]
    saliente = P.TIG_TCP_Z - z_boq                # 5 mm fuera de la boquilla
    r = TUNGSTENO_D / 2
    tri += tri_tronco(z_boq - 10.0, P.TIG_TCP_Z - 1.0, r, r, n=16)   # electrodo
    tri += tri_tronco(P.TIG_TCP_Z - 1.0, P.TIG_TCP_Z, r, 0.2, n=16)  # punta afilada
    escribir_stl("antorcha_tig.stl", tri)
    print(f"  TCP en la punta del tungsteno: Z = {P.TIG_TCP_Z:.1f} mm, saliente {saliente:.1f} mm")


# ---------------------------------------------------------------------------
# Estación de servicio de la antorcha
# ---------------------------------------------------------------------------
PEDESTAL = (250.0, 250.0, 900.0)


def estacion_servicio():
    """Pedestal, bandeja de cambio de tungsteno y horquilla de verificación de TCP.

    Origen en el centro de la base. El cruce de los dos haces es el punto de
    verificación (P.SERVICIO_PUNTO).
    """
    lx, ly, lz = PEDESTAL
    tri = tri_caja(-lx / 2, -ly / 2, 0, lx, ly, lz)                 # pedestal
    tri += tri_caja(-lx / 2, -ly / 2, lz, lx, 120.0, 15.0)          # bandeja de servicio
    tri += tri_caja(-60.0, 10.0, lz, 120.0, 100.0, 20.0)            # base de la horquilla
    tri += tri_caja(-60.0, 10.0, lz + 20.0, 20.0, 100.0, 80.0)      # brazo izquierdo
    tri += tri_caja(40.0, 10.0, lz + 20.0, 20.0, 100.0, 80.0)       # brazo derecho
    xc, yc, zc = P.SERVICIO_PUNTO
    tri += tri_caja(-40.0, yc - 1.0, zc - 1.0, 80.0, 2.0, 2.0)      # haz 1 (en X)
    tri += tri_caja(xc - 1.0, 20.0, zc - 1.0, 2.0, 80.0, 2.0)       # haz 2 (en Y)
    escribir_stl("estacion_servicio_antorcha.stl", tri)


# ---------------------------------------------------------------------------
# Cerramiento, puerta y cortina de luz
# ---------------------------------------------------------------------------
def _pared_x(x, ya, yb, huecos, tri):
    """Paneles de una pared paralela a Y en x, salteando los huecos.

    huecos: lista de (y0, y1, z0, z1). Cada tramo en Y se cubre con paneles
    por debajo y por encima del hueco que lo atraviesa.
    """
    t, H = P.CERR_PANEL, P.CERR_ALTO
    cortes = sorted({ya, yb} | {h[0] for h in huecos} | {h[1] for h in huecos})
    for y0, y1 in zip(cortes[:-1], cortes[1:]):
        ym = (y0 + y1) / 2
        h = next((h for h in huecos if h[0] <= ym <= h[1]), None)
        if h is None:
            tri += tri_caja_ext(x - t / 2, x + t / 2, y0, y1, 0, H)
        else:
            if h[2] > 0:
                tri += tri_caja_ext(x - t / 2, x + t / 2, y0, y1, 0, h[2])
            if h[3] < H:
                tri += tri_caja_ext(x - t / 2, x + t / 2, y0, y1, h[3], H)


def _pared_y(y, xa, xb, tri):
    t, H = P.CERR_PANEL, P.CERR_ALTO
    tri += tri_caja_ext(xa, xb, y - t / 2, y + t / 2, 0, H)


def cerramiento(sufijo="", huecos_este=None, y_sur=None, tunel_y=None, pared_sur=True):
    """Cerramiento rectangular de CERR_ALTO con aberturas en las caras oeste y este.

    Oeste: túnel de entrada de la cinta. Este: los huecos indicados más el vano
    de la puerta. Por defecto (v02), la ventana del pallet. Origen en el origen
    de la celda.

    y_sur y tunel_y permiten mover la cara sur y los túneles (v04). Con
    pared_sur=False la cara sur no se genera: en la v04 la forman los paneles
    desmontables (paneles_desmontables_sur).
    """
    (x0, x1), (y0, y1) = P.CERR_X, P.CERR_Y
    if y_sur is not None:
        y0 = y_sur
    tunel_y = tunel_y or P.CERR_ABERTURA_CINTA_Y
    p, H = P.CERR_POSTE, P.CERR_ALTO
    if huecos_este is None:
        huecos_este = [(*P.CERR_VENTANA_PALLET_Y, *P.CERR_VENTANA_PALLET_Z)]
    paneles, estructura = [], []
    _pared_x(x0, y0, y1, [(*tunel_y, 0.0, P.CERR_ABERTURA_CINTA_Z)], paneles)
    _pared_x(x1, y0, y1, huecos_este + [(*P.CERR_PUERTA_Y, 0.0, H)], paneles)
    if pared_sur:
        _pared_y(y0, x0, x1, paneles)
    _pared_y(y1, x0, x1, paneles)
    # Postes en las esquinas, en los bordes de la puerta y cada ~1 m en las paredes largas.
    postes = [(x0, y0), (x0, y1), (x1, y0), (x1, y1),
              (x1, P.CERR_PUERTA_Y[0]), (x1, P.CERR_PUERTA_Y[1]),
              (x0, 350.0), (x0, 1100.0), (-200.0, y0), (-200.0, y1)]
    for x, y in postes:
        estructura += tri_caja(x - p / 2, y - p / 2, 0, p, p, H)
    # Largueros superiores.
    estructura += tri_caja_ext(x0, x1, y0 - p / 2, y0 + p / 2, H - p, H)
    estructura += tri_caja_ext(x0, x1, y1 - p / 2, y1 + p / 2, H - p, H)
    estructura += tri_caja_ext(x0 - p / 2, x0 + p / 2, y0, y1, H - p, H)
    estructura += tri_caja_ext(x1 - p / 2, x1 + p / 2, y0, y1, H - p, H)
    escribir_stl(f"cerramiento_paneles{sufijo}.stl", paneles)
    escribir_stl(f"cerramiento_estructura{sufijo}.stl", estructura)


def puerta():
    """Hoja de la puerta con origen en la bisagra (borde y0 del vano, al piso)."""
    ancho = P.CERR_PUERTA_Y[1] - P.CERR_PUERTA_Y[0]
    tri = tri_caja_ext(-15, 15, 0, ancho, 0, P.CERR_ALTO - 80)        # marco y malla simplificados
    tri += tri_caja_ext(15, 45, ancho - 120, ancho - 90, 950, 1100)    # manija exterior
    escribir_stl("puerta.stl", tri)


def cortina_luz():
    """Emisor y receptor verticales en los bordes de la ventana del pallet.

    Origen en el centro inferior de la ventana, sobre la cara exterior del cerramiento.
    """
    ya, yb = P.CERR_VENTANA_PALLET_Y
    za, zb = P.CERR_VENTANA_PALLET_Z
    tri = tri_caja_ext(0, 40, ya - 40, ya, za, zb)      # emisor
    tri += tri_caja_ext(0, 40, yb, yb + 40, za, zb)     # receptor
    escribir_stl("cortina_luz.stl", tri)


# ---------------------------------------------------------------------------
# Mejora 01 (v03): tramo de salida de la cinta y cortinas de entrada y salida
# ---------------------------------------------------------------------------
def cinta_extension():
    """Tramo de salida que prolonga la banda del modelo ConveyorA hasta afuera.

    Coordenadas de Frame_Celda. Empieza en el final de la banda del modelo y
    termina en CINTA_EXT_FIN_X. Mantiene la altura (cara superior de la banda a
    CINTA_ALTURA_BANDA) y el ancho de la banda, con largueros laterales y patas.
    Es geometría fija: lo que viaja sobre la banda lo mueve el eje del mecanismo.
    """
    x_base = P.CINTA_TOMA[0] + 250.0 - P.CINTA_LARGO          # misma base que en construir_celda.py
    y_eje = P.CINTA_TOMA[1]
    x0, x1 = x_base + P.CINTA_BANDA_FIN_REL, P.CINTA_EXT_FIN_X
    zt = P.CINTA_ALTURA_BANDA
    a = P.CINTA_ANCHO_BANDA / 2
    banda = tri_caja_ext(x0, x1, y_eje - a, y_eje + a, zt - 20.0, zt)
    estructura = []
    for lado in (-1, 1):                                        # largueros laterales
        yb = y_eje + lado * (a + 20.0)
        estructura += tri_caja_ext(x0, x1, yb - 20.0, yb + 20.0, zt - 110.0, zt + 5.0)
    x = x0 + 150.0
    while x < x1 - 50.0:                                        # patas cada 600 mm
        for lado in (-1, 1):
            yb = y_eje + lado * (a + 20.0)
            estructura += tri_caja_ext(x - 30.0, x + 30.0, yb - 30.0, yb + 30.0, 0.0, zt - 110.0)
        x += 600.0
    escribir_stl("cinta_extension_banda.stl", banda)
    escribir_stl("cinta_extension_estructura.stl", estructura)


def cortina_cinta(nombre="cortina_luz_cinta.stl", tunel_y=None):
    """Emisor y receptor de una cortina de luz en el paso de la cinta por el cerramiento.

    Dos columnas verticales en los bordes del túnel (por defecto
    CERR_ABERTURA_CINTA_Y), hasta CERR_ABERTURA_CINTA_Z. Origen sobre la cara de
    la pared; se instancia una vez en la entrada (oeste) y otra en la salida (este).
    """
    ya, yb = tunel_y or P.CERR_ABERTURA_CINTA_Y
    zt = P.CERR_ABERTURA_CINTA_Z
    tri = tri_caja_ext(-20, 20, ya - 40, ya, 0, zt)             # emisor
    tri += tri_caja_ext(-20, 20, yb, yb + 40, 0, zt)            # receptor
    escribir_stl(nombre, tri)


# ---------------------------------------------------------------------------
# Mejora 02 (v04): mantenimiento, aislamiento y operación
# ---------------------------------------------------------------------------
def _desplazar(tri, d):
    """Traslada una lista de triángulos en el vector d."""
    return [tuple(tuple(c + o for c, o in zip(v, d)) for v in t) for t in tri]


def paneles_desmontables_sur():
    """Cara sur del cerramiento v04 formada por paneles desmontables.

    Cada panel lleva dos manijas del lado del pasillo. Entre panel y panel queda
    una junta de 10 mm (los postes de la estructura no cambian).
    """
    (x0, x1), y = P.CERR_X, P.V4_CERR_Y_SUR
    t, H = P.CERR_PANEL, P.CERR_ALTO
    n = max(1, round((x1 - x0) / P.V4_PANEL_DESMONTABLE))
    ancho = (x1 - x0) / n
    paneles, manijas = [], []
    for i in range(n):
        xa, xb = x0 + i * ancho + 5.0, x0 + (i + 1) * ancho - 5.0
        paneles += tri_caja_ext(xa, xb, y - t / 2, y + t / 2, 0, H)
        for xm in (xa + 80.0, xb - 110.0):                      # manijas hacia el pasillo (-Y)
            manijas += tri_caja_ext(xm, xm + 30.0, y - 40.0, y - t / 2, 1000.0, 1150.0)
    escribir_stl("paneles_desmontables_sur.stl", paneles)
    escribir_stl("paneles_desmontables_manijas.stl", manijas)


def pasillo_mantenimiento():
    """Marca en el piso del pasillo de mantenimiento, del lado sur, afuera."""
    xa, xb = P.V4_PASILLO_X
    y = P.V4_CERR_Y_SUR
    tri = tri_caja_ext(xa, xb, y - 5.0 - P.V4_PASILLO_ANCHO, y - 5.0, 0.0, 3.0)
    escribir_stl("pasillo_mantenimiento.stl", tri)


def accionamiento_cinta():
    """Motorreductor de la cinta con su resguardo, en el extremo oeste, afuera.

    Origen en el centro de la base del conjunto (P.V4_ACCIONAMIENTO), al piso.
    """
    zt = P.CINTA_ALTURA_BANDA
    motor = tri_caja_ext(-70, 70, -60, 60, zt - 210, zt - 70)          # reductor
    motor += tri_caja_ext(-60, 60, 60, 260, zt - 200, zt - 80)         # motor, hacia el norte
    motor += tri_caja_ext(-40, 40, -40, 40, 0, zt - 210)               # soporte
    resguardo = tri_caja_ext(-110, 110, -100, 300, zt - 240, zt - 40)
    escribir_stl("accionamiento_cinta.stl", motor)
    escribir_stl("accionamiento_cinta_resguardo.stl", resguardo)


def tablero_loto():
    """Tablero de aislamiento: gabinete con cuatro seccionadores y una válvula de gas.

    Seccionadores: IRB 1200, CRB 1300, cinta y fuente TIG. Válvula: argón.
    Origen en el centro de la base, frente hacia +X (afuera de la cara este).
    """
    gabinete = tri_caja_ext(0, 150, -250, 250, 900, 1600)
    gabinete += tri_caja_ext(20, 80, -40, 40, 0, 900)                  # pie
    manijas = []
    for i in range(5):
        yc = -200 + i * 100
        manijas += tri_caja_ext(150, 200, yc - 15, yc + 15, 1200, 1320)
    escribir_stl("tablero_loto.stl", gabinete)
    escribir_stl("tablero_loto_manijas.stl", manijas)


def panel_operador():
    """Panel de operador en pedestal: consola y pantalla simplificadas."""
    tri = tri_caja_ext(-60, 60, -60, 60, 0, 950)                       # pedestal
    tri += tri_caja_ext(-200, 200, -250, 250, 950, 1150)               # consola
    tri += tri_caja_ext(-20, 20, -180, 180, 1150, 1400)                # pantalla
    escribir_stl("panel_operador.stl", tri)


def parada_emergencia():
    """Pulsador de emergencia en poste: poste gris y hongo rojo (dos archivos)."""
    poste = tri_caja_ext(-40, 40, -40, 40, 0, 1050)
    poste += tri_caja_ext(-60, 60, -60, 60, 1050, 1150)                # caja del pulsador
    escribir_stl("parada_emergencia_poste.stl", poste)
    escribir_stl("parada_emergencia_hongo.stl", _desplazar(tri_tronco(0, 40, 45, 45, n=32), (0, 0, 1150)))


def equipos_auxiliares():
    """Gabinete de controlador, fuente TIG y cilindro de argón (fuera de la celda, al norte)."""
    escribir_stl("gabinete_controlador.stl", tri_caja_ext(-300, 300, 0, 500, 0, 1200))
    escribir_stl("fuente_tig.stl", tri_caja_ext(-200, 200, 0, 600, 0, 800))
    escribir_stl("cilindro_argon.stl", tri_tronco(0, 1450, 110, 110) + tri_tronco(1450, 1550, 110, 40))


if __name__ == "__main__":
    paquete_estator()
    pallet()
    soporte_pallet()
    antorcha_tig()
    estacion_servicio()
    cerramiento()                                               # v02: ventana del pallet
    cerramiento("_v03", [(*P.CERR_ABERTURA_SALIDA_Y, 0.0, P.CERR_ABERTURA_SALIDA_Z)])
    puerta()
    cortina_luz()
    cinta_extension()
    cortina_cinta()
    # v04
    cerramiento("_v04", [(*P.V4_TUNEL_Y, 0.0, P.CERR_ABERTURA_SALIDA_Z)],
                y_sur=P.V4_CERR_Y_SUR, tunel_y=P.V4_TUNEL_Y, pared_sur=False)
    cortina_cinta("cortina_luz_cinta_v04.stl", P.V4_TUNEL_Y)
    paneles_desmontables_sur()
    pasillo_mantenimiento()
    accionamiento_cinta()
    tablero_loto()
    panel_operador()
    parada_emergencia()
    equipos_auxiliares()
