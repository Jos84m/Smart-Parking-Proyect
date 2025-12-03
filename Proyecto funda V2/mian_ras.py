# main.py  -- MicroPython (Pico W)
# Requisitos: firmware MicroPython para RP2040 con network activo
# Subir a cada Pico W y configurar SSID/PASS abajo.

import network
import socket
import ujson as json
import time
from machine import Pin, ADC, PWM
from ubinascii import hexlify

# -----------------------
# CONFIG - ajusta pines
# -----------------------
SSID = "TU_SSID"
PASSWORD = "TU_PASS"

# Pines (ejemplos; cámbialos según tu conexión)
PIN_BTN1 = 14        # GPIO14 - botón 1
PIN_BTN2 = 15        # GPIO15 - botón 2
PIN_LDR = 26         # ADC0 - GP26 (ADC0)
PIN_LED_RED = 2      # GP2  - LED rojo (o primer LED)
PIN_LED_GREEN = 3    # GP3  - LED verde (o segundo LED)
PIN_SERVO = 16       # PWM servo - GP16
# 7-seg pins (a,b,c,d,e,f,g,dp) - ejemplo
SEG_PINS = [4, 5, 6, 7, 8, 9, 10]  

# -----------------------
# HARDWARE SETUP
# -----------------------
btn1 = Pin(PIN_BTN1, Pin.IN, Pin.PULL_DOWN)  # o PULL_UP si tu circuito lo pide
btn2 = Pin(PIN_BTN2, Pin.IN, Pin.PULL_DOWN)
ldr = ADC(PIN_LDR)

led_red = Pin(PIN_LED_RED, Pin.OUT)
led_green = Pin(PIN_LED_GREEN, Pin.OUT)

servo_pwm = PWM(Pin(PIN_SERVO))
servo_pwm.freq(50)  # 50Hz para servos

# Mapeo 7-seg (común ánodo/cátodo depende; este ejemplo es para COMÚN CATODO)
seg_pins = [Pin(p, Pin.OUT) for p in SEG_PINS]
# tabla números 0-9 (a,b,c,d,e,f,g) ; 1 = ON, 0 = OFF (ajusta si usas ánodo)
SEG_DIGITS = {
    0: (1,1,1,1,1,1,0),
    1: (0,1,1,0,0,0,0),
    2: (1,1,0,1,1,0,1),
    3: (1,1,1,1,0,0,1),
    4: (0,1,1,0,0,1,1),
    5: (1,0,1,1,0,1,1),
    6: (1,0,1,1,1,1,1),
    7: (1,1,1,0,0,0,0),
    8: (1,1,1,1,1,1,1),
    9: (1,1,1,1,0,1,1)
}

# Estado local del "parqueo" simplificado
estado = {
    "btn1": 0,
    "btn2": 0,
    "leds": [0, 1],   # [rojo, verde] por defecto
    "servo": 0,
    "display": 2
}

# -----------------------
# UTILIDADES
# -----------------------
def set_led(index, valor):
    # index 0 -> rojo, 1 -> verde
    if index == 0:
        led_red.value(1 if valor else 0)
        estado["leds"][0] = 1 if valor else 0
    elif index == 1:
        led_green.value(1 if valor else 0)
        estado["leds"][1] = 1 if valor else 0

def toggle_led(index, color=None):
    # color param es ignorado aquí, mantenido por compatibilidad
    new = 0 if estado["leds"][index] else 1
    set_led(index, new)
    return True

def mover_servo(angulo):
    # ángulo en grados 0-180 -> convertir a pulso
    # periodo = 20ms -> duty_u16 = pulse_ms/20ms * 65535
    # pulse 0 deg -> 0.5ms, 180deg -> 2.5ms (ajustar si tu servo difiere)
    pulse_ms = 0.5 + (angulo / 180.0) * 2.0  # 0.5..2.5 ms
    duty = int((pulse_ms / 20.0) * 65535)
    servo_pwm.duty_u16(duty)
    estado["servo"] = angulo
    return True

def leer_ldr_normalizado():
    # ADC.read_u16() returns 0..65535 in most builds; in some returns 0..65535 via read_u16
    try:
        val = ldr.read_u16()
    except AttributeError:
        val = ldr.read()  # fallback
    # normalizar 0..1023-like
    return int((val / 65535) * 1023)

def set_display_num(n):
    # Si n entre 0-9, muestra en el 7-seg. (Si tienes multiplex, ampliar).
    d = int(n) % 10
    pattern = SEG_DIGITS.get(d, SEG_DIGITS[0])
    for pin, val in zip(seg_pins, pattern):
        pin.value(val)
    estado["display"] = d
    return True

# -----------------------
# BOTON ANTI-REBOTE
# -----------------------
_last_btn1 = 0
_last_btn2 = 0
_last_time_btn1 = 0
_last_time_btn2 = 0
DEBOUNCE_MS = 150

def update_buttons():
    global _last_btn1, _last_btn2, _last_time_btn1, _last_time_btn2
    now = time.ticks_ms()
    v1 = btn1.value()
    v2 = btn2.value()
    # btn1
    if v1 != _last_btn1 and time.ticks_diff(now, _last_time_btn1) > DEBOUNCE_MS:
        _last_time_btn1 = now
        _last_btn1 = v1
        estado["btn1"] = 1 if v1 else 0
    # btn2
    if v2 != _last_btn2 and time.ticks_diff(now, _last_time_btn2) > DEBOUNCE_MS:
        _last_time_btn2 = now
        _last_btn2 = v2
        estado["btn2"] = 1 if v2 else 0

