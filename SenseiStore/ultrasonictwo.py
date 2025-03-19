from gpiozero import DistanceSensor
ultrasonic = DistanceSensor(echo=24, trigger=23)

while True:
    print(ultrasonic.distance)
