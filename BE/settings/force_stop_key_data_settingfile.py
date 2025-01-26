import json
import os
from pathlib import Path
from BE.log.base_log_manager import BaseLogManager

class ForceStopKeyDataSettingFilesManager:
    """강제 중지 키 설정 파일 관리 클래스 (싱글톤)"""
    
    _instance = None
    
    @classmethod
    def instance(cls):
        """싱글톤 인스턴스 반환"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """초기화 - 싱글톤 패턴 적용"""
        if ForceStopKeyDataSettingFilesManager._instance is not None:
            raise Exception("이 클래스는 싱글톤입니다. instance() 메서드를 사용하세요.")
            
        self.base_log_manager = BaseLogManager.instance()
        
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.force_stop_key_file = Path(current_dir).resolve() / "settings" / "setting files" / "Force_Stop_key.json"
        
        # 초기 설정 로드
        self.force_stop_key = self._load_force_stop_key()
        
        ForceStopKeyDataSettingFilesManager._instance = self

    def _get_default_force_stop_key(self):
        """기본 강제 중지 키 설정 반환"""
        return {
            "type": "key_input",
            "key_code": "ESC",
            "scan_code": 1,
            "virtual_key": 27,
            "modifiers_key_flag": 0
        }

    def _load_force_stop_key(self):
        """강제 중지 키 설정 로드"""
        if self.force_stop_key_file.exists():
            try:
                with open(self.force_stop_key_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.base_log_manager.log(
                    message=f"강제 중지 키 설정 로드 중 오류 발생: {e}",
                    level="ERROR", 
                    file_name="force_stop_key_data_settingfile",
                    method_name="_load_force_stop_key",
                    print_to_terminal=True
                )
                return self._get_default_force_stop_key()
        return self._get_default_force_stop_key()

    def get_force_stop_key(self):
        """강제 중지 키 설정 반환"""
        return self.force_stop_key

    def save_force_stop_key(self, force_stop_key):
        """강제 중지 키 설정 저장"""
        try:
            # KeyboardModifier 객체를 정수로 변환
            if isinstance(force_stop_key.get('modifiers_key_flag'), object):
                force_stop_key['modifiers_key_flag'] = int(force_stop_key['modifiers_key_flag'])

            with open(self.force_stop_key_file, 'w', encoding='utf-8') as f:
                json.dump(force_stop_key, f, ensure_ascii=False, indent=4)
            self.force_stop_key = force_stop_key
            return True
        except Exception as e:
            self.base_log_manager.log(
                message=f"강제 중지 키 설정 저장 중 오류 발생: {e}",
                level="ERROR", 
                file_name="force_stop_key_data_settingfile",
                method_name="save_force_stop_key",
                print_to_terminal=True
            )
            return False
