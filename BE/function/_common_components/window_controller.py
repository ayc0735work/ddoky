import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import numpy as np
import cv2
import os
from BE.log.base_log_manager import BaseLogManager

class WindowController:
    """윈도우 제어 및 화면 캡처를 위한 클래스"""
    
    def __init__(self):
        """초기화"""
        self.target_hwnd = None
        self.debug_counter = 0
        self.base_log_manager = BaseLogManager.instance()
        
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
            
            self.base_log_manager.log(
                message=f"디버그 이미지 저장 경로 = {self.debug_dir}",
                level="INFO",
                file_name="window_controller",
                method_name="__init__"
            )
            self.base_log_manager.log(
                message=f"디렉토리 존재 여부 = {os.path.exists(self.debug_dir)}",
                level="DEBUG", 
                file_name="window_controller",
                method_name="__init__"
            )
            self.base_log_manager.log(
                message=f"디렉토리 쓰기 권한 = {os.access(self.debug_dir, os.W_OK)}",
                level="DEBUG",
                file_name="window_controller", 
                method_name="__init__"
            )
        except Exception as e:
            self.base_log_manager.log(
                message=f"디렉토리 설정 중 오류 발생 - {str(e)}",
                level="ERROR",
                file_name="window_controller",
                method_name="__init__",
                print_to_terminal=True
            )
            self.debug_dir = None
    
    def is_target_window_active(self) -> bool:
        """대상 윈도우가 활성화되어 있는지 확인"""
        if not self.target_hwnd:
            self.base_log_manager.log(
                message="target_hwnd가 설정되지 않음",
                level="WARNING",
                file_name="window_controller",
                method_name="is_target_window_active"
            )
            return False
        active_hwnd = win32gui.GetForegroundWindow()
        self.base_log_manager.log(
            message=f"target_hwnd={self.target_hwnd}, active_hwnd={active_hwnd}",
            level="DEBUG",
            file_name="window_controller",
            method_name="is_target_window_active"
        )
        return active_hwnd == self.target_hwnd
    
    def set_target_window(self, hwnd):
        """대상 윈도우 설정"""
        self.target_hwnd = hwnd
    
    def capture_screen(self, x, y, width, height):
        """화면 캡처"""
        try:
            if not self.target_hwnd:
                self.base_log_manager.log(
                    message="대상 윈도우가 설정되지 않았습니다",
                    level="WARNING",
                    file_name="window_controller",
                    method_name="capture_screen"
                )
                return None
            
            if not self.debug_dir or not os.path.exists(self.debug_dir):
                self.base_log_manager.log(
                    message="디버그 디렉토리가 존재하지 않습니다",
                    level="WARNING",
                    file_name="window_controller",
                    method_name="capture_screen"
                )
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
            
            self.base_log_manager.log(
                message=f"윈도우 위치 = {window_rect}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            self.base_log_manager.log(
                message=f"클라이언트 영역 = {client_rect}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            self.base_log_manager.log(
                message=f"프레임 크기 = x:{frame_x}, y:{frame_y}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            self.base_log_manager.log(
                message=f"클라이언트 시작점 = x:{client_x}, y:{client_y}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            self.base_log_manager.log(
                message=f"요청된 전체화면 좌표 = x:{x}, y:{y}, width:{width}, height:{height}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            self.base_log_manager.log(
                message=f"변환된 클라이언트 좌표 = x:{capture_x}, y:{capture_y}, width:{capture_width}, height:{capture_height}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            
            # DC 및 비트맵 생성
            hwnd_dc = win32gui.GetWindowDC(self.target_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, client_rect[2], client_rect[3])
            save_dc.SelectObject(save_bitmap)
            
            # 화면 캡처
            result = windll.user32.PrintWindow(self.target_hwnd, save_dc.GetSafeHdc(), 3)
            self.base_log_manager.log(
                message=f"PrintWindow 결과 = {result}",
                level="DEBUG",
                file_name="window_controller",
                method_name="capture_screen"
            )
            
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
                        debug_path = os.path.join('BE', 'captures', 'capture_setting_img', f"capture_{self.debug_counter}.png")
                        
                        # 디렉토리가 없으면 생성
                        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
                        
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
                                        self.base_log_manager.log(
                                            message=f"디버그 이미지 저장됨 = {debug_path}",
                                            level="INFO",
                                            file_name="window_controller",
                                            method_name="capture_screen"
                                        )
                                        self.base_log_manager.log(
                                            message=f"파일 크기 = {os.path.getsize(debug_path)} bytes",
                                            level="DEBUG",
                                            file_name="window_controller",
                                            method_name="capture_screen"
                                        )
                                    else:
                                        self.base_log_manager.log(
                                            message="PIL 저장 실패",
                                            level="ERROR",
                                            file_name="window_controller",
                                            method_name="capture_screen",
                                            print_to_terminal=True
                                        )
                                except Exception as e:
                                    self.base_log_manager.log(
                                        message=f"PIL 저장 실패 - {str(e)}",
                                        level="ERROR",
                                        file_name="window_controller",
                                        method_name="capture_screen",
                                        print_to_terminal=True
                                    )
                                    success = False
                                
                                # 방법 2: OpenCV 시도 (PIL이 실패한 경우)
                                if not success:
                                    try:
                                        success = cv2.imwrite(str(debug_path), img)
                                        if success:
                                            self.base_log_manager.log(
                                                message=f"OpenCV로 이미지 저장됨 = {debug_path}",
                                                level="INFO",
                                                file_name="window_controller",
                                                method_name="capture_screen"
                                            )
                                        else:
                                            self.base_log_manager.log(
                                                message="OpenCV 저장 실패",
                                                level="ERROR",
                                                file_name="window_controller",
                                                method_name="capture_screen",
                                                print_to_terminal=True
                                            )
                                    except Exception as e:
                                        self.base_log_manager.log(
                                            message=f"OpenCV 저장 실패 - {str(e)}",
                                            level="ERROR",
                                            file_name="window_controller",
                                            method_name="capture_screen",
                                            print_to_terminal=True
                                        )
                            else:
                                self.base_log_manager.log(
                                    message=f"유효하지 않은 이미지 데이터 - shape: {img.shape if img is not None else 'None'}",
                                    level="ERROR",
                                    file_name="window_controller",
                                    method_name="capture_screen",
                                    print_to_terminal=True
                                )
                        except Exception as e:
                            self.base_log_manager.log(
                                message=f"이미지 저장 실패 - {str(e)}",
                                level="ERROR",
                                file_name="window_controller",
                                method_name="capture_screen",
                                print_to_terminal=True
                            )
                            import traceback
                            traceback.print_exc()
                        
                        # 이미지 정보 출력
                        self.base_log_manager.log(
                            message=f"이미지 shape = {img.shape}",
                            level="DEBUG",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        self.base_log_manager.log(
                            message=f"이미지 dtype = {img.dtype}",
                            level="DEBUG",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        self.base_log_manager.log(
                            message=f"이미지 min/max = {np.min(img)}/{np.max(img)}",
                            level="DEBUG",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        
                        # 리소스 해제
                        win32gui.DeleteObject(save_bitmap.GetHandle())
                        save_dc.DeleteDC()
                        mfc_dc.DeleteDC()
                        win32gui.ReleaseDC(self.target_hwnd, hwnd_dc)
                        
                        return img
                    else:
                        self.base_log_manager.log(
                            message="캡처 영역이 클라이언트 영역을 벗어났습니다",
                            level="WARNING",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        self.base_log_manager.log(
                            message=f"요청 영역: ({capture_x}, {capture_y}, {capture_width}, {capture_height})",
                            level="DEBUG",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        self.base_log_manager.log(
                            message=f"클라이언트 영역: (0, 0, {client_rect[2]}, {client_rect[3]})",
                            level="DEBUG",
                            file_name="window_controller",
                            method_name="capture_screen"
                        )
                        return None
                except Exception as e:
                    self.base_log_manager.log(
                        message=f"이미지 처리 중 오류 발생 - {str(e)}",
                        level="ERROR",
                        file_name="window_controller",
                        method_name="capture_screen",
                        print_to_terminal=True
                    )
                    import traceback
                    traceback.print_exc()
                    return None
            else:
                self.base_log_manager.log(
                    message="PrintWindow 실패",
                    level="ERROR",
                    file_name="window_controller",
                    method_name="capture_screen",
                    print_to_terminal=True
                )
                return None
        except Exception as e:
            self.base_log_manager.log(
                message=f"캡처 중 오류 발생 - {str(e)}",
                level="ERROR",
                file_name="window_controller",
                method_name="capture_screen",
                print_to_terminal=True
            )
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

        self.base_log_manager.log(
            message=f"클라이언트 영역 = {client_rect}",
            level="DEBUG",
            file_name="window_controller",
            method_name="capture_window_region"
        )
        self.base_log_manager.log(
            message=f"캡처 좌표 = x:{client_x}, y:{client_y}, width:{width}, height:{height}",
            level="DEBUG",
            file_name="window_controller",
            method_name="capture_window_region"
        )

        # 캡처할 영역이 클라이언트 영역을 벗어나는지 확인
        if (client_x < 0 or client_y < 0 or 
            client_x + width > client_rect[2] or 
            client_y + height > client_rect[3]):
            self.base_log_manager.log(
                message="캡처 영역이 클라이언트 영역을 벗어남",
                level="WARNING",
                file_name="window_controller",
                method_name="capture_window_region"
            )
            return None

        # 윈도우 캡처
        wDC = win32gui.GetWindowDC(self.target_hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, width, height)
        cDC.SelectObject(dataBitMap)
        
        result = win32gui.PrintWindow(self.target_hwnd, cDC.GetSafeHdc(), 2)
        self.base_log_manager.log(
            message=f"PrintWindow 결과 = {result}",
            level="DEBUG",
            file_name="window_controller",
            method_name="capture_window_region"
        )

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
                self.base_log_manager.log(
                    message=f"디버그 이미지 저장됨 = {debug_path}",
                    level="INFO",
                    file_name="window_controller",
                    method_name="capture_window_region"
                )
                self.base_log_manager.log(
                    message=f"파일 크기 = {file_size} bytes",
                    level="DEBUG",
                    file_name="window_controller",
                    method_name="capture_window_region"
                )
                self.base_log_manager.log(
                    message=f"이미지 shape = {img.shape}",
                    level="DEBUG",
                    file_name="window_controller",
                    method_name="capture_window_region"
                )
                self.base_log_manager.log(
                    message=f"이미지 dtype = {img.dtype}",
                    level="DEBUG",
                    file_name="window_controller",
                    method_name="capture_window_region"
                )
                self.base_log_manager.log(
                    message=f"이미지 min/max = {img.min()}/{img.max()}",
                    level="DEBUG",
                    file_name="window_controller",
                    method_name="capture_window_region"
                )
            except Exception as e:
                self.base_log_manager.log(
                    message=f"디버그 이미지 저장 실패: {str(e)}",
                    level="ERROR",
                    file_name="window_controller",
                    method_name="capture_window_region",
                    print_to_terminal=True
                )

        # 리소스 해제
        win32gui.DeleteObject(dataBitMap.GetHandle())
        cDC.DeleteDC()
        dcObj.DeleteDC()
        win32gui.ReleaseDC(self.target_hwnd, wDC)

        return img if result == 1 else None 