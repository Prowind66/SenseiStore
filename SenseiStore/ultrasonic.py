import RPi.GPIO as GPIO
import time

# Define GPIO pins based on your wiring
TRIG = 23  # GPIO 23 (Pin 16)
ECHO = 24  # GPIO 24 (Pin 18)

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Prevent floating values

def measure_distance():
    # Reset Echo pin before measurement
    GPIO.setup(ECHO, GPIO.OUT)
    GPIO.output(ECHO, False)
    time.sleep(0.1)
    GPIO.setup(ECHO, GPIO.IN)

    # Send a short pulse to trigger the sensor
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)

    # Wait for Echo to go HIGH (Start of signal)
    timeout_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if time.time() - timeout_start > 0.02:  # Timeout after 20ms
            return "Timeout waiting for Echo HIGH"

    # Wait for Echo to go LOW (End of signal)
    timeout_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time() 
        if time.time() - timeout_start > 0.02:  # Timeout after 20ms
            return "Timeout waiting for Echo LOW"
    
     # Calculate distance
    pulse_duration = pulse_end - pulse_start
    distance = (pulse_duration * 34300) / 2  # Speed of sound = 34300 cm/s

    return round(distance, 2)

try:
    while True:
        distance = measure_distance()
        print(f"Distance: {distance} cm")
        time.sleep(1)

except KeyboardInterrupt:
    GPIO.cleanup()

if __name__ == "__main__":
    measure_distance()
