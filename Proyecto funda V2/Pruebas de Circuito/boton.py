from machine import Pin
import time

# Configurar el botón en GP14 con resistencia pull-up
boton = Pin(3, Pin.IN, Pin.PULL_UP)

while True:
    if boton.value() == 1:  # 1 = NO presionado
        print("El botón NO está presionado")
    else:
        print("El botón está presionado")

    time.sleep(0.2)  # Pequeña pausa para no saturar el serial
