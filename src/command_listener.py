#!/usr/bin/env python3
"""
Command Listener for Raspberry Pi
Listens to Adafruit IO MQTT feeds for control commands from Flask web app
"""
import json
import os
import sys
import time
import signal
import subprocess
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

# Global car instance (reused)
_car_instance = None

def get_car():
    """Get or create car instance (singleton)"""
    global _car_instance
    if _car_instance is None:
        try:
            from hardware.motor import Ordinary_Car
            _car_instance = Ordinary_Car()
        except Exception as e:
            print(f"Error creating car instance: {e}")
    return _car_instance

def handle_motor_control(action):
    """Handle motor control commands"""
    try:
        car = get_car()
        if not car:
            print("Motor not available")
            return
        
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

# Global LED instance (reused)
_led_instance = None

def get_led():
    """Get or create LED instance (singleton)"""
    global _led_instance
    if _led_instance is None:
        try:
            from hardware.spi_ledpixel import Freenove_SPI_LedPixel
            _led_instance = Freenove_SPI_LedPixel(count=60, bright=120, sequence='GRB', bus=0, device=0)
            _led_instance.led_begin(bus=0, device=0)
            _led_instance.set_led_count(60)
        except Exception as e:
            print(f"Error creating LED instance: {e}")
    return _led_instance

def handle_led_control(state):
    """Handle LED control commands"""
    try:
        led = get_led()
        if not led:
            print("LED not available")
            return
        
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
    PID_FILE = Path("/tmp/line_follow.pid")
    
    if command == "start":
        # Check if already running
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    print("Line tracking already running")
                    return
                except OSError:
                    # Process doesn't exist, remove stale PID file
                    PID_FILE.unlink()
            except (ValueError, OSError):
                PID_FILE.unlink()
        
        # Start line following script
        script = BASE_DIR / "line_follow.py"
        try:
            # Don't capture stdout/stderr - let it print to console for debugging
            # This prevents buffering issues and allows seeing real-time output
            process = subprocess.Popen(
                ["python3", str(script)],
                stdout=None,  # Don't capture - print to console
                stderr=None,  # Don't capture - print to console
                preexec_fn=os.setsid  # Start in new process group
            )
            # Save PID
            PID_FILE.write_text(str(process.pid))
            
            # Check if it started successfully (wait a bit longer)
            time.sleep(1.0)
            if process.poll() is not None:
                # Process died immediately - try to get error from stderr
                print(f"❌ Line tracking failed to start (PID {process.pid} exited immediately)")
                PID_FILE.unlink()
            else:
                print(f"✅ Line tracking started (PID: {process.pid})")
        except Exception as e:
            print(f"❌ Error starting line tracking: {e}", file=sys.stderr)
            if PID_FILE.exists():
                PID_FILE.unlink()
    elif command == "stop":
        # Stop line following
        stopped = False
        processes_killed = []
        
        # First try using PID file
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                print(f"[DEBUG] Found PID file with PID: {pid}")
                try:
                    # Check if process exists
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    print(f"[DEBUG] Process {pid} exists, attempting to kill...")
                    
                    # Try to get process group and kill it
                    try:
                        pgid = os.getpgid(pid)
                        print(f"[DEBUG] Process group: {pgid}")
                        os.killpg(pgid, signal.SIGTERM)  # Kill process group
                        time.sleep(0.5)
                        
                        # Check if still running
                        try:
                            os.kill(pid, 0)
                            print(f"[DEBUG] Process still running, force killing...")
                            os.killpg(pgid, signal.SIGKILL)  # Force kill
                            time.sleep(0.2)
                        except (OSError, ProcessLookupError):
                            print(f"[DEBUG] Process {pid} terminated")
                        
                        stopped = True
                        processes_killed.append(pid)
                    except (OSError, ProcessLookupError) as e:
                        print(f"[DEBUG] Could not kill process group: {e}")
                        # Try killing just the process
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.3)
                            os.kill(pid, signal.SIGKILL)
                            stopped = True
                            processes_killed.append(pid)
                        except (OSError, ProcessLookupError):
                            pass
                except (OSError, ProcessLookupError):
                    print(f"[DEBUG] Process {pid} does not exist")
                finally:
                    PID_FILE.unlink()
            except (ValueError, OSError) as e:
                print(f"[DEBUG] Error reading PID file: {e}")
                PID_FILE.unlink()
        
        # Always try pkill as well (most reliable method)
        try:
            print("[DEBUG] Using pkill to find and kill line_follow.py processes...")
            # Try multiple patterns to catch the process
            patterns = ["line_follow.py", "line-follow", "line_follow"]
            for pattern in patterns:
                result = subprocess.run(
                    ["pkill", "-9", "-f", pattern],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2
                )
                if result.returncode == 0:
                    stopped = True
                    print(f"[DEBUG] pkill killed processes matching: {pattern}")
                    break
        except subprocess.TimeoutExpired:
            print("[DEBUG] pkill timed out")
        except Exception as e:
            print(f"[DEBUG] Error using pkill: {e}")
        
        # Verify it's actually stopped - check multiple patterns
        try:
            patterns_to_check = ["line_follow.py", "line-follow", "line_follow"]
            all_stopped = True
            for pattern in patterns_to_check:
                check_result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=1
                )
                if check_result.returncode == 0:
                    remaining_pids = check_result.stdout.decode().strip().split('\n')
                    remaining_pids = [p for p in remaining_pids if p]
                    if remaining_pids:
                        print(f"[DEBUG] Warning: Still found processes matching '{pattern}': {remaining_pids}")
                        all_stopped = False
                        # Force kill any remaining processes
                        for pid_str in remaining_pids:
                            try:
                                pid = int(pid_str)
                                os.kill(pid, signal.SIGKILL)
                                print(f"[DEBUG] Force killed remaining process {pid}")
                            except:
                                pass
            if all_stopped:
                stopped = True
        except Exception as e:
            print(f"[DEBUG] Error verifying stop: {e}")
        
        # Always stop motors when stopping line tracking
        try:
            car = get_car()
            if car:
                car.set_motor_model(0, 0, 0, 0)
                print("[DEBUG] Motors stopped")
        except Exception as e:
            print(f"[DEBUG] Error stopping motors: {e}")
        
        if stopped:
            print("✅ Line tracking stopped")
        else:
            print("⚠️  Line tracking stop attempted (check if process was running)")

