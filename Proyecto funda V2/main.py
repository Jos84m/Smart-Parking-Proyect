#------------------------------------------------------------------------------------------------------------------------------------------------------------
# Zona de importaciones
#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
import pygame
import sys
from datetime import datetime
from Variables import (
    ANCHO, ALTO, FPS,
    NEGRO, BLANCO, GRIS,GRIS_CLARO,
    VERDE, VERDE_HOVER, ROJO, ROJO_HOVER,
    AZUL, AZUL_HOVER, NARANJA, NARANJA_HOVER,
    MORADO, MORADO_HOVER, AMARILLO, CYAN, CYAN_HOVER, COLOR_TEXTO, hex_to_rgb
)
import requests
from PIL import Image, ImageSequence  
from Comunicacion import ComunicadorPico ,GestorComunicaciones

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Inicializar Pygame
pygame.init()

# Clase Button con efectos mejorados y sus características
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
        # Efecto de click
        offset = self.click_effect
        rect_actual = self.rect.inflate(-offset * 2, -offset * 2)

        # Color según hover
        color_actual = self.color_hover if self.hover else self.color

        # Sombra
        shadow_rect = rect_actual.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=10)
        
        # Botón principal
        pygame.draw.rect(screen, color_actual, rect_actual, border_radius=10)

        # Borde brillante si hay hover
        if self.hover:
            pygame.draw.rect(screen, hex_to_rgb(COLOR_TEXTO), rect_actual, 3, border_radius=10)
        else:
            pygame.draw.rect(screen, GRIS_CLARO, rect_actual, 2, border_radius=10)

        # Texto
        texto_render = font.render(self.texto, True, BLANCO)
        texto_rect = texto_render.get_rect(center=rect_actual.center)
        screen.blit(texto_render, texto_rect)

        # Reducir efecto de click
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

# Clase para representar un espacio de parqueo
class EspacioParqueo:
    def __init__(self, id_espacio):
        self.id = id_espacio
        self.ocupado = False
        self.hora_entrada = None
        self.led_encendido = True
        
    def ocupar(self):
        if not self.ocupado:
            self.ocupado = True
            self.hora_entrada = datetime.now()
            self.led_encendido = False
            return True
        return False
    
    def liberar(self):
        if self.ocupado:
            self.ocupado = False
            self.led_encendido = True
            tiempo_estancia = (datetime.now() - self.hora_entrada).total_seconds()
            self.hora_entrada = None
            return tiempo_estancia
        return 0
    
    def toggle_led(self):
        self.led_encendido = not self.led_encendido

# Clase para representar un parqueo
class Parqueo:
    def __init__(self, id_parqueo):
        self.id = id_parqueo
        self.espacios = [EspacioParqueo(i) for i in range(2)]
        self.aguja_abierta = False
        self.vehiculos_totales = 0
        self.tiempo_total_estancia = 0
        self.ganancias_colones = 0
        self.activo = False
        
    def espacios_disponibles(self):
        return sum(1 for e in self.espacios if not e.ocupado)
    
    def toggle_aguja(self):
        self.aguja_abierta = not self.aguja_abierta
    
    def registrar_salida(self, tiempo_estancia):
        self.vehiculos_totales += 1
        self.tiempo_total_estancia += tiempo_estancia
        # 1000 colones por cada 10 segundos
        costo = (tiempo_estancia / 10) * 1000
        self.ganancias_colones += costo
        return costo
    
    def promedio_estancia(self):
        if self.vehiculos_totales > 0:
            return self.tiempo_total_estancia / self.vehiculos_totales
        return 0

