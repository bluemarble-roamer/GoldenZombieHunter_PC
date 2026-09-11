import time
import pyautogui


# 실행 후 준비시간
START_DELAY = 3

# 게임 화면 중앙 근처
START_X = 1157
START_Y = 533

# 드래그 거리
DRAG_DISTANCE = 600

# 드래그 시간
DRAG_DURATION = 0.6


print(f"{START_DELAY}초 후 드래그합니다.")
print("Last War 창을 활성화해 주세요.")

time.sleep(START_DELAY)

# 시작 위치로 이동
pyautogui.moveTo(
    START_X,
    START_Y,
    duration=0.2
)

# 왼쪽으로 드래그
END_X = START_X - DRAG_DISTANCE
END_Y = START_Y

print(
    f"[드래그] "
    f"({START_X}, {START_Y}) "
    f"→ ({END_X}, {END_Y})"
)

pyautogui.dragTo(
    END_X,
    END_Y,
    duration=DRAG_DURATION,
    button="left"
)

print("[드래그] 완료")
