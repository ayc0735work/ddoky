import os
import cv2
import numpy as np
import win32gui
import win32ui
import win32con
import win32api
import win32com.client
from PIL import ImageGrab
import time

class WindowController:
    def __init__(self, target_hwnd=None):
        self.target_hwnd = target_hwnd
        self.shell = win32com.client.Dispatch("WScript.Shell")
        
        # 디버그용 디렉토리 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))  # BE/function/components/advanced
        be_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))  # BE
        self.debug_dir = os.path.join(be_dir, 'BE', 'captures', 'Real_time_Capture')
        
        # 디버그 디렉토리 생성
        try:
            if not os.path.exists(self.debug_dir):
                os.makedirs(self.debug_dir)
                
            # 디버그 출력 추가
            print(f"WindowController: 현재 디렉토리 = {current_dir}")
            print(f"WindowController: BE 디렉토리 = {be_dir}")
            print(f"WindowController: 디버그 이미지 저장 경로 = {self.debug_dir}")
            print(f"WindowController: 디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}")
            print(f"WindowController: 디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}")
            print(f"WindowController: 디렉토리 절대 경로 = {os.path.abspath(self.debug_dir)}")
        except Exception as e:
            print(f"WindowController: 디렉토리 생성 중 오류 발생 - {str(e)}")
            import traceback
            traceback.print_exc()
            self.debug_dir = None
            
        print(f"WindowController: 디버그 이미지 저장 경로 = {self.debug_dir}")
        print(f"WindowController: 디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}")
        print(f"WindowController: 디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}")
    
    def set_target_window(self, hwnd):
        """대상 윈도우를 설정합니다."""
        self.target_hwnd = hwnd
        print(f"WindowController: 대상 윈도우 설정됨 (hwnd: {hwnd})")
        return True
    
    def get_window_info(self):
        """윈도우 정보를 가져옵니다."""
        if not self.target_hwnd:
            return None
            
        try:
            # 윈도우 영역
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            window_info = {
                'x': window_rect[0],
                'y': window_rect[1],
                'width': window_rect[2] - window_rect[0],
                'height': window_rect[3] - window_rect[1]
            }
            
            # 클라이언트 영역
            client_rect = win32gui.GetClientRect(self.target_hwnd)
            client_point = win32gui.ClientToScreen(self.target_hwnd, (0, 0))
            
            # DPI 스케일링 고려
            try:
                dpi = win32gui.GetDpiForWindow(self.target_hwnd)
                scale_factor = dpi / 96.0  # 기본 DPI는 96
            except AttributeError:
                scale_factor = 1.0
            
            client_info = {
                'x': client_point[0],
                'y': client_point[1],
                'width': int(client_rect[2] * scale_factor),
                'height': int(client_rect[3] * scale_factor)
            }
            
            print(f"WindowController: 윈도우 정보 = {{'window': {window_info}, 'client': {client_info}}}")
            
            return {
                'window': window_info,
                'client': client_info
            }
            
        except Exception as e:
            print(f"WindowController: 윈도우 정보 가져오기 실패 - {e}")
            return None
    
    def get_client_rect(self):
        """클라이언트 영역의 정보를 가져옵니다."""
        if not self.target_hwnd:
            print("대상 창이 설정되지 않았습니다.")
            return None
            
        try:
            window_info = self.get_window_info()
            if not window_info:
                return None
                
            client_info = window_info['client']
            return {
                'x': client_info['x'],
                'y': client_info['y'],
                'width': client_info['width'],
                'height': client_info['height']
            }
            
        except Exception as e:
            print(f"클라이언트 영역 정보 가져오기 실패: {e}")
            return None
    
    def capture_region(self, x, y, width, height, gauge_type=None):
        """지정된 영역을 캡처합니다."""
        try:
            if not self.target_hwnd:
                print("대상 창이 설정되지 않았습니다.")
                return None

            # 창이 최소화되어 있는지 확인하고 복원
            if win32gui.IsIconic(self.target_hwnd):
                win32gui.ShowWindow(self.target_hwnd, win32con.SW_RESTORE)
            
            # 창 활성화
            try:
                current_hwnd = win32gui.GetForegroundWindow()
                if current_hwnd != self.target_hwnd:
                    self.shell.SendKeys('%')
                    win32gui.SetForegroundWindow(self.target_hwnd)
                    time.sleep(0.1)  # 창 활성화 대기
            except Exception as e:
                print(f"창 활성화 실패 (무시하고 진행): {e}")

            # 클라이언트 영역의 절대 좌표 계산
            client_rect = self.get_client_rect()
            if not client_rect:
                return None
            
            # DPI 스케일링 고려
            try:
                dpi = win32gui.GetDpiForWindow(self.target_hwnd)
                scale_factor = dpi / 96.0
            except AttributeError:
                scale_factor = 1.0
            
            # 스케일링된 좌표 계산
            scaled_x = int(x * scale_factor)
            scaled_y = int(y * scale_factor)
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            
            # 절대 좌표 계산
            abs_x = client_rect['x'] + scaled_x
            abs_y = client_rect['y'] + scaled_y
            
            # 캡처 영역이 클라이언트 영역을 벗어나는지 확인
            if (abs_x < client_rect['x'] or 
                abs_y < client_rect['y'] or 
                abs_x + scaled_width > client_rect['x'] + client_rect['width'] or 
                abs_y + scaled_height > client_rect['y'] + client_rect['height']):
                print("캡처 영역이 클라이언트 영역을 벗어남")
                print(f"캡처 영역: x={abs_x}, y={abs_y}, width={scaled_width}, height={scaled_height}")
                print(f"클라이언트 영역: x={client_rect['x']}, y={client_rect['y']}, width={client_rect['width']}, height={client_rect['height']}")
                return None
            
            # 화면 캡처
            screenshot = ImageGrab.grab(bbox=(abs_x, abs_y, abs_x + scaled_width, abs_y + scaled_height))
            img_array = np.array(screenshot)
            
            # RGB 이미지의 중앙 픽셀 색상 출력 (디버그용)
            height, width = img_array.shape[:2]
            middle_y = height // 2
            middle_x = width // 2
            rgb_color = img_array[middle_y, middle_x]
            print(f"\n캡처된 이미지 중앙 픽셀 RGB 값:")
            print(f"RGB: R={rgb_color[0]}, G={rgb_color[1]}, B={rgb_color[2]}")
            
            # BGR로 변환하여 저장
            bgr_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # BGR 이미지의 중앙 픽셀 색상 출력 (디버그용)
            bgr_color = bgr_image[middle_y, middle_x]
            print(f"BGR: B={bgr_color[0]}, G={bgr_color[1]}, R={bgr_color[2]}\n")
            
            # 이미지 저장
            try:
                # BGR로 변환하여 저장
                # 이미지 데이터 유효성 검사
                if bgr_image is None or bgr_image.size == 0:
                    print("WindowController: 이미지 데이터가 유효하지 않음")
                    return None

                try:
                    # BE/captures/Real_time_Capture 경로 계산 (한글 경로 피하기)
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    be_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
                    capture_dir = os.path.join(be_dir, 'BE', 'captures', 'Real_time_Capture')
                    
                    # 디렉토리가 없으면 생성
                    if not os.path.exists(capture_dir):
                        os.makedirs(capture_dir)
                    
                    # 파일명 설정
                    if gauge_type:
                        filename = f'capture_{gauge_type}.png'
                    else:
                        filename = f'capture_{x}_{y}.png'
                    
                    # 전체 경로
                    save_path = os.path.join(capture_dir, filename)
                    
                    print(f"WindowController: 이미지 저장 시도")
                    print(f"  - 이미지 정보:")
                    print(f"    - 데이터 타입: {bgr_image.dtype}")
                    print(f"    - 최소값: {bgr_image.min()}")
                    print(f"    - 최대값: {bgr_image.max()}")
                    print(f"    - 평균값: {bgr_image.mean()}")
                    print(f"  - 저장 경로: {save_path}")
                    print(f"  - 원본 이미지 크기: {img_array.shape}")
                    print(f"  - 저장할 이미지 크기: {bgr_image.shape}")
                    
                    # PIL을 사용하여 이미지 저장 시도
                    try:
                        from PIL import Image
                        pil_image = Image.fromarray(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB))
                        # 회전 없이 원본 그대로 저장
                        pil_image.save(save_path)
                        success = True
                    except Exception as e:
                        print(f"PIL 저장 실패: {str(e)}")
                        # OpenCV로 저장 시도 - 회전 없이 원본 그대로 저장
                        success = cv2.imwrite(str(save_path), bgr_image)
                    
                    print(f"  - 파일 저장 성공: {success}")
                    print(f"  - 파일 존재 여부: {os.path.exists(save_path)}")
                    if os.path.exists(save_path):
                        print(f"  - 파일 크기: {os.path.getsize(save_path)} bytes")
                        
                    if not success:
                        print("  - 저장 실패 원인 확인:")
                        print(f"    - 디렉토리 존재: {os.path.exists(os.path.dirname(save_path))}")
                        print(f"    - 디렉토리 쓰기 권한: {os.access(os.path.dirname(save_path), os.W_OK)}")
                        print(f"    - 전체 경로: {os.path.abspath(save_path)}")
                        
                except Exception as e:
                    print(f"WindowController: 이미지 저장 중 오류 발생 - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    success = False
            except Exception as e:
                print(f"WindowController: 이미지 저장 중 오류 발생 - {str(e)}")
                import traceback
                traceback.print_exc()
            
            return img_array if success else None
            
        except Exception as e:
            print(f"이미지 캡처 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def is_target_window_active(self):
        """대상 윈도우가 활성화되어 있는지 확인"""
        if not self.target_hwnd:
            return False
        return self.target_hwnd == win32gui.GetForegroundWindow()