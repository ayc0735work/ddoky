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
            
            # 이미 존재하는 로직인지 확인
            if logic_name in logics:
                # 기존 로직을 반환
                self.current_logic = logics[logic_name]
                self.current_logic_name = logic_name
                self.logic_loaded.emit(self.current_logic)
                return self.current_logic
            
            return None
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
    
    def get_all_logics(self, force=False):
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
    
    def validate_logic(self, logic_data):
        """로직 데이터 유효성 검사"""
        if not logic_data.get('name'):
            raise ValueError("로직 이름은 필수입니다.")
            
        # 중첩로직용이 아닐 경우에만 트리거 키 검사
        if not logic_data.get('is_nested', False):
            if not logic_data.get('trigger_key'):
                raise ValueError("트리거 키는 필수입니다.")
        
        if not logic_data.get('items'):
            raise ValueError("최소 하나의 동작이 필요합니다.")
            
        return True
    
    def save_logic(self, logic_id, logic_data):
        """로직 저장"""
        try:
            self.validate_logic(logic_data)
            
            # 중첩 로직인 경우 중복 생성 방지
            if logic_data.get('is_nested', False):
                existing_logics = self.get_all_logics()
                for existing_id, existing_logic in existing_logics.items():
                    if (existing_logic['name'] == logic_data['name'] and 
                        existing_logic['is_nested'] == True):
                        # 기존 로직 ID 반환
                        return True, existing_id
            
            # 새 로직 저장
            self.logics[logic_id] = logic_data
            self._save_to_file()
            # 캐시 즉시 업데이트
            self.get_all_logics(force=True)
            return True, logic_id
        except ValueError as e:
            return False, str(e)
