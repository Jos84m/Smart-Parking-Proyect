#===========================================================================
# Zona de Importaciones Y Bibliotecas)
#===========================================================================
import pygame
import sys
from datetime import datetime
from Variables import (
    ANCHO, ALTO, FPS,
    NEGRO, BLANCO, GRIS, GRIS_CLARO,
    VERDE, VERDE_HOVER, ROJO, ROJO_HOVER,
    AZUL, AZUL_HOVER, NARANJA, NARANJA_HOVER,
    MORADO, MORADO_HOVER, AMARILLO, CYAN, CYAN_HOVER, 
    COLOR_TEXTO, hex_to_rgb, logger_com, CONFIG
)
import requests
from PIL import Image, ImageSequence
import logging
from Comunicacion import ComunicadorPico, GestorComunicaciones
# ============================================================================
# CONFIGURACIÓN DE COMUNICACION 
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('comunicacion.log'),
        logging.StreamHandler()
    ]
)
# ============================================================================
# CLASE DE BUTON Y SUS CARACTERISTICAS 
# ============================================================================
class Button:
    def __init__(self, x, y, ancho, alto, texto, color, color_hover, accion=None, icono=None):
        self.rect = pygame.Rect(x, y, ancho, alto)
        self.texto = texto
        self.color = color
        self.color_hover = color_hover
        self.accion = accion
        self.icono = icono
        self.hover = False
        self.click_effect = 0
        
    def draw(self, screen, font):
        offset = self.click_effect
        rect_actual = self.rect.inflate(-offset * 2, -offset * 2)
        color_actual = self.color_hover if self.hover else self.color

        shadow_rect = rect_actual.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=10)
        
        pygame.draw.rect(screen, color_actual, rect_actual, border_radius=10)

        if self.hover:
            pygame.draw.rect(screen, hex_to_rgb(COLOR_TEXTO), rect_actual, 3, border_radius=10)
        else:
            pygame.draw.rect(screen, GRIS_CLARO, rect_actual, 2, border_radius=10)

        texto_render = font.render(self.texto, True, BLANCO)
        texto_rect = texto_render.get_rect(center=rect_actual.center)
        screen.blit(texto_render, texto_rect)

        if self.click_effect > 0:
            self.click_effect -= 1

    def handle_event(self, event, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hover:
                self.click_effect = 5
                if self.accion:
                    self.accion()
                return True
        return False
# ============================================================================
# CLASE ESPACIO DEL PARQUEO (OCUPAR Y lIBERAR)
# ============================================================================
class EspacioParqueo:
    def __init__(self, id_espacio):
        self.id = id_espacio
        self.ocupado = False
        self.hora_entrada = None
        self.led_encendido = True
        # Ocupar y Liberar espacio
    def ocupar(self):
        if not self.ocupado:
            self.ocupado = True
            self.hora_entrada = datetime.now()
            self.led_encendido = False
            return True
        return False
        # Liberar espacio
    def liberar(self):
        if self.ocupado:
            self.ocupado = False
            self.led_encendido = True
            tiempo_estancia = (datetime.now() - self.hora_entrada).total_seconds()
            self.hora_entrada = None
            return tiempo_estancia
        return 0
        # Alternar estado del LED
    def toggle_led(self):
        self.led_encendido = not self.led_encendido

# ============================================================================
# CLASE PARQUEO CON SU CONFIGURACION Y CARACTERISTICAS 
# ============================================================================
class Parqueo:
    def __init__(self, id_parqueo, ip_pico=None, puerto=8080):
        self.id = id_parqueo
        self.espacios = [EspacioParqueo(i) for i in range(2)]
        self.aguja_abierta = False
        self.vehiculos_totales = 0
        self.tiempo_total_estancia = 0
        self.ganancias_colones = 0
        self.activo = False
        
        self.ip_pico = ip_pico
        self.puerto = puerto
        self.comunicador = ComunicadorPico(ip_pico, puerto) if ip_pico else None
        # Espacios disponibles
    def espacios_disponibles(self):
        return sum(1 for e in self.espacios if not e.ocupado)
        # Alternar aguja
    def toggle_aguja(self):
        self.aguja_abierta = not self.aguja_abierta
        
        if self.activo and self.comunicador:
            self.comunicador.toggle_aguja()
        
        self.actualizar_display_remoto()
        # Registrar salida de vehículo
    def registrar_salida(self, tiempo_estancia):
        self.vehiculos_totales += 1
        self.tiempo_total_estancia += tiempo_estancia
        costo = (tiempo_estancia / 10) * 1000
        self.ganancias_colones += costo
        return costo
        # Promedio de estancia
    def promedio_estancia(self):
        if self.vehiculos_totales > 0:
            return self.tiempo_total_estancia / self.vehiculos_totales
        return 0
    # Actualizar display remoto
    def actualizar_display_remoto(self):
        if self.activo and self.comunicador:
            espacios = self.espacios_disponibles()
            try:
                self.comunicador.actualizar_display(espacios)
            except Exception as e:
                logging.warning(f"Parqueo {self.id} | Error al actualizar display: {e}")

# ============================================================================
# APLICACIÓN PRINCIPAL CON SUS CARACTERISTICAS Y FUNCIONES
# ============================================================================
class AplicacionParqueo:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Fuentes
        self.font_titulo = pygame.font.Font(None, 64)
        self.font_subtitulo = pygame.font.Font(None, 40)
        self.font_normal = pygame.font.Font(None, 28)
        self.font_pequeña = pygame.font.Font(None, 22)
        
        # Parqueos con comunicación remota
        self.parqueos = [
            Parqueo(1, ip_pico=CONFIG['ip_parqueo1'], puerto=CONFIG['puerto']),
            Parqueo(2, ip_pico=CONFIG['ip_parqueo2'], puerto=CONFIG['puerto'])
        ]
        # Estado de la aplicación y características
        self.estado = 0
        self.config = CONFIG.copy()
        self.logger = logger_com
        self.historial_comandos = []
        self.max_historial = 10
        self.comunicadores_activos = False
        self.gestor_comunicaciones = None
        
        # Crear botones
        self.crear_botones()
        
        # Cargar GIF de fondo
        self.cargar_fondo_gif("fondo2.gif")
        
        # Inicializar comunicadores
        self.inicializar_comunicadores()

    # ========================================================================
    # COMUNICACIÓN CON RASPBERRY PI
    # ========================================================================
    # Inicializar comunicadores
    def inicializar_comunicadores(self):
        try:
            print("\n" + "="*60)
            print(" INICIALIZANDO COMUNICACIÓN CON RASPBERRY PI PICO W")
            print("="*60)
            
            ips = [self.config['ip_parqueo1'], self.config['ip_parqueo2']]
            
            self.gestor_comunicaciones = GestorComunicaciones(
                ips=ips,
                puerto=self.config['puerto']
            )
            
            resultados = self.gestor_comunicaciones.activar_todos()
            
            print("\n Resultados de conexión:")
            for parqueo_id, conectado in resultados.items():
                ip = ips[parqueo_id]
                estado = "CONECTADO" if conectado else "NO DISPONIBLE"
                if conectado:
                    print(f"   Parqueo {parqueo_id + 1} ({ip}): {estado}")
                    self.logger.registrar_conexion_exitosa(ip, 8080)
                    self.parqueos[parqueo_id].activo = True
                else:
                    print(f"  Parqueo {parqueo_id + 1} ({ip}): {estado}")
                    self.logger.registrar_conexion_fallida(ip, 8080, "No responde")
            
            self.comunicadores_activos = any(resultados.values())
            
            if self.comunicadores_activos:
                print("\n Sistema en MODO COMUNICACIÓN REAL")
            else:
                print("\n  Sistema en MODO SIMULACIÓN (sin conexión)")
            
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n Error al inicializar comunicadores: {e}")
            print("  Sistema operará en MODO SIMULACIÓN\n")
            self.logger.error(f"Inicialización: {e}")
            self.comunicadores_activos = False
    
    def agregar_a_historial(self, comando_texto):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.historial_comandos.append(f"[{timestamp}] {comando_texto}")
        
        if len(self.historial_comandos) > self.max_historial:
            self.historial_comandos.pop(0)

    # ========================================================================
    # COMANDOS CON COMUNICACIÓN 
    # ========================================================================
    
    def toggle_led(self, parqueo_id, espacio_id):
        print(f"\n [COMANDO] Toggle LED - Parqueo {parqueo_id + 1}, Espacio {espacio_id + 1}")
        
        self.parqueos[parqueo_id].espacios[espacio_id].toggle_led()
        nuevo_estado = self.parqueos[parqueo_id].espacios[espacio_id].led_encendido
        
        self.agregar_a_historial(f"LED P{parqueo_id+1} E{espacio_id+1}: {'ON' if nuevo_estado else 'OFF'}")
        
        if self.comunicadores_activos and self.gestor_comunicaciones:
            comunicador = self.gestor_comunicaciones.get_comunicador(parqueo_id)
            if comunicador and comunicador.activo:
                color = "verde" if nuevo_estado else "apagado"
                resultado = comunicador.toggle_led(espacio_id, color)
                
                if resultado:
                    print(f"   ✓ Comando enviado exitosamente")
                    self.logger.registrar_comando("toggle_led", {"parqueo": parqueo_id, "espacio": espacio_id})
                else:
                    print(f"   ✗ Error al enviar comando")
            else:
                print(f"     Parqueo no conectado")
        else:
            print(f"     Modo simulación")
    
    def toggle_aguja(self, parqueo_id):
        print(f"\n [COMANDO] Toggle Aguja - Parqueo {parqueo_id + 1}")
        
        self.parqueos[parqueo_id].toggle_aguja()
        nuevo_estado = self.parqueos[parqueo_id].aguja_abierta
        
        self.agregar_a_historial(f"Aguja P{parqueo_id+1}: {'ABIERTA' if nuevo_estado else 'CERRADA'}")
        
        if self.comunicadores_activos and self.gestor_comunicaciones:
            comunicador = self.gestor_comunicaciones.get_comunicador(parqueo_id)
            if comunicador and comunicador.activo:
                resultado = comunicador.toggle_aguja()
                if resultado:
                    print(f"  Comando enviado exitosamente")
                    self.logger.registrar_comando("toggle_aguja", {"parqueo": parqueo_id})
    
    def ocupar_espacio(self, parqueo_id, espacio_id):
        print(f"\n [COMANDO] Ocupar Espacio - Parqueo {parqueo_id + 1}, Espacio {espacio_id + 1}")
        
        resultado = self.parqueos[parqueo_id].espacios[espacio_id].ocupar()
        
        if resultado:
            print(f" Espacio marcado como OCUPADO")
            self.agregar_a_historial(f"Ocupar P{parqueo_id+1} E{espacio_id+1}")
            
            if self.comunicadores_activos and self.gestor_comunicaciones:
                comunicador = self.gestor_comunicaciones.get_comunicador(parqueo_id)
                if comunicador and comunicador.activo:
                    resultado_pico = comunicador.ocupar_espacio(espacio_id)
                    
                    if resultado_pico:
                        print(f"   ✓ Comando enviado al Pico")
                        self.logger.registrar_comando("ocupar", {"parqueo": parqueo_id, "espacio": espacio_id})
                        espacios_libres = self.parqueos[parqueo_id].espacios_disponibles()
                        comunicador.actualizar_display(espacios_libres)
    
    def liberar_espacio(self, parqueo_id, espacio_id):
        print(f"\n [COMANDO] Liberar Espacio - Parqueo {parqueo_id + 1}, Espacio {espacio_id + 1}")
        
        tiempo = self.parqueos[parqueo_id].espacios[espacio_id].liberar()
        
        if tiempo > 0:
            self.parqueos[parqueo_id].registrar_salida(tiempo)
            costo = (tiempo / 10) * 1000
            
            print(f"   Espacio liberado")
            print(f"     Tiempo: {tiempo:.1f}s")
            print(f"    Costo: ₡{costo:.0f}")
            
            self.agregar_a_historial(f"Liberar P{parqueo_id+1} E{espacio_id+1} - ₡{costo:.0f}")
            
            if self.comunicadores_activos and self.gestor_comunicaciones:
                comunicador = self.gestor_comunicaciones.get_comunicador(parqueo_id)
                if comunicador and comunicador.activo:
                    resultado_pico = comunicador.liberar_espacio(espacio_id)
                    
                    if resultado_pico:
                        print(f"  Comando enviado al Pico")
                        espacios_libres = self.parqueos[parqueo_id].espacios_disponibles()
                        comunicador.actualizar_display(espacios_libres)

    # ========================================================================
    # GIF DE FONDO
    # ========================================================================
    
    def cargar_fondo_gif(self, ruta_gif):
        try:
            self.gif_frames = []
            gif = Image.open(ruta_gif)
            
            for frame in ImageSequence.Iterator(gif):
                frame_rgba = frame.convert("RGBA")
                frame_resized = frame_rgba.resize((ANCHO, ALTO))
                frame_str = frame_resized.tobytes()
                pygame_surface = pygame.image.fromstring(frame_str, (ANCHO, ALTO), "RGBA")
                self.gif_frames.append(pygame_surface)
            
            self.frame_actual = 0
            self.gif_delay = 50
            self.ultimo_frame_tiempo = pygame.time.get_ticks()
            self.gif_cargado = True
            print(f" GIF cargado: {len(self.gif_frames)} frames")
        except Exception as e:
            print(f" Error al cargar GIF: {e}")
            self.gif_cargado = False

    def actualizar_fondo_gif(self):
        if not self.gif_cargado:
            return
        
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.ultimo_frame_tiempo > self.gif_delay:
            self.frame_actual = (self.frame_actual + 1) % len(self.gif_frames)
            self.ultimo_frame_tiempo = tiempo_actual

    def dibujar_fondo_gif(self):
        if self.gif_cargado and self.gif_frames:
            fondo = self.gif_frames[self.frame_actual].copy()
            fondo.set_alpha(200)
            self.screen.blit(fondo, (0, 0))
            
            overlay = pygame.Surface((ANCHO, ALTO))
            overlay.set_alpha(120)
            overlay.fill(NEGRO)
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(NEGRO)

    # ========================================================================
    # BOTONES
    # ========================================================================
    
    def crear_botones(self):
        center_x = ANCHO // 2
        btn_width = 400
        btn_height = 70
        
        num_botones = 5
        espacio_total = ALTO - 300
        spacing = espacio_total // (num_botones + 1)
        start_y = 120
        
        self.btn_menu_iniciar = Button(
            center_x - btn_width // 2, start_y, btn_width, btn_height,
            "INICIAR CONTROL", VERDE, VERDE_HOVER, lambda: self.cambiar_estado(1)
        )
        
        self.btn_menu_estadisticas = Button(
            center_x - btn_width // 2, start_y + spacing, btn_width, btn_height,
            "ESTADÍSTICAS", AZUL, AZUL_HOVER, lambda: self.cambiar_estado(2)
        )
        
        self.btn_menu_config = Button(
            center_x - btn_width // 2, start_y + spacing * 2, btn_width, btn_height,
            "CONFIGURACIÓN", NARANJA, NARANJA_HOVER, lambda: self.cambiar_estado(3)
        )
        
        self.btn_menu_about = Button(
            center_x - btn_width // 2, start_y + spacing * 3, btn_width, btn_height,
            "ACERCA DE", MORADO, MORADO_HOVER, lambda: self.cambiar_estado(4)
        )
        
        self.btn_salir = Button(
            center_x - btn_width // 2, start_y + spacing * 4, btn_width, btn_height,
            "SALIR", ROJO, ROJO_HOVER, lambda: self.quit()
        )
        
        self.btn_volver = Button(
            50, 20, 150, 50, "← VOLVER", GRIS, GRIS_CLARO, 
            lambda: self.cambiar_estado(0)
        )
        
        self.btn_config_rapida = Button(
            ANCHO - 200, 20, 150, 50, "⚙ CONFIG", 
            NARANJA, NARANJA_HOVER, lambda: self.cambiar_estado(3)
        )
        
        # Botones de control 
        p1_x_start = 50
        p1_y_start = 580
        btn_w = 110
        btn_h = 45
        spacing_x = 125
        spacing_y = 55
        
        # Parqueo 1
        self.btn_led1_esp1 = Button(
            p1_x_start, p1_y_start,
            btn_w, btn_h, "LED 1", VERDE, VERDE_HOVER,
            lambda: self.toggle_led(0, 0)
        )
        
        self.btn_ocupar1_esp1 = Button(
            p1_x_start + spacing_x, p1_y_start,
            btn_w, btn_h, "Ocupar 1", ROJO, ROJO_HOVER,
            lambda: self.ocupar_espacio(0, 0)
        )
        
        self.btn_liberar1_esp1 = Button(
            p1_x_start + spacing_x * 2, p1_y_start,
            btn_w, btn_h, "Liberar 1", AZUL, AZUL_HOVER,
            lambda: self.liberar_espacio(0, 0)
        )
        
        self.btn_led1_esp2 = Button(
            p1_x_start, p1_y_start + spacing_y,
            btn_w, btn_h, "LED 2", VERDE, VERDE_HOVER,
            lambda: self.toggle_led(0, 1)
        )
        
        self.btn_ocupar1_esp2 = Button(
            p1_x_start + spacing_x, p1_y_start + spacing_y,
            btn_w, btn_h, "Ocupar 2", ROJO, ROJO_HOVER,
            lambda: self.ocupar_espacio(0, 1)
        )
        
        self.btn_liberar1_esp2 = Button(
            p1_x_start + spacing_x * 2, p1_y_start + spacing_y,
            btn_w, btn_h, "Liberar 2", AZUL, AZUL_HOVER,
            lambda: self.liberar_espacio(0, 1)
        )
        
        self.btn_aguja1 = Button(
            p1_x_start + spacing_x * 3, p1_y_start + spacing_y // 2,
            btn_w, btn_h, "Aguja", NARANJA, NARANJA_HOVER,
            lambda: self.toggle_aguja(0)
        )
        
        # Parqueo 2
        p2_x_start = 750
        p2_y_start = 580
        
        self.btn_led2_esp1 = Button(
            p2_x_start, p2_y_start,
            btn_w, btn_h, "LED 1", VERDE, VERDE_HOVER,
            lambda: self.toggle_led(1, 0)
        )
        
        self.btn_ocupar2_esp1 = Button(
            p2_x_start + spacing_x, p2_y_start,
            btn_w, btn_h, "Ocupar 1", ROJO, ROJO_HOVER,
            lambda: self.ocupar_espacio(1, 0)
        )
        
        self.btn_liberar2_esp1 = Button(
            p2_x_start + spacing_x * 2, p2_y_start,
            btn_w, btn_h, "Liberar 1", AZUL, AZUL_HOVER,
            lambda: self.liberar_espacio(1, 0)
        )
        
        self.btn_led2_esp2 = Button(
            p2_x_start, p2_y_start + spacing_y,
            btn_w, btn_h, "LED 2", VERDE, VERDE_HOVER,
            lambda: self.toggle_led(1, 1)
        )
        
        self.btn_ocupar2_esp2 = Button(
            p2_x_start + spacing_x, p2_y_start + spacing_y,
            btn_w, btn_h, "Ocupar 2", ROJO, ROJO_HOVER,
            lambda: self.ocupar_espacio(1, 1)
        )
        
        self.btn_liberar2_esp2 = Button(
            p2_x_start + spacing_x * 2, p2_y_start + spacing_y,
            btn_w, btn_h, "Liberar 2", AZUL, AZUL_HOVER,
            lambda: self.liberar_espacio(1, 1)
        )
        
        self.btn_aguja2 = Button(
            p2_x_start + spacing_x * 3, p2_y_start + spacing_y // 2,
            btn_w, btn_h, "Aguja", NARANJA, NARANJA_HOVER,
            lambda: self.toggle_aguja(1)
        )
        
        self.btn_actualizar_tc = Button(
            ANCHO - 300, ALTO - 100, 250, 50,
            "Actualizar Tipo Cambio", CYAN, CYAN_HOVER,
            self.actualizar_tipo_cambio
        )
        
        # Agrupar botones
        self.botones_menu = [
            self.btn_menu_iniciar, 
            self.btn_menu_estadisticas,
            self.btn_menu_config, 
            self.btn_menu_about, 
            self.btn_salir
        ]
        # Agrupar botones de control
        self.botones_control = [
            self.btn_led1_esp1, self.btn_ocupar1_esp1, self.btn_liberar1_esp1,
            self.btn_led1_esp2, self.btn_ocupar1_esp2, self.btn_liberar1_esp2,
            self.btn_aguja1,
            self.btn_led2_esp1, self.btn_ocupar2_esp1, self.btn_liberar2_esp1,
            self.btn_led2_esp2, self.btn_ocupar2_esp2, self.btn_liberar2_esp2,
            self.btn_aguja2
        ]
    
    # ========================================================================
    # MÉTODOS DE UTILIDAD y CAMBIO DE ESTADO y ACTUALIZACIÓN TIPO CAMBIO 
    # ========================================================================
    
    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado

    def quit(self):
        self.running = False
    
    def actualizar_tipo_cambio(self):
        print("\n[TC] Actualizando tipo de cambio...")
        try:
            resp = requests.get('https://api.exchangerate.host/latest?base=USD&symbols=CRC', timeout=6)
            if resp.status_code == 200:
                j = resp.json()
                if 'rates' in j and 'CRC' in j['rates']:
                    rate = float(j['rates']['CRC'])
                    self.config['tipo_cambio'] = rate
                    print(f" Tipo de cambio actualizado: ₡{rate}")
                    self.agregar_a_historial(f"TC actualizado: ₡{rate:.2f}")
                    return
        except:
            pass

        try:
            response = requests.get('https://api.hacienda.go.cr/indicadores/tc/dolar', timeout=6)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'venta' in data:
                    self.config['tipo_cambio'] = float(data['venta'])
                    print(f"  Tipo de cambio actualizado: ₡{self.config['tipo_cambio']}")
                    self.agregar_a_historial(f"TC actualizado: ₡{self.config['tipo_cambio']:.2f}")
                    return
        except Exception as e:
            print(f"   Error: {e}")

        print(f"  No se pudo actualizar, usando: ₡{self.config['tipo_cambio']}")
    
    # ========================================================================
    # MONITORES Y DEBUG UI
    # ========================================================================
    def draw_monitor_comunicacion(self):
        if not self.comunicadores_activos:
            return
        
        monitor_x = 10
        monitor_y = ALTO - 200
        monitor_w = 300
        monitor_h = 180
        
        pygame.draw.rect(self.screen, (20, 20, 30), 
                         (monitor_x, monitor_y, monitor_w, monitor_h), 
                         border_radius=10)
        pygame.draw.rect(self.screen, CYAN, 
                         (monitor_x, monitor_y, monitor_w, monitor_h), 
                         2, border_radius=10)
        
        titulo = self.font_pequeña.render("Monitor de Conexión", True, CYAN)
        self.screen.blit(titulo, (monitor_x + 10, monitor_y + 10))
        
        y_pos = monitor_y + 45
        for i in range(2):
            if self.gestor_comunicaciones:
                comunicador = self.gestor_comunicaciones.get_comunicador(i)
                if comunicador:
                    estado = comunicador.get_estado_conexion()
                    color = VERDE if comunicador.conectado else ROJO
                    
                    pygame.draw.circle(self.screen, color, 
                                     (monitor_x + 20, y_pos + 10), 8)
                    
                    texto = self.font_pequeña.render(
                        f"Parqueo {i+1}: {estado}", 
                        True, BLANCO
                    )
                    self.screen.blit(texto, (monitor_x + 35, y_pos))
                    
                    ip_texto = self.font_pequeña.render(
                        f"  {comunicador.ip}:{comunicador.puerto}", 
                        True, GRIS_CLARO
                    )
                    self.screen.blit(ip_texto, (monitor_x + 35, y_pos + 20))
                    
                    y_pos += 50
# HISTORIAL DE COMANDOS
    def draw_historial_comandos(self):
        if not self.historial_comandos:
            return
        
        panel_x = ANCHO - 420
        panel_y = ALTO - 350
        panel_w = 400
        panel_h = 330
        
        pygame.draw.rect(self.screen, (20, 20, 30),
                         (panel_x, panel_y, panel_w, panel_h),
                         border_radius=10)
        pygame.draw.rect(self.screen, MORADO,
                         (panel_x, panel_y, panel_w, panel_h),
                         2, border_radius=10)
        
        titulo = self.font_pequeña.render(" Historial de Comandos", True, MORADO)
        self.screen.blit(titulo, (panel_x + 10, panel_y + 10))
        
        y_pos = panel_y + 45
        for comando in reversed(self.historial_comandos):
            texto = self.font_pequeña.render(comando, True, GRIS_CLARO)
            if texto.get_width() > panel_w - 20:
                comando = comando[:50] + "..."
                texto = self.font_pequeña.render(comando, True, GRIS_CLARO)
            self.screen.blit(texto, (panel_x + 10, y_pos))
            y_pos += 25
    # ========================================================================
    # DIBUJO DE PANTALLAS
    # ========================================================================
    def draw_menu_principal(self):
        titulo = self.font_titulo.render("CEstaciona", True, BLANCO)
        titulo_rect = titulo.get_rect(center=(ANCHO // 2, 150))
        titulo_shadow = self.font_titulo.render("CEstaciona", True, GRIS)
        self.screen.blit(titulo_shadow, (titulo_rect.x + 4, titulo_rect.y + 4))
        self.screen.blit(titulo, titulo_rect)
        
        subtitulo = self.font_normal.render("Sistema Inteligente de Parqueo", True, GRIS_CLARO)
        subtitulo_rect = subtitulo.get_rect(center=(ANCHO // 2, 210))
        self.screen.blit(subtitulo, subtitulo_rect)
        
        for btn in self.botones_menu:
            btn.draw(self.screen, self.font_subtitulo)
        
        footer = self.font_pequeña.render(
            "TEC - Fundamentos de Sistemas Computacionales 2025",
            True, GRIS_CLARO
        )
        self.screen.blit(footer, (ANCHO // 2 - footer.get_width() // 2, ALTO - 40))
    # Dibujo de parqueo
    def draw_parqueo(self, parqueo, x, y):
        panel_rect = pygame.Rect(x, y, 600, 400)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, AZUL, panel_rect, 3, border_radius=15)
        
        titulo = self.font_subtitulo.render(f"Parqueo {parqueo.id}", True, BLANCO)
        self.screen.blit(titulo, (x + 20, y + 20))
        
        espacios_disp = parqueo.espacios_disponibles()
        color_espacios = VERDE if espacios_disp > 0 else ROJO
        texto_espacios = self.font_titulo.render(f"{espacios_disp}/2", True, color_espacios)
        self.screen.blit(texto_espacios, (x + 250, y + 80))
        
        texto_label = self.font_pequeña.render("Espacios disponibles", True, GRIS_CLARO)
        self.screen.blit(texto_label, (x + 220, y + 140))
        
        for i, espacio in enumerate(parqueo.espacios):
            espacio_x = x + 80 + i * 200
            espacio_y = y + 200
            
            color_espacio = ROJO if espacio.ocupado else VERDE
            espacio_rect = pygame.Rect(espacio_x, espacio_y, 120, 80)
            pygame.draw.rect(self.screen, color_espacio, espacio_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLANCO, espacio_rect, 2, border_radius=8)
            
            estado = "OCUPADO" if espacio.ocupado else "LIBRE"
            texto_estado = self.font_pequeña.render(estado, True, BLANCO)
            texto_rect = texto_estado.get_rect(center=(espacio_x + 60, espacio_y + 30))
            self.screen.blit(texto_estado, texto_rect)
            
            led_color = AMARILLO if espacio.led_encendido else GRIS
            pygame.draw.circle(self.screen, led_color, (espacio_x + 60, espacio_y + 55), 12)
            pygame.draw.circle(self.screen, BLANCO, (espacio_x + 60, espacio_y + 55), 12, 2)
            
            texto_led = self.font_pequeña.render("LED", True, BLANCO)
            self.screen.blit(texto_led, (espacio_x + 45, espacio_y + 65))
        
        aguja_color = VERDE if parqueo.aguja_abierta else ROJO
        aguja_texto = "ABIERTA" if parqueo.aguja_abierta else "CERRADA"
        pygame.draw.rect(self.screen, aguja_color, (x + 220, y + 320, 160, 50), border_radius=8)
        pygame.draw.rect(self.screen, BLANCO, (x + 220, y + 320, 160, 50), 2, border_radius=8)
        texto_aguja = self.font_normal.render(f"Aguja: {aguja_texto}", True, BLANCO)
        self.screen.blit(texto_aguja, (x + 235, y + 333))
    # Dibujo de control
    def draw_control(self):
        titulo = self.font_titulo.render("Control de Parqueos", True, BLANCO)
        self.screen.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 25))
        
        self.draw_parqueo(self.parqueos[0], 100, 120)
        self.draw_parqueo(self.parqueos[1], 750, 120)
        
        for btn in self.botones_control:
            btn.draw(self.screen, self.font_pequeña)
        
        instruccion = self.font_pequeña.render(
            "Controla los LEDs, agujas y espacios de forma remota",
            True, GRIS_CLARO
        )
        self.screen.blit(instruccion, (ANCHO // 2 - instruccion.get_width() // 2, 550))
        
        self.btn_config_rapida.draw(self.screen, self.font_normal)
        self.draw_monitor_comunicacion()
        self.draw_historial_comandos()
        # Dibujo de estadísticas
    def draw_estadisticas(self):
        panel_rect = pygame.Rect(100, 120, 1200, 700)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, MORADO, panel_rect, 3, border_radius=15)
        
        titulo = self.font_titulo.render("Estadísticas del Sistema", True, BLANCO)
        self.screen.blit(titulo, (120, 140))
        
        y_offset = 250
        
        for i, parqueo in enumerate(self.parqueos):
            x_base = 150 + i * 550
            
            subtitulo = self.font_subtitulo.render(f"Parqueo {parqueo.id}", True, AZUL)
            self.screen.blit(subtitulo, (x_base, y_offset))
            
            texto = self.font_normal.render(
                f"Vehículos totales: {parqueo.vehiculos_totales}",
                True, BLANCO
            )
            self.screen.blit(texto, (x_base, y_offset + 50))
            
            promedio_min = parqueo.promedio_estancia() / 60
            texto = self.font_normal.render(
                f"Promedio estancia: {promedio_min:.1f} min",
                True, BLANCO
            )
            self.screen.blit(texto, (x_base, y_offset + 90))
            
            ganancias_dolares = parqueo.ganancias_colones / self.config['tipo_cambio']
            texto = self.font_normal.render(
                f"Ganancias: ₡{parqueo.ganancias_colones:,.0f}",
                True, VERDE
            )
            self.screen.blit(texto, (x_base, y_offset + 130))
            texto = self.font_normal.render(
                f"            ${ganancias_dolares:,.2f}",
                True, VERDE
            )
            self.screen.blit(texto, (x_base, y_offset + 160))
        
        y_offset = 550
        subtitulo = self.font_subtitulo.render("Total del Sistema", True, NARANJA)
        self.screen.blit(subtitulo, (150, y_offset))
        
        total_vehiculos = sum(p.vehiculos_totales for p in self.parqueos)
        total_ganancias = sum(p.ganancias_colones for p in self.parqueos)
        total_ganancias_usd = total_ganancias / self.config['tipo_cambio']
        promedio_global = sum(p.promedio_estancia() for p in self.parqueos) / 2 / 60
        
        texto = self.font_normal.render(
            f"Vehículos totales: {total_vehiculos}",
            True, BLANCO
        )
        self.screen.blit(texto, (150, y_offset + 50))
        
        texto = self.font_normal.render(
            f"Promedio estancia: {promedio_global:.1f} min",
            True, BLANCO
        )
        self.screen.blit(texto, (150, y_offset + 90))
        
        texto = self.font_normal.render(
            f"Ganancias totales: ₡{total_ganancias:,.0f} / ${total_ganancias_usd:,.2f}",
            True, VERDE
        )
        self.screen.blit(texto, (150, y_offset + 130))
        
        texto = self.font_pequeña.render(
            f"Tipo de cambio: ₡{self.config['tipo_cambio']:.2f} / $1",
            True, GRIS_CLARO
        )
        self.screen.blit(texto, (150, y_offset + 180))
        
        self.btn_actualizar_tc.draw(self.screen, self.font_normal)
        # Dibujo de configuración
    def draw_configuracion(self):
        panel_rect = pygame.Rect(200, 120, 1000, 700)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, NARANJA, panel_rect, 3, border_radius=15)
        
        titulo = self.font_titulo.render("Configuración", True, BLANCO)
        self.screen.blit(titulo, (220, 140))
        
        y_pos = 230
        x_label = 250
        x_value = 650
        line_height = 60
        
        configs = [
            ("Tarifa (₡/10seg):", f"₡{self.config['tarifa_por_10seg']}"),
            ("Tipo de cambio:", f"₡{self.config['tipo_cambio']:.2f}"),
            ("IP Parqueo 1:", self.config['ip_parqueo1']),
            ("IP Parqueo 2:", self.config['ip_parqueo2']),
            ("Puerto:", str(self.config['puerto'])),
            ("Auto-refresh:", "Activado" if self.config['auto_refresh'] else "Desactivado")
        ]
        
        for i, (label, value) in enumerate(configs):
            texto_label = self.font_normal.render(label, True, GRIS_CLARO)
            self.screen.blit(texto_label, (x_label, y_pos + i * line_height))
            
            texto_value = self.font_normal.render(value, True, BLANCO)
            self.screen.blit(texto_value, (x_value, y_pos + i * line_height))
        
        info_y = y_pos + len(configs) * line_height + 40
        info_text = [
            "Las configuraciones se pueden modificar desde aquí.",
            "Los cambios se aplicarán en tiempo real al sistema.",
            "Asegúrate de que las IPs sean correctas para la comunicación."
        ]
        
        for i, text in enumerate(info_text):
            texto = self.font_pequeña.render(text, True, GRIS_CLARO)
            self.screen.blit(texto, (x_label, info_y + i * 30))
        # Dibujo de about
    def draw_about(self):
        panel_rect = pygame.Rect(200, 120, 1000, 700)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, MORADO, panel_rect, 3, border_radius=15)
        
        titulo = self.font_titulo.render("Acerca de CEstaciona", True, BLANCO)
        self.screen.blit(titulo, (220, 140))
        
        y_pos = 250
        x_pos = 250
        
        info = [
            ("Proyecto:", "CEstaciona - Parqueo Inteligente"),
            ("Curso:", "CE-1104 Fundamentos de Sistemas Computacionales"),
            ("Institución:", "Tecnológico de Costa Rica"),
            ("Escuela:", "Ingeniería en Computadores"),
            ("Profesor:", "Luis Barboza"),
            ("Semestre:", "II Semestre 2025"),
            ("", ""),
            ("Descripción:", "Sistema inteligente de control y administración"),
            ("", "de parqueos con sensores y botones."),
            ("", ""),
            ("Componentes:", "• Raspberry Pi Pico W"),
            ("", "• Display 7 segmentos"),
            ("", "• Fotoresistencias y LEDs"),
            ("", "• Servomotores"),
            ("", "• Botones de control"),
        ]
        
        for i, (label, value) in enumerate(info):
            if label:
                texto_label = self.font_normal.render(label, True, CYAN)
                self.screen.blit(texto_label, (x_pos, y_pos + i * 35))
            
            texto_value = self.font_normal.render(value, True, BLANCO)
            offset_x = 200 if label else 0
            self.screen.blit(texto_value, (x_pos + offset_x, y_pos + i * 35))
        
        pygame.draw.circle(self.screen, AZUL, (ANCHO // 2, 700), 60, 5)
        pygame.draw.circle(self.screen, VERDE, (ANCHO // 2 - 30, 700), 20)
        pygame.draw.circle(self.screen, ROJO, (ANCHO // 2 + 30, 700), 20)

    # ========================================================================
    # INTEGRACIÓN CON HARDWARE (BOTONES FÍSICOS)
    # ========================================================================
    
    def leer_hardware_raspberry(self):
        """Lee el estado de los botones físicos de las Raspberry Pi Pico"""
        if not self.comunicadores_activos or not self.gestor_comunicaciones:
            return
        
        # Parqueo 1
        com1 = self.gestor_comunicaciones.get_comunicador(0)
        if com1 and com1.activo:
            estado1 = com1.obtener_estado()
            
            if estado1:
                btn1 = estado1.get("btn1", 0)
                btn2 = estado1.get("btn2", 0)
                
                # BOTÓN 1 = OCUPAR ESPACIO + ABRIR BARRERA
                if btn1 == 1:
                    self.ocupar_espacio(0, 0)
                    self.toggle_aguja(0)
                    com1.enviar_comando("mover_servo", angulo=90)
                    com1.enviar_comando("toggle_led", index=0)
                
                # BOTÓN 2 = LIBERAR ESPACIO + CERRAR BARRERA
                if btn2 == 1:
                    self.liberar_espacio(0, 0)
                    self.toggle_aguja(0)
                    com1.enviar_comando("mover_servo", angulo=0)
                    com1.enviar_comando("toggle_led", index=1)
                
                # Actualizar LEDs según estado del espacio
                espacio = self.parqueos[0].espacios[0]
                if espacio.ocupado:
                    com1.enviar_comando("set_led", index=0, valor=1)  # Rojo ON
                    com1.enviar_comando("set_led", index=1, valor=0)  # Verde OFF
                else:
                    com1.enviar_comando("set_led", index=0, valor=0)  # Rojo OFF
                    com1.enviar_comando("set_led", index=1, valor=1)  # Verde ON
        
        # Parqueo 2
        com2 = self.gestor_comunicaciones.get_comunicador(1)
        if com2 and com2.activo:
            estado2 = com2.obtener_estado()
            
            if estado2:
                btn1 = estado2.get("btn1", 0)
                btn2 = estado2.get("btn2", 0)
                
                if btn1 == 1:
                    self.ocupar_espacio(1, 0)
                    com2.enviar_comando("mover_servo", angulo=90)
                
                if btn2 == 1:
                    self.liberar_espacio(1, 0)
                    com2.enviar_comando("mover_servo", angulo=0)
    
    # ========================================================================
    # LOOP PRINCIPAL
    # ========================================================================
    def run(self):
        """Loop principal de la aplicación"""
        while self.running:
            # Leer hardware de las Raspberry Pi
            self.leer_hardware_raspberry()
            
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                if self.estado == 0:  # Menú principal
                    for btn in self.botones_menu:
                        btn.handle_event(event, mouse_pos)
                
                elif self.estado == 1:  # Control
                    self.btn_volver.handle_event(event, mouse_pos)
                    self.btn_config_rapida.handle_event(event, mouse_pos)
                    for btn in self.botones_control:
                        btn.handle_event(event, mouse_pos)
                
                elif self.estado == 2:  # Estadísticas
                    self.btn_volver.handle_event(event, mouse_pos)
                    self.btn_actualizar_tc.handle_event(event, mouse_pos)
                
                elif self.estado == 3:  # Configuración
                    self.btn_volver.handle_event(event, mouse_pos)
                
                elif self.estado == 4:  # About
                    self.btn_volver.handle_event(event, mouse_pos)
            
            # Actualizar y dibujar fondo GIF animado
            self.actualizar_fondo_gif()
            self.dibujar_fondo_gif()
            
            # Dibujar según el estado
            if self.estado == 0:
                self.draw_menu_principal()
            
            elif self.estado == 1:
                self.draw_control()
                self.btn_volver.draw(self.screen, self.font_normal)
            
            elif self.estado == 2:
                self.draw_estadisticas()
                self.btn_volver.draw(self.screen, self.font_normal)
            
            elif self.estado == 3:
                self.draw_configuracion()
                self.btn_volver.draw(self.screen, self.font_normal)
            
            elif self.estado == 4:
                self.draw_about()
                self.btn_volver.draw(self.screen, self.font_normal)
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Cerrar conexiones
        if self.gestor_comunicaciones:
            self.gestor_comunicaciones.desactivar_todos()
        
        pygame.quit()
        return 
# ============================================================================
# EJECUTAR APLICACIÓN
# ============================================================================
if __name__ == "__main__":
    app = AplicacionParqueo()
    app.run()