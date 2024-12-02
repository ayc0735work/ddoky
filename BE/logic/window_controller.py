import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import numpy as np
import cv2
import os

class WindowController:
    """윈도우 제어 및 화면 캡처를 위한 클래스"""
    
    def __init__(self):
        """초기화"""
        self.target_hwnd = None
        self.debug_counter = 0
        
        try:
            # BE 폴더 경로 찾기
            current_dir = os.path.dirname(os.path.abspath(__file__))  # BE/logic
            be_dir = os.path.dirname(os.path.dirname(current_dir))    # BE
            
            # 디버그 이미지 저장 경로 설정 (BE/captures/Real_time_Capture)
            self.debug_dir = os.path.join(be_dir, 'BE', 'captures', 'Real_time_Capture')
            
            # 디렉토리 구조 생성
            if not os.path.exists(os.path.join(be_dir, 'BE')):
                os.makedirs(os.path.join(be_dir, 'BE'), exist_ok=True)
            if not os.path.exists(os.path.join(be_dir, 'BE', 'captures')):
                os.makedirs(os.path.join(be_dir, 'BE', 'captures'), exist_ok=True)
            if not os.path.exists(self.debug_dir):
                os.makedirs(self.debug_dir, exist_ok=True)
            
            print(f"WindowController: 디버그 이미지 저장 경로 = {self.debug_dir}")
            print(f"WindowController: 디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}")
            print(f"WindowController: 디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}")
        except Exception as e:
            print(f"WindowController: 디렉토리 설정 중 오류 발생 - {str(e)}")
            self.debug_dir = None
    
    def is_target_window_active(self) -> bool:
        """대상 윈도우가 활성화되어 있는지 확인"""
        if not self.target_hwnd:
            print("WindowController: target_hwnd가 설정되지 않음")
            return False
        active_hwnd = win32gui.GetForegroundWindow()
        print(f"WindowController: target_hwnd={self.target_hwnd}, active_hwnd={active_hwnd}")
        return active_hwnd == self.target_hwnd
    
    def set_target_window(self, hwnd):
        """대상 윈도우 설정"""
        self.target_hwnd = hwnd
    
    def capture_screen(self, x, y, width, height):
        """화면 캡처"""
        try:
            if not self.target_hwnd:
                print("WindowController: 대상 윈도우가 설정되지 않았습니다")
                return None
            
            if not self.debug_dir or not os.path.exists(self.debug_dir):
                print("WindowController: 디버그 디렉토리가 존재하지 않습니다")
                return None
            
            # 윈도우 정보 가져오기
            window_rect = win32gui.GetWindowRect(self.target_hwnd)
            client_rect = win32gui.GetClientRect(self.target_hwnd)
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]
            
            print(f"WindowController: 윈도우 위치 = {window_rect}")
            print(f"WindowController: 클라이언트 영역 = {client_rect}")
            print(f"WindowController: 캡처 영역 = x:{x}, y:{y}, width:{width}, height:{height}")
            
            # DC 및 비트맵 생성
            hwnd_dc = win32gui.GetWindowDC(self.target_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, window_width, window_height)
            save_dc.SelectObject(save_bitmap)
            
            # 화면 캡처
            result = windll.user32.PrintWindow(self.target_hwnd, save_dc.GetSafeHdc(), 3)
            print(f"WindowController: PrintWindow 결과 = {result}")
            
            if result:
                try:
                    # 전체 이미지를 numpy 배열로 변환
                    bmp_str = save_bitmap.GetBitmapBits(True)
                    full_img = np.frombuffer(bmp_str, dtype='uint8')
                    full_img.shape = (window_height, window_width, 4)
                    full_img = full_img[:, :, :3]  # BGR로 변환
                    
                    # 지정된 영역 추출
                    if x >= 0 and y >= 0 and x + width <= window_width and y + height <= window_height:
                        img = full_img[y:y+height, x:x+width].copy()  # 메모리 연속성을 위해 copy() 사용
                        
                        # 디버그: 캡처된 이미지 저장
                        self.debug_counter += 1
                        debug_path = os.path.join(self.debug_dir, f"capture_{self.debug_counter}.png")
                        
                        # 이미지 저장 시도
                        try:
                            # 이미지가 유효한지 확인
                            if img is not None and img.size > 0 and len(img.shape) == 3:
                                # 이미지 데이터가 연속적인지 확인
                                if not img.flags['C_CONTIGUOUS']:
                                    img = np.ascontiguousarray(img)
                                
                                success = cv2.imwrite(debug_path, img)
                                if success and os.path.exists(debug_path):
                                    print(f"WindowController: 디버그 이미지 저장됨 = {debug_path}")
                                    print(f"WindowController: 파일 크기 = {os.path.getsize(debug_path)} bytes")
                                else:
                                    print(f"WindowController: 이미지 저장 실패 - cv2.imwrite 반환값: {success}")
                            else:
                                print(f"WindowController: 유효하지 않은 이미지 데이터 - shape: {img.shape if img is not None else 'None'}")
                        except Exception as e:
                            print(f"WindowController: 이미지 저장 실패 - {str(e)}")
                            import traceback
                            traceback.print_exc()
                        
                        # 이미지 정보 출력
                        print(f"WindowController: 이미지 shape = {img.shape}")
                        print(f"WindowController: 이미지 dtype = {img.dtype}")
                        print(f"WindowController: 이미지 min/max = {np.min(img)}/{np.max(img)}")
                        
                        # 리소스 해제
                        win32gui.DeleteObject(save_bitmap.GetHandle())
                        save_dc.DeleteDC()
                        mfc_dc.DeleteDC()
                        win32gui.ReleaseDC(self.target_hwnd, hwnd_dc)
                        
                        return img
                    else:
                        print("WindowController: 캡처 영역이 윈도우 범위를 벗어났습니다")
                        return None
                except Exception as e:
                    print(f"WindowController: 이미지 처리 중 오류 발생 - {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return None
            else:
                print("WindowController: PrintWindow 실패")
                return None
        except Exception as e:
            print(f"WindowController: 캡처 중 오류 발생 - {str(e)}")
            import traceback
            traceback.print_exc()
            return None 