#!/usr/bin/env python3
"""
Command Listener for Raspberry Pi
Listens to Adafruit IO MQTT feeds for control commands from Flask web app
"""
import json
import os
import sys
import time
import paho.mqtt.client as mqtt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE / "config"

# Load Adafruit IO config
def load_config():
    try:
        with open(CONFIG_DIR / "adafruit.json") as f:
            cfg = json.load(f)
            if "adafruit" in cfg:
                return cfg["adafruit"]
            return cfg
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

config = load_config()
if not config:
    print("Failed to load configuration")
    sys.exit(1)

AIO_USERNAME = config.get("username")
AIO_KEY = config.get("key")
AIO_FEEDS = config.get("feeds", {})

# Control feed names (add these to your Adafruit IO feeds)
CONTROL_FEEDS = {
    "motor_control": "motor-control",
    "led_control": "led-control",
    "buzzer_control": "buzzer-control",
    "line_tracking": "line-tracking",
    "obstacle_avoidance": "obstacle-avoidance"
}

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print("Connected to Adafruit IO")
        # Subscribe to all control feeds
        for key, feed_name in CONTROL_FEEDS.items():
            topic = f"{AIO_USERNAME}/feeds/{feed_name}"
            client.subscribe(topic)
            print(f"Subscribed to {topic}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when message is received"""
    try:
        feed_name = msg.topic.split('/')[-1]
        value = msg.payload.decode('utf-8')
        
        print(f"Received command: {feed_name} = {value}")
        
        # Handle motor control
        if feed_name == CONTROL_FEEDS["motor_control"]:
            handle_motor_control(value)
        
        # Handle LED control
        elif feed_name == CONTROL_FEEDS["led_control"]:
            handle_led_control(value)
        
        # Handle buzzer control
        elif feed_name == CONTROL_FEEDS["buzzer_control"]:
            handle_buzzer_control(value)
        
        # Handle line tracking
        elif feed_name == CONTROL_FEEDS["line_tracking"]:
            handle_line_tracking(value)
        
        # Handle obstacle avoidance
        elif feed_name == CONTROL_FEEDS["obstacle_avoidance"]:
            handle_obstacle_avoidance(value)
    
    except Exception as e:
        print(f"Error processing message: {e}")

def handle_motor_control(action):
    """Handle motor control commands"""
    try:
        from hardware.motor import Ordinary_Car
        car = Ordinary_Car()
        
        speed = 800
        turn_power = 1200
        drive_sign = -1  # Match car_tui.py behavior
        
        if action == "forward":
            car.set_motor_model(int(speed)*drive_sign, int(speed)*drive_sign, int(speed)*drive_sign, int(speed)*drive_sign)
        elif action == "backward":
            car.set_motor_model(-int(speed)*drive_sign, -int(speed)*drive_sign, -int(speed)*drive_sign, -int(speed)*drive_sign)
        elif action == "left":
            car.set_motor_model(-int(turn_power)*drive_sign, -int(turn_power)*drive_sign, +int(turn_power)*drive_sign, +int(turn_power)*drive_sign)
        elif action == "right":
            car.set_motor_model(+int(turn_power)*drive_sign, +int(turn_power)*drive_sign, -int(turn_power)*drive_sign, -int(turn_power)*drive_sign)
        elif action == "stop":
            car.set_motor_model(0, 0, 0, 0)
        
        print(f"Motor control: {action}")
    except Exception as e:
        print(f"Error controlling motor: {e}")

def handle_led_control(state):
    """Handle LED control commands"""
    try:
        # Use SPI LED driver directly (same as car_tui.py)
        from hardware.spi_ledpixel import Freenove_SPI_LedPixel
        led = Freenove_SPI_LedPixel(count=60, bright=120, sequence='GRB', bus=0, device=0)
        led.led_begin(bus=0, device=0)
        led.set_led_count(60)
        
        if state == "on":
            # Turn on LEDs (white, brightness 200)
            led.set_all_led_color(200, 200, 200)
        elif state == "off":
            # Turn off LEDs
            led.set_all_led_color(0, 0, 0)
        
        print(f"LED control: {state}")
    except Exception as e:
        print(f"Error controlling LED: {e}")

def handle_buzzer_control(state):
    """Handle buzzer control commands"""
    try:
        from hardware.buzzer import Buzzer
        buzzer = Buzzer()
        
        if state == "on":
            buzzer.set_state(1)
        elif state == "off":
            buzzer.set_state(0)
        
        print(f"Buzzer control: {state}")
    except Exception as e:
        print(f"Error controlling buzzer: {e}")

def handle_line_tracking(command):
    """Handle line tracking commands"""
    import subprocess
    BASE_DIR = Path(__file__).resolve().parent
    
    if command == "start":
        # Start line following script
        script = BASE_DIR / "line_follow.py"
        process = subprocess.Popen(
            ["python3", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Check if it started successfully
        time.sleep(0.5)
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"Line tracking failed to start: {stderr}")
        else:
            print("Line tracking started")
    elif command == "stop":
        # Stop line following (find and kill process)
        subprocess.run(["pkill", "-f", "line_follow.py"],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
        print("Line tracking stopped")

def handle_obstacle_avoidance(command):
    """Handle obstacle avoidance commands"""
    import subprocess
    import os
    BASE_DIR = Path(__file__).resolve().parent
    
    if command == "start":
        # Start obstacle navigator script
        # Don't hide errors so we can see what's wrong
        script = BASE_DIR / "obstacle_navigator.py"
        # Run in background but capture errors
        process = subprocess.Popen(
            ["python3", str(script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Check if it started successfully (wait a bit to see if it crashes immediately)
        time.sleep(0.5)
        if process.poll() is not None:
            # Process already exited (crashed)
            stdout, stderr = process.communicate()
            print(f"Obstacle avoidance failed to start: {stderr}")
        else:
            print("Obstacle avoidance started")
    elif command == "stop":
        # Stop obstacle navigator
        subprocess.run(["pkill", "-f", "obstacle_navigator.py"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        print("Obstacle avoidance stopped")

def main():
    """Main function"""
    client = mqtt.Client(client_id="robot_command_listener")
    client.username_pw_set(AIO_USERNAME, AIO_KEY)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect("io.adafruit.com", 1883, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

