from PySide6.QtCore import QObject, QTimer
from .advanced_widget import AdvancedWidget
from .gauge_monitor import GaugeMonitor
from BE.logic.logic_executor import LogicExecutor
import time
import os
import json
from BE.settings.settings import Settings

class AdvancedController(QObject):
    def __init__(self, process_manager, logic_manager, parent=None):
        super().__init__(parent)
        self.widget = AdvancedWidget()
        self.gauge_monitor = GaugeMonitor()
        self.logic_executor = LogicExecutor(process_manager, logic_manager)
        
        # 모니터링 타이머 설정
        self.monitor_timer = QTimer()
        self.monitor_timer.setInterval(500000000)
        self.monitor_timer.timeout.connect(self.gauge_monitor.capture_and_analyze)
        
        # 게이지 분석 결과 시그널 연결
        self.gauge_monitor.gauge_analyzed.connect(self._handle_gauge_analysis)
        
        # 실행 중인 로직 정보
        self.executing_logic = None
        self.last_execution_time = 0
        
        # 모니터링 활성화 여부
        self.is_monitoring_enabled = False
    
    def set_monitoring_enabled(self, enabled: bool):
        """로직 동작 체크박스 상태에 따른 모니터링 설정"""
        self.is_monitoring_enabled = enabled
        if enabled:
            self.monitor_timer.start()
        else:
            self.monitor_timer.stop()
    
    def _handle_gauge_analysis(self, type_, ratio):
        """게이지 분석 결과 처리"""
        if not self.is_monitoring_enabled:
            return
        
        current_time = time.time()
        if current_time - self.last_execution_time < 3:
            return
        
        # settings.json에서 설정 로드
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        settings_path = os.path.join(base_path, 'settings', 'setting files', 'settings.json')
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                advanced_settings = settings.get('advanced_settings', {})
                hp_threshold = advanced_settings.get('hp_threshold', 24)
                mp_threshold = advanced_settings.get('mp_threshold', 24)
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {str(e)}")
            hp_threshold = 24
            mp_threshold = 24
        
        # 공통 로직 체크
        if (self.widget.common_logic_checkbox.isChecked() and 
            self.widget.common_selected_logic):
            print(f"공통 로직 체크 - {type_} 게이지: {ratio}%, 기준값: {hp_threshold if type_=='hp' else mp_threshold}%")
            if ((type_ == 'hp' and ratio < hp_threshold) or
                (type_ == 'mp' and ratio < mp_threshold)):
                print("공통 로직 실행")
                self.logic_executor.selected_logic = self.widget.common_selected_logic
                self.logic_executor._execute_next_step()
                self.last_execution_time = current_time
                return
        
        # 개별 로직 체크
        if type_ == 'hp':
            print(f"HP 로직 체크 - 게이지: {ratio}%, 기준값: {hp_threshold}%")
            if (self.widget.hp_logic_checkbox.isChecked() and 
                self.widget.hp_selected_logic and 
                ratio < hp_threshold):
                print("HP 회복 로직 실행")
                self.logic_executor.selected_logic = self.widget.hp_selected_logic
                self.logic_executor._execute_next_step()
                self.last_execution_time = current_time
                
        elif type_ == 'mp':
            print(f"MP 로직 체크 - 게이지: {ratio}%, 기준값: {mp_threshold}%")
            if (self.widget.mp_logic_checkbox.isChecked() and 
                self.widget.mp_selected_logic and 
                ratio < mp_threshold):
                print("MP 회복 로직 실행")
                self.logic_executor.selected_logic = self.widget.mp_selected_logic
                self.logic_executor._execute_next_step()
                self.last_execution_time = current_time
    
    def set_target_process(self, process_info):
        """대상 프로세스 설정"""
        self.gauge_monitor.set_target_process(process_info)
    
    def initialize(self):
        settings = Settings()
        recovery_enabled = settings.get("recovery_detection_enabled", False)
        self.widget.recovery_detection_checkbox.setChecked(recovery_enabled)