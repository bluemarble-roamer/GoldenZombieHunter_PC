import time
import pyautogui

print("마우스를 원하는 위치에 올리세요.")
print("Ctrl+C로 종료")
print()

try:
    while True:
        x, y = pyautogui.position()
        print(f"\rX={x:4d}  Y={y:4d}", end="", flush=True)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n종료")
