from PySide6.QtCore import QObject, Signal

class LogicManager(QObject):
    """로직 관리를 담당하는 클래스"""
    
    # 시그널 정의
    logic_loaded = Signal(dict)  # 로직이 로드되었을 때
    logic_changed = Signal(dict)  # 현재 로직이 변경되었을 때
    
    def __init__(self, settings_manager):
        """초기화
        
        Args:
            settings_manager: 설정 관리자 인스턴스
        """
        super().__init__()
        self.settings_manager = settings_manager
        self.current_logic = None
        self.current_logic_name = None
    
    def load_logic(self, logic_name):
        """로직 로드
        
        Args:
            logic_name (str): 로드할 로직의 이름
            
        Returns:
            dict: 로드된 로직 정보
        """
        try:
            settings = self.settings_manager._load_settings()
            logics = settings.get('logics', {})
            
            if logic_name not in logics:
                return None
            
            self.current_logic = logics[logic_name]
            self.current_logic_name = logic_name
            self.logic_loaded.emit(self.current_logic)
            return self.current_logic
        except Exception as e:
            print(f"로직 로드 중 오류 발생: {e}")
            return None
    
    def get_current_logic(self):
        """현재 로직 반환
        
        Returns:
            dict: 현재 로직 정보
        """
        return self.current_logic
    
    def get_current_logic_name(self):
        """현재 로직 이름 반환
        
        Returns:
            str: 현재 로직 이름
        """
        return self.current_logic_name
    
    def get_all_logics(self):
        """모든 로직 반환
        
        Returns:
            dict: 모든 로직 정보
        """
        try:
            settings = self.settings_manager._load_settings()
            return settings.get('logics', {})
        except Exception as e:
            print(f"로직 로드 중 오류 발생: {e}")
            return {}
    
    def remove_logic(self, logic_name):
        """로직을 제거합니다.
        
        Args:
            logic_name (str): 제거할 로직의 이름
        """
        if self.current_logic_name == logic_name:
            self.current_logic = None
            self.current_logic_name = None
