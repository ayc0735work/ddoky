from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, 
                               QHBoxLayout, QCheckBox, QSlider, QSpinBox, QPushButton, QProgressBar, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QImage
import os
import json
import cv2
import numpy as np
from ...constants.styles import (FRAME_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import (ADVANCED_FRAME_WIDTH, ADVANCED_SECTION_HEIGHT,
                                   DEFAULT_RECOVERY_THRESHOLD, MIDDLE_SPACE)
from BE.ui.components.logic_maker.logic_selector_dialog import LogicSelectorDialog
from .compare_area_dialog import CompareAreaDialog
from ...data.settings_manager import SettingsManager
from .gauge_monitor import GaugeMonitor

class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSuffix(" / 100")
        self.setRange(0, 100)
        self.setValue(DEFAULT_RECOVERY_THRESHOLD)
        self.setFixedWidth(80)
        
        # 라인에딧의 선택 가능 범위를 제한
        self.lineEdit().selectionChanged.connect(self._limit_selection)
    
    def _limit_selection(self):
        # 현재 선택된 텍스트 범위
        start = self.lineEdit().selectionStart()
        end = self.lineEdit().selectionEnd()
        
        # 숫자 부분의 길이
        num_length = len(str(self.value()))
        
        # 선택 범위가 숫자 부분을 벗어나면 선택을 제한
        if end > num_length:
            self.lineEdit().setSelection(start, num_length)
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # 텍스트 선택을 지우고 커서를 숫자 끝으로 이동
        self.lineEdit().deselect()
        self.lineEdit().setCursorPosition(len(str(self.value())))
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # suffix 부분을 클릭한 경우 커서를 숫자 끝으로 이동
        cursor_pos = self.lineEdit().cursorPosition()
        if cursor_pos > len(str(self.value())):
            self.lineEdit().setCursorPosition(len(str(self.value())))

class AdvancedWidget(QWidget):
    """고급 기능을 위한 위젯"""
    
    # 시그널 정의
    advanced_action = Signal(str)  # 고급 기능 액션이 발생했을 때
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 선택된 로직 정보 저장
        self.hp_selected_logic = None
        self.mp_selected_logic = None
        self.common_selected_logic = None  # 공통 로직 정보 저장 변수 추가
        self.saved_logics = {}  # 저장된 로직 정보
        
        # UI 초기화
        self.init_ui()
        self._connect_signals()
        
        # 초기화 시에는 설정을 로드하지 않음
        # 로직 정보가 업데이트될 때 load_settings가 호출됨
    
    def _connect_signals(self):
        """시그널 연결"""
        # 체력 로직 관련 시그널
        self.hp_logic_select_btn.clicked.connect(lambda: self._show_logic_select_dialog('hp'))
        self.hp_logic_reset_btn.clicked.connect(lambda: self._reset_logic('hp'))
        
        # 마력 로직 관련 시그널
        self.mp_logic_select_btn.clicked.connect(lambda: self._show_logic_select_dialog('mp'))
        self.mp_logic_reset_btn.clicked.connect(lambda: self._reset_logic('mp'))
        
        # 공통 로직 관련 시그널
        self.common_logic_select_btn.clicked.connect(lambda: self._show_logic_select_dialog('common'))
        self.common_logic_reset_btn.clicked.connect(lambda: self._reset_logic('common'))
        
        # 공통 로직 체크박스 상태 변경 시그널
        self.common_logic_checkbox.stateChanged.connect(
            lambda state: self._update_individual_controls(not bool(state))
        )
        
        # 게이지 값 변경 시그널
        self.hp_slider.valueChanged.connect(self.hp_spinbox.setValue)
        self.hp_spinbox.valueChanged.connect(self.hp_slider.setValue)
        self.mp_slider.valueChanged.connect(self.mp_spinbox.setValue)
        self.mp_spinbox.valueChanged.connect(self.mp_slider.setValue)
        
        # 실시간 비교 영역 관리 버튼 시그널 연결
        self.hp_compare_area_btn.clicked.connect(lambda: self._show_compare_area_dialog('hp'))
        self.mp_compare_area_btn.clicked.connect(lambda: self._show_compare_area_dialog('mp'))
        
        # 설정 저장 시그널 연결
        self.hp_slider.valueChanged.connect(self.save_settings)
        self.mp_slider.valueChanged.connect(self.save_settings)
        self.hp_logic_checkbox.stateChanged.connect(self.save_settings)
        self.mp_logic_checkbox.stateChanged.connect(self.save_settings)
        self.common_logic_checkbox.stateChanged.connect(self.save_settings)
        
        # 게이지 모니터링 시그널 연결
        self.gauge_monitor = GaugeMonitor()
        self.gauge_monitor.gauge_analyzed.connect(self._update_gauge_info)
        self.gauge_monitor.image_captured.connect(self._update_capture_image)
    
    def _show_logic_select_dialog(self, type_):
        """로직 선택 다이얼로그 표시"""
        dialog = LogicSelectorDialog(self.saved_logics, self)
        if dialog.exec_():
            selected_logic = dialog.selected_logic
            if selected_logic and selected_logic in self.saved_logics:
                logic_info = self.saved_logics[selected_logic]
                logic_name = logic_info.get('name', '알 수 없는 로직')
                if type_ == 'hp':
                    self.hp_selected_logic = selected_logic
                    self.hp_logic_name.setText(logic_name)
                    self.hp_logic_name.setWordWrap(True)
                    self.hp_logic_checkbox.setEnabled(True)
                    self.hp_logic_checkbox.setChecked(True)
                elif type_ == 'mp':
                    self.mp_selected_logic = selected_logic
                    self.mp_logic_name.setText(logic_name)
                    self.mp_logic_name.setWordWrap(True)
                    self.mp_logic_checkbox.setEnabled(True)
                    self.mp_logic_checkbox.setChecked(True)
                else:  # common 타입
                    self.common_selected_logic = selected_logic
                    self.common_logic_name.setText(logic_name)
                    self.common_logic_name.setWordWrap(True)
                    self.common_logic_checkbox.setEnabled(True)
                    self.common_logic_checkbox.setChecked(True)
                    # 공통 로직 선택 시 개별 체트롤 비활성화
                    self._update_individual_controls(False)
            # 로직 선택 후 설정 저장
            self.save_settings()
    
    def _reset_logic(self, type_):
        """로직 초기화"""
        if type_ == 'hp':
            self.hp_selected_logic = None
            self.hp_logic_name.setText("선택된 로직 없음")
            self.hp_logic_checkbox.setChecked(False)
            # 공통 로직이 체크되어 있을 때만 비활성화
            if self.common_logic_checkbox.isChecked():
                self.hp_logic_checkbox.setEnabled(False)
                self.hp_logic_select_btn.setEnabled(False)
        elif type_ == 'mp':
            self.mp_selected_logic = None
            self.mp_logic_name.setText("선택된 로직 없음")
            self.mp_logic_checkbox.setChecked(False)
            # 공통 로직이 체크되어 있을 때만 비활성화
            if self.common_logic_checkbox.isChecked():
                self.mp_logic_checkbox.setEnabled(False)
                self.mp_logic_select_btn.setEnabled(False)
        else:  # common 타입
            self.common_selected_logic = None
            self.common_logic_name.setText("선택된 로직 없음")
            self.common_logic_checkbox.setChecked(False)
            self.common_logic_checkbox.setEnabled(False)
            # 공통 로직 초기화  개별 체트롤 활성화
            self._update_individual_controls(True)
        # 로직 초기화 후 설정 저장
        self.save_settings()
    
    def _update_individual_controls(self, enabled: bool):
        """개별 로직 컨트롤 활성화/비활성화"""
        # 공통 로직이 체크되어 있을 때만 개별 컨트롤을 비활성화
        if self.common_logic_checkbox.isChecked():
            self.hp_logic_checkbox.setEnabled(False)
            self.hp_logic_select_btn.setEnabled(False)
            self.mp_logic_checkbox.setEnabled(False)
            self.mp_logic_select_btn.setEnabled(False)
        else:
            # 공통 로직이 체크되어 있지 않으면 개별 컨트롤 활성화
            self.hp_logic_checkbox.setEnabled(True)
            self.hp_logic_select_btn.setEnabled(True)
            self.mp_logic_checkbox.setEnabled(True)
            self.mp_logic_select_btn.setEnabled(True)
    
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedWidth(ADVANCED_FRAME_WIDTH)
        
        # 고급 기능 영역 타이틀
        title = QLabel("고급 기능 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        
        # 고급 기능 컨테이너
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setFixedSize(ADVANCED_FRAME_WIDTH, ADVANCED_SECTION_HEIGHT)
        
        # 회복 기준 프레임
        recovery_frame = QFrame()
        recovery_frame.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        
        # 체력 컨텐츠 레이아웃
        hp_content_layout = QVBoxLayout()
        hp_content_layout.setSpacing(8)
        hp_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 체력 게이지 프레임
        hp_gauge_frame = QFrame()
        hp_gauge_frame.setStyleSheet("QFrame { background-color: transparent; }")
        hp_gauge_layout = QHBoxLayout(hp_gauge_frame)
        hp_gauge_layout.setContentsMargins(0, 0, 0, 0)
        hp_gauge_layout.setSpacing(20)
        
        hp_label = QLabel("체력 회복 기준")
        hp_label.setFixedWidth(80)
        self.hp_slider = QSlider(Qt.Horizontal)
        self.hp_slider.setRange(0, 100)
        self.hp_slider.setValue(DEFAULT_RECOVERY_THRESHOLD)
        self.hp_slider.setFixedWidth(200)
        self.hp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #ff6b6b;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
        """)
        self.hp_spinbox = CustomSpinBox()
        
        # 실시간 캡처 이미지 영역
        hp_capture_frame = QFrame()
        hp_capture_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        hp_capture_layout = QHBoxLayout(hp_capture_frame)
        hp_capture_layout.setContentsMargins(10, 5, 10, 5)
        hp_capture_layout.setSpacing(15)
        
        # 캡처 이미지 표시 라벨
        self.hp_capture_label = QLabel()
        self.hp_capture_label.setFixedSize(100, 30)
        self.hp_capture_label.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.hp_capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 분석 수치값 표시 라벨
        self.hp_ratio_label = QLabel("0%")
        self.hp_ratio_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # 기준값 비교 결과 표시 라벨
        self.hp_compare_label = QLabel("-")
        self.hp_compare_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
            }
        """)
        
        hp_capture_layout.addWidget(self.hp_capture_label)
        hp_capture_layout.addWidget(self.hp_ratio_label)
        hp_capture_layout.addWidget(self.hp_compare_label)
        
        hp_gauge_layout.addWidget(hp_label)
        hp_gauge_layout.addWidget(self.hp_slider)
        hp_gauge_layout.addWidget(self.hp_spinbox)
        hp_gauge_layout.addWidget(hp_capture_frame)
        hp_gauge_layout.addStretch()
        
        hp_content_layout.addWidget(hp_gauge_frame)
        
        # 체력 로직 프레임
        hp_logic_frame = QFrame()
        hp_logic_frame.setStyleSheet("QFrame { background-color: transparent; }")
        hp_logic_layout = QVBoxLayout(hp_logic_frame)
        hp_logic_layout.setContentsMargins(0, 0, 0, 0)
        hp_logic_layout.setSpacing(5)
        
        hp_logic_header = QHBoxLayout()
        self.hp_logic_checkbox = QCheckBox("체력 회복 동작 로직")
        self.hp_logic_checkbox.setEnabled(False)
        self.hp_logic_name = QLabel("선택된 로직 없음")
        self.hp_logic_name.setWordWrap(True)
        
        hp_logic_header.addWidget(self.hp_logic_checkbox)
        hp_logic_header.addWidget(self.hp_logic_name, 1)
        
        hp_button_layout = QHBoxLayout()
        hp_button_layout.setSpacing(10)
        
        self.hp_logic_select_btn = QPushButton("체력 회복 로직 선택")
        self.hp_logic_reset_btn = QPushButton("선택 로직 초기화")
        self.hp_compare_area_btn = QPushButton("체력 실시간 비교 영역 관리")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.hp_logic_select_btn.setStyleSheet(button_style)
        self.hp_logic_reset_btn.setStyleSheet(button_style)
        self.hp_compare_area_btn.setStyleSheet(button_style)
        
        hp_button_layout.addWidget(self.hp_logic_select_btn, 1)
        hp_button_layout.addWidget(self.hp_logic_reset_btn, 1)
        hp_button_layout.addWidget(self.hp_compare_area_btn, 1)
        
        hp_logic_layout.addLayout(hp_logic_header)
        hp_logic_layout.addLayout(hp_button_layout)
        
        hp_content_layout.addWidget(hp_logic_frame)
        
        # 마력 컨텐츠 레이아웃
        mp_content_layout = QVBoxLayout()
        mp_content_layout.setSpacing(8)
        mp_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 마력 게이지 프레임
        mp_gauge_frame = QFrame()
        mp_gauge_frame.setStyleSheet("QFrame { background-color: transparent; }")
        mp_gauge_layout = QHBoxLayout(mp_gauge_frame)
        mp_gauge_layout.setContentsMargins(0, 0, 0, 0)
        mp_gauge_layout.setSpacing(20)
        
        mp_label = QLabel("마력 회복 기준")
        mp_label.setFixedWidth(80)
        self.mp_slider = QSlider(Qt.Horizontal)
        self.mp_slider.setRange(0, 100)
        self.mp_slider.setValue(DEFAULT_RECOVERY_THRESHOLD)
        self.mp_slider.setFixedWidth(200)
        self.mp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #4b7bec;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
        """)
        self.mp_spinbox = CustomSpinBox()
        
        # 실시간 캡처 이미지 영역
        mp_capture_frame = QFrame()
        mp_capture_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        mp_capture_layout = QHBoxLayout(mp_capture_frame)
        mp_capture_layout.setContentsMargins(10, 5, 10, 5)
        mp_capture_layout.setSpacing(15)
        
        # 캡처 이미지 표시 라벨
        self.mp_capture_label = QLabel()
        self.mp_capture_label.setFixedSize(100, 30)
        self.mp_capture_label.setStyleSheet("border: 1px solid #ccc; background-color: white;")
        self.mp_capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 분석 수치값 표시 라벨
        self.mp_ratio_label = QLabel("0%")
        self.mp_ratio_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        # 기준값 비교 결과 표시 라벨
        self.mp_compare_label = QLabel("-")
        self.mp_compare_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 13px;
            }
        """)
        
        mp_capture_layout.addWidget(self.mp_capture_label)
        mp_capture_layout.addWidget(self.mp_ratio_label)
        mp_capture_layout.addWidget(self.mp_compare_label)
        
        mp_gauge_layout.addWidget(mp_label)
        mp_gauge_layout.addWidget(self.mp_slider)
        mp_gauge_layout.addWidget(self.mp_spinbox)
        mp_gauge_layout.addWidget(mp_capture_frame)
        mp_gauge_layout.addStretch()
        
        mp_content_layout.addWidget(mp_gauge_frame)
        
        # 마력 로직 프레임
        mp_logic_frame = QFrame()
        mp_logic_frame.setStyleSheet("QFrame { background-color: transparent; }")
        mp_logic_layout = QVBoxLayout(mp_logic_frame)
        mp_logic_layout.setContentsMargins(0, 0, 0, 0)
        mp_logic_layout.setSpacing(5)
        
        mp_logic_header = QHBoxLayout()
        self.mp_logic_checkbox = QCheckBox("마력 회복 동작 로직")
        self.mp_logic_checkbox.setEnabled(False)
        self.mp_logic_name = QLabel("선택된 로직 없음")
        self.mp_logic_name.setWordWrap(True)
        
        mp_logic_header.addWidget(self.mp_logic_checkbox)
        mp_logic_header.addWidget(self.mp_logic_name, 1)
        
        mp_button_layout = QHBoxLayout()
        mp_button_layout.setSpacing(10)
        
        self.mp_logic_select_btn = QPushButton("마력 회복 로직 선택")
        self.mp_logic_reset_btn = QPushButton("선택 로직 초기화")
        self.mp_compare_area_btn = QPushButton("마력 실시간 비교 영역 관리")
        
        self.mp_logic_select_btn.setStyleSheet(button_style)
        self.mp_logic_reset_btn.setStyleSheet(button_style)
        self.mp_compare_area_btn.setStyleSheet(button_style)
        
        mp_button_layout.addWidget(self.mp_logic_select_btn, 1)
        mp_button_layout.addWidget(self.mp_logic_reset_btn, 1)
        mp_button_layout.addWidget(self.mp_compare_area_btn, 1)
        
        mp_logic_layout.addLayout(mp_logic_header)
        mp_logic_layout.addLayout(mp_button_layout)
        
        mp_content_layout.addWidget(mp_logic_frame)
        
        # 공통 로직 레이아웃
        common_logic_info_layout = QVBoxLayout()
        common_logic_info_layout.setSpacing(8)
        common_logic_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        common_logic_header = QHBoxLayout()
        self.common_logic_checkbox = QCheckBox("체력, 마력 회복 기준 이하시 동작할 공통 로직")
        self.common_logic_checkbox.setEnabled(False)
        self.common_logic_name = QLabel("선택된 로직 없음")
        self.common_logic_name.setWordWrap(True)
        
        common_logic_header.addWidget(self.common_logic_checkbox)
        common_logic_header.addWidget(self.common_logic_name, 1)
        
        common_button_layout = QHBoxLayout()
        common_button_layout.setSpacing(10)
        
        self.common_logic_select_btn = QPushButton("체력, 마력 회복에 사용할 로직 선택")
        self.common_logic_reset_btn = QPushButton("선택 로직 초기화")
        
        self.common_logic_select_btn.setStyleSheet(button_style)
        self.common_logic_reset_btn.setStyleSheet(button_style)
        
        common_button_layout.addWidget(self.common_logic_select_btn, 1)
        common_button_layout.addWidget(self.common_logic_reset_btn, 1)
        
        common_logic_info_layout.addLayout(common_logic_header)
        common_logic_info_layout.addLayout(common_button_layout)
        
        # 메인 레이아웃 구성
        main_layout = QVBoxLayout(recovery_frame)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(hp_content_layout)
        main_layout.addLayout(mp_content_layout)
        main_layout.addLayout(common_logic_info_layout)
        
        # 최종 레이아웃 구성
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        layout.addWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(recovery_frame)
        
        # 시그널 연결
        self.hp_slider.valueChanged.connect(self.hp_spinbox.setValue)
        self.hp_spinbox.valueChanged.connect(self.hp_slider.setValue)
        self.mp_slider.valueChanged.connect(self.mp_spinbox.setValue)
        self.mp_spinbox.valueChanged.connect(self.mp_slider.setValue)
    
    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics
        # 로직 정보가 업데이트되 후에 설정을 로드
        self.load_settings()
    
    def _show_compare_area_dialog(self, type_):
        """실시간 비교 영역 관리 다이얼로그 표시"""
        dialog = CompareAreaDialog(type_, self)
        dialog.exec_()
    
    def save_settings(self):
        """현재 설정을 저장"""
        try:
            # 설정 파일 경로
            self.settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'settings.json')
            
            # 현재 settings.json 파일 읽기
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # advanced_settings 섹션이 없으면 생성
            if 'advanced_settings' not in settings:
                settings['advanced_settings'] = {}
            
            # 현재 설정 업데이트
            settings['advanced_settings'].update({
                'hp_threshold': self.hp_slider.value(),
                'mp_threshold': self.mp_slider.value(),
                'hp_logic': {
                    'uuid': self.hp_selected_logic,
                    'enabled': self.hp_logic_checkbox.isChecked()
                } if self.hp_selected_logic else None,
                'mp_logic': {
                    'uuid': self.mp_selected_logic,
                    'enabled': self.mp_logic_checkbox.isChecked()
                } if self.mp_selected_logic else None,
                'common_logic': {
                    'uuid': self.common_selected_logic,
                    'enabled': self.common_logic_checkbox.isChecked()
                } if self.common_selected_logic else None
            })
            
            # 변경된 설정을 파일에 저장
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            print("설정이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_settings(self):
        """저장된 설정 불러오기"""
        try:
            # 설정 파일 경로
            self.settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'settings.json')
            
            # settings.json 파일 로드
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 고급 설정 로드
            advanced_settings = settings.get('advanced_settings', {})
            
            # 슬라이더 값 설정
            hp_threshold = advanced_settings.get('hp_threshold', DEFAULT_RECOVERY_THRESHOLD)
            mp_threshold = advanced_settings.get('mp_threshold', DEFAULT_RECOVERY_THRESHOLD)
            
            self.hp_slider.setValue(hp_threshold)
            self.hp_spinbox.setValue(hp_threshold)
            self.mp_slider.setValue(mp_threshold)
            self.mp_spinbox.setValue(mp_threshold)
            
            # HP 로직 설정
            hp_logic = advanced_settings.get('hp_logic')
            if hp_logic and hp_logic.get('uuid') in self.saved_logics:
                self.hp_selected_logic = hp_logic['uuid']
                logic_info = self.saved_logics[self.hp_selected_logic]
                self.hp_logic_name.setText(logic_info.get('name', '알 수 없는 로직'))
                self.hp_logic_checkbox.setEnabled(True)
                self.hp_logic_checkbox.setChecked(hp_logic.get('enabled', False))
            
            # MP 로직 설정
            mp_logic = advanced_settings.get('mp_logic')
            if mp_logic and mp_logic.get('uuid') in self.saved_logics:
                self.mp_selected_logic = mp_logic['uuid']
                logic_info = self.saved_logics[self.mp_selected_logic]
                self.mp_logic_name.setText(logic_info.get('name', '알 수 없는 로직'))
                self.mp_logic_checkbox.setEnabled(True)
                self.mp_logic_checkbox.setChecked(mp_logic.get('enabled', False))
            
            # 공통 로직 설정
            common_logic = advanced_settings.get('common_logic')
            if common_logic and common_logic.get('uuid') in self.saved_logics:
                self.common_selected_logic = common_logic['uuid']
                logic_info = self.saved_logics[self.common_selected_logic]
                self.common_logic_name.setText(logic_info.get('name', '알 수 없는 로직'))
                self.common_logic_checkbox.setEnabled(True)
                self.common_logic_checkbox.setChecked(common_logic.get('enabled', False))
                if common_logic.get('enabled', False):
                    self._update_individual_controls(False)
            
            # 게이지 모니터 설정 로드
            gauge_monitor = settings.get('gauge_monitor', {})
            print("HP 캡처 영역 로드:", gauge_monitor.get('hp_gauge', {}))
            print("MP 캡처 영역 로드:", gauge_monitor.get('mp_gauge', {}))
            
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _update_gauge_info(self, type_, ratio):
        """게이지 정보 업데이트"""
        try:
            if type_ == 'hp':
                # 비율 표시 업데이트
                self.hp_ratio_label.setText(f"{ratio:.1f}%")
                
                # 기준값과 비교하여 상태 표시
                threshold = self.hp_slider.value()
                if ratio < threshold:
                    self.hp_compare_label.setText("위험")
                    self.hp_compare_label.setStyleSheet("""
                        QLabel {
                            color: #ff4444;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                else:
                    self.hp_compare_label.setText("양호")
                    self.hp_compare_label.setStyleSheet("""
                        QLabel {
                            color: #44bb44;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                
                # 프로그레스바 업데이트
                self.hp_progress.setValue(int(ratio))
                
            else:  # mp
                # 비율 표시 업데이트
                self.mp_ratio_label.setText(f"{ratio:.1f}%")
                
                # 기준값과 비교하여 상태 표시
                threshold = self.mp_slider.value()
                if ratio < threshold:
                    self.mp_compare_label.setText("위험")
                    self.mp_compare_label.setStyleSheet("""
                        QLabel {
                            color: #ff4444;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                else:
                    self.mp_compare_label.setText("양호")
                    self.mp_compare_label.setStyleSheet("""
                        QLabel {
                            color: #44bb44;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                
                # 프로그레스바 업데이트
                self.mp_progress.setValue(int(ratio))
                
        except Exception as e:
            print(f"게이지 정보 업데이트 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    def _update_capture_image(self, type_, image):
        """캡처된 이미지 업데이트"""
        try:
            # QPixmap을 해당하는 라벨에 표시
            if type_ == 'hp':
                self.hp_capture_label.setPixmap(image)
            else:  # mp
                self.mp_capture_label.setPixmap(image)
                
        except Exception as e:
            print(f"캡처 이미지 업데이트 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
