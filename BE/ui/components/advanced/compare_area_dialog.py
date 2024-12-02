from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QFrame, QLineEdit,
                              QGridLayout, QWidget, QRubberBand, QApplication,
                              QMessageBox)
from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PySide6.QtGui import QScreen, QPixmap, QColor, QPainter, QPen, QBrush
import win32gui
import win32con
import json
import os
from datetime import datetime
import time
from ..process_selector.process_selector_dialog import ProcessSelectorDialog

class CaptureOverlay(QDialog):
    def __init__(self, target_hwnd, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 대상 윈도우 핸들
        self.target_hwnd = target_hwnd
        
        # 캡처 관련 변수
        self.start_pos = None
        self.current_pos = None
        self.is_capturing = False
        self.captured_rect = None
        
        # 화면 크기 가져오기
        screen = QApplication.primaryScreen()
        
        # 대상 윈도우의 위치와 크기 가져오기
        window_rect = win32gui.GetWindowRect(self.target_hwnd)
        self.window_x = window_rect[0]
        self.window_y = window_rect[1]
        self.window_width = window_rect[2] - window_rect[0]
        self.window_height = window_rect[3] - window_rect[1]
        
        # 오버레이 위치와 크기 설정
        self.setGeometry(
            self.window_x, self.window_y,
            self.window_width, self.window_height
        )
        
        # 반투명 오버레이 설정
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        
        # 초기 이미지와 확대경 설정
        self.window_image = QPixmap()  # 빈 픽스맵으로 초기화
        self.magnifier_size = QSize(120, 120)  # 확대경 크기
        self.magnifier_scale = 2.0  # 확대 비율
        
        # 타이머 설정
        self.init_timer = QTimer(self)
        self.init_timer.setSingleShot(True)
        self.init_timer.timeout.connect(self._initialize_capture)
        
    def showEvent(self, event):
        """오버레이가 표시될 때 호출"""
        super().showEvent(event)
        # 지정된 시간 후에 초기화 함수 호출
        self.init_timer.start(800)
        
    def _initialize_capture(self):
        """캡처 초기화"""
        # 대상 윈도우의 현재 위치와 크기 가져오기
        window_rect = win32gui.GetWindowRect(self.target_hwnd)
        self.window_x = window_rect[0]
        self.window_y = window_rect[1]
        self.window_width = window_rect[2] - window_rect[0]
        self.window_height = window_rect[3] - window_rect[1]
        
        # 오버레이 위치와 크기 업데이트
        self.setGeometry(
            self.window_x, self.window_y,
            self.window_width, self.window_height
        )
        
        # 대상 윈도우 스크린샷
        screen = QApplication.primaryScreen()
        self.window_image = screen.grabWindow(0, self.window_x, self.window_y, 
                                            self.window_width, self.window_height)
        
        # 화면 갱신
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 배경 이미지 그리기
        if hasattr(self, 'window_image') and not self.window_image.isNull():
            painter.drawPixmap(0, 0, self.window_image)
            
            # 반투명 어두운 오버레이
            overlay = QColor(0, 0, 0, 128)
            painter.fillRect(self.rect(), overlay)
            
        if self.start_pos and self.current_pos:
            # 선택 영역 계산
            capture_rect = QRect(self.start_pos, self.current_pos).normalized()
            
            # 선택 영역은 원본 이미지 보이게
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawPixmap(capture_rect, self.window_image, capture_rect)
            
            # 선택 영역 테두리 그리기
            pen = QPen(QColor(0, 120, 215), 1)
            painter.setPen(pen)
            painter.drawRect(capture_rect)
            
            # 확대경 그리기
            if self.current_pos:
                self._draw_magnifier(painter, self.current_pos)
                
            # 크기 정보 표시
            size_text = f"{capture_rect.width()} x {capture_rect.height()}"
            text_rect = capture_rect.adjusted(0, -25, 0, 0)
            painter.setPen(Qt.white)
            painter.drawText(text_rect, Qt.AlignCenter, size_text)
    
    def _draw_magnifier(self, painter, pos):
        # 확대경이 표시될 위치 계산
        magnifier_x = pos.x() + 20
        magnifier_y = pos.y() - self.magnifier_size.height() - 20
        
        # 화면 경계를 벗어나지 않도록 조정
        if magnifier_x + self.magnifier_size.width() > self.window_width:
            magnifier_x = pos.x() - self.magnifier_size.width() - 20
        if magnifier_y < 0:
            magnifier_y = pos.y() + 20
            
        # 확대할 영역 계산
        source_rect = QRect(
            pos.x() - self.magnifier_size.width() / (2 * self.magnifier_scale),
            pos.y() - self.magnifier_size.height() / (2 * self.magnifier_scale),
            self.magnifier_size.width() / self.magnifier_scale,
            self.magnifier_size.height() / self.magnifier_scale
        )
        
        # 확대경 배경
        painter.fillRect(
            QRect(magnifier_x, magnifier_y, self.magnifier_size.width(), self.magnifier_size.height()),
            QColor(255, 255, 255, 200)
        )
        
        # 확대된 이미지 그리기
        painter.drawPixmap(
            QRect(magnifier_x, magnifier_y, self.magnifier_size.width(), self.magnifier_size.height()),
            self.window_image,
            source_rect
        )
        
        # 확대경 테두리
        painter.setPen(QPen(QColor(0, 120, 215), 2))
        painter.drawRect(
            magnifier_x, magnifier_y,
            self.magnifier_size.width(), self.magnifier_size.height()
        )
        
        # 십자선 그리기
        center_x = magnifier_x + self.magnifier_size.width() / 2
        center_y = magnifier_y + self.magnifier_size.height() / 2
        
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawLine(
            center_x - 10, center_y,
            center_x + 10, center_y
        )
        painter.drawLine(
            center_x, center_y - 10,
            center_x, center_y + 10
        )
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.is_capturing = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_capturing:
            self.current_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_capturing:
            self.is_capturing = False
            if self.start_pos and self.current_pos:
                self.captured_rect = QRect(self.start_pos, self.current_pos).normalized()
                self.accept()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()

class CompareAreaDialog(QDialog):
    def __init__(self, type_, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        # 타입 저장 (hp 또는 mp)
        self.type_ = type_
        
        # 타입에 따른 윈도우 제목 설정
        title = "체력 실시간 비교 영역 관리" if type_ == "hp" else "마력 실시간 비교 영역 관리"
        self.setWindowTitle(title)
        
        self.setFixedSize(600, 500)
        self.selected_process = None
        self.captured_image = None
        self.captured_rect = None
        
        # 설정 파일 경로
        self.settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'settings.json')
        self.captures_dir = os.path.join(os.path.dirname(self.settings_file), 'captures')
        os.makedirs(self.captures_dir, exist_ok=True)
        
        # 저장된 캡처 정보
        self.saved_captures = []
        self.last_capture = None
        
        # 마지막 저장된 캡처 정보 로드
        self._load_last_capture()
        
        self.init_ui()
        
    def _load_last_capture(self):
        """마지막으로 저장된 캡처 정보 로드"""
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'data', 'captures', f'captures_{self.type_}.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    captures = json.load(f)
                if captures:
                    self.last_capture = captures[-1]  # 가장 최근 캡처 정보
            except Exception:
                self.last_capture = None
                
    def _load_saved_capture(self):
        """저장된 캡처 정보로 UI 업데이트"""
        if not self.last_capture:
            return
            
        # 이미지 로드
        image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                'data', 'captures', self.last_capture['image_file'])
        if os.path.exists(image_path):
            self.captured_image = QPixmap(image_path)
            
            # 좌표 정보 설정
            coords = self.last_capture['coordinates']
            self.captured_rect = QRect(coords['x'], coords['y'], coords['width'], coords['height'])
            
            # UI 업데이트
            self._update_capture_display()
            
            # 프로세스 정보 표시
            self.process_info.setText(f"{self.last_capture['process_name']} ({self.last_capture['process_id']})")
            
            # 좌표 입력란 업데이트
            self.top_left_x.setText(str(coords['x']))
            self.top_left_y.setText(str(coords['y']))
            self.top_right_x.setText(str(coords['x'] + coords['width']))
            self.top_right_y.setText(str(coords['y']))
            self.bottom_left_x.setText(str(coords['x']))
            self.bottom_left_y.setText(str(coords['y'] + coords['height']))
            self.bottom_right_x.setText(str(coords['x'] + coords['width']))
            self.bottom_right_y.setText(str(coords['y'] + coords['height']))
            
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 프로세스 선택 영역
        process_frame = QFrame()
        process_frame.setStyleSheet("QFrame { background-color: transparent; }")
        process_layout = QVBoxLayout(process_frame)
        process_layout.setContentsMargins(0, 0, 0, 0)
        process_layout.setSpacing(5)
        
        # 프로세스 정보 표시 영역
        process_header = QHBoxLayout()
        self.process_info = QLabel("선택된 프로세스 없음")
        self.process_info.setWordWrap(True)
        process_header.addWidget(self.process_info)
        
        # 프로세스 선택 버튼 영역
        process_button_layout = QHBoxLayout()
        process_button_layout.setSpacing(10)
        
        self.process_select_btn = QPushButton("프로세스 선택")
        self.process_reset_btn = QPushButton("프로세스 초기화")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.process_select_btn.setStyleSheet(button_style)
        self.process_reset_btn.setStyleSheet(button_style)
        
        process_button_layout.addWidget(self.process_select_btn)
        process_button_layout.addWidget(self.process_reset_btn)
        process_button_layout.addStretch()
        
        process_layout.addLayout(process_header)
        process_layout.addLayout(process_button_layout)
        
        layout.addWidget(process_frame)
        
        # 캡처된 영역 정보
        self.captured_area_info = QLabel("캡처된 영역이 없습니다")
        self.captured_area_info.setWordWrap(True)
        layout.addWidget(self.captured_area_info)
        
        # 캡처 영역 좌표 입력 필드들을 포함할 수평 레이아웃
        coordinates_container = QHBoxLayout()
        
        # 캡처 영역 좌표 입력 필드들
        coordinates_frame = QFrame()
        coordinates_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        coordinates_layout = QGridLayout()
        coordinates_layout.setSpacing(10)
        coordinates_layout.setContentsMargins(10, 10, 10, 10)
        
        # 좌상단 좌표
        top_left_layout = QHBoxLayout()
        top_left_layout.addWidget(QLabel("좌상단:"))
        self.top_left_x = QLineEdit()
        self.top_left_x.setReadOnly(True)
        self.top_left_x.setPlaceholderText("X")
        self.top_left_x.setFixedWidth(60)
        top_left_layout.addWidget(self.top_left_x)
        self.top_left_y = QLineEdit()
        self.top_left_y.setReadOnly(True)
        self.top_left_y.setPlaceholderText("Y")
        self.top_left_y.setFixedWidth(60)
        top_left_layout.addWidget(self.top_left_y)
        top_left_widget = QWidget()
        top_left_widget.setLayout(top_left_layout)
        coordinates_layout.addWidget(top_left_widget, 0, 0)
        
        # 우상단 좌표
        top_right_layout = QHBoxLayout()
        top_right_layout.addWidget(QLabel("우상단:"))
        self.top_right_x = QLineEdit()
        self.top_right_x.setReadOnly(True)
        self.top_right_x.setPlaceholderText("X")
        self.top_right_x.setFixedWidth(60)
        top_right_layout.addWidget(self.top_right_x)
        self.top_right_y = QLineEdit()
        self.top_right_y.setReadOnly(True)
        self.top_right_y.setPlaceholderText("Y")
        self.top_right_y.setFixedWidth(60)
        top_right_layout.addWidget(self.top_right_y)
        top_right_widget = QWidget()
        top_right_widget.setLayout(top_right_layout)
        coordinates_layout.addWidget(top_right_widget, 0, 1)
        
        # 좌하단 좌표
        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(QLabel("좌하단:"))
        self.bottom_left_x = QLineEdit()
        self.bottom_left_x.setReadOnly(True)
        self.bottom_left_x.setPlaceholderText("X")
        self.bottom_left_x.setFixedWidth(60)
        bottom_left_layout.addWidget(self.bottom_left_x)
        self.bottom_left_y = QLineEdit()
        self.bottom_left_y.setReadOnly(True)
        self.bottom_left_y.setPlaceholderText("Y")
        self.bottom_left_y.setFixedWidth(60)
        bottom_left_layout.addWidget(self.bottom_left_y)
        bottom_left_widget = QWidget()
        bottom_left_widget.setLayout(bottom_left_layout)
        coordinates_layout.addWidget(bottom_left_widget, 1, 0)
        
        # 우하단 좌표
        bottom_right_layout = QHBoxLayout()
        bottom_right_layout.addWidget(QLabel("우하단:"))
        self.bottom_right_x = QLineEdit()
        self.bottom_right_x.setReadOnly(True)
        self.bottom_right_x.setPlaceholderText("X")
        self.bottom_right_x.setFixedWidth(60)
        bottom_right_layout.addWidget(self.bottom_right_x)
        self.bottom_right_y = QLineEdit()
        self.bottom_right_y.setReadOnly(True)
        self.bottom_right_y.setPlaceholderText("Y")
        self.bottom_right_y.setFixedWidth(60)
        bottom_right_layout.addWidget(self.bottom_right_y)
        bottom_right_widget = QWidget()
        bottom_right_widget.setLayout(bottom_right_layout)
        coordinates_layout.addWidget(bottom_right_widget, 1, 1)
        
        coordinates_frame.setLayout(coordinates_layout)
        coordinates_container.addWidget(coordinates_frame)
        coordinates_container.addStretch()
        layout.addLayout(coordinates_container)
        
        # 캡처 이미지 표시 영역
        self.capture_frame = QFrame()
        self.capture_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        self.capture_frame.setMinimumHeight(150)
        
        # 캡처 이미지가 없을 때 표시할 안내 텍스트
        guide_label = QLabel("캡처된 이미지가 없습니다.\n영역을 지정해주세요.")
        guide_label.setAlignment(Qt.AlignCenter)
        guide_label.setStyleSheet("color: #666;")
        
        capture_layout = QVBoxLayout(self.capture_frame)
        capture_layout.addWidget(guide_label)
        
        layout.addWidget(self.capture_frame)
        
        # 캡처 영역 관리 버튼들
        capture_button_layout = QHBoxLayout()
        capture_button_layout.setSpacing(10)
        
        self.capture_btn = QPushButton("캡처 영역 지정")
        self.capture_btn.setEnabled(False)  # 초기에는 비활성화
        self.reset_btn = QPushButton("캡처 영역 초기화")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.capture_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(button_style)
        
        capture_button_layout.addWidget(self.capture_btn)
        capture_button_layout.addWidget(self.reset_btn)
        capture_button_layout.addStretch()
        
        layout.addLayout(capture_button_layout)
        
        # 저장/취소 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("저장", self)
        self.save_btn.clicked.connect(self._save_area)
        self.save_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("취소", self)
        self.cancel_btn.clicked.connect(self.reject)
        
        save_button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """
        
        cancel_button_style = """
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """
        
        self.save_btn.setStyleSheet(save_button_style)
        self.cancel_btn.setStyleSheet(cancel_button_style)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 시그널 연결
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        self.capture_btn.clicked.connect(self._capture_area)
        self.cancel_btn.clicked.connect(self.reject)  # 취소 버튼에 reject 연결
        
    def _select_process(self):
        """프로세스 선택"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec_():
            self.selected_process = dialog.selected_process
            if self.selected_process:
                process_info_text = f"선택된 프로세스 [PID: {self.selected_process['pid']}] {self.selected_process['name']} - {self.selected_process['title']}"
                self.process_info.setText(process_info_text)
                self.capture_btn.setEnabled(True)
                
    def _reset_process(self):
        """프로세스 초기화"""
        self.process_info.setText("선택된 프로세스 없음")
        self.capture_btn.setEnabled(False)
        
    def _capture_area(self):
        """영역 캡처"""
        if not self.selected_process:
            return
            
        # 선택된 프로세스 창을 최상위로 가져오기
        hwnd = self.selected_process['hwnd']
        
        # 창이 최소화되어 있다면 복원
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
        # 창을 최상위로 가져오고 활성화
        win32gui.SetForegroundWindow(hwnd)
        
        # 캡처 오버레이 표시 (타이머를 통해 지연 초기화)
        self.current_overlay = CaptureOverlay(hwnd, self)  # self를 부모로 전달
        self.current_overlay.setAttribute(Qt.WA_DeleteOnClose)  # 창이 닫힐 때 자동으로 메모리 해제
        self.current_overlay.show()
        
        # 모달 실행
        if self.current_overlay.exec_():
            self.captured_rect = self.current_overlay.captured_rect
            
            # 프로세스 창의 위치와 크기 가져오기
            window_rect = win32gui.GetWindowRect(hwnd)
            
            # 캡처할 영역 계산
            capture_rect = self.captured_rect
            x = window_rect[0] + capture_rect.x()
            y = window_rect[1] + capture_rect.y()
            width = capture_rect.width()
            height = capture_rect.height()
            
            # 스크린샷 캡처
            screen = QApplication.primaryScreen()
            self.captured_image = screen.grabWindow(
                0,
                x, y, width, height
            )
            
            # UI 업데이트
            self._update_capture_display()
            
    def _update_capture_display(self):
        """캡처된 이미지와 좌표 표시 업데이트"""
        if self.captured_image:
            # 이전 이미지 제거
            if self.capture_frame.layout().count() > 0:
                item = self.capture_frame.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 새 이미지 표시
            self.capture_label = QLabel()
            scaled_pixmap = self.captured_image.scaled(
                self.capture_frame.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.capture_label.setPixmap(scaled_pixmap)
            self.capture_frame.layout().addWidget(self.capture_label)
            
            # 좌표 표시
            self.top_left_x.setText(str(self.captured_rect.x()))
            self.top_left_y.setText(str(self.captured_rect.y()))
            self.top_right_x.setText(str(self.captured_rect.x() + self.captured_rect.width()))
            self.top_right_y.setText(str(self.captured_rect.y()))
            self.bottom_left_x.setText(str(self.captured_rect.x()))
            self.bottom_left_y.setText(str(self.captured_rect.y() + self.captured_rect.height()))
            self.bottom_right_x.setText(str(self.captured_rect.x() + self.captured_rect.width()))
            self.bottom_right_y.setText(str(self.captured_rect.y() + self.captured_rect.height()))
            
            # 저장 버튼 활성화
            self.save_btn.setEnabled(True)
            
    def _save_area(self):
        """캡처된 영역 저장"""
        if not self.captured_image or not self.selected_process:
            return
            
        # 저장할 디렉토리 생성
        save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'captures')
        os.makedirs(save_dir, exist_ok=True)
        
        # 현재 시간을 파일명에 포함
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 이미지 파일명 (타입 포함)
        image_filename = f"capture_{self.type_}_{timestamp}.png"
        image_path = os.path.join(save_dir, image_filename)
        
        # 캡처 정보
        capture_info = {
            'timestamp': timestamp,
            'process_name': self.selected_process['name'],
            'process_id': self.selected_process['pid'],
            'window_title': self.selected_process['title'],
            'coordinates': {
                'x': self.captured_rect.x(),
                'y': self.captured_rect.y(),
                'width': self.captured_rect.width(),
                'height': self.captured_rect.height()
            },
            'image_file': image_filename
        }
        
        try:
            # 이미지 저장
            self.captured_image.save(image_path)
            
            # 캡처 정보 JSON 파일에 저장 (타입별로 구분)
            json_path = os.path.join(save_dir, f'captures_{self.type_}.json')
            
            # 기존 데이터 로드 또는 새로운 리스트 생성
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    captures = json.load(f)
            else:
                captures = []
            
            # 새로운 캡처 정보 추가
            captures.append(capture_info)
            self.last_capture = capture_info  # 마지막 캡처 정보 업데이트
            
            # JSON 파일 저장
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(captures, f, indent=4, ensure_ascii=False)
            
            # 저장 성공 메시지
            QMessageBox.information(self, "저장 완료", "캡처 정보가 성공적으로 저장되었습니다.")
            
            # 성공적으로 저장되었음을 알리는 결과 설정
            self.setResult(QDialog.Accepted)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"캡처 정보 저장 중 오류가 발생했습니다.\n{str(e)}")
            
    def showEvent(self, event):
        """다이얼로그가 표시될 때 호출"""
        super().showEvent(event)
        # 저장된 캡처 정보가 있으면 로드
        if self.last_capture:
            self._load_saved_capture()
            
    def closeEvent(self, event):
        """다이얼로그가 닫힐 때 호출되는 이벤트"""
        # 현재 활성화된 오버레이가 있다면 닫기
        if self.current_overlay and not self.current_overlay.isHidden():
            self.current_overlay.close()
        super().closeEvent(event)