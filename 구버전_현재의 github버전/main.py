import os
import sys
import time

import cv2
import numpy as np
import pyautogui
import requests


# ============================================================
# 경로
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "images")

GOLDEN_ZOMBIE_FAR = os.path.join(
    IMAGE_DIR,
    "golden_zombie_far.png"
)

ATTACK_BUTTON = os.path.join(
    IMAGE_DIR,
    "attack_button.png"
)

DISPATCH_BUTTON = os.path.join(
    IMAGE_DIR,
    "dispatch_button.png"
)

RETURNING_IMAGE = os.path.join(
    IMAGE_DIR,
    "returning.png"
)

STAMINA_RECOVERY = os.path.join(
    IMAGE_DIR,
    "stamina_recovery.png"
)

ZOMBIE_CHOICE = os.path.join(
    IMAGE_DIR,
    "zombie_choice.png"
)


# ============================================================
# 이미지 인식 기준값
# ============================================================

# 정상 황금좀비 약 0.95
# 빨간 일반좀비 오탐 약 0.7984
FAR_THRESHOLD = 0.90

ATTACK_THRESHOLD = 0.75
DISPATCH_THRESHOLD = 0.75
RETURNING_THRESHOLD = 0.75
STAMINA_THRESHOLD = 0.75
ZOMBIE_CHOICE_THRESHOLD = 0.75


# ============================================================
# 줌 설정
# ============================================================

ZOOM_OUT_STEPS = 8
ZOOM_INTERVAL = 0.12


# ============================================================
# PC 게임창 기준 좌표
# ============================================================

# 줌인 후 황금좀비 위치
GAME_CENTER_X = 1157
GAME_CENTER_Y = 533


# ============================================================
# 부대 선택
#
# 1군 BAT → python main.py 1
# 2군 BAT → python main.py 2
# ============================================================

SQUAD_NUMBER = 1

if len(sys.argv) >= 2:
    try:
        SQUAD_NUMBER = int(sys.argv[1])
    except ValueError:
        print("부대 번호는 1 또는 2만 가능합니다.")
        sys.exit(1)


if SQUAD_NUMBER == 1:

    SQUAD_X = 985
    SQUAD_Y = 943

elif SQUAD_NUMBER == 2:

    SQUAD_X = 1099
    SQUAD_Y = 943

else:

    print("부대 번호는 1 또는 2만 가능합니다.")
    sys.exit(1)


# ============================================================
# 맵 드래그
# ============================================================

DRAG_START_X = 1157
DRAG_START_Y = 533

# 직접 테스트해서 확정한 거리
DRAG_DISTANCE = 600

DRAG_DURATION = 0.6

# 드래그 후 화면 안정화
AFTER_DRAG_WAIT = 0.8

# 황금좀비가 없을 경우
# 최대 5번 화면 이동
MAX_DRAG_COUNT = 5


# ============================================================
# 시간 설정
# ============================================================

START_DELAY = 3.0

# far 황금좀비 클릭 → 자동 줌인
AFTER_FAR_CLICK_WAIT = 1.2

# 중앙 황금좀비 클릭 후
# zombie_choice가 생길 시간을 약간 줌
CHOICE_CHECK_WAIT = 0.4

# zombie_choice 클릭 후
CHOICE_CLICK_WAIT = 0.4

# 공격 버튼
ATTACK_SEARCH_TIMEOUT = 3.0
ATTACK_SEARCH_INTERVAL = 0.15

# 공격 버튼 클릭 후 부대 화면
AFTER_ATTACK_WAIT = 1.5

# 출정 버튼
DISPATCH_SEARCH_TIMEOUT = 3.0
DISPATCH_SEARCH_INTERVAL = 0.15

# 출정 이후 returning 감시 시작
AFTER_DISPATCH_WAIT = 3.0

# returning 확인 간격
RETURNING_CHECK_INTERVAL = 0.4

# returning 발견 후 다음 사냥
AFTER_RETURNING_WAIT = 1.2


# ============================================================
# ntfy
# ============================================================

NTFY_URL = (
    "https://ntfy.sh/"
    "goldenzombie_8x4k2q7m"
)


# ============================================================
# PyAutoGUI 안전장치
# ============================================================

# 급할 때 마우스를 모니터 맨 왼쪽 위로 보내면 중단
pyautogui.FAILSAFE = True


# ============================================================
# ntfy 체력부족 알림
# ============================================================

def send_stamina_alert():

    print()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(" 체력 부족! 폰 알림 전송")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print()

    try:

        response = requests.post(
            NTFY_URL,
            data=(
                "황금좀비 체력이 부족합니다.\n"
                "게임을 확인해주세요."
            ).encode("utf-8"),
            headers={
                "Title": "GoldenZombieHunter",
                "Priority": "high",
            },
            timeout=10,
        )

        response.raise_for_status()

        print(
            "[알림] ntfy 전송 성공"
        )

    except Exception as e:

        print(
            f"[알림 실패] {e}"
        )


