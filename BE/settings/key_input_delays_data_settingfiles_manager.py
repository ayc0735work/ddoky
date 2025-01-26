import json
import os
from pathlib import Path
from BE.log.base_log_manager import BaseLogManager

class KeyInputDelaysDataSettingFilesManager:
    """키 입력 딜레이 설정 파일 관리 클래스"""

    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.key_input_delays_data_file = Path(current_dir).resolve() / "settings" / "setting files" / "key_input_delays_data.json"
        
        # 초기 설정 로드
        self.key_input_delays_data = self._load_key_input_delays_data()

    def _get_default_key_input_delays_data(self):
        """기본 키 딜레이 설정 반환"""
        return {
            "press": 0.0192,
            "release": 0.0,
            "mouse_input": 0.025,
            "default": 0.02
        }

    def _load_key_input_delays_data(self):
        """키 딜레이 설정 파일 로드"""
        try:
            with open(self.key_input_delays_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            default_delays = self._get_default_key_input_delays_data()
            self.save_key_input_delays_data(default_delays)
            return default_delays

    def get_key_input_delays_data(self):
        """키 딜레이 설정 반환"""
        return self.key_input_delays_data

    def save_key_input_delays_data(self, key_input_delays_data):
        """키 딜레이 설정 저장"""
        try:
            with open(self.key_input_delays_data_file, 'w', encoding='utf-8') as f:
                json.dump(key_input_delays_data, f, indent=4)
            self.key_input_delays_data = key_input_delays_data
            return True
        except Exception as e:
            self.base_log_manager.log(
                message=f"키 딜레이 설정 저장 중 오류 발생: {e}",
                level="ERROR",
                file_name="key_input_delays_data_settingfiles_manager",
                method_name="save_key_input_delays_data",
                print_to_terminal=True
            )
            return False
