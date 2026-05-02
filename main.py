import time
from machine import Pin, I2C, UART
from pico_car import SSD1306_I2C, pico_car, ultrasonic

# ═══════════════════════════════════════════════
#  KONSTANSOK
# ═══════════════════════════════════════════════

UART_BAUD   = 9600
UART_TX_PIN = 16
UART_RX_PIN = 17
I2C_SCL_PIN = 15
I2C_SDA_PIN = 14

BASE_SPEED  = 150
DRIVE_TIME  = 0.5   # mp – egyenes
TURN_TIME   = 0.18  # mp – kanyar
STEP_PAUSE  = 0.2   # mp – lépések között
OBSTACLE_CM = 5    # cm – megállási távolság
OFFSET_STEP = 5     # trim lépésköz

BT_NOISE = {"+CONNECTED", "+DISCONNECT", "+READY", "READY"}

# ═══════════════════════════════════════════════
#  HARDVER
# ═══════════════════════════════════════════════

uart  = UART(0, UART_BAUD, bits=8, parity=None, stop=1,
             tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
i2c   = I2C(1, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=100_000)
oled  = SSD1306_I2C(128, 32, i2c)
motor = pico_car()
sonar = ultrasonic()

# ═══════════════════════════════════════════════
#  ÁLLAPOT
# ═══════════════════════════════════════════════

sequence = []
offset   = 0

# ═══════════════════════════════════════════════
#  KIJELZŐ
# ═══════════════════════════════════════════════

def update_oled(raw_msg=""):
    seq_preview = "".join(sequence)[-12:]
    oled.fill(0)
    oled.text("S:" + seq_preview,     0,  0)
    oled.text("trim: " + str(offset), 0, 11)
    if raw_msg:
        oled.text(">" + raw_msg[:14], 0, 24)
    oled.show()

def show_obstacle():
    oled.fill(0)
    oled.text("!!!!!!!!!!", 20,  0)
    oled.text("AKADALY!",   32, 12)
    oled.text("!!!!!!!!!!", 20, 24)
    oled.show()

# ═══════════════════════════════════════════════
#  MOZGÁS
# ═══════════════════════════════════════════════

def execute_sequence():
    if not sequence:
        return

    lv = max(0, min(255, BASE_SPEED - offset))
    rv = max(0, min(255, BASE_SPEED + offset))

    for step in sequence:
        if 0 < sonar.Distance() <= OBSTACLE_CM:
            motor.Car_Stop()
            show_obstacle()
            time.sleep(2)
            break

        if   step == 'F': motor.Car_Run(lv, rv);                   time.sleep(DRIVE_TIME)
        elif step == 'B': motor.Car_Back(lv, rv);                  time.sleep(DRIVE_TIME)
        elif step == 'L': motor.Car_Left(BASE_SPEED, BASE_SPEED);  time.sleep(TURN_TIME)
        elif step == 'R': motor.Car_Right(BASE_SPEED, BASE_SPEED); time.sleep(TURN_TIME)

        motor.Car_Stop()
        time.sleep(STEP_PAUSE)

    update_oled()

# ═══════════════════════════════════════════════
#  PARANCSOK
# ═══════════════════════════════════════════════

def is_bt_noise(msg):
    return any(noise in msg for noise in BT_NOISE)

def handle_char(char):
    global offset
    if   char in 'FBLR': sequence.append(char)
    elif char == 'E':     execute_sequence()
    elif char == 'C':     sequence.clear()
    elif char == 'D':
        if sequence: sequence.pop()
    elif char == '+':     offset += OFFSET_STEP
    elif char == '-':     offset -= OFFSET_STEP

def process_uart():
    if not uart.any():
        return
    try:
        raw = uart.read().decode('utf-8').strip()
        msg = raw.upper()
        update_oled(raw_msg=raw)
        if is_bt_noise(msg):
            return
        for char in msg:
            handle_char(char)
        update_oled(raw_msg=raw)
    except Exception:
        pass

# ═══════════════════════════════════════════════
#  INDULÁS
# ═══════════════════════════════════════════════

update_oled()
while uart.any():
    uart.read()

# ═══════════════════════════════════════════════
#  FŐCIKLUS
# ═══════════════════════════════════════════════

while True:
    process_uart()
    time.sleep(0.1)