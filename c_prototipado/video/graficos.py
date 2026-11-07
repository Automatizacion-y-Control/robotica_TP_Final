"""Gráficos del video: portada, placa final y fondos de pantalla dividida con los programas de la v05.

Las tarjetas reproducen las instrucciones tal como están en la estación (relevadas con la API); se omiten tramos
con «…» y la sangría de IF/WHILE es solo de lectura. Una línea que empieza con «!» se resalta.
Uso: python graficos.py   (escribe g/*.png, 1920x1080)
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
G = AQUI / "g"
W, H = 1920, 1080
FUENTES = Path("C:/Windows/Fonts")

FONDO = "#0E1B2C"
TARJETA = "#F4F6F8"
TEXTO = "#1F2933"
TENUE = "#6B7785"
ACENTO = "#E8A33D"       # resaltado de la línea que se nombra
RESALTE = "#FCE9C7"
AZUL = "#2F6690"

# Rectángulo de la grabación en la pantalla dividida (editar.py usa los mismos valores).
VIDEO = (40, 180, 1280, 720)
CARTA = (1360, 60, 520, 960)


def fuente(nombre, tam):
    return ImageFont.truetype(str(FUENTES / nombre), tam)


SANS, SANS_B, SANS_L = "segoeui.ttf", "segoeuib.ttf", "segoeuisl.ttf"
MONO, MONO_B = "consola.ttf", "consolab.ttf"

PROGRAMA, ESTACION = "Programa de RoboDK (v05)", "Estación en RoboDK (v05)"
# Cada tarjeta: (archivo, título sobre la grabación, encabezado, [(programa, líneas)], nota al pie o None).
# «!» resalta la línea; «# » marca un comentario (en RoboDK, instrucción de comentario).
TARJETAS = [
    ("d_principal", "Programa principal y coordinador", PROGRAMA, [
        ("Programa_Principal", [
            "# Celda de soldadura TIG de paquetes de estator - Grupo 4",
            "# Ciclo nativo de un lote de 4 estatores; no necesita el panel",
            "!Inicio_Celda",
            "!Ciclo_Pieza_1",
            "!Ciclo_Pieza_2",
            "!Ciclo_Pieza_3",
            "!Ciclo_Pieza_4",
            "!Fin_Lote",
        ]),
        ("Coordinador_Panel (extracto)", [
            "WHILE COORDINADOR_ACTIVO == 1",
            "  …",
            "  IF AUTO_ACTIVO == 1",
            "    INDICE_CAPTURADO = PROXIMA_PIEZA",
            "    IF INDICE_CAPTURADO == 1",
            "      Set PIEZA_ACTIVA=1",
            "!      Ciclo_Pieza_1",
            "      Set PIEZA_ACTIVA=0",
            "      Set PROXIMA_PIEZA=2",
            "    END",
            "    …",
            "  END",
            "END",
        ]),
    ], "El panel (Python) solo envía solicitudes; Coordinador_Panel, nativo de RoboDK, decide y llama a los programas."),
    ("d_ciclo", "Ciclo de una pieza", PROGRAMA, [
        ("Ciclo_Pieza_1", [
            "# Ciclo completo del estator 1: tomar, soldar 4 cordones, devolver a la banda",
            "Set FASE_PIEZA=1",
            "!Cinta_Avanzar_1",
            "Set FASE_PIEZA=2",
            "!Man_Tomar_Cinta",
            "Set FASE_PIEZA=3",
            "!Man_Presentar_Lado1",
            "Set FASE_PIEZA=4",
            "!Sold_Par_Cordones",
            "Set FASE_PIEZA=5",
            "!Man_Presentar_Lado2",
            "Set FASE_PIEZA=6",
            "!Sold_Par_Cordones",
            "Set FASE_PIEZA=7",
            "!Man_Depositar_Cinta",
        ]),
    ], "Los robots se esperan con señales: PIEZA_EN_TOMA, PIEZA_PRESENTADA y SOLDADURA_TERMINADA."),
    ("d_soldadura", "Soldadura: dos cordones por lado", PROGRAMA, [
        ("Sold_Par_Cordones", [
            "Est. Ref.: Frame_Soldadura",
            "Est. herr: Antorcha_TIG",
            "Wait PIEZA_PRESENTADA=1",
            "MoveJ (Sold_Zona_Aprox)",
            "MoveL (Sold_A_Aprox)",
            "MoveL (Sold_A_Inicio)",
            "# Cordón A: arco encendido, avance recto",
            "Set ARCO_TIG=1",
            "!Establecer velocidad (5.0 mm/s)",
            "!MoveL (Sold_A_Fin)",
            "Set ARCO_TIG=0",
            "MoveL (Sold_A_Salida)",
            "# Transición en arco alrededor del eje",
            "!MoveC (Sold_Transicion_Medio, Sold_B_Entrada)",
            "MoveL (Sold_B_Inicio)",
            "Set ARCO_TIG=1",
            "!Establecer velocidad (5.0 mm/s)",
            "!MoveL (Sold_B_Fin)",
            "Set ARCO_TIG=0",
            "MoveL (Sold_B_Retiro)",
            "Set PIEZA_PRESENTADA=0",
            "Set SOLDADURA_TERMINADA=1",
            "Sold_Ir_Reposo",
        ]),
    ], "Se omiten los cambios de velocidad de los tramos de aproximación y salida."),
    ("d_deposito", "Depósito: pieza correcta o de revisión", PROGRAMA, [
        ("Man_Depositar_Cinta", [
            "!Est. Ref.: Frame_Deposito_Cinta",
            "Wait SOLDADURA_TERMINADA=1",
            "MoveJ (Man_Deposito_Aprox)",
            "MoveL (Man_Deposito)",
            "Pinza_Cerrar",
            "Evento_Soltar_Pieza",
            "MoveL (Man_Deposito_Aprox)",
        ]),
        ("Man_Depositar_Retrabajo", [
            "# Pieza de revisión o retrabajo: se deposita corrida",
            "!Est. Ref.: Frame_Deposito_Retrabajo",
            "Wait SOLDADURA_TERMINADA=1",
            "MoveJ (Man_Retrabajo_Aprox)",
            "MoveL (Man_Retrabajo_Salida)",
            "MoveL (Man_Retrabajo)",
            "Pinza_Cerrar",
            "Evento_Soltar_Pieza",
            "MoveL (Man_Retrabajo_Salida)",
        ]),
    ], "Se omiten las velocidades y el retiro desde la zona de soldadura."),
    ("d_recuperacion", "Parada y recuperación", PROGRAMA, [
        ("Recuperar_Pieza (extracto)", [
            "# Retoma la pieza interrumpida; la soldadura se repite",
            "FASE_CAPTURADA = FASE_PIEZA",
            "Set RETRABAJO_ACTUAL=0",
            "IF FASE_CAPTURADA == 4",
            "!  Set RETRABAJO_ACTUAL=1",
            "END",
            "IF FASE_CAPTURADA == 6",
            "!  Set RETRABAJO_ACTUAL=1",
            "END",
            "…",
        ]),
        ("Recuperar_Desde_Lado1", [
            "Set ARCO_TIG=0",
            "IF FASE_CAPTURADA == 4",
            "!  Sold_Retirar",
            "END",
            "…",
            "Man_Presentar_Lado1",
            "Sold_Par_Cordones",
            "Man_Presentar_Lado2",
            "Sold_Par_Cordones",
            "IF RETRABAJO_ACTUAL == 1",
            "!  Man_Depositar_Retrabajo",
            "END",
            "…",
        ]),
    ], "Una pieza cortada durante el cordón se termina y se deja corrida para revisarla; no cuenta como buena."),
    ("d_equipos", "Robots, herramientas y equipos", ESTACION, [
        ("Frame_Celda", [
            "Base_Manipulador_IRB1200",
            "!  ABB IRB 1200-7/0.7",
            "!    Pinza_2F85",
            "     TCP_Pinza",
            "Base_Soldador_CRB1300",
            "!  ABB CRB 1300-10/1.15",
            "!    Antorcha_TIG",
            "Base_Cinta_Pasante",
            "   Cinta_Pasante",
            "     Frame_Banda: Estator_1 … Estator_4",
            "Sensor_Pieza_En_Toma",
            "Estacion_Servicio_Antorcha",
            "Controlador_IRB1200",
            "Controlador_CRB1300",
            "!Fuente_TIG",
            "!Cilindro_Argon",
        ]),
    ], "Elementos del árbol de la estación. La pinza es un mecanismo de un eje; TCP_Pinza es el punto de trabajo del IRB."),
    ("d_seguridad", "Seguridad y mantenimiento", ESTACION, [
        ("Frame_Cerramiento", [
            "Bisagra_Puerta",
            "!  Puerta",
            "Cerramiento_Estructura",
            "Cerramiento_Paneles",
            "!Paneles_Desmontables_Sur",
            "!Cortina_Luz_Entrada",
            "!Cortina_Luz_Salida",
        ]),
        ("Frame_Celda", [
            "!Parada_Emergencia_Panel",
            "!Parada_Emergencia_Puerta",
            "!Parada_Emergencia_Entrada",
            "!Parada_Emergencia_Salida",
            "!Pasillo_Mantenimiento",
            "!Tablero_LOTO",
            "Tablero_LOTO_Seccionadores",
            "Accionamiento_Cinta_Resguardo",
        ]),
    ], "Puerta enclavada, cortinas de luz y cuatro pulsadores; la cara sur se desmonta para sacar la banda."),
    ("d_pedido", "Pedido de piezas buenas", PROGRAMA, [
        ("Coordinador_Panel (extracto)", [
            "!PIEZAS_BUENAS = PIEZAS_COMPLETADAS - PIEZAS_RETRABAJO",
            "IF AUTO_ACTIVO == 1",
            "  IF OBJETIVO_PIEZAS > 0",
            "!    IF PIEZAS_BUENAS >= OBJETIVO_PIEZAS",
            "      Set PEDIDO_CUMPLIDO=1",
            "    END",
            "  END",
            "END",
            "…",
            "IF PEDIDO_CUMPLIDO == 1",
            "  …",
            "!    Cerrar_Pedido",
        ]),
        ("Cerrar_Pedido (extracto)", [
            "# Evacúa y repone las piezas, aunque el lote esté incompleto, y deja todo en cero",
            "IF PROXIMA_PIEZA != 1",
            "  Man_Ir_Reposo",
            "  Fin_Lote",
            "END",
            "Set PIEZAS_COMPLETADAS=0",
            "…",
        ]),
    ], "El objetivo lo fija producción en el panel; las piezas de retrabajo no cuentan como buenas."),
    ("d_giro", "Giro de la pieza para el segundo lado", PROGRAMA, [
        ("Man_Presentar_Lado2", [
            "# Gira 180° sobre el eje de la pinza (J6) para subir las aristas C y D",
            "Est. Ref.: Frame_Soldadura",
            "Est. herr: TCP_Pinza",
            "!Wait SOLDADURA_TERMINADA=1",
            "Set SOLDADURA_TERMINADA=0",
            "Establecer velocidad (100.0 mm/s)",
            "!MoveJ (Man_Presentar_Lado2)",
            "!Set PIEZA_PRESENTADA=1",
        ]),
    ], "El manipulador espera a que el soldador termine el primer par, gira la pieza y avisa que está presentada."),
]

VERSIONES = [
    ("v01", "Posicionador y cilindro de seis cordones: primera entrega."),
    ("v02", "Manipulador con pinza, soldador y el paquete de estator real."),
    ("v03", "Cinta pasante: la misma cinta trae y saca las piezas, sin pallet."),
    ("v04", "Mantenimiento: pasillo, cara desmontable y equipos afuera."),
    ("v05", "Coordinador, modos, paradas, recuperación y panel de operador."),
]


def envolver(draw, texto, f, ancho):
    palabras, lineas, actual = texto.split(), [], ""
    for p in palabras:
        prueba = (actual + " " + p).strip()
        if draw.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    return lineas + [actual]


def marco(titulo, encabezado):
    """Fondo de pantalla dividida: título, recuadro de la grabación y tarjeta vacía con su encabezado."""
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    vx, vy, vw, vh = VIDEO
    d.text((vx, vy - 78), titulo, font=fuente(SANS_B, 40), fill="white")
    d.rectangle((vx - 2, vy - 2, vx + vw + 1, vy + vh + 1), outline="#2B3D55", width=2)
    d.text((vx, vy + vh + 26), "Celda robotizada de soldadura TIG de paquetes de estator · Grupo 4",
           font=fuente(SANS, 24), fill="#8FA3B8")

    cx, cy, cw, ch = CARTA
    d.rounded_rectangle((cx, cy, cx + cw, cy + ch), radius=14, fill=TARJETA)
    d.rounded_rectangle((cx, cy, cx + cw, cy + 54), radius=14, fill=AZUL)
    d.rectangle((cx, cy + 40, cx + cw, cy + 54), fill=AZUL)
    d.text((cx + 22, cy + 11), encabezado, font=fuente(SANS_B, 24), fill="white")
    return im, d


def nota_al_pie(d, nota):
    cx, cy, cw, ch = CARTA
    f = fuente(SANS, 19)
    lineas = envolver(d, nota, f, cw - 44)
    ny = cy + ch - 26 - 26 * len(lineas)
    d.line((cx + 22, ny - 14, cx + cw - 22, ny - 14), fill="#C9D2DB", width=1)
    for r in lineas:
        d.text((cx + 22, ny), r, font=f, fill=TENUE)
        ny += 26


def tarjeta(nombre, titulo, encabezado, bloques, nota):
    im, d = marco(titulo, encabezado)
    cx, cy, cw, ch = CARTA

    total = sum(len(l) for _, l in bloques) + 2 * len(bloques)
    tam = 18 if total <= 30 else 16
    # El código no se envuelve: se achica la letra hasta que entre la línea más larga.
    codigo = [l.lstrip("!") for _, ls in bloques for l in ls if not l.lstrip("!").startswith("# ")]
    while tam > 13 and max(d.textlength(l, font=fuente(MONO_B, tam)) for l in codigo) > cw - 44:
        tam -= 1
    paso = tam + 9
    mono, mono_b = fuente(MONO, tam), fuente(MONO_B, tam)
    y = cy + 76
    margen = cx + 22
    for programa, lineas in bloques:
        d.text((margen, y), programa, font=fuente(SANS_B, 23), fill=AZUL)
        y += 38
        for linea in lineas:
            resaltar = linea.startswith("!")
            texto = linea[1:] if resaltar else linea
            comentario = texto.startswith("# ")
            texto = texto[2:] if comentario else texto
            f = mono_b if resaltar else mono
            color = TENUE if comentario else TEXTO
            renglones = envolver(d, texto, f, cw - 60) if comentario else [texto]
            for r in renglones:
                if resaltar:
                    d.rectangle((cx + 12, y - 3, cx + cw - 12, y + paso - 5), fill=RESALTE)
                    d.rectangle((cx + 12, y - 3, cx + 17, y + paso - 5), fill=ACENTO)
                d.text((margen, y), r, font=f, fill=color)
                y += paso
        y += 22
    if nota:
        nota_al_pie(d, nota)
    assert y < cy + ch - 60, (nombre, y)  # el código no debe pisar la nota
    im.save(G / f"{nombre}.png")


def producto():
    """El motor de referencia (tres vistas) y dónde entra la celda en su fabricación."""
    im, d = marco("Qué se fabrica", "Motor universal de lavarropas")
    cx, cy, cw, ch = CARTA
    fotos = AQUI.parents[1] / "b_investigacion" / "img"
    y = cy + 74
    for n in ("weg_u0075_01.jpg", "weg_u0075_02.jpg", "weg_u0075_03.jpg"):
        foto = Image.open(fotos / n).convert("RGB")
        caja = ImageChops.difference(foto, Image.new("RGB", foto.size, "white")).convert("L").point(
            lambda v: 255 if v > 18 else 0).getbbox()
        foto = foto.crop(caja)
        alto = 170
        foto = foto.resize((round(foto.width * alto / foto.height), alto), Image.LANCZOS)
        im.paste(foto, (cx + (cw - foto.width) // 2, y))
        y += alto + 12
    pasos = [("Chapas apiladas", False), ("Soldadura del paquete: esta celda", True),
             ("Bobinado de campo", False), ("Armado del motor", False)]
    y += 14
    for i, (paso, propio) in enumerate(pasos):
        f = fuente(SANS_B if propio else SANS, 22)
        if propio:
            d.rounded_rectangle((cx + 14, y - 6, cx + cw - 14, y + 30), radius=6, fill=RESALTE)
            d.rectangle((cx + 14, y - 6, cx + 19, y + 30), fill=ACENTO)
        d.text((cx + 34, y), paso, font=f, fill=TEXTO)
        y += 36
        if i < len(pasos) - 1:
            d.text((cx + 40, y - 6), "↓", font=fuente(SANS, 20), fill=TENUE)
            y += 20
    assert y < cy + ch - 20, ("d_producto", y)
    im.save(G / "d_producto.png")


def versiones():
    im, d = marco("Cómo evolucionó la celda", "Versiones de la estación")
    cx, cy, cw, ch = CARTA
    y = cy + 84
    for v, texto in VERSIONES:
        actual = v == VERSIONES[-1][0]
        if actual:
            d.rounded_rectangle((cx + 14, y - 10, cx + cw - 14, y + 104), radius=8, fill=RESALTE)
        d.text((cx + 26, y), v, font=fuente(MONO_B, 30), fill=ACENTO if actual else AZUL)
        yy = y
        for r in envolver(d, texto, fuente(SANS, 22), cw - 140):
            d.text((cx + 112, yy + 2), r, font=fuente(SANS, 22), fill=TEXTO)
            yy += 31
        y += max(yy - y, 62) + 56
    nota_al_pie(d, "Cada versión se generó a partir de la anterior; la v05 es la que se entrega.")
    im.save(G / "d_versiones.png")


def centrado(d, y, texto, f, color):
    d.text(((W - d.textlength(texto, font=f)) / 2, y), texto, font=f, fill=color)


def portada():
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    centrado(d, 150, "Universidad Tecnológica Nacional · Facultad Regional Córdoba", fuente(SANS, 34), "#C9D6E3")
    centrado(d, 200, "Licenciatura en Automatización y Control · Robótica Industrial", fuente(SANS, 30), "#8FA3B8")
    centrado(d, 330, "TRABAJO DE FIN DE CURSO", fuente(SANS_B, 28), ACENTO)
    centrado(d, 390, "Celda robotizada de soldadura TIG", fuente(SANS_B, 76), "white")
    centrado(d, 485, "de paquetes de estator", fuente(SANS_B, 76), "white")
    d.line((W / 2 - 120, 615, W / 2 + 120, 615), fill=ACENTO, width=4)
    centrado(d, 660, "Grupo 4", fuente(SANS_B, 40), "white")
    centrado(d, 718, "Casali Emiliano · Ferrero Facundo · Vera Gonzalo", fuente(SANS, 34), "#C9D6E3")
    centrado(d, 820, "Docentes: Ing. Julián Luque · Lic. Sergio Perassi", fuente(SANS, 28), "#8FA3B8")
    centrado(d, 865, "Comisión 2LA1 · 2026", fuente(SANS, 28), "#8FA3B8")
    im.save(G / "portada.png")


def placa():
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    centrado(d, 430, "Gracias", fuente(SANS_B, 80), "white")
    d.line((W / 2 - 90, 545, W / 2 + 90, 545), fill=ACENTO, width=4)
    centrado(d, 585, "Grupo 4 · Robótica Industrial · UTN FRC · 2026", fuente(SANS, 32), "#C9D6E3")
    im.save(G / "placa.png")


if __name__ == "__main__":
    G.mkdir(exist_ok=True)
    portada()
    placa()
    for t in TARJETAS:
        tarjeta(*t)
    producto()
    versiones()
    print("gráficos en", G)
