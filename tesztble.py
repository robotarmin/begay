import time
from machine import Pin, UART

# Bluetooth (UART0) inicializalasa a laborutmutato szerint
# GP16 = TX0, GP17 = RX0
uart = UART(0, 9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))

print("Bluetooth modul inicializalasa...")
time.sleep(5) # 5 masodperc varakozas a stabil kapcsolathoz
print("Rendszer kesz! Varom a parancsot...")

while True:
    # Ellenorizzuk, erkezett-e adat
    if uart.any() > 0:
        try:
            # Beolvassuk a nyers adatot
            dat = uart.read()
            # Kiirjuk a konzolra, hogy lassuk a VS Code-ban
            print("Erkezett adat:", dat)
        except Exception as e:
            print("Hiba az olvasas soran:", e)
    
    time.sleep(0.1)