def handle_obstacle_avoidance(command):
    """Handle obstacle avoidance commands"""
    BASE_DIR = Path(__file__).resolve().parent
    PID_FILE = Path("/tmp/obstacle_navigator.pid")
    
    if command == "start":
        # Check if already running
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                # Check if process is still running
                try:
                    os.kill(pid, 0)  # Signal 0 just checks if process exists
                    print("Obstacle avoidance already running")
                    return
                except OSError:
                    # Process doesn't exist, remove stale PID file
                    PID_FILE.unlink()
            except (ValueError, OSError):
                PID_FILE.unlink()
        
        # Start obstacle navigator script
        script = BASE_DIR / "obstacle_navigator.py"
        try:
            process = subprocess.Popen(
                ["python3", str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Start in new process group
            )
            # Save PID
            PID_FILE.write_text(str(process.pid))
            
            # Check if it started successfully (wait a bit longer)
            time.sleep(1.0)
            if process.poll() is not None:
                # Process died immediately
                print(f"❌ Obstacle avoidance failed to start (PID {process.pid} exited immediately)")
                PID_FILE.unlink()
            else:
                print(f"✅ Obstacle avoidance started (PID: {process.pid})")
        except Exception as e:
            print(f"Error starting obstacle avoidance: {e}")
            if PID_FILE.exists():
                PID_FILE.unlink()
    elif command == "stop":
        # Stop obstacle navigator
        stopped = False
        
        # First try using PID file
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                print(f"[DEBUG] Found PID file with PID: {pid}")
                try:
                    # Check if process exists
                    os.kill(pid, 0)
                    print(f"[DEBUG] Process {pid} exists, attempting to kill...")
                    
                    # Try to get process group and kill it
                    try:
                        pgid = os.getpgid(pid)
                        print(f"[DEBUG] Process group: {pgid}")
                        os.killpg(pgid, signal.SIGTERM)
                        time.sleep(0.5)
                        
                        # Check if still running
                        try:
                            os.kill(pid, 0)
                            print(f"[DEBUG] Process still running, force killing...")
                            os.killpg(pgid, signal.SIGKILL)
                            time.sleep(0.2)
                        except (OSError, ProcessLookupError):
                            print(f"[DEBUG] Process {pid} terminated")
                        
                        stopped = True
                    except (OSError, ProcessLookupError) as e:
                        print(f"[DEBUG] Could not kill process group: {e}")
                        # Try killing just the process
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.3)
                            os.kill(pid, signal.SIGKILL)
                            stopped = True
                        except (OSError, ProcessLookupError):
                            pass
                except (OSError, ProcessLookupError):
                    print(f"[DEBUG] Process {pid} does not exist")
                finally:
                    PID_FILE.unlink()
            except (ValueError, OSError) as e:
                print(f"[DEBUG] Error reading PID file: {e}")
                PID_FILE.unlink()
        
        # Always try pkill as well (most reliable method)
        try:
            print("[DEBUG] Using pkill to find and kill obstacle_navigator.py processes...")
            result = subprocess.run(
                ["pkill", "-f", "obstacle_navigator.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            if result.returncode == 0:
                stopped = True
                print("[DEBUG] pkill found and killed obstacle_navigator.py processes")
            elif result.returncode == 1:
                print("[DEBUG] pkill found no matching processes")
        except subprocess.TimeoutExpired:
            print("[DEBUG] pkill timed out")
        except Exception as e:
            print(f"[DEBUG] Error using pkill: {e}")
        
        # Verify it's actually stopped
        try:
            check_result = subprocess.run(
                ["pgrep", "-f", "obstacle_navigator.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1
            )
            if check_result.returncode == 0:
                remaining_pids = check_result.stdout.decode().strip().split('\n')
                remaining_pids = [p for p in remaining_pids if p]
                if remaining_pids:
                    print(f"[DEBUG] Warning: Still found processes: {remaining_pids}")
                    # Try one more time with SIGKILL
                    for pid_str in remaining_pids:
                        try:
                            pid = int(pid_str)
                            os.kill(pid, signal.SIGKILL)
                            print(f"[DEBUG] Force killed remaining process {pid}")
                        except:
                            pass
                else:
                    stopped = True
            else:
                stopped = True
        except:
            pass
        
        # Always stop motors when stopping obstacle avoidance
        try:
            car = get_car()
            if car:
                car.set_motor_model(0, 0, 0, 0)
                print("[DEBUG] Motors stopped")
        except Exception as e:
            print(f"[DEBUG] Error stopping motors: {e}")
        
        if stopped:
            print("✅ Obstacle avoidance stopped")
        else:
            print("⚠️  Obstacle avoidance stop attempted (check if process was running)")

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