# ============================================================
# 이미지 로드
# ============================================================

def load_template(path):

    template = cv2.imread(
        path,
        cv2.IMREAD_COLOR
    )

    if template is None:

        raise FileNotFoundError(
            f"이미지를 불러오지 못했습니다: {path}"
        )

    return template


# ============================================================
# 화면 캡처
# ============================================================

def capture_screen():

    screenshot = pyautogui.screenshot()

    screen = np.array(
        screenshot
    )

    screen = cv2.cvtColor(
        screen,
        cv2.COLOR_RGB2BGR
    )

    return screen


# ============================================================
# 이미지 찾기
# ============================================================

def find_template(template):

    screen = capture_screen()

    result = cv2.matchTemplate(
        screen,
        template,
        cv2.TM_CCOEFF_NORMED
    )

    _, max_score, _, max_location = (
        cv2.minMaxLoc(result)
    )

    h, w = template.shape[:2]

    x = (
        max_location[0]
        + w // 2
    )

    y = (
        max_location[1]
        + h // 2
    )

    return x, y, max_score


# ============================================================
# 이미지 존재 여부
# ============================================================

def is_visible(
    template,
    threshold
):

    x, y, score = find_template(
        template
    )

    return (
        score >= threshold,
        score,
        x,
        y,
    )


# ============================================================
# 이미지 기다렸다가 클릭
#
# attack / dispatch 기다리는 동안
# stamina_recovery도 함께 확인
# ============================================================

def wait_and_click(
    template,
    name,
    threshold,
    timeout,
    interval,
    stamina_template
):

    start_time = time.time()
    best_score = 0.0

    print(
        f"[대기탐색] {name} "
        f"최대 {timeout:.1f}초"
    )

    while (
        time.time() - start_time
        < timeout
    ):

        # ----------------------------------------------------
        # 체력 부족 확인
        # ----------------------------------------------------

        visible, stamina_score, _, _ = (
            is_visible(
                stamina_template,
                STAMINA_THRESHOLD
            )
        )

        if visible:

            print(
                f"[체력부족] "
                f"stamina_recovery "
                f"score={stamina_score:.4f}"
            )

            send_stamina_alert()

            return "STAMINA"


        # ----------------------------------------------------
        # 원래 찾던 버튼
        # ----------------------------------------------------

        x, y, score = find_template(
            template
        )

        if score > best_score:
            best_score = score

        if score >= threshold:

            print(
                f"[성공] {name} "
                f"score={score:.4f} "
                f"위치=({x}, {y})"
            )

            pyautogui.click(
                x=x,
                y=y
            )

            print(
                f"[클릭] {name}"
            )

            return "SUCCESS"

        time.sleep(
            interval
        )


    print(
        f"[실패] {name} 인식 실패 "
        f"(최고점수={best_score:.4f}, "
        f"기준={threshold:.2f})"
    )

    return "FAIL"


# ============================================================
# 줌아웃
# ============================================================

def zoom_out():

    print()
    print(
        f"[줌아웃] "
        f"{ZOOM_OUT_STEPS}단계 시작"
    )

    pyautogui.moveTo(
        GAME_CENTER_X,
        GAME_CENTER_Y,
        duration=0.2
    )

    for i in range(
        ZOOM_OUT_STEPS
    ):

        pyautogui.scroll(-1)

        print(
            f"[줌아웃] "
            f"{i + 1}/{ZOOM_OUT_STEPS}"
        )

        time.sleep(
            ZOOM_INTERVAL
        )

    print(
        "[줌아웃] 완료"
    )


# ============================================================
# 맵 드래그
# ============================================================

def drag_map():

    end_x = (
        DRAG_START_X
        - DRAG_DISTANCE
    )

    print()
    print(
        f"[맵이동] "
        f"({DRAG_START_X}, {DRAG_START_Y}) "
        f"→ ({end_x}, {DRAG_START_Y})"
    )

    pyautogui.moveTo(
        DRAG_START_X,
        DRAG_START_Y,
        duration=0.15
    )

    pyautogui.dragTo(
        end_x,
        DRAG_START_Y,
        duration=DRAG_DURATION,
        button="left"
    )

    print(
        "[맵이동] 600px 드래그 완료"
    )

    time.sleep(
        AFTER_DRAG_WAIT
    )


# ============================================================
# 황금좀비 far 찾기
#
# 없으면 드래그 → 다시 검색
# ============================================================

