from gpiozero import DistanceSensor, PWMSoftwareFallback, DistanceSensorNoEcho
import warnings
import time
import os

class Ultrasonic:
    def __init__(self, trigger_pin: int = 27, echo_pin: int = 22, max_distance: float = 3.0):
        # Initialize the Ultrasonic class and set up the distance sensor.
        warnings.filterwarnings("ignore", category = DistanceSensorNoEcho)
        warnings.filterwarnings("ignore", category = PWMSoftwareFallback)  # Ignore PWM software fallback warnings
        self.trigger_pin = trigger_pin  # Set the trigger pin number
        self.echo_pin = echo_pin        # Set the echo pin number
        self.max_distance = max_distance  # Set the maximum distance
        
        # Try to initialize with retries (GPIO might be busy or need time to initialize)
        max_retries = 5
        last_error = None
        
        # First, try to ensure GPIO pins are not in use by checking /sys/class/gpio
        # Give a small delay to let any previous processes release GPIO
        time.sleep(0.2)
        
        for attempt in range(max_retries):
            try:
                # Try to initialize the sensor
                self.sensor = DistanceSensor(
                    echo=self.echo_pin, 
                    trigger=self.trigger_pin, 
                    max_distance=self.max_distance,
                    queue_len=1  # Reduce queue length for faster response
                )
                # Small delay to let sensor initialize
                time.sleep(0.1)
                # Test if sensor is working by reading distance once
                try:
                    _ = self.sensor.distance
                except:
                    pass  # First read might fail, that's okay
                break  # Success
            except RuntimeError as e:
                last_error = e
                error_msg = str(e).lower()
                if "edge detection" in error_msg or "gpio" in error_msg:
                    # GPIO conflict - wait longer and retry
                    wait_time = 0.5 * (attempt + 1)  # Increasing wait time
                    if attempt < max_retries - 1:
                        print(f"[ultrasonic] GPIO busy, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                    else:
                        raise RuntimeError(f"Failed to initialize ultrasonic sensor: GPIO pins {self.trigger_pin}/{self.echo_pin} are busy or not available. Error: {last_error}")
                else:
                    # Other error, retry with shorter delay
                    if attempt < max_retries - 1:
                        time.sleep(0.3)
                    else:
                        raise RuntimeError(f"Failed to initialize ultrasonic sensor after {max_retries} attempts: {last_error}")
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"[ultrasonic] Initialization attempt {attempt + 1} failed: {e}, retrying...")
                    time.sleep(0.3)
                else:
                    raise RuntimeError(f"Failed to initialize ultrasonic sensor after {max_retries} attempts: {last_error}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get_distance(self) -> float:
        """
        Get the distance measurement from the ultrasonic sensor.

        Returns:
        float: The distance measurement in centimeters, rounded to one decimal place.
        """
        try:
            distance = self.sensor.distance * 100  # Get the distance in centimeters
            return round(float(distance), 1)  # Return the distance rounded to one decimal place
        except RuntimeWarning as e:
            print(f"Warning: {e}")
            return None

    def close(self):
        # Close the distance sensor.
        self.sensor.close()  # Close the sensor to release resources

if __name__ == '__main__':
    # Initialize the Ultrasonic instance with default pin numbers and max distance
    with Ultrasonic() as ultrasonic:
        try:
            while True:
                distance = ultrasonic.get_distance()  # Get the distance measurement in centimeters
                if distance is not None:
                    print(f"Ultrasonic distance: {distance}cm")  # Print the distance measurement
                time.sleep(0.5)  # Wait for 0.5 seconds
        except KeyboardInterrupt:  # Handle keyboard interrupt (Ctrl+C)
            print("\nEnd of program")  # Print an end message