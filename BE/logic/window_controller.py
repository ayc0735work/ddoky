import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import numpy as np

class WindowController:
    """윈도우 제어 및 화면 캡처를 위한 클래스"""
    
    def __init__(self):
        self.target_hwnd = None
    
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
        """지정된 영역의 화면을 캡처
        
        Args:
            x (int): 캡처 영역의 x 좌표
            y (int): 캡처 영역의 y 좌표
            width (int): 캡처 영역의 너비
            height (int): 캡처 영역의 높이
            
        Returns:
            numpy.ndarray: 캡처된 이미지 (BGR 형식)
        """
        try:
            if not self.target_hwnd:
                return None
                
            # 윈도우 DC와 메모리 DC 생성
            hwnd_dc = win32gui.GetWindowDC(self.target_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            
            # 비트맵 생성
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            
            # 화면 복사
            result = windll.user32.PrintWindow(self.target_hwnd, save_dc.GetSafeHdc(), 3)
            
            if result:
                # 지정된 영역만큼 복사
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (x, y), win32con.SRCCOPY)
                
                # 비트맵 정보 가져오기
                bmp_info = save_bitmap.GetInfo()
                bmp_str = save_bitmap.GetBitmapBits(True)
                
                # numpy 배열로 변환
                img = np.frombuffer(bmp_str, dtype='uint8')
                img.shape = (height, width, 4)  # RGBA
                img = img[:, :, :3]  # BGR로 변환
                
                # 리소스 해제
                win32gui.DeleteObject(save_bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(self.target_hwnd, hwnd_dc)
                
                return img
                
        except Exception as e:
            print(f"화면 캡처 중 오류 발생: {e}")
            
        return None 