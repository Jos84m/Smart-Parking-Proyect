from machine import ADC, Pin
import time

# Configuración
ldr = ADC(Pin(27))        # LDR en GP27 (ADC1) — cambia si lo tienes en otro pin ADC
led = Pin(16, Pin.OUT)    # LED en GP15 — puedes cambiarlo

# Umbral de oscuridad
# Ajusta este valor según tu LDR y resistencia
UMBRAL = 2000   # entre 0 y 65535

while True:
    valor = ldr.read_u16()    # Lee la luz (0 oscurísimo, 65535 muy iluminado)
    print("Luz:", valor)

    if valor < UMBRAL:
        led.value(1)   # Encender LED si hay poca luz
    else:
        led.value(0)   # Apagar LED si hay mucha luz

    time.sleep(0.1)