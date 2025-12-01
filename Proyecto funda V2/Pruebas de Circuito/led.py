from machine import Pin, PWM
import time

# Pines de cada color (cambia los números a los que estés usando)
red = PWM(Pin(13))
green = PWM(Pin(14))
blue = PWM(Pin(15))

# Frecuencia para LED RGB
red.freq(1000)
green.freq(1000)
blue.freq(1000)

# Función para colocar un color usando RGB (0 = apagado, 255 = máximo)
def set_color(r, g, b):
    red.duty_u16(int(r * 257))
    green.duty_u16(int(g * 257))
    blue.duty_u16(int(b * 257))

# CICLO DE COLORES
while True:
    set_color(255, 0, 0)   # Rojo
    time.sleep(1)

    set_color(0, 255, 0)   # Verde
    time.sleep(1)

    set_color(0, 0, 255)   # Azul
    time.sleep(1)

    set_color(255, 255, 0) # Amarillo
    time.sleep(1)

    set_color(0, 255, 255) # Cyan
    time.sleep(1)

    set_color(255, 0, 255) # Magenta
    time.sleep(1)

    set_color(255, 255, 255) # Blanco
    time.sleep(1)

    set_color(0, 0, 0) # Apagado
    time.sleep(1)
