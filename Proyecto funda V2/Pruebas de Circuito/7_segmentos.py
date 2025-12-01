from machine import Pin
import time

# -------------------------------
# PINES DE SEGMENTOS
# -------------------------------
segment_pins = [
    Pin(9, Pin.OUT),   # a
    Pin(10, Pin.OUT),  # b
    Pin(11, Pin.OUT),  # c
    Pin(12, Pin.OUT),  # d
    Pin(19, Pin.OUT),  # e
    Pin(20, Pin.OUT),  # f
    Pin(21, Pin.OUT)   # g
]

# ---------- VERSIÓN 1 ----------
# En muchos montajes 1 = ENCENDIDO y 0 = APAGADO.
# Primero probamos así:

def encender_todos():
    for pin in segment_pins:
        pin.value(1)   # prueba así primero

def apagar_todos():
    for pin in segment_pins:
        pin.value(0)

try:
    while True:
        print("Encendiendo TODOS los segmentos...")
        encender_todos()
        time.sleep(3)

        print("Apagando TODOS los segmentos...")
        apagar_todos()
        time.sleep(3)

except KeyboardInterrupt:
    apagar_todos()
    print("Finalizado")
