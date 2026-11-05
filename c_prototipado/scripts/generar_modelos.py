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


def cerramiento():
    """Cerramiento rectangular de CERR_ALTO con tres aberturas.

    Oeste: túnel de entrada de la cinta. Este: ventana del pallet (con cortina)
    y vano de la puerta. Origen en el origen de la celda.
    """
    (x0, x1), (y0, y1) = P.CERR_X, P.CERR_Y
    p, H = P.CERR_POSTE, P.CERR_ALTO
    paneles, estructura = [], []
    _pared_x(x0, y0, y1, [(*P.CERR_ABERTURA_CINTA_Y, 0.0, P.CERR_ABERTURA_CINTA_Z)], paneles)
    _pared_x(x1, y0, y1, [(*P.CERR_VENTANA_PALLET_Y, *P.CERR_VENTANA_PALLET_Z),
                          (*P.CERR_PUERTA_Y, 0.0, H)], paneles)
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
    escribir_stl("cerramiento_paneles.stl", paneles)
    escribir_stl("cerramiento_estructura.stl", estructura)


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


if __name__ == "__main__":
    paquete_estator()
    pallet()
    soporte_pallet()
    antorcha_tig()
    estacion_servicio()
    cerramiento()
    puerta()
    cortina_luz()
