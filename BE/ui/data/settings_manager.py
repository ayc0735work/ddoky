import json
import os

class SettingsManager:
    def __init__(self):
        # BE 디렉토리 경로 계산
        self.be_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.settings_path = os.path.join(self.be_dir, 'settings.json')
        self.advanced_settings_path = os.path.join(self.be_dir, 'advanced_settings.json')
        
        # settings 디렉토리가 없으면 생성
        if not os.path.exists(os.path.dirname(self.advanced_settings_path)):
            os.makedirs(os.path.dirname(self.advanced_settings_path))
        
        # 설정 파일이 없으면 기본 설정으로 생성
        if not os.path.exists(self.settings_path):
            self._create_default_settings()
    
    def _create_default_settings(self):
        """기본 설정 파일 생성"""
        default_settings = {
            "window": {
                "position": {"x": 100, "y": 100},
                "size": {"width": 900, "height": 2000}
            },
            "gauge_monitor": {
                "hp_gauge": {
                    "coordinates": {"x": 0, "y": 0, "width": 100, "height": 20}
                },
                "mp_gauge": {
                    "coordinates": {"x": 0, "y": 30, "width": 100, "height": 20}
                }
            },
            "advanced_settings": {
                "hp_threshold": 30,
                "mp_threshold": 30,
                "hp_logic": {"uuid": "", "enabled": False},
                "mp_logic": {"uuid": "", "enabled": False},
                "common_logic": None
            }
        }
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"기본 설정 파일 생성 중 오류 발생: {e}")
    
    def save_settings(self, settings):
        """설정 저장"""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
    
    def load_settings(self):
        """설정 불러오기"""
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"설정 파일이 존재하지 않음: {self.settings_path}")
                return None
        except Exception as e:
            print(f"설정 불러오기 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_advanced_settings(self, settings):
        """고급 설정 저장"""
        try:
            print(f"설정 저장 경로: {self.advanced_settings_path}")  # 디버그 출력
            with open(self.advanced_settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            print("설정 저장 완료")  # 디버그 출력
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
    
    def load_advanced_settings(self):
        """고급 설정 불러오기"""
        try:
            if os.path.exists(self.advanced_settings_path):
                print(f"설정 파일 존재: {self.advanced_settings_path}")  # 디버그 출력
                with open(self.advanced_settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    print("설정 불러오기 완료")  # 디버그 출력
                    return settings
            else:
                print("설정 파일이 존재하지 않음")  # 디버그 출력
        except Exception as e:
            print(f"설정 불러오기 중 오류 발생: {e}")
        return None