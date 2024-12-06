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
            
            # 윈도우 프레임 크기 계산
            frame_x = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
            frame_y = (window_rect[3] - window_rect[1]) - client_rect[3] - frame_x
            
            # 클라이언트 영역의 실제 좌표 계산
            client_x = window_rect[0] + frame_x
            client_y = window_rect[1] + frame_y
            
            # 전체 화면 좌표를 클라이언트 영역 좌표로 변환
            capture_x = x - client_x
            capture_y = y - client_y
            capture_width = width
            capture_height = height
            
            print(f"WindowController: 윈도우 위치 = {window_rect}")
            print(f"WindowController: 클라이언트 영역 = {client_rect}")
            print(f"WindowController: 프레임 크기 = x:{frame_x}, y:{frame_y}")
            print(f"WindowController: 클라이언트 시작점 = x:{client_x}, y:{client_y}")
            print(f"WindowController: 요청된 전체화면 좌표 = x:{x}, y:{y}, width:{width}, height:{height}")
            print(f"WindowController: 변환된 클라이언트 좌표 = x:{capture_x}, y:{capture_y}, width:{capture_width}, height:{capture_height}")
            
            # DC 및 비트맵 생성
            hwnd_dc = win32gui.GetWindowDC(self.target_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, client_rect[2], client_rect[3])
            save_dc.SelectObject(save_bitmap)
            
            # 화면 캡처
            result = windll.user32.PrintWindow(self.target_hwnd, save_dc.GetSafeHdc(), 3)
            print(f"WindowController: PrintWindow 결과 = {result}")
            
            if result:
                try:
                    # 전체 이미지를 numpy 배열로 변환
                    bmp_str = save_bitmap.GetBitmapBits(True)
                    full_img = np.frombuffer(bmp_str, dtype='uint8')
                    full_img.shape = (client_rect[3], client_rect[2], 4)
                    full_img = full_img[:, :, :3]  # BGR로 변환
                    
                    # 지정된 영역 추출
                    if (capture_x >= 0 and capture_y >= 0 and 
                        capture_x + capture_width <= client_rect[2] and 
                        capture_y + capture_height <= client_rect[3]):
                        
                        img = full_img[capture_y:capture_y+capture_height, 
                                     capture_x:capture_x+capture_width].copy()
                        
                        # 디버그: 캡처된 이미지 저장
                        self.debug_counter += 1
                        debug_path = os.path.join(self.debug_dir, f"capture_{self.debug_counter}.png")
                        
                        # 이미지 저장 시도
                        try:
                            if img is not None and img.size > 0 and len(img.shape) == 3:
                                if not img.flags['C_CONTIGUOUS']:
                                    img = np.ascontiguousarray(img)
                                
                                # 방법 1: PIL 사용
                                try:
                                    from PIL import Image
                                    # BGR에서 RGB로 변환
                                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                    pil_img = Image.fromarray(rgb_img)
                                    pil_img.save(debug_path)
                                    success = os.path.exists(debug_path)
                                    if success:
                                        print(f"WindowController: 디버그 이미지 저장됨 = {debug_path}")
                                        print(f"WindowController: 파일 크기 = {os.path.getsize(debug_path)} bytes")
                                    else:
                                        print(f"WindowController: PIL 저장 실패")
                                except Exception as e:
                                    print(f"WindowController: PIL 저장 실패 - {str(e)}")
                                    success = False
                                
                                # 방법 2: OpenCV 시도 (PIL이 실패한 경우)
                                if not success:
                                    try:
                                        success = cv2.imwrite(str(debug_path), img)
                                        if success:
                                            print(f"WindowController: OpenCV로 이미지 저장됨 = {debug_path}")
                                        else:
                                            print("WindowController: OpenCV 저장 실패")
                                    except Exception as e:
                                        print(f"WindowController: OpenCV 저장 실패 - {str(e)}")
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
                        print("WindowController: 캡처 영역이 클라이언트 영역을 벗어났습니다")
                        print(f"요청 영역: ({capture_x}, {capture_y}, {capture_width}, {capture_height})")
                        print(f"클라이언트 영역: (0, 0, {client_rect[2]}, {client_rect[3]})")
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

    def capture_window_region(self, x, y, width, height):
        if not self.is_window_active():
            return None

        # 클라이언트 영역 크기 확인
        client_rect = win32gui.GetClientRect(self.target_hwnd)
        
        # 입력받은 좌표는 이미 클라이언트 좌표이므로 그대로 사용
        client_x = x
        client_y = y

        self.log_debug(f"클라이언트 영역 = {client_rect}")
        self.log_debug(f"캡처 좌표 = x:{client_x}, y:{client_y}, width:{width}, height:{height}")

        # 캡처할 영역이 클라이언트 영역을 벗어나는지 확인
        if (client_x < 0 or client_y < 0 or 
            client_x + width > client_rect[2] or 
            client_y + height > client_rect[3]):
            self.log_debug("캡처 영역이 클라이언트 영역을 벗어남")
            return None

        # 윈도우 캡처
        wDC = win32gui.GetWindowDC(self.target_hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
        cDC.SelectObject(dataBitMap)
        
        result = win32gui.PrintWindow(self.target_hwnd, cDC.GetSafeHdc(), 2)
        self.log_debug(f"PrintWindow 결과 = {result}")

        if result == 1:
            cDC.BitBlt((0, 0), (width, height), dcObj, (client_x, client_y), win32con.SRCCOPY)
            
            # 비트맵을 numpy 배열로 변환
            bmpinfo = dataBitMap.GetInfo()
            bmpstr = dataBitMap.GetBitmapBits(True)
            img = np.frombuffer(bmpstr, dtype=np.uint8)
            img = img.reshape((height, width, 4))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 디버그용 이미지 저장
            debug_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'captures', 'Real_time_Capture', f'capture_{self.capture_count}.png')
            self.capture_count += 1
            
            try:
                cv2.imwrite(debug_path, img)
                file_size = os.path.getsize(debug_path)
                self.log_debug(f"디버그 이미지 저장됨 = {debug_path}")
                self.log_debug(f"파일 크기 = {file_size} bytes")
                self.log_debug(f"이미지 shape = {img.shape}")
                self.log_debug(f"이미지 dtype = {img.dtype}")
                self.log_debug(f"이미지 min/max = {img.min()}/{img.max()}")
            except Exception as e:
                self.log_debug(f"디버그 이미지 저장 실패: {str(e)}")

        # 리소스 해제
        win32gui.DeleteObject(dataBitMap.GetHandle())
        cDC.DeleteDC()
        dcObj.DeleteDC()
        win32gui.ReleaseDC(self.target_hwnd, wDC)

        return img if result == 1 else None 