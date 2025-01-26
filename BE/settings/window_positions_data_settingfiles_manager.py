import json
import os
from pathlib import Path
from BE.log.base_log_manager import BaseLogManager

class WindowPositionsDataSettingFilesManager:
    """윈도우 창 위치 설정 파일 관리 클래스"""

    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.window_positions_file = Path(current_dir).resolve() / "settings" / "setting files" / "window_positions_data_settingfile.json"
        
        # 초기 설정 로드
        self.window_positions = self._load_window_positions()

    def _get_default_window_positions(self):
        """기본 윈도우 위치 설정 반환"""
        return {
            "position": {
                "x": 100,
                "y": 100
            },
            "size": {
                "width": 800,
                "height": 600
            }
        }

    def _load_window_positions(self):
        """윈도우 위치 설정 파일 로드"""
        if self.window_positions_file.exists():
            try:
                with open(self.window_positions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._get_default_window_positions()
        return self._get_default_window_positions()

    def _save_window_positions(self, positions):
        """윈도우 위치 설정 저장"""
        try:
            with open(self.window_positions_file, 'w', encoding='utf-8') as f:
                json.dump(positions, f, ensure_ascii=False, indent=4)
            self.window_positions = positions
            return True
        except Exception as e:
            self.base_log_manager.log(
                message=f"윈도우 위치 설정 저장 중 오류 발생: {e}",
                level="ERROR",
                file_name="window_positions_data_settingfiles_manager",
                method_name="_save_window_positions",
                print_to_terminal=True
            )
            return False

    def get_window_positions(self):
        """윈도우 위치 설정 반환"""
        return self.window_positions

    def set_window_position(self, x, y):
        """윈도우 위치 설정"""
        current_positions = self._load_window_positions()
        current_positions["position"] = {"x": x, "y": y}
        return self._save_window_positions(current_positions)

    def set_window_size(self, width, height):
        """윈도우 크기 설정"""
        current_positions = self._load_window_positions()
        current_positions["size"] = {"width": width, "height": height}
        return self._save_window_positions(current_positions)
