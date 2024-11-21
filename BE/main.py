import cv2
import numpy as np
import keyboard
import time
from mss import mss
import easyocr
from PIL import Image

class GameScreenRecognition:
    def __init__(self):
        # EasyOCR 리더 초기화 (한글, 영어 지원)
        self.reader = easyocr.Reader(['ko', 'en'])
        # 스크린샷 캡처를 위한 mss 초기화
        self.sct = mss()
        # 프로그램 실행 상태
        self.running = True

    def capture_screen(self, monitor_number=1):
        """화면 캡처 함수"""
        monitor = self.sct.monitors[monitor_number]
        screenshot = self.sct.grab(monitor)
        # Convert to numpy array
        img = np.array(screenshot)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def find_image_on_screen(self, template_path, threshold=0.8):
        """화면에서 특정 이미지 찾기"""
        # 템플릿 이미지 로드
        template = cv2.imread(template_path)
        if template is None:
            print(f"Error: Cannot load template image from {template_path}")
            return None

        # 현재 화면 캡처
        screen = self.capture_screen()
        
        # 템플릿 매칭 수행
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= threshold:
            return max_loc
        return None

    def read_text_from_region(self, region):
        """특정 영역에서 텍스트 읽기"""
        screen = self.capture_screen()
        # region은 (x, y, width, height) 형식
        roi = screen[region[1]:region[1]+region[3], region[0]:region[0]+region[2]]
        
        # EasyOCR로 텍스트 인식
        results = self.reader.readtext(roi)
        return [text for _, text, conf in results]

    def check_health_gauge(self, region):
        """체력 게이지 확인"""
        screen = self.capture_screen()
        roi = screen[region[1]:region[1]+region[3], region[0]:region[0]+region[2]]
        
        # 여기서는 예시로 빨간색 픽셀의 비율을 체크
        # 실제 게임에 맞게 수정 필요
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)
        
        red_pixel_ratio = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
        return red_pixel_ratio

    def run(self):
        """메인 실행 루프"""
        print("프로그램 시작... 'q'를 누르면 종료됩니다.")
        
        while self.running:
            try:
                # 'q' 키를 누르면 프로그램 종료
                if keyboard.is_pressed('q'):
                    self.running = False
                    break

                # 예시: 특정 이미지 찾기
                # image_loc = self.find_image_on_screen('template.png')
                # if image_loc:
                #     print(f"이미지를 찾았습니다: {image_loc}")

                # 예시: 체력 게이지 확인
                # health_region = (100, 100, 200, 20)  # 실제 게임에 맞게 조정 필요
                # health_ratio = self.check_health_gauge(health_region)
                # if health_ratio < 0.1:  # 체력이 10% 미만일 때
                #     print("체력이 위험합니다!")

                # 프레임 간 딜레이
                time.sleep(0.1)

            except Exception as e:
                print(f"에러 발생: {e}")
                continue

        print("프로그램 종료")

if __name__ == "__main__":
    recognition = GameScreenRecognition()
    recognition.run()
