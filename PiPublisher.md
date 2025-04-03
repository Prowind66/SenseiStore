# Hardware Publisher Setup Guide
This documents provides information about the Publisher Set Up

## Raspberry Pi 400 GPIO Pinout
<img src="/SenseiStore/static/images/pi400_connectivity_guide.jpg" height="600px" width="500px">

## Wiring Connections
| Signal     | Raspberry Pi Pin | Description |
|------------|------------------|-------------|
| VCC        | Pin 2 (5V)       | Power supply |
| TRIG       | Pin 16 (GPIO 23) | GPIO |
| ECHO       | Pin 18 (GPIO 24) | GPIO |
| GND        | Pin 6 (Ground)   | Ground |

## Hardware Diagram
```
                            Raspberry Pi 400  
                         +---------------------+
                         |                     |
+-------------+          |                     |
| Camera      +----------+ USB Port            |
| Module      |          |                     |
+-------------+          |                     |
                         |                     |
                         |                     |
+-------------+          |                     |
|  Raspberry  |          |                     |                       
|  Pi Power  +-----------+  USB C              |
|  Supply     |          |                     |
+-------------+          |                     |
                         |                     |
                         |                     |
                         |  Pin 2 (5V)         |
+-------------+          |                     |
|             +----------+  Pin 16 (GPIO 23    |
|             |          |                     |
|   HC-SR04   +----------+  Pin 18 (GPIO 24)   |
|  UltraSonic |          |                     |
|             +----------+  Pin 6 (Ground)     |
+-------------+          |                     |
                         +---------------------+
```
## Hardware Diagram Picture
<img src="/SenseiStore/static/images/publisher_connectivity_guide.jpeg" height="300px" width="100%">

## Setup Instructions
1. Clone The Repo To The Computer 
2. In Your Window Command Prompt scp -r SenseiStore pi@192.168.238.33:/home/pi
3. cd to the directory and pip install the packages from requirements.txt
4. python3 pub.py
Note: You Should Create An Virutal Environment To Manage These Packages

## 1. Clone The Repository
```
git clone https://github.com/your-username/SenseiStore.git
cd SenseiStore
```
## 2. Create a Python Virtual Environment (Recommended)
```
python3 -m venv venv
source venv/bin/activate  # For Linux/macOS
```

##  3. Install Publisher Requirements
```
pip install -r publisher_requirements.txt
```

## Run the publisher Script
```
cd SenseiStore
python3 pub.py
```

## Troubleshooting
| Issue     | Possible Cause | Solution |
|------------|------------------|-------------|
| Ultrasonic sensor not detecting presence        | Loose or incorrect wiring to TRIG/ECHO pins       | Double-check connections: Refer To The Wiring Connections Section |
| Camera not detected or showing black screen       | USB port issue or permission error | Run lsusb to verify detection , sudo apt install fswebcam . 
| Script pub.py throws ModuleNotFoundError       | Virtual environment not activated or packages not installed | Activate the virtual environment: source venv/bin/activate or Install requirements: pip install -r publisher_requirements.txt|
| Port busy" or "Resource unavailable" error        | Camera or GPIO resource not released properly   | Reboot the Raspberry Pi and Make sure no other scripts are using the camera or GPIOs  |
