#!/usr/bin/python3
import os
import sys
import time
from picamera2 import Picamera2

def capture_photo():
    # 1. Define and create the destination path
    output_dir = "./images"
    output_file = os.path.join(output_dir, "capture.jpg")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    print("Initializing camera...")
    try:
        # 2. Directly initialize the camera object
        picam2 = Picamera2()
        picam2.start()
        
        # 3. Give the sensor a moment to adjust exposure and white balance
        print("Waiting for auto-exposure to settle (2 seconds)...")
        time.sleep(2)
        
        # 4. Capture and save the image
        print(f"Capturing image and saving to {output_file}...")
        picam2.capture_file(output_file)
        
        # 5. Clean up the camera resources
        picam2.stop()
        print("Success! Photo saved.")

    except RuntimeError as e:
        print(f"\n[ERROR] Camera hardware connection failure: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to capture photo: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    capture_photo()