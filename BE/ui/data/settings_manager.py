import json
import os

class SettingsManager:
    def __init__(self):
        self.settings_dir = os.path.join(os.path.dirname(__file__), 'settings')
        self.advanced_settings_path = os.path.join(self.settings_dir, 'advanced_settings.json')
        
        # settings 디렉토리가 없으면 생성
        if not os.path.exists(self.settings_dir):
            os.makedirs(self.settings_dir)
    
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