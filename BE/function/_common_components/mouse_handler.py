import win32api
import win32con
import win32gui
import time

class MouseHandler:
    """마우스 입력을 처리하는 클래스"""
    
    @staticmethod
    def click(x, y, button="left", hwnd=None, x_ratio=None, y_ratio=None):
        """마우스 클릭 실행
        
        Args:
            x (int): 클릭할 X 좌표 (클라이언트 영역 내 상대 좌표)
            y (int): 클릭할 Y 좌표 (클라이언트 영역 내 상대 좌표)
            button (str): 마우스 버튼 ("left", "right", "middle")
            hwnd: 대상 윈도우 핸들 (None이면 절대 좌표 사용)
            x_ratio (float): X 좌표 비율 (0.0 ~ 1.0)
            y_ratio (float): Y 좌표 비율 (0.0 ~ 1.0)
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 버튼에 따른 이벤트 플래그 설정
            if button == "right":
                down_flag = win32con.MOUSEEVENTF_RIGHTDOWN
                up_flag = win32con.MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                down_flag = win32con.MOUSEEVENTF_MIDDLEDOWN
                up_flag = win32con.MOUSEEVENTF_MIDDLEUP
            else:  # left
                down_flag = win32con.MOUSEEVENTF_LEFTDOWN
                up_flag = win32con.MOUSEEVENTF_LEFTUP
            
            # 현재 마우스 위치 저장
            current_x, current_y = win32api.GetCursorPos()
            
            # 윈도우 핸들이 제공된 경우 클라이언트 영역 기준으로 계산
            if hwnd:
                try:
                    # 클라이언트 영역 정보 가져오기
                    client_rect = win32gui.GetClientRect(hwnd)
                    client_width = client_rect[2]
                    client_height = client_rect[3]
                    
                    # 클라이언트 영역의 화면 좌표 얻기
                    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
                    client_x = client_point[0]
                    client_y = client_point[1]
                    
                    # DPI 스케일링 고려
                    try:
                        dpi = win32gui.GetDpiForWindow(hwnd)
                        scale_factor = dpi / 96.0
                    except AttributeError:
                        scale_factor = 1.0
                    
                    # 비율이 제공된 경우 비율 사용, 아니면 상대 좌표 사용
                    if x_ratio is not None and y_ratio is not None:
                        screen_x = client_x + int(client_width * x_ratio)
                        screen_y = client_y + int(client_height * y_ratio)
                    else:
                        screen_x = client_x + int(x * scale_factor)
                        screen_y = client_y + int(y * scale_factor)
                    
                    print(f"마우스 클릭 좌표 계산:")
                    print(f"  클라이언트 영역: {client_width}x{client_height}")
                    print(f"  클라이언트 시작점: ({client_x}, {client_y})")
                    print(f"  DPI 스케일: {scale_factor}")
                    if x_ratio is not None:
                        print(f"  비율: ({x_ratio:.3f}, {y_ratio:.3f})")
                    print(f"  상대 좌표: ({x}, {y})")
                    print(f"  화면 좌표: ({screen_x}, {screen_y})")
                
                except Exception as e:
                    print(f"클라이언트 영역 계산 중 오류: {str(e)}")
                    return False
            else:
                # 윈도우 핸들이 없는 경우 절대 좌표 사용
                screen_x = x
                screen_y = y
            
            # Settings에서 마우스 입력 지연시간 가져오기
            from BE.settings.settings_singleton import Settings
            settings = Settings()
            delays = settings.get('key_delays', {})
            
            # 기본값 설정
            DEFAULT_DELAY = 0.0245
            mouse_delay = DEFAULT_DELAY
            
            # 설정에서 값을 가져오되, 없으면 기본값 사용
            if isinstance(delays, dict):
                mouse_delay = delays.get('mouse_input', DEFAULT_DELAY)
            
            # 잠시 대기 후 마우스 이동 및 클릭 
            time.sleep(mouse_delay)
            win32api.SetCursorPos((screen_x, screen_y))
            
            # 클릭 이벤트 처리
            win32api.mouse_event(down_flag | win32con.MOUSEEVENTF_ABSOLUTE, 0, 0, 0, 0)
            win32api.mouse_event(up_flag | win32con.MOUSEEVENTF_ABSOLUTE, 0, 0, 0, 0)
            
            # 잠시 대기 후 원래 위치로 복귀
            time.sleep(mouse_delay)
            win32api.SetCursorPos((current_x, current_y))
            
            return True
            
        except Exception as e:
            print(f"마우스 클릭 실행 중 오류 발생: {str(e)}")
            return False
    
    @staticmethod
    def move(x, y):
        """마우스 이동
        
        Args:
            x (int): 이동할 X 좌표
            y (int): 이동할 Y 좌표
            
        Returns:
            bool: 성공 여부
        """
        try:
            win32api.SetCursorPos((x, y))
            return True
        except Exception as e:
            print(f"마우스 이동 중 오류 발생: {str(e)}")
            return False
    
    @staticmethod
    def drag(start_x, start_y, end_x, end_y, button="left"):
        """마우스 드래그
        
        Args:
            start_x (int): 시작 X 좌표
            start_y (int): 시작 Y 좌표
            end_x (int): 끝 X 좌표
            end_y (int): 끝 Y 좌표
            button (str): 마우스 버튼 ("left", "right", "middle")
            
        Returns:
            bool: 성공 여부
        """
        try:
            # 버튼에 따른 이벤트 플래그 설정
            if button == "right":
                down_flag = win32con.MOUSEEVENTF_RIGHTDOWN
                up_flag = win32con.MOUSEEVENTF_RIGHTUP
            elif button == "middle":
                down_flag = win32con.MOUSEEVENTF_MIDDLEDOWN
                up_flag = win32con.MOUSEEVENTF_MIDDLEUP
            else:  # left
                down_flag = win32con.MOUSEEVENTF_LEFTDOWN
                up_flag = win32con.MOUSEEVENTF_LEFTUP
            
            # 시작 위치로 이동
            win32api.SetCursorPos((start_x, start_y))
            
            # 버튼 누르기
            win32api.mouse_event(down_flag, start_x, start_y, 0, 0)
            
            # 끝 위치로 이동
            win32api.SetCursorPos((end_x, end_y))
            
            # 버튼 떼기
            win32api.mouse_event(up_flag, end_x, end_y, 0, 0)
            
            return True
            
        except Exception as e:
            print(f"마우스 드래그 중 오류 발생: {str(e)}")
            return False