def find_far_with_drag(
    far_template
):

    print()
    print(
        "[황금좀비] 줌아웃 아이콘 탐색"
    )


    # --------------------------------------------------------
    # 현재 화면 먼저 검색
    # --------------------------------------------------------

    x, y, score = find_template(
        far_template
    )

    print(
        f"[탐색] golden_zombie_far "
        f"score={score:.4f}"
    )

    if score >= FAR_THRESHOLD:

        print(
            f"[성공] 황금좀비 발견 "
            f"위치=({x}, {y})"
        )

        pyautogui.click(
            x=x,
            y=y
        )

        print(
            "[클릭] golden_zombie_far"
        )

        return True


    # --------------------------------------------------------
    # 없으면 드래그 반복
    # --------------------------------------------------------

    for drag_count in range(
        1,
        MAX_DRAG_COUNT + 1
    ):

        print()
        print(
            f"[황금좀비 없음] "
            f"맵 이동 {drag_count}/"
            f"{MAX_DRAG_COUNT}"
        )

        drag_map()

        x, y, score = find_template(
            far_template
        )

        print(
            f"[재탐색] golden_zombie_far "
            f"score={score:.4f}"
        )

        if score >= FAR_THRESHOLD:

            print(
                f"[성공] 황금좀비 발견 "
                f"위치=({x}, {y})"
            )

            pyautogui.click(
                x=x,
                y=y
            )

            print(
                "[클릭] golden_zombie_far"
            )

            return True


    print()
    print(
        "[실패] 맵 이동 후에도 "
        "황금좀비를 찾지 못했습니다."
    )

    return False


# ============================================================
# zombie_choice 확인
#
# 황금좀비와 다른 사물이 겹쳐있을 경우
# "10레벨 침입 좀비" 선택창이 뜸
# ============================================================

def handle_zombie_choice(
    zombie_choice_template
):

    time.sleep(
        CHOICE_CHECK_WAIT
    )

    x, y, score = find_template(
        zombie_choice_template
    )

    print(
        f"[선택창 확인] "
        f"zombie_choice "
        f"score={score:.4f}"
    )

    # 선택창이 없다면
    # 그냥 정상 상황
    if score < ZOMBIE_CHOICE_THRESHOLD:

        print(
            "[선택창] 없음"
        )

        return False


    # 선택창이 있다면
    # 황금좀비 선택
    print(
        f"[선택창] 황금좀비 선택 "
        f"위치=({x}, {y})"
    )

    pyautogui.click(
        x=x,
        y=y
    )

    print(
        "[클릭] zombie_choice"
    )

    time.sleep(
        CHOICE_CLICK_WAIT
    )

    return True


# ============================================================
# returning 감시
# ============================================================

def wait_for_returning(
    returning_template
):

    print()
    print(
        "[복귀감시] "
        "returning.png 감시 시작"
    )

    check_count = 0

    while True:

        check_count += 1

        x, y, score = find_template(
            returning_template
        )

        print(
            f"[복귀대기] "
            f"{check_count}회 "
            f"score={score:.4f}"
        )

        if score >= RETURNING_THRESHOLD:

            print()
            print(
                f"[복귀감지] "
                f"returning 발견! "
                f"score={score:.4f}"
            )

            return

        time.sleep(
            RETURNING_CHECK_INTERVAL
        )


# ============================================================
# 황금좀비 한 마리 사냥
# ============================================================

