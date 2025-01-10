from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from ...constants.styles import (TITLE_FONT_FAMILY, SECTION_FONT_SIZE, 
                               CONTAINER_STYLE, LABEL_FONT_SIZE)
from ...constants.dimensions import (KEY_COUNTDOWN_WIDTH, EMPTY_SECTION_WIDTH,
                                   SECTION_MARGIN)

class EtcFunctionWidget(QWidget):
    """기타 기능 위젯"""
    
    # 시그널 정의
    log_message = Signal(str)  # 로그 메시지 시그널
    countdown_value_changed = Signal(int)  # 카운트다운 값 변경 시그널
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
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
        hellfire_label.setFont(QFont(TITLE_FONT_FAMILY, LABEL_FONT_SIZE))
        countdown_layout.addWidget(hellfire_label)
        
        # 카운트다운 라벨
        self.countdown_label = QLabel("헬파이어 마법 미감지")
        self.countdown_label.setStyleSheet("border: none;")
        self.countdown_label.setFont(QFont(TITLE_FONT_FAMILY, LABEL_FONT_SIZE))
        countdown_layout.addWidget(self.countdown_label)
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
        
    def _on_countdown_value_changed(self, value):
        """카운트다운 값이 변경되었을 때 호출"""
        self.countdown_value_changed.emit(value)
        self.log_message.emit(f"키 입력 카운트다운 시간이 {value}초로 설정되었습니다.")
