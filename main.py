import cv2
import mediapipe as mp
import pyautogui
import math
import os
import time

# ========= CONFIGURAÇÕES =========
FRAME_WIDTH = 640
FRAME_HEIGHT = 360

frame_margin = 60
smoothening = 7

click_threshold = 30
release_threshold = 50

scroll_speed_divider = 6

CLICK_DELAY = 0.6
last_click_time = 0

gesture_cooldown = 3
last_gesture_time = 0

scroll_mode = False


# =================================

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
    max_num_hands=1
)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

screen_w, screen_h = pyautogui.size()
prev_x, prev_y = screen_w // 2, screen_h // 2
prev_scroll_y = 0
clicking = False

cv2.namedWindow("AirMouse PRO", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AirMouse PRO", FRAME_WIDTH, FRAME_HEIGHT)

def fingers_up(hand):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    fingers.append(hand.landmark[4].x < hand.landmark[3].x)

    for i in range(1, 5):
        fingers.append(hand.landmark[tips[i]].y < hand.landmark[tips[i] - 2].y)

    return fingers

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    cv2.rectangle(
        frame,
        (frame_margin, frame_margin),
        (w - frame_margin, h - frame_margin),
        (255, 0, 255),
        2
    )

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for hand in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            lm = hand.landmark

            ix = int(lm[8].x * w)
            iy = int(lm[8].y * h)

            tx = int(lm[4].x * w)
            ty = int(lm[4].y * h)

            # ===== ZONA ATIVA =====
            if not (frame_margin < ix < w - frame_margin and frame_margin < iy < h - frame_margin):
                continue

            # ===== MOUSE =====
            mapped_x = (ix - frame_margin) / (w - 2 * frame_margin)
            mapped_y = (iy - frame_margin) / (h - 2 * frame_margin)

            target_x = screen_w * mapped_x
            target_y = screen_h * mapped_y

            curr_x = prev_x + (target_x - prev_x) / smoothening
            curr_y = prev_y + (target_y - prev_y) / smoothening

            pyautogui.moveTo(curr_x, curr_y)
            prev_x, prev_y = curr_x, curr_y

            # ===== CLIQUE COM COOLDOWN =====
            distance = math.hypot(tx - ix, ty - iy)
            cv2.line(frame, (ix, iy), (tx, ty), (0, 255, 0), 2)

            now = time.time()
            if distance < click_threshold and (now - last_click_time) > CLICK_DELAY:
                pyautogui.click()
                last_click_time = now

           # ===== SCROLL =====
            # ===== SCROLL MODE =====
            fingers = fingers_up(hand)

            if fingers == [False, True, True, False, False]:
                scroll_mode = True
                cv2.putText(frame, "SCROLL MODE", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if prev_scroll_y == 0:
                    prev_scroll_y = iy
                else:
                    delta = prev_scroll_y - iy

                    if abs(delta) > 8:
                        pyautogui.scroll(int(delta / scroll_speed_divider))

                    prev_scroll_y = iy

            else:
                scroll_mode = False
                prev_scroll_y = 0

            # ===== GESTOS DE APPS (DESATIVADOS POR SEGURANÇA) =====
            """
            current_time = time.time()
            if current_time - last_gesture_time > gesture_cooldown:

                if fingers == [False, False, False, False, False]:
                    os.system("start chrome")
                    last_gesture_time = current_time

                elif fingers == [True, True, True, True, True]:
                    os.system("code")
                    last_gesture_time = current_time
            """

    cv2.imshow("AirMouse PRO", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
