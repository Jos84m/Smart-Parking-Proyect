import requests
import time
from typing import Optional, Dict
from Variables import logger_com


class ComunicadorPico:
    """Maneja la comunicación HTTP con las Raspberry Pi Pico W"""

    def __init__(self, ip: str, puerto: int = 8080, timeout: int = 2):
        self.ip = ip
        self.puerto = puerto
        self.timeout = timeout
        self.base_url = f"http://{ip}:{puerto}"
        self.conectado = False
        self.activo = False
        self.ultimo_estado = None
        self.ultimo_error = None
        self.logger = logger_com

    # --------------------------------------------------------------
    # ACTIVACIÓN
    # --------------------------------------------------------------
    def activar(self) -> bool:
        """Activa el comunicador y verifica conexión"""
        if self.verificar_conexion():
            self.activo = True
            self.logger.registrar_conexion_exitosa(self.ip, self.puerto)
            return True
        self.logger.registrar_conexion_fallida(self.ip, self.puerto, "No responde")
        return False

    def desactivar(self):
        """Desactiva el comunicador"""
        self.activo = self.conectado = False
        self.logger.info(f"[STOP] Comunicador desactivado: {self.ip}:{self.puerto}")

    # --------------------------------------------------------------
    # VERIFICAR CONEXIÓN
    # --------------------------------------------------------------
    def verificar_conexion(self) -> bool:
        """Verifica si el Pico está disponible"""
        try:
            response = requests.get(f"{self.base_url}/estado", timeout=self.timeout)
            self.conectado = (response.status_code == 200 or response.ok)
            self.ultimo_error = None
            return self.conectado

        except Exception as e:
            self.conectado = False
            self.ultimo_error = str(e)
            self.logger.debug(f"Error al verificar conexión {self.ip}: {e}")
            return False

    # --------------------------------------------------------------
    # ENVÍO DE COMANDOS
    # --------------------------------------------------------------
    def enviar_comando(self, accion: str, **kwargs) -> Optional[Dict]:
        """Envía un comando al Pico"""

        if not self.activo:
            # Simulación consistente
            return {"status": "simulacion", "mensaje": "Modo simulación"}

        try:
            comando = {"accion": accion, **kwargs}
            self.logger.registrar_comando(accion, kwargs)

            response = requests.post(
                f"{self.base_url}/comando",
                json=comando,
                timeout=self.timeout
            )

            if response.status_code == 200 or response.ok:
                self.ultimo_error = None
                try:
                    return response.json()
                except:
                    return {"status": "ok", "mensaje": "ok"}

            # Error HTTP
            self.ultimo_error = f"HTTP {response.status_code}"
            return {"status": "error", "mensaje": self.ultimo_error}

        except requests.exceptions.Timeout:
            self.ultimo_error = "Timeout"
            self.logger.warning(f"Timeout en {self.ip} (acción: {accion})")

        except requests.exceptions.ConnectionError:
            self.ultimo_error = "Sin conexión"
            self.logger.error(f"Sin conexión con {self.ip}")
            self.conectado = False

        except Exception as e:
            self.ultimo_error = str(e)
            self.logger.error(f"Error al enviar comando '{accion}': {e}")

        return {"status": "error", "mensaje": self.ultimo_error}

    # --------------------------------------------------------------
    # OBTENER ESTADO
    # --------------------------------------------------------------
    def obtener_estado(self) -> Optional[Dict]:
        """Obtiene el estado actual del parqueo desde la Pico"""
        if not self.activo:
            return None

        try:
            response = requests.get(f"{self.base_url}/estado", timeout=self.timeout)
            if response.status_code == 200 or response.ok:
                self.ultimo_estado = response.json()
                self.ultimo_error = None
                return self.ultimo_estado

        except Exception as e:
            self.ultimo_error = str(e)
            self.logger.debug(f"Error al obtener estado de {self.ip}: {e}")

        return None

    # --------------------------------------------------------------
    # MÉTODO AUXILIAR
    # --------------------------------------------------------------
    def _ejecutar_comando(self, accion: str, **kwargs) -> bool:
        resultado = self.enviar_comando(accion, **kwargs)
        return resultado and resultado.get("status") in ("ok", "simulacion")

    # --------------------------------------------------------------
    # MÉTODOS ESPECÍFICOS (USADOS POR TU INTERFAZ)
    # --------------------------------------------------------------
    def ocupar_espacio(self, num_espacio: int) -> bool:
        return self._ejecutar_comando("ocupar", espacio=num_espacio)

    def liberar_espacio(self, num_espacio: int) -> bool:
        return self._ejecutar_comando("liberar", espacio=num_espacio)

    def toggle_led(self, num_espacio: int, color: str = "verde") -> bool:
        return self._ejecutar_comando("toggle_led", espacio=num_espacio, color=color)

    def toggle_aguja(self) -> bool:
        return self._ejecutar_comando("toggle_aguja")

    def actualizar_display(self, numero: int) -> bool:
        return self._ejecutar_comando("actualizar_display", numero=numero)

    # --- ALIAS IMPORTANTE PARA COMPATIBILIDAD ---
    def mover_servo(self, angulo: int) -> bool:
        return self._ejecutar_comando("mover_servo", angulo=angulo)

    def mover_servo_boton(self, angulo: int) -> bool:
        return self._ejecutar_comando("mover_servo_boton", angulo=angulo)

    # --------------------------------------------------------------
    def get_estado_conexion(self) -> str:
        """Retorna el estado de conexión como texto"""
        if not self.activo:
            return "Inactivo"
        if self.conectado:
            return "Conectado"
        if self.ultimo_error:
            return f"Error: {self.ultimo_error}"
        return "Desconectado"


# ================================================================
# GESTOR DE COMUNICACIONES
# ================================================================
class GestorComunicaciones:
    """Gestiona múltiples comunicadores"""

    def __init__(self, ips: list, puerto: int = 8080):
        self.comunicadores = [ComunicadorPico(ip, puerto) for ip in ips]
        self.activo = False
        self.logger = logger_com

    def activar_todos(self) -> Dict[int, bool]:
        self.activo = True
        self.logger.info("Activando todos los comunicadores...")
        resultados = {}

        for i, com in enumerate(self.comunicadores):
            resultados[i] = com.activar()
            time.sleep(0.2)

        return resultados

    def desactivar_todos(self):
        self.activo = False
        self.logger.info("Desactivando todos los comunicadores...")
        for com in self.comunicadores:
            com.desactivar()

    def verificar_conexiones(self) -> Dict[int, bool]:
        return {
            i: com.verificar_conexion() if com.activo else False
            for i, com in enumerate(self.comunicadores)
        }

    def obtener_estados(self) -> Dict[int, Optional[Dict]]:
        return {i: com.obtener_estado() for i, com in enumerate(self.comunicadores)}

    def get_comunicador(self, index: int) -> Optional[ComunicadorPico]:
        return (
            self.comunicadores[index]
            if 0 <= index < len(self.comunicadores)
            else None
        )
