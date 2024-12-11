import win32api
import win32con
import win32gui

class MouseHandler:
    """마우스 입력을 처리하는 클래스"""
    
    @staticmethod
    def click(x, y, button="left"):
        """마우스 클릭 실행
        
        Args:
            x (int): 클릭할 X 좌표
            y (int): 클릭할 Y 좌표
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
            
            # 현재 마우스 위치 저장
            current_x, current_y = win32api.GetCursorPos()
            
            # 마우스 이동
            win32api.SetCursorPos((x, y))
            
            # 클릭 실행
            win32api.mouse_event(down_flag, x, y, 0, 0)
            win32api.mouse_event(up_flag, x, y, 0, 0)
            
            # 원래 위치로 복귀
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