# Aplicación principal
class AplicacionParqueo:
    def __init__(self):
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("CEstaciona - Sistema de Parqueo Inteligente")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Fuentes
        self.font_titulo = pygame.font.Font(None, 64)
        self.font_subtitulo = pygame.font.Font(None, 40)
        self.font_normal = pygame.font.Font(None, 28)
        self.font_pequeña = pygame.font.Font(None, 22)
        
        # Parqueos
        self.parqueos = [Parqueo(1), Parqueo(2)]
        
        # Estado de la aplicación
        self.estado = 0
        
        # Configuración
        self.config = {
            'tarifa_por_10seg': 1000,
            'tipo_cambio': 520.0,
            'ip_parqueo1': '192.168.1.119',
            'ip_parqueo2': '192.168.1.101',
            'puerto': 8080,
            'auto_refresh': True
        }
        
        # Crear botones
        self.crear_botones()
        
        # Cargar GIF de fondo
        self.cargar_fondo_gif("fondo2.gif")

    def cargar_fondo_gif(self, ruta_gif):
        """Carga y procesa el GIF para usarlo como fondo"""
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
            print(f"✓ GIF cargado exitosamente: {len(self.gif_frames)} frames")
        except Exception as e:
            print(f"⚠ Error al cargar GIF: {e}")
            print("  Se usará fondo por defecto")
            self.gif_cargado = False

    def actualizar_fondo_gif(self):
        """Actualiza el frame del GIF según el tiempo"""
        if not self.gif_cargado:
            return
        
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.ultimo_frame_tiempo > self.gif_delay:
            self.frame_actual = (self.frame_actual + 1) % len(self.gif_frames)
            self.ultimo_frame_tiempo = tiempo_actual

    def dibujar_fondo_gif(self):
        """Dibuja el frame actual del GIF como fondo"""
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

    def crear_botones(self):
        # ======================================================================
        # BOTONES DEL MENÚ PRINCIPAL
        # ======================================================================
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
        
        # ======================================================================
        # BOTONES COMUNES
        # ======================================================================
        self.btn_volver = Button(
            50, 20, 150, 50, "← VOLVER", GRIS, GRIS_CLARO, 
            lambda: self.cambiar_estado(0)
        )
        
        self.btn_config_rapida = Button(
            ANCHO - 200, 20, 150, 50, "⚙ CONFIG", 
            NARANJA, NARANJA_HOVER, lambda: self.cambiar_estado(3)
        )
        
        # ======================================================================
        # BOTONES DE CONTROL - PARQUEO 1 (IZQUIERDA)
        # ======================================================================
        p1_x_start = 50
        p1_y_start = 580
        btn_w = 110
        btn_h = 45
        spacing_x = 125
        spacing_y = 55
        
        # ESPACIO 1 - Parqueo 1
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
        
        # ESPACIO 2 - Parqueo 1
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
        
        # AGUJA - Parqueo 1
        self.btn_aguja1 = Button(
            p1_x_start + spacing_x * 3, p1_y_start + spacing_y // 2,
            btn_w, btn_h, "Aguja", NARANJA, NARANJA_HOVER,
            lambda: self.toggle_aguja(0)
        )
        
        # ======================================================================
        # BOTONES DE CONTROL - PARQUEO 2 (DERECHA)
        # ======================================================================
        p2_x_start = 750
        p2_y_start = 580
        
        # ESPACIO 1 - Parqueo 2
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
        
        # ESPACIO 2 - Parqueo 2
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
        
        # AGUJA - Parqueo 2
        self.btn_aguja2 = Button(
            p2_x_start + spacing_x * 3, p2_y_start + spacing_y // 2,
            btn_w, btn_h, "Aguja", NARANJA, NARANJA_HOVER,
            lambda: self.toggle_aguja(1)
        )
        
        # ======================================================================
        # BOTÓN ACTUALIZAR TIPO DE CAMBIO
        # ======================================================================
        self.btn_actualizar_tc = Button(
            ANCHO - 300, ALTO - 100, 250, 50,
            "Actualizar Tipo Cambio", CYAN, CYAN_HOVER,
            self.actualizar_tipo_cambio
        )
        
        # ======================================================================
        # AGRUPAR BOTONES
        # ======================================================================
        self.botones_menu = [
            self.btn_menu_iniciar, 
            self.btn_menu_estadisticas,
            self.btn_menu_config, 
            self.btn_menu_about, 
            self.btn_salir
        ]
        
        self.botones_control = [
            # Parqueo 1
            self.btn_led1_esp1, self.btn_ocupar1_esp1, self.btn_liberar1_esp1,
            self.btn_led1_esp2, self.btn_ocupar1_esp2, self.btn_liberar1_esp2,
            self.btn_aguja1,
            # Parqueo 2
            self.btn_led2_esp1, self.btn_ocupar2_esp1, self.btn_liberar2_esp1,
            self.btn_led2_esp2, self.btn_ocupar2_esp2, self.btn_liberar2_esp2,
            self.btn_aguja2
        ]
    
    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado

    def quit(self):
        self.running = False
    
    def toggle_led(self, parqueo_id, espacio_id):
        self.parqueos[parqueo_id].espacios[espacio_id].toggle_led()
    
    def toggle_aguja(self, parqueo_id):
        self.parqueos[parqueo_id].toggle_aguja()
    
    def ocupar_espacio(self, parqueo_id, espacio_id):
        self.parqueos[parqueo_id].espacios[espacio_id].ocupar()
    
    def liberar_espacio(self, parqueo_id, espacio_id):
        tiempo = self.parqueos[parqueo_id].espacios[espacio_id].liberar()
        if tiempo > 0:
            self.parqueos[parqueo_id].registrar_salida(tiempo)
    
    def actualizar_tipo_cambio(self):
        try:
            resp = requests.get('https://api.exchangerate.host/latest?base=USD&symbols=CRC', timeout=6)
            if resp.status_code == 200:
                j = resp.json()
                if 'rates' in j and 'CRC' in j['rates']:
                    rate = float(j['rates']['CRC'])
                    self.config['tipo_cambio'] = rate
                    print(f"Tipo de cambio actualizado: ₡{rate}")
                    return
        except Exception:
            pass

        try:
            response = requests.get('https://api.hacienda.go.cr/indicadores/tc/dolar', timeout=6)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    if 'venta' in data:
                        self.config['tipo_cambio'] = float(data['venta'])
                        print(f"Tipo de cambio actualizado: ₡{self.config['tipo_cambio']}")
                        return
        except Exception as e:
            print(f"Error al actualizar tipo de cambio: {e}")

        print(f"No se pudo actualizar, usando: ₡{self.config['tipo_cambio']}")
    
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
    
    def draw_about(self):
        panel_rect = pygame.Rect(200, 120, 1000, 700)
        pygame.draw.rect(self.screen, (40, 40, 50), panel_rect, border_radius=15)
        pygame.draw.rect(self.screen, MORADO, panel_rect, 3, border_radius=15)
        
        titulo = self.font_titulo.render("Acerca de CEstaciona", True, BLANCO)
        self.screen.blit(titulo, (220, 140))
        
        y_pos = 250
        x_pos = 250
        
        info = [
            ("Proyecto:", "CEstaciona - Prototipo de Parqueo Inteligente"),
            ("Curso:", "CE-1104 Fundamentos de Sistemas Computacionales"),
            ("Institución:", "Tecnológico de Costa Rica"),
            ("Escuela:", "Ingeniería en Computadores"),
            ("Profesor:", "Luis Barboza"),
            ("Semestre:", "II Semestre 2025"),
            ("", ""),
            ("Descripción:", "Sistema inteligente de control y administración"),
            ("", "de parqueos con sensores y actuadores."),
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
    
    def run(self):
        """Loop principal de la aplicación"""
        while self.running:
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
        
        pygame.quit()
        sys.exit()

# Ejecutar aplicación
if __name__ == "__main__":
    app = AplicacionParqueo()
    app.run()