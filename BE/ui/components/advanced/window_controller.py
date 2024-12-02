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
        self.debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 
                                    'captures', 'Real_time_Capture')
        
        # 디버그 디렉토리 생성
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            
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
            client_info = {
                'x': client_point[0],
                'y': client_point[1],
                'width': client_rect[2],
                'height': client_rect[3]
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
                
            abs_x = client_rect['x'] + x
            abs_y = client_rect['y'] + y
            
            # 화면 캡처
            screenshot = ImageGrab.grab(bbox=(abs_x, abs_y, abs_x + width, abs_y + height))
            img_array = np.array(screenshot)
            
            # 디버그용 이미지 저장
            if gauge_type:
                debug_path = os.path.join(self.debug_dir, f'debug_{gauge_type}.png')
            else:
                debug_path = os.path.join(self.debug_dir, f'capture_{x}_{y}.png')
                
            cv2.imwrite(debug_path, cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))
            print(f"캡처 이미지 저장됨: {debug_path}")
            
            return img_array
            
        except Exception as e:
            print(f"이미지 캡처 중 오류: {e}")
            return None
    
    def is_target_window_active(self):
        """대상 윈도우가 활성화되어 있는지 확인"""
        if not self.target_hwnd:
            return False
        return self.target_hwnd == win32gui.GetForegroundWindow()