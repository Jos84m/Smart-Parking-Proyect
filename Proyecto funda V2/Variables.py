# Variables.py - Configuración centralizada

# Dimensiones y rendimiento
ANCHO, ALTO, FPS = 1400, 900, 60

# Conversión HEX a RGB
hex_to_rgb = lambda h: tuple(int(h.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

# Colores HEX
COLOR_PRIMARIO = "#2C3E50"
COLOR_SECUNDARIO = "#3498DB"
COLOR_TEXTO = "#ECF0F1"
COLOR_BOTON = "#27AE60"
COLOR_BOTON_HOVER = "#229954"
COLOR_FONDO = "#1A1A1A"

# Colores RGB
NEGRO, BLANCO = (0, 0, 0), (255, 255, 255)
GRIS, GRIS_CLARO = (100, 100, 100), (180, 180, 180)
VERDE, VERDE_HOVER = (46, 204, 113), (39, 174, 96)
ROJO, ROJO_HOVER = (231, 76, 60), (192, 57, 43)
AZUL, AZUL_HOVER = (52, 152, 219), (41, 128, 185)
NARANJA, NARANJA_HOVER = (230, 126, 34), (211, 84, 0)
MORADO, MORADO_HOVER = (155, 89, 182), (142, 68, 173)
AMARILLO = (241, 196, 15)
CYAN, CYAN_HOVER = (26, 188, 156), (22, 160, 133)

# Configuración del sistema
CONFIG = {
    'tarifa_por_10seg': 1000,
    'tipo_cambio': 520.0,
    'ip_parqueo1': '192.168.1.119',
    'ip_parqueo2': '192.168.1.101',
    'puerto': 8080,
    'auto_refresh': True,
    'espacios_por_parqueo': 2
}

# UI
PADDING, BORDER_RADIUS = 20, 10
RUTA_GIF = "fondo2.gif"