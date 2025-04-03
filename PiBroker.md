# Raspberry Pi 400 Broker 

**1. Install and Configure the MQTT Broker on a Raspberry Pi 400:**

   a. Update the Raspberry Pi's package list (optional):
   ```
   sudo apt update
   ```

   b. Install the Mosquitto MQTT broker:
   ```
   sudo apt install mosquitto
   ```

   c. Locate the Mosquitto Configuration File:
   - Use a text editor to open the `mosquitto.conf` file located in `/etc/mosquitto/` using the following command:
     ```
     sudo nano /etc/mosquitto/mosquitto.conf
     ```
   
   d. Edit the Mosquitto Configuration file:
   - Inside the `mosquitto.conf` file, you'll find various configuration options. Be careful when editing this file to avoid introducing errors.
   - Include the following into the configuration file to allow the brokker to listen to port 1883 and allow anonymous clients to connect and use the MQTT broker which means that clients can connect without providing a username and password:
     ```
     listener 1883
     allow_anonymous true    
     ```

   e. Start your mosquitto broker manually:
   ```
   sudo mosquitto -c /etc/mosquitto/mosquitto.conf 
   ```


**2. Enable Mosquitto Broker to run on boot**

   a. Start and enable Mosquitto to run on boot:
   ```
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

   b. Restarting Mosquitto Broker to apply the new configuration by using the following command:
   ```
   sudo systemctl restart mosquitto
   ```

   c. Verify that Mosquitto is running:
   ```
   systemctl status mosquitto
   ```

