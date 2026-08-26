import time
import pyautogui

# =========================
# 설정
# =========================

# 현재 스크린샷 기준 게임창 중앙 근처
MOUSE_X = 750
MOUSE_Y = 500

# 줌아웃 횟수
ZOOM_OUT_STEPS = 8

# 휠 입력 사이 간격
ZOOM_INTERVAL = 0.12

# 실행 후 준비시간
START_DELAY = 3


def zoom_out():
    print(f"{START_DELAY}초 후 줌아웃 시작")
    print("그동안 Last War 창을 클릭해서 활성화해 주세요.")

    time.sleep(START_DELAY)

    # 게임 화면 중앙으로 마우스 이동
    pyautogui.moveTo(MOUSE_X, MOUSE_Y, duration=0.2)

    print(f"줌아웃 시작: {ZOOM_OUT_STEPS}단계")

    for i in range(ZOOM_OUT_STEPS):
        pyautogui.scroll(-1)
        print(f"  {i + 1}/{ZOOM_OUT_STEPS}")
        time.sleep(ZOOM_INTERVAL)

    print("줌아웃 완료")


if __name__ == "__main__":
    zoom_out()
