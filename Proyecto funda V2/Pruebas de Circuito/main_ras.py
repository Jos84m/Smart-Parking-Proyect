import network
import socket
import ujson
from machine import Pin, PWM, ADC
import time

# ----------------------
#  CONFIG WIFI
# ----------------------
SSID = "Vaglio Mora"
PASSWORD = "Vavvglio21#JH"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(0.2)

print("Conectado:", wlan.ifconfig())

# ----------------------
#  PINES
# ----------------------

# LEDs
leds = [
    Pin(13, Pin.OUT),
    Pin(14, Pin.OUT),
    Pin(15, Pin.OUT),
    Pin(16, Pin.OUT),
    Pin(17, Pin.OUT),
    Pin(18, Pin.OUT)
]

# Servos
servo = PWM(Pin(0))
servo.freq(50)

servo_btn = PWM(Pin(7))
servo_btn.freq(50)

def mover_servo(pwm, grados):
    duty = int((grados / 180) * 8000) + 1000
    pwm.duty_u16(duty)

# Fotoresistencias
ldr1 = ADC(27)
ldr2 = ADC(26)

# Botones
btn1 = Pin(3, Pin.IN, Pin.PULL_DOWN)
btn2 = Pin(4, Pin.IN, Pin.PULL_DOWN)

# Display 7 segmentos
segmentos = {
    "a": Pin(9, Pin.OUT),
    "b": Pin(10, Pin.OUT),
    "c": Pin(11, Pin.OUT),
    "d": Pin(12, Pin.OUT),
    "e": Pin(19, Pin.OUT),
    "f": Pin(20, Pin.OUT),
    "g": Pin(21, Pin.OUT)
}

numeros = {
    0: [1,1,1,1,1,1,0],
    1: [0,1,1,0,0,0,0],
    2: [1,1,0,1,1,0,1],
    3: [1,1,1,1,0,0,1],
    4: [0,1,1,0,0,1,1],
    5: [1,0,1,1,0,1,1],
    6: [1,0,1,1,1,1,1],
    7: [1,1,1,0,0,0,0],
    8: [1,1,1,1,1,1,1],
    9: [1,1,1,1,0,1,1]
}

def display_num(num):
    estados = numeros.get(num, [0]*7)
    for pin, estado in zip(segmentos.values(), estados):
        pin.value(estado)

# ----------------------
#  SERVIDOR
# ----------------------

def serve():
    addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(5)
    print("Servidor listo")

    while True:
        client, addr = s.accept()
        req = client.recv(1024).decode()

        # -------- ESTADO --------
        if "GET /estado" in req:
            estado = {
                "leds": [led.value() for led in leds],
                "ldr1": ldr1.read_u16(),
                "ldr2": ldr2.read_u16(),
                "btn1": btn1.value(),
                "btn2": btn2.value(),
            }

            client.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            client.send(ujson.dumps(estado))

        # -------- COMANDOS --------
        elif "POST /comando" in req:
            body = req.split("\r\n\r\n")[1]
            data = ujson.loads(body)

            accion = data.get("accion")

            if accion == "toggle_led":
                i = data.get("index", 0)
                leds[i].toggle()

            elif accion == "mover_servo":
                mover_servo(servo, data.get("angulo", 90))

            elif accion == "mover_servo_btn":
                mover_servo(servo_btn, data.get("angulo", 90))

            elif accion == "display":
                display_num(data.get("numero", 0))

            client.send("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            client.send('{"status":"ok"}')

        client.close()

serve()

