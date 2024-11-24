import json
import os
from pathlib import Path

class SettingsManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self):
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_file = Path(current_dir) / "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """설정 파일 로드"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._get_default_settings()
        return self._get_default_settings()
    
    def _save_settings(self):
        """설정 파일 저장"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
    
    def _get_default_settings(self):
        """기본 설정값 반환"""
        return {
            "window": {
                "position": {
                    "x": 100,
                    "y": 100
                },
                "size": {
                    "width": 800,
                    "height": 600
                }
            }
        }
    
    def get_window_settings(self):
        """윈도우 설정 반환"""
        return self.settings.get("window", self._get_default_settings()["window"])
    
    def set_window_position(self, x, y):
        """윈도우 위치 설정"""
        # 현재 설정 파일의 최신 내용을 로드
        current_settings = self._load_settings()
        
        # window 설정 업데이트
        current_settings.setdefault("window", {})["position"] = {"x": x, "y": y}
        self.settings = current_settings
        
        # 업데이트된 설정 저장
        self._save_settings()
    
    def set_window_size(self, width, height):
        """윈도우 크기 설정"""
        # 현재 설정 파일의 최신 내용을 로드
        current_settings = self._load_settings()
        
        # window 설정 업데이트
        current_settings.setdefault("window", {})["size"] = {"width": width, "height": height}
        self.settings = current_settings
        
        # 업데이트된 설정 저장
        self._save_settings()
