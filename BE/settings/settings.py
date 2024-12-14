import os
import json
from .settings_manager import SettingsManager

class Settings:
    """싱글톤 설정 클래스"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
            cls._instance.settings_manager = SettingsManager()
        return cls._instance
    
    def get(self, key, default=None):
        """설정값을 가져옵니다."""
        return self.settings_manager.get(key, default)
    
    def set(self, key, value):
        """설정값을 저장합니다."""
        return self.settings_manager.set(key, value)