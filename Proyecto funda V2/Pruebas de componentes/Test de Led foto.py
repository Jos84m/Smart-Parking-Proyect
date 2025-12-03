from machine import ADC, Pin
import time

# --- 2 Fotoresistencias ---
ldr1 = ADC(27)   # LDR1 en GP26 (ADC0)
ldr2 = ADC(26)   # LDR2 en GP27 (ADC1)

# --- LED RGB 1 ---
r1 = Pin(15, Pin.OUT)
g1 = Pin(16, Pin.OUT)
b1 = Pin(17, Pin.OUT)

# --- LED RGB 2 ---
r2 = Pin(13, Pin.OUT)
g2 = Pin(14, Pin.OUT)
b2 = Pin(15, Pin.OUT)

# Función para controlar LEDs RGB
def set_led(led, r, g, b):
    if led == 1:
        r1.value(r)
        g1.value(g)
        b1.value(b)
    elif led == 2:
        r2.value(r)
        g2.value(g)
        b2.value(b)

while True:
    # Leer valores analógicos (0 - 65535)
    luz1 = ldr1.read_u16()
    luz2 = ldr2.read_u16()

    print("LDR1:", luz1, "| LDR2:", luz2)

    # --- LED RGB 1 ---
    if luz1 > 20000:    # oscuro
        set_led(1, 1, 0, 0)   # rojo
    else:               # claro
        set_led(1, 0, 0, 1)   # azul

    # --- LED RGB 2 ---
    if luz2 < 20000:    # oscuro
        set_led(2, 1, 0, 0)   # rojo
    else:
        set_led(2, 0, 0, 1)   # azul

    time.sleep(0.1)

