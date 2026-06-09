#!/usr/bin/python3
# SHA256:mGwYn98sTJO/BVBP3/v7PPQQYEabyNPPPNI8txX6N0s hkrugerilingworth@gmail.com
import os
import sys
import time
from picamera2 import Picamera2

OUTPUT_RELATIVE_PATH = "./images"
OUTPUT_ABSOLUTE_PATH = os.path.join(OUTPUT_RELATIVE_PATH, "capture.jpg")


def capture_photo(camera: Picamera2, output_file: str):
    """Capture a photo and save it to the specified output file path"""
    camera.start()
    camera.capture_file(output_file)        
    camera.stop()

def validate_output_path(output_path: str):
    """Create the output directory if it does not exist"""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"Created directory: {output_path}")

def main():
    validate_output_path(OUTPUT_ABSOLUTE_PATH)
    try:
        camera = Picamera2()
        capture_photo(camera, OUTPUT_ABSOLUTE_PATH)
    except RuntimeError as e:
        print(f"\n[ERROR] Camera hardware connection failure: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to capture photo: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()