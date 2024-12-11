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
        """로직 저장
        
        Args:
            logic_id (str): 저장할 로직의 ID
            logic_data (dict): 저장할 로직 데이터
            
        Returns:
            tuple: (성공 여부, 로직 ID 또는 에러 메시지)
        """
        try:
            print(f"[DEBUG] LogicManager.save_logic 시작 - logic_id: {logic_id}")
            self.validate_logic(logic_data)
            
            settings = self.settings_manager._load_settings()
            logics = settings.get('logics', {})
            
            # 이름 중복 검사 (중첩 로직은 제외)
            logic_name = logic_data.get('name')
            if not logic_data.get('is_nested', False):
                for existing_id, existing_logic in logics.items():
                    if (existing_logic['name'] == logic_name and 
                        existing_id != logic_id and  # 자기 자신은 제외
                        not existing_logic.get('is_nested', False)):  # 중첩 로직은 제외
                        print(f"[DEBUG] 이름 중복 발견: {logic_name}")
                        return False, "동일한 이름의 로직이 이미 존재합니다."
            
            # 중첩 로직인 경우 중복 생성 방지 및 원본 ID 유지
            if logic_data.get('is_nested', False):
                print(f"[DEBUG] 중첩 로직 처리 시작 - 이름: {logic_name}")
                # 새 로직 저장
                if not logic_id:  # 새 로직인 경우
                    print(f"[DEBUG] 새 로직 저장 - ID: {logic_id}")
                    logics[logic_id] = logic_data
                    settings['logics'] = logics
                    self.settings_manager._save_settings(settings)
                    return True, logic_id
                
                # 기존 로직 업데이트
                print(f"[DEBUG] 기존 로직 업데이트 - ID: {logic_id}")
                logics[logic_id] = logic_data
                settings['logics'] = logics
                self.settings_manager._save_settings(settings)
                return True, logic_id
            
            # 새 로직 저장 또는 기존 로직 업데이트
            print(f"[DEBUG] 일반 로직 저장 처리 시작")
            if logic_id in logics:  # 기존 로직 업데이트
                print(f"[DEBUG] 기존 로직 업데이트 - ID: {logic_id}")
                logics[logic_id] = logic_data
            else:  # 새 로직 저장
                print(f"[DEBUG] 새 로직 저장 - ID: {logic_id}")
                # 이름 중복 한번 더 검사
                for existing_logic in logics.values():
                    if (existing_logic['name'] == logic_name and 
                        not existing_logic.get('is_nested', False)):
                        print(f"[DEBUG] 새 로직 저장 시 이름 중복 발견: {logic_name}")
                        return False, "동일한 이름의 로직이 이미 존재합니다."
                logics[logic_id] = logic_data
            
            settings['logics'] = logics
            print(f"[DEBUG] settings_manager._save_settings 호출 전")
            self.settings_manager._save_settings(settings)
            print(f"[DEBUG] settings_manager._save_settings 호출 후")
            
            # 현재 로직 업데이트
            if self.current_logic_name == logic_name:
                self.current_logic = logic_data
                self.logic_changed.emit(self.current_logic)
            
            print(f"[DEBUG] LogicManager.save_logic 완료 - ID: {logic_id}")
            return True, logic_id
            
        except ValueError as e:
            print(f"[DEBUG] LogicManager.save_logic 에러 발생: {str(e)}")
            return False, str(e)
    
    def __del__(self):
        pass