# -----------------------
# WIFI + HTTP SERVER
# -----------------------
def conectar_wifi(ssid, password, wait=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a WiFi...", ssid)
        wlan.connect(ssid, password)
        t0 = time.time()
        while not wlan.isconnected() and (time.time() - t0) < wait:
            time.sleep(0.5)
    if wlan.isconnected():
        print("Conectado, IP:", wlan.ifconfig()[0])
    else:
        print("No se pudo conectar a WiFi")
    return wlan

# manejador simple de requests
def handle_request(method, path, body_json):
    # rutas:
    # GET /estado -> devuelve estado JSON
    # POST /comando -> ejecuta comando {"accion": "...", ...}
    if method == "GET" and path == "/estado":
        # actualizar lectura LDR y botones antes de devolver
        update_buttons()
        estado["ldr"] = leer_ldr_normalizado()
        return (200, estado)
    if method == "POST" and path == "/comando":
        if not body_json:
            return (400, {"status": "error", "mensaje": "JSON faltante"})
        accion = body_json.get("accion", "")
        # mapear acciones esperadas por la interfaz
        try:
            if accion == "ocupar":
                espacio = int(body_json.get("espacio", 0))
                # Simula ocupación: apaga led verde, enciende rojo
                set_led(1, 0)
                set_led(0, 1)
                return (200, {"status": "ok", "mensaje": f"ocupado {espacio}"})
            if accion == "liberar":
                espacio = int(body_json.get("espacio", 0))
                set_led(0, 0)
                set_led(1, 1)
                return (200, {"status": "ok", "mensaje": f"liberado {espacio}"})
            if accion == "toggle_led":
                espacio = int(body_json.get("espacio", 0))
                color = body_json.get("color", "verde")
                # elegir index por espacio (ejemplo)
                toggle_led(espacio)
                return (200, {"status": "ok", "mensaje": "toggle_led"})
            if accion == "set_led":
                index = int(body_json.get("index", 0))
                valor = int(body_json.get("valor", 0))
                set_led(index, 1 if valor else 0)
                return (200, {"status": "ok", "mensaje": "set_led"})
            if accion in ("mover_servo", "mover_servo_boton"):
                ang = int(body_json.get("angulo", 0))
                mover_servo(ang)
                return (200, {"status": "ok", "mensaje": f"servo {ang}"})
            if accion == "toggle_aguja":
                # abre/cierra aguja -> vamos a mover servo 0/90
                nuevo = 90 if estado["servo"] == 0 else 0
                mover_servo(nuevo)
                return (200, {"status": "ok", "mensaje": "toggle_aguja", "servo": nuevo})
            if accion == "actualizar_display":
                numero = int(body_json.get("numero", 0))
                set_display_num(numero)
                return (200, {"status": "ok", "mensaje": "display actualizado"})
            # comandos custom
            return (400, {"status": "error", "mensaje": "accion desconocida"})
        except Exception as e:
            return (500, {"status": "error", "mensaje": str(e)})

    return (404, {"status": "error", "mensaje": "ruta no encontrada"})

def start_server(port=8080):
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Servidor HTTP en", addr)
    while True:
        cl, addr = s.accept()
        # timeout corto
        cl.settimeout(5)
        try:
            req = cl.recv(4096)
            if not req:
                cl.close()
                continue
            req_str = req.decode("utf-8")
            # parse minimal HTTP
            lines = req_str.split("\r\n")
            request_line = lines[0]
            parts = request_line.split(" ")
            if len(parts) < 2:
                cl.close()
                continue
            method = parts[0]
            path = parts[1].split("?")[0]
            # read body if any (simple)
            body = ""
            if "\r\n\r\n" in req_str:
                body = req_str.split("\r\n\r\n", 1)[1]
            body_json = None
            if body:
                try:
                    body_json = json.loads(body)
                except:
                    body_json = None
            # manejar ruta
            status, resp_obj = handle_request(method, path, body_json)
            resp = json.dumps(resp_obj)
            cl.send("HTTP/1.1 {} OK\r\n".format(status))
            cl.send("Content-Type: application/json\r\n")
            cl.send("Content-Length: {}\r\n".format(len(resp)))
            cl.send("Connection: close\r\n\r\n")
            cl.send(resp)
        except Exception as e:
            try:
                err = json.dumps({"status":"error","mensaje":str(e)})
                cl.send("HTTP/1.1 500 Internal Server Error\r\n")
                cl.send("Content-Type: application/json\r\n")
                cl.send("Content-Length: {}\r\n".format(len(err)))
                cl.send("\r\n")
                cl.send(err)
            except:
                pass
        finally:
            try:
                cl.close()
            except:
                pass

# -----------------------
# MAIN
# -----------------------
if __name__ == "__main__":
    wlan = conectar_wifi(SSID, PASSWORD, wait=10)
    # inicializar estado físico según defaults
    set_led(0, estado["leds"][0])
    set_led(1, estado["leds"][1])
    set_display_num(estado["display"])
    mover_servo(estado["servo"])
    # Ejecutar servidor (bloqueante)
    start_server(8080)
