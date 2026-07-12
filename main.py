#!/usr/bin/python3
import os
import sys
import time
import numpy as np
from picamera2 import Picamera2
from dataclasses import dataclass
from contextlib import contextmanager
from gpiozero import LED

OUTPUT_RELATIVE_PATH = "./images"
OUTPUT_ABSOLUTE_PATH = os.path.join(OUTPUT_RELATIVE_PATH, "capture.jpg")
DEFAULT_CAMERA_SETTINGS = {
    "AeEnable": False,
    "AwbEnable": False,
    "ColourGains": (1.0, 1.0),
}

def validate_output_path(output_path: str):
    """Create the output directory if it does not exist"""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created directory: {output_path}")

@dataclass
class LedAttributes:
    """Configuration settings for an LED"""
    led: LED | None # None for dark frame capture
    exposure_time_us: int
    analogue_gain: float

SPECTRAL_CONFIG = {
    "led1": {"pin": 17,   "exposure": 1000000, "gain": 1.0},
    "led2": {"pin": 27,   "exposure": 1000000, "gain": 1.0},
    "led3": {"pin": 22,   "exposure": 1000000, "gain": 1.0},
    "dark": {"pin": None, "exposure": 1000000, "gain": 1.0}  # Core dark frame addition
}

SPECTRAL_CHANNELS = {
    band: LedAttributes(
        led=LED(cfg["pin"]) if cfg["pin"] is not None else None,
        exposure_time_us=cfg["exposure"],
        analogue_gain=cfg["gain"]
    )
    for band, cfg in SPECTRAL_CONFIG.items()
}

@contextmanager
def switch_lighting(channel: LedAttributes):
    """Cleanly isolates the targeted wavelength LED, keeping all others off."""
    if channel.led is not None:
        channel.led.on()
        print(f"LED ON: {channel.led}")
    else:
        print("Acquiring Dark Frame (All LEDs OFF)")
    try:
        yield
    finally:
        if channel.led is not None:
            channel.led.off()

def capture_multispectral_image(camera: Picamera2, output_dir: str):
    """Execute a lockstep illumination and capture loop across all bands"""
    config = camera.create_preview_configuration(buffer_count=2)
    camera.configure(config)
    camera.set_controls(DEFAULT_CAMERA_SETTINGS)
    camera.start()
    try:
        for band, channel in SPECTRAL_CHANNELS.items():
            print(f"Acquiring spectral layer: [{band}]...")            
            # Everything inside this block happens while the LED is explicitly ON
            with switch_lighting(channel):  
                # Apply explicit hardware parameters stored in the dataclass
                camera.set_controls({
                    "ExposureTime": channel.exposure_time_us,
                    "AnalogueGain": channel.analogue_gain
                })
                camera.switch_mode(config)
                frame_array = camera.capture_array("main")

                filename = f"capture_{band}.npy"
                output_file_path = os.path.join(output_dir, filename)
                np.save(output_file_path, frame_array)
                # with camera.captured_request(flush=True) as request:
                #     request.save("main", output_file_path)                    
            print(f"Successfully saved: {output_file_path}\n")
            
    finally:
        camera.stop()

def acquire_spectral_cube(camera: Picamera2, config) -> tuple[np.ndarray, list[str]]:
    """Executes lockstep sequential capture and stacks a 4D hypercube."""
    cube_bands = []
    band_names = []
    try:
        for band, channel in SPECTRAL_CHANNELS.items():
            print(f"Acquiring spectral layer: [{band}]...")            
            
            with switch_lighting(channel):  
                camera.set_controls({
                    "ExposureTime": channel.exposure_time_us,
                    "AnalogueGain": channel.analogue_gain
                })
                camera.switch_mode(config)
                
                # Fetch raw 3D array: (Height, Width, Channels)
                frame_array = camera.capture_array("main")
                cube_bands.append(frame_array)
                band_names.append(band)
        # Stack along the 4th dimension to construct the 4D Hypercube
        hypercube = np.stack(cube_bands, axis=-1)
        return hypercube, band_names
            
    finally:
        camera.stop()

def main():
    validate_output_path(OUTPUT_RELATIVE_PATH)
    try:
        if not Picamera2.global_camera_info():
            raise RuntimeError("No cameras detected")
        # camera = Picamera2()
        # capture_multispectral_image(camera, OUTPUT_RELATIVE_PATH)
        camera = Picamera2()
        config = camera.create_preview_configuration(buffer_count=2)
        camera.configure(config)
        camera.set_controls(DEFAULT_CAMERA_SETTINGS)
        camera.start()
        hypercube, bands = acquire_spectral_cube(camera, config)
        output_file = os.path.join(OUTPUT_RELATIVE_PATH, "multispectral_cube.npz")
        np.savez_compressed(output_file, data=hypercube, bands=bands)

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