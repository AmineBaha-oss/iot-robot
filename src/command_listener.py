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
        from motor import Ordinary_Car
        car = Ordinary_Car()
        
        speed = 800
        turn_power = 1200
        
        if action == "forward":
            car.set_motor_model(speed, speed, speed, speed)
        elif action == "backward":
            car.set_motor_model(-speed, -speed, -speed, -speed)
        elif action == "left":
            car.set_motor_model(-turn_power, -turn_power, turn_power, turn_power)
        elif action == "right":
            car.set_motor_model(turn_power, turn_power, -turn_power, -turn_power)
        elif action == "stop":
            car.set_motor_model(0, 0, 0, 0)
        
        print(f"Motor control: {action}")
    except Exception as e:
        print(f"Error controlling motor: {e}")

def handle_led_control(state):
    """Handle LED control commands"""
    try:
        from hardware.led import Led
        led = Led()
        
        if state == "on":
            # Turn on LEDs (white)
            for i in range(led.strip.get_led_count()):
                led.strip.set_led_rgb_data(i, [255, 255, 255])
            led.strip.show()
        elif state == "off":
            # Turn off LEDs
            led.strip.set_all_led_color(0, 0, 0)
            led.strip.show()
        
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
        subprocess.Popen(["python3", str(script)], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("Line tracking started")
    elif command == "stop":
        # Stop line following (find and kill process)
        subprocess.run(["pkill", "-f", "line_follow.py"])
        print("Line tracking stopped")

def handle_obstacle_avoidance(command):
    """Handle obstacle avoidance commands"""
    import subprocess
    BASE_DIR = Path(__file__).resolve().parent
    
    if command == "start":
        # Start obstacle navigator script
        script = BASE_DIR / "obstacle_navigator.py"
        subprocess.Popen(["python3", str(script)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        print("Obstacle avoidance started")
    elif command == "stop":
        # Stop obstacle navigator
        subprocess.run(["pkill", "-f", "obstacle_navigator.py"])
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

