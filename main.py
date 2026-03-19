import time
from machine import Pin, I2C, UART
from pico_car import SSD1306_I2C, pico_car, ir, ultrasonic

# --- INICIALIZÁLÁS ---
uart = UART(0, 9600, bits=8, parity=None, stop=1, tx=Pin(16), rx=Pin(17))
print("Bluetooth inicializalasa (5s)...")
time.sleep(5) 

i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=100000)
oled = SSD1306_I2C(128, 32, i2c)
motor = pico_car()
sonar = ultrasonic()

# Változók
sequence = []     
offset = 0        
base_speed = 150  

def update_oled(status_msg="parancsolj:)"):
    oled.fill(0)
    oled.text("Tanulo Robot", 16, 0)
    seq_str = "".join(sequence)[-10:]
    oled.text("Seq:" + seq_str + " T:" + str(offset), 0, 12)
    oled.text(status_msg, 0, 24)
    oled.show()

def execute_sequence():
    global sequence, offset, base_speed
    
    if not sequence:
        update_oled("Ures lista!")
        time.sleep(1)
        return

    update_oled("Futtatas...")
    
    left_v = max(0, min(255, base_speed - offset))
    right_v = max(0, min(255, base_speed + offset))

    for step in sequence:
        dist = sonar.Distance()
        if 0 < dist <= 15:
            motor.Car_Stop()
            update_oled("AKADALY! STOP")
            time.sleep(2)
            break
        
        if step == 'F':
            motor.Car_Run(left_v, right_v)
            time.sleep(0.5)
        elif step == 'B':
            motor.Car_Back(left_v, right_v)
            time.sleep(0.5)
        elif step == 'L':
            motor.Car_Left(150, 150)
            time.sleep(0.15) 
        elif step == 'R':
            motor.Car_Right(150, 150)
            time.sleep(0.15) 
        
        motor.Car_Stop()
        time.sleep(0.2)

    update_oled("Kesz!")
    time.sleep(1.5)

update_oled()
print("Rendszer kesz, varom a parancsokat!")

# Puffer ürítése induláskor
while uart.any() > 0:
    uart.read()

while True:
    changed = False
    
    if uart.any() > 0:
        try:
            raw_data = uart.read()
            msg = raw_data.decode('utf-8').strip().upper()
            
            # --- ÚJ: RENDSZERÜZENETEK KISZŰRÉSE ---
            # Ha az üzenet tartalmazza a CONN (Connected) vagy DISC (Disconnected) szót,
            # vagy +-al kezdődik de hosszabb 1 karakternél (pl. +AT), akkor eldobjuk!
            if "CONN" in msg or "DISC" in msg or (msg.startswith('+') and len(msg) > 1):
                print("Rendszeruzenet kiszurve:", msg)
                continue
            
            # Ha a szűrőn átjutott, akkor az az én parancsom
            for char in msg:
                if char in 'FBLR': 
                    sequence.append(char)
                    changed = True
                elif char == 'E':    
                    execute_sequence()
                    changed = True
                elif char == 'C':    
                    sequence = []
                    changed = True
                elif char == 'D':    
                    if sequence: sequence.pop()
                    changed = True
                elif char == '+':    
                    offset += 1
                    changed = True
                elif char == '-':    
                    offset -= 1
                    changed = True
        except:
            pass

    if changed:
        update_oled()
    
    time.sleep(0.1)