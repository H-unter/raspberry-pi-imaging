#!/usr/bin/python3
import os
import sys
import time
from picamera2 import Picamera2
from dataclasses import dataclass
from gpiozero import LED

OUTPUT_RELATIVE_PATH = "./images"
OUTPUT_ABSOLUTE_PATH = os.path.join(OUTPUT_RELATIVE_PATH, "capture.jpg")
def validate_output_path(output_path: str):
    """Create the output directory if it does not exist"""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created directory: {output_path}")

@dataclass
class LedAttributes:
    """Configuration settings for an LED"""
    led: LED
    exposure_time_us: int
    analogue_gain: float

SPECTRAL_CHANNELS = {
    "led1": LedAttributes(led=LED(17), exposure_time_us=100000, analogue_gain=1),
    "led2": LedAttributes(led=LED(27), exposure_time_us=100000, analogue_gain=1),
    "led3": LedAttributes(led=LED(22), exposure_time_us=100000, analogue_gain=1)
}

def switch_lighting(target_band: str):
    """Cleanly isolates the targeted wavelength LED, keeping all others off"""
    for band, channel in SPECTRAL_CHANNELS.items():
        if band == target_band:
            channel.led.on()
        else:
            channel.led.off()

def capture_photo(camera: Picamera2, output_file: str):
    """Capture a photo and save it to the specified output file path"""
    camera.start()
    camera.capture_file(output_file)        
    camera.stop()

def capture_multispectral_image(camera: Picamera2, output_dir: str):
    """Execute a lockstep illumination and capture loop across all bands"""
    config = camera.create_preview_configuration(buffer_count=4)
    camera.configure(config)
    camera.set_controls({"AeEnable": False})
    camera.start()
    try:
        for band, channel in SPECTRAL_CHANNELS.items():
            print(f"Acquiring spectral layer: [{band}]...")            
            switch_lighting(band) # toggles the light of interest on and all others off
            
            # 2. Apply explicit hardware parameters stored in the dataclass
            camera.set_controls({
                "ExposureTime": channel.exposure_time_us,
                "AnalogueGain": channel.analogue_gain
            })
            time.sleep(0.01)  # Minor wait for sensor registers to latch
            filename = f"capture_{band}.jpg"
            output_file_path = os.path.join(output_dir, filename)
            
            with camera.captured_request(flush=True) as request:
                request.save("main", output_file_path)
                
            print(f"Successfully saved: {output_file_path}")
            
    finally:
        # Mandatory teardown execution sequence to protect physical lines
        camera.stop()
        for channel in SPECTRAL_CHANNELS.values():
            channel.led.off()

def main():
    validate_output_path(OUTPUT_RELATIVE_PATH)
    try:
        if not Picamera2.global_camera_info():
            raise RuntimeError("No cameras detected")
        camera = Picamera2()
        capture_multispectral_image(camera, OUTPUT_RELATIVE_PATH)
    except RuntimeError as e:
        print(f"\n[ERROR] Camera hardware connection failure: {e}", file=sys.stderr)
        sys.exit(1)
    except IndexError as e:
        print(f"\n[ERROR] Camera hardware connection failure: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed multispectral block acquisition: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()