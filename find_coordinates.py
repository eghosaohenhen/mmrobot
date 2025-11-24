"""
Utility script to find mouse coordinates on screen.
Run this and hover over the "Trigger Frame" button in mmWave Studio.
Press Ctrl+C to exit.
"""
import pyautogui
import time

print("Move your mouse to the 'Trigger Frame' button in mmWave Studio...")
print("Position will be displayed every 2 seconds")
print("Press Ctrl+C when done")
print()

try:
    while True:
        x, y = pyautogui.position()
        print(f"Current position: X={x}, Y={y}")
        time.sleep(2)
except KeyboardInterrupt:
    print("\nFinal position noted!")
