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
    'ip_parqueo1': '192.168.100.179',
    'ip_parqueo2': '172.20.10.3',
    'puerto': 8080,
    'auto_refresh': True,
    'espacios_por_parqueo': 2
}



# UI
PADDING, BORDER_RADIUS = 20, 10
RUTA_GIF = "fondo2.gif"

# ==========================================
# Logger para Comunicaciones
# ==========================================
import logging
from datetime import datetime

class LoggerComunicador:
    """Gestor centralizado de logging para comunicaciones con Picos"""
    
    def __init__(self, nombre="ComunicadorPico", archivo="comunicacion.log"):
        self.nombre = nombre
        self.archivo = archivo
        
        # Crear logger
        self.logger = logging.getLogger(nombre)
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo
        file_handler = logging.FileHandler(archivo, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.estadisticas = {
            'conexiones_exitosas': 0,
            'conexiones_fallidas': 0,
            'comandos_enviados': 0,
            'errores': []
        }
    
    def info(self, mensaje: str):
        """Log de información"""
        self.logger.info(mensaje)
    
    def warning(self, mensaje: str):
        """Log de advertencia"""
        self.logger.warning(mensaje)
    
    def error(self, mensaje: str):
        """Log de error"""
        self.logger.error(mensaje)
        self.estadisticas['errores'].append({
            'timestamp': datetime.now().isoformat(),
            'mensaje': mensaje
        })
    
    def debug(self, mensaje: str):
        """Log de debug"""
        self.logger.debug(mensaje)
    
    def registrar_conexion_exitosa(self, ip: str, puerto: int):
        """Registra conexión exitosa"""
        self.estadisticas['conexiones_exitosas'] += 1
        self.info(f"[OK] Conexion exitosa: {ip}:{puerto}")
    
    def registrar_conexion_fallida(self, ip: str, puerto: int, razon: str):
        """Registra conexión fallida"""
        self.estadisticas['conexiones_fallidas'] += 1
        self.warning(f"[FAIL] Conexion fallida: {ip}:{puerto} - {razon}")
    
    def registrar_comando(self, accion: str, parametros: dict = None):
        """Registra envío de comando"""
        self.estadisticas['comandos_enviados'] += 1
        params_str = f" | Params: {parametros}" if parametros else ""
        self.debug(f"[CMD] Comando enviado: {accion}{params_str}")
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas de comunicación"""
        return self.estadisticas.copy()
    
    def limpiar_estadisticas(self):
        """Limpia las estadísticas"""
        self.estadisticas['conexiones_exitosas'] = 0
        self.estadisticas['conexiones_fallidas'] = 0
        self.estadisticas['comandos_enviados'] = 0
        self.estadisticas['errores'] = []

# Instancia global del logger
logger_com = LoggerComunicador("CEstaciona", "comunicacion.log")