def hunt_one_zombie(
    far_template,
    zombie_choice_template,
    attack_template,
    dispatch_template,
    returning_template,
    stamina_template
):

    # --------------------------------------------------------
    # 1. 줌아웃
    # --------------------------------------------------------

    zoom_out()

    time.sleep(
        0.5
    )


    # --------------------------------------------------------
    # 2. 황금좀비 찾기
    # --------------------------------------------------------

    success = find_far_with_drag(
        far_template
    )

    if not success:

        return "NO_ZOMBIE"


    # --------------------------------------------------------
    # 3. 자동 줌인
    # --------------------------------------------------------

    print(
        f"[대기] 줌인 "
        f"{AFTER_FAR_CLICK_WAIT:.1f}초"
    )

    time.sleep(
        AFTER_FAR_CLICK_WAIT
    )


    # --------------------------------------------------------
    # 4. 줌인된 황금좀비 클릭
    # --------------------------------------------------------

    print(
        f"[클릭] 줌인 황금좀비 "
        f"({GAME_CENTER_X}, "
        f"{GAME_CENTER_Y})"
    )

    pyautogui.click(
        GAME_CENTER_X,
        GAME_CENTER_Y
    )


    # --------------------------------------------------------
    # 5. 겹친 오브젝트 선택창 확인
    #
    # 있으면 zombie_choice 클릭
    # 없으면 그냥 다음 단계
    # --------------------------------------------------------

    handle_zombie_choice(
        zombie_choice_template
    )


    # --------------------------------------------------------
    # 6. 공격 버튼
    # --------------------------------------------------------

    result = wait_and_click(
        attack_template,
        "attack_button",
        ATTACK_THRESHOLD,
        timeout=ATTACK_SEARCH_TIMEOUT,
        interval=ATTACK_SEARCH_INTERVAL,
        stamina_template=stamina_template
    )

    if result == "STAMINA":

        return "STAMINA"

    if result != "SUCCESS":

        return "ERROR"


    # --------------------------------------------------------
    # 7. 부대 선택 화면 대기
    # --------------------------------------------------------

    print(
        f"[대기] 부대 선택 화면 "
        f"{AFTER_ATTACK_WAIT:.1f}초"
    )

    time.sleep(
        AFTER_ATTACK_WAIT
    )


    # --------------------------------------------------------
    # 8. 선택한 부대 클릭
    # --------------------------------------------------------

    print(
        f"[클릭] {SQUAD_NUMBER}군 "
        f"({SQUAD_X}, {SQUAD_Y})"
    )

    pyautogui.click(
        SQUAD_X,
        SQUAD_Y
    )


    # --------------------------------------------------------
    # 9. 출정 버튼
    # --------------------------------------------------------

    result = wait_and_click(
        dispatch_template,
        "dispatch_button",
        DISPATCH_THRESHOLD,
        timeout=DISPATCH_SEARCH_TIMEOUT,
        interval=DISPATCH_SEARCH_INTERVAL,
        stamina_template=stamina_template
    )

    if result == "STAMINA":

        return "STAMINA"

    if result != "SUCCESS":

        return "ERROR"


    print()
    print(
        f"[출정완료] "
        f"{SQUAD_NUMBER}군 황금좀비 공격 출발"
    )


    # --------------------------------------------------------
    # 10. 출정 후 3초 대기
    # --------------------------------------------------------

    print(
        f"[대기] "
        f"{AFTER_DISPATCH_WAIT:.1f}초 후 "
        "복귀 감시 시작"
    )

    time.sleep(
        AFTER_DISPATCH_WAIT
    )


    # --------------------------------------------------------
    # 11. returning 감시
    # --------------------------------------------------------

    wait_for_returning(
        returning_template
    )


    # --------------------------------------------------------
    # 12. 다음 사냥
    # --------------------------------------------------------

    print(
        f"[다음사냥] "
        f"{AFTER_RETURNING_WAIT:.1f}초 후 "
        "재시작"
    )

    time.sleep(
        AFTER_RETURNING_WAIT
    )

    return "SUCCESS"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=================================="
    )
    print(
        " GoldenZombieHunter PC"
    )
    print(
        f" {SQUAD_NUMBER}군 자동사냥"
    )
    print(
        "=================================="
    )
    print()

    print(
        f"{START_DELAY:.0f}초 안에 "
        "Last War 창을 클릭하세요."
    )

    time.sleep(
        START_DELAY
    )


    # --------------------------------------------------------
    # 이미지 로드
    # --------------------------------------------------------

    far_template = load_template(
        GOLDEN_ZOMBIE_FAR
    )

    zombie_choice_template = load_template(
        ZOMBIE_CHOICE
    )

    attack_template = load_template(
        ATTACK_BUTTON
    )

    dispatch_template = load_template(
        DISPATCH_BUTTON
    )

    returning_template = load_template(
        RETURNING_IMAGE
    )

    stamina_template = load_template(
        STAMINA_RECOVERY
    )


    # --------------------------------------------------------
    # 무한 반복
    # --------------------------------------------------------

    cycle = 0

    while True:

        cycle += 1

        print()
        print()
        print(
            "=================================="
        )
        print(
            f" 황금좀비 사냥 #{cycle}"
        )
        print(
            "=================================="
        )

        result = hunt_one_zombie(
            far_template,
            zombie_choice_template,
            attack_template,
            dispatch_template,
            returning_template,
            stamina_template
        )


        # ----------------------------------------------------
        # 정상 사냥 완료
        # ----------------------------------------------------

        if result == "SUCCESS":

            continue


        # ----------------------------------------------------
        # 체력 부족
        # ----------------------------------------------------

        if result == "STAMINA":

            print()
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )
            print(
                " 체력 부족으로 자동사냥 종료"
            )
            print(
                " 폰 알림을 확인하세요."
            )
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

            break


        # ----------------------------------------------------
        # 황금좀비 없음
        # ----------------------------------------------------

        if result == "NO_ZOMBIE":

            print()
            print(
                "=================================="
            )
            print(
                " 황금좀비를 찾지 못해 종료"
            )
            print(
                "=================================="
            )

            break


        # ----------------------------------------------------
        # 기타 인식 실패
        # ----------------------------------------------------

        print()
        print(
            "=================================="
        )
        print(
            " 진행 중 이미지 인식 실패"
        )
        print(
            " 자동사냥 종료"
        )
        print(
            "=================================="
        )

        break


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    main()
