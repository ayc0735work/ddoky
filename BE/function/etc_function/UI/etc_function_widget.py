import logging
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from ...constants.styles import (TITLE_FONT_FAMILY, SECTION_FONT_SIZE, 
                               CONTAINER_STYLE, ETC_FUNCTION_COUNTDOWN_FONT_SIZE)
from ...constants.dimensions import (KEY_COUNTDOWN_WIDTH, EMPTY_SECTION_WIDTH,
                                   SECTION_MARGIN)

class EtcFunctionWidget(QWidget):
    """기타 기능 위젯"""
    
    # 시그널 정의
    log_message = Signal(str)  # 로그 메시지 시그널
    countdown_value_changed = Signal(float)  # 카운트다운 값 변경 시그널
    
    def __init__(self):
        super().__init__()
        self.is_logic_enabled = False
        self.controller = None  # 컨트롤러 참조 저장
        self._process_active = False  # 프로세스 활성 상태
        self.init_ui()
        logging.debug("[위젯] 초기화 완료")
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 제목 레이블
        title_label = QLabel("기타 기능 영역")
        title_font = QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
        title_font.setWeight(QFont.Bold)
        title_label.setFont(title_font)
        self.main_layout.addWidget(title_label)
        
        # 섹션들을 담을 수평 레이아웃
        sections_layout = QHBoxLayout()
        sections_layout.setSpacing(SECTION_MARGIN)
        
        # 키 입력 카운트다운 섹션
        sections_layout.addWidget(self.init_key_countdown_section())
        
        # 빈 섹션
        sections_layout.addWidget(self.init_empty_section())
        
        self.main_layout.addLayout(sections_layout)
        
    def init_key_countdown_section(self):
        """키 입력 카운트다운 섹션 초기화"""
        # 컨테이너 프레임
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setFixedWidth(KEY_COUNTDOWN_WIDTH)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)  # 여백 최소화
        container_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # 왼쪽 상단 정렬
        container.setLayout(container_layout)
        
        # 섹션 제목
        section_title = QLabel("키 입력 카운트다운")
        section_title.setStyleSheet("border: none;")
        section_title.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬
        section_font = QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE - 2)
        section_font.setWeight(QFont.Bold)
        section_title.setFont(section_font)
        container_layout.addWidget(section_title)
        
        # 카운트다운 표시 영역
        countdown_layout = QHBoxLayout()
        
        # 헬파이어 라벨
        hellfire_label = QLabel("헬파이어:")
        hellfire_label.setStyleSheet("border: none;")
        hellfire_label.setFont(QFont(TITLE_FONT_FAMILY, ETC_FUNCTION_COUNTDOWN_FONT_SIZE))
        countdown_layout.addWidget(hellfire_label)
        
        # 카운트다운 레이블
        self.hellfire_countdown_label = QLabel("10.00")
        self.hellfire_countdown_label.setStyleSheet("border: none; color: red; font-weight: bold;")
        self.hellfire_countdown_label.setFont(QFont(TITLE_FONT_FAMILY, ETC_FUNCTION_COUNTDOWN_FONT_SIZE))
        self.hellfire_countdown_label.setAlignment(Qt.AlignCenter)
        countdown_layout.addWidget(self.hellfire_countdown_label)
        countdown_layout.addStretch()
        
        container_layout.addLayout(countdown_layout)
        return container
        
    def init_empty_section(self):
        """빈 섹션 초기화"""
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setFixedWidth(EMPTY_SECTION_WIDTH)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)  # 여백 최소화
        container_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # 왼쪽 상단 정렬
        container.setLayout(container_layout)
        
        # 섹션 제목
        section_title = QLabel("아직 기능 구현이 없는 영역")
        section_title.setStyleSheet("border: none;")
        section_title.setAlignment(Qt.AlignLeft)  # 왼쪽 정렬
        section_font = QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE - 2)
        section_font.setWeight(QFont.Bold)
        section_title.setFont(section_font)
        container_layout.addWidget(section_title)
        
        return container
        
    def update_hellfire_countdown_label(self, text):
        """헬파이어 카운트다운 레이블 업데이트"""
        # 값이 변경될 때만 업데이트
        if not self.hellfire_countdown_label.text() == text:
            self.hellfire_countdown_label.setText(text)
        
    def set_controller(self, controller):
        """컨트롤러 설정
        
        Args:
            controller: EtcFunctionController 인스턴스
        """
        self.controller = controller
        logging.debug("[위젯] 컨트롤러 설정 완료")
        
    def set_logic_enabled(self, enabled):
        """로직 활성화 상태 설정
        
        Args:
            enabled (bool): 활성화 여부
        """
        logging.debug(f"[위젯] 로직 활성화 상태 변경: {enabled}")
        self.log_message.emit(f"[위젯] 로직 활성화 상태 변경: {enabled}")  # 로그 메시지 발생
        
        self.is_logic_enabled = enabled
        
        # 상태 변경을 컨트롤러에 알림
        if self.controller:
            if enabled and self.is_process_active():
                logging.debug("[위젯] 조건 충족 - 카운트다운 시작 요청")
                self.log_message.emit("[위젯] 조건 충족 - 카운트다운 시작 요청")
                self.controller.start_hellfire_countdown()
            else:
                logging.debug("[위젯] 조건 불충족 - 카운트다운 중지 요청")
                self.log_message.emit("[위젯] 조건 불충족 - 카운트다운 중지 요청")
                self.controller.stop_hellfire_countdown()
                
    def is_process_active(self):
        """선택된 프로세스가 활성 상태인지 확인"""
        return self._process_active
        
    def update_process_state(self, is_active):
        """프로세스 활성 상태 업데이트
        
        Args:
            is_active (bool): 프로세스 활성화 여부
        """
        logging.debug(f"[위젯] 프로세스 상태 업데이트: {is_active}")
        if self._process_active != is_active:
            logging.debug(f"[위젯] 프로세스 상태 변경: {is_active}")
            self._process_active = is_active
            if self.is_logic_enabled and is_active and self.controller:
                logging.debug("[위젯] 프로세스 활성화로 인한 카운트다운 시작 요청")
                self.controller.start_hellfire_countdown()
            elif not is_active and self.controller:
                logging.debug("[위젯] 프로세스 비활성화로 인한 카운트다운 중지 요청")
                self.controller.stop_hellfire_countdown()
                
    def _on_countdown_value_changed(self, value):
        """카운트다운 값이 변경되었을 때 호출"""
        self.countdown_value_changed.emit(value)
        self.log_message.emit(f"키 입력 카운트다운 시간이 {value}초로 설정되었습니다.")
