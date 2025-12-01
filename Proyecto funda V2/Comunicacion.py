import requests
import time
from typing import Optional, Dict

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
    
    def activar(self) -> bool:
        """Activa el comunicador y verifica conexión"""
        if self.verificar_conexion():
            self.activo = True
            print(f"✓ Comunicador activado: {self.ip}:{self.puerto}")
            return True
        print(f"✗ No se pudo conectar a: {self.ip}:{self.puerto}")
        return False
    
    def desactivar(self):
        """Desactiva el comunicador"""
        self.activo = self.conectado = False
        print(f"○ Comunicador desactivado: {self.ip}:{self.puerto}")
    
    def verificar_conexion(self) -> bool:
        """Verifica si el Pico está disponible"""
        try:
            response = requests.get(f"{self.base_url}/estado", timeout=1)
            self.conectado = response.status_code == 200
            self.ultimo_error = None
            return self.conectado
        except Exception as e:
            self.conectado = False
            self.ultimo_error = str(e)
            return False
    
    def enviar_comando(self, accion: str, **kwargs) -> Optional[Dict]:
        """Envía un comando al Pico"""
        if not self.activo:
            return {"status": "ok", "mensaje": "Modo simulación"}
        
        try:
            comando = {"accion": accion, **kwargs}
            response = requests.post(
                f"{self.base_url}/comando",
                json=comando,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.ultimo_error = None
                return response.json()
            
            self.ultimo_error = f"HTTP {response.status_code}"
            return None
            
        except requests.exceptions.Timeout:
            self.ultimo_error = "Timeout"
            print(f"⚠ Timeout comunicándose con {self.ip}")
        except requests.exceptions.ConnectionError:
            self.ultimo_error = "Sin conexión"
            print(f"⚠ Error de conexión con {self.ip}")
            self.conectado = False
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"⚠ Error: {e}")
        
        return None
    
    def obtener_estado(self) -> Optional[Dict]:
        """Obtiene el estado actual del parqueo"""
        if not self.activo:
            return None
        
        try:
            response = requests.get(f"{self.base_url}/estado", timeout=self.timeout)
            if response.status_code == 200:
                self.ultimo_estado = response.json()
                self.ultimo_error = None
                return self.ultimo_estado
        except Exception as e:
            self.ultimo_error = str(e)
        
        return None
    
    # Comandos específicos simplificados
    def _ejecutar_comando(self, accion: str, **kwargs) -> bool:
        """Método auxiliar para ejecutar comandos"""
        resultado = self.enviar_comando(accion, **kwargs)
        return resultado and resultado.get("status") == "ok"
    
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
    
    def mover_servo_boton(self, angulo: int) -> bool:
        return self._ejecutar_comando("mover_servo_boton", angulo=angulo)
    
    def get_estado_conexion(self) -> str:
        """Retorna el estado de conexión como texto"""
        if not self.activo:
            return "Inactivo"
        if self.conectado:
            return "Conectado"
        if self.ultimo_error:
            return f"Error: {self.ultimo_error}"
        return "Desconectado"


class GestorComunicaciones:
    """Gestiona múltiples comunicadores"""
    
    def __init__(self, ips: list, puerto: int = 8080):
        self.comunicadores = [ComunicadorPico(ip, puerto) for ip in ips]
        self.activo = False
    
    def activar_todos(self) -> Dict[int, bool]:
        """Activa todos los comunicadores"""
        self.activo = True
        resultados = {}
        for i, com in enumerate(self.comunicadores):
            resultados[i] = com.activar()
            time.sleep(0.2)
        return resultados
    
    def desactivar_todos(self):
        """Desactiva todos los comunicadores"""
        self.activo = False
        for com in self.comunicadores:
            com.desactivar()
    
    def verificar_conexiones(self) -> Dict[int, bool]:
        """Verifica el estado de todas las conexiones"""
        return {i: com.verificar_conexion() if com.activo else False 
                for i, com in enumerate(self.comunicadores)}
    
    def obtener_estados(self) -> Dict[int, Optional[Dict]]:
        """Obtiene el estado de todos los parqueos"""
        return {i: com.obtener_estado() for i, com in enumerate(self.comunicadores)}
    
    def get_comunicador(self, index: int) -> Optional[ComunicadorPico]:
        """Obtiene un comunicador específico"""
        return self.comunicadores[index] if 0 <= index < len(self.comunicadores) else None