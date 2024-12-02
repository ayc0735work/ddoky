from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QFrame, QLineEdit,
                              QGridLayout, QWidget, QRubberBand, QApplication,
                              QMessageBox)
from PySide6.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PySide6.QtGui import QScreen, QPixmap, QColor, QPainter, QPen, QBrush, QImage
import win32gui
import win32con
import json
import os
from datetime import datetime
import time
import cv2
import numpy as np
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
        
        # 마우스 추적을 위한 변수
        self.mouse_pos = None
        
        # 윈도우 정보 가져오기
        window_rect = win32gui.GetWindowRect(self.target_hwnd)
        client_rect = win32gui.GetClientRect(self.target_hwnd)
        
        # 프라이언트 영역 크기 저장
        self.client_width = client_rect[2]
        self.client_height = client_rect[3]
        
        # 프레임 크기 계산
        self.frame_x = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
        self.frame_y = (window_rect[3] - window_rect[1]) - client_rect[3] - self.frame_x
        
        # 클라이언트 영역의 실제 좌표 계산
        self.client_x = window_rect[0] + self.frame_x
        self.client_y = window_rect[1] + self.frame_y
        
        # 오버레이 위치와 크기 설정
        self.setGeometry(
            window_rect[0], window_rect[1],
            window_rect[2] - window_rect[0],
            window_rect[3] - window_rect[1]
        )
        
        # 반투명 오버레이 설정
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        
        # 초기 이미지와 확대경 설정
        self.window_image = QPixmap()
        self.magnifier_size = QSize(120, 120)
        self.magnifier_scale = 2.0
        
        # 마우스 추적 활성화
        self.setMouseTracking(True)
        
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
        """화면 그리기 이벤트"""
        painter = QPainter(self)
        
        # 배경 이미지 그리기
        if hasattr(self, 'window_image') and not self.window_image.isNull():
            painter.drawPixmap(0, 0, self.window_image)
            
            # 반투명 어두운 오버레이
            overlay = QColor(0, 0, 0, 128)
            painter.fillRect(self.rect(), overlay)
            
            # 캡처 영역 그리기
            if self.start_pos and self.current_pos:
                capture_rect = QRect(self.start_pos, self.current_pos).normalized()
                
                # 선택 영역은 원본 이미지 보이게
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.drawPixmap(capture_rect, self.window_image, capture_rect)
                
                # 선택 영역 테두리 그리기
                pen = QPen(QColor(0, 120, 215), 1)
                painter.setPen(pen)
                painter.drawRect(capture_rect)
                
                # 크기 정보 표시
                size_text = f"{capture_rect.width()} x {capture_rect.height()}"
                text_rect = capture_rect.adjusted(0, -25, 0, 0)
                painter.setPen(Qt.white)
                painter.drawText(text_rect, Qt.AlignCenter, size_text)
            
            # 마우스 위치에 돋보기 그리기
            if self.mouse_pos:
                self._draw_magnifier(painter, self.mouse_pos)
    
    def _draw_magnifier(self, painter, pos):
        """돋보기 그리기"""
        # 확대경이 표시될 위치 계산
        magnifier_x = pos.x() + 20
        magnifier_y = pos.y() - self.magnifier_size.height() - 20
        
        # 화면 경계를 벗어나지 않도록 조정
        if magnifier_x + self.magnifier_size.width() > self.width():
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
        
        # 현재 좌표 표시
        coord_text = f"X: {pos.x()}, Y: {pos.y()}"
        text_rect = QRect(
            magnifier_x,
            magnifier_y + self.magnifier_size.height() + 5,
            self.magnifier_size.width(),
            20
        )
        painter.setPen(Qt.white)
        painter.drawText(text_rect, Qt.AlignCenter, coord_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.current_pos = event.pos()
            self.is_capturing = True
            self.update()
    
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        self.mouse_pos = event.pos()
        if self.is_capturing:
            self.current_pos = event.pos()
        self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_capturing:
            self.is_capturing = False
            if self.start_pos and self.current_pos:
                # 전체 화면 기준 캡처 영역
                screen_rect = QRect(self.start_pos, self.current_pos).normalized()
                
                # 클라이언트 영역 기준 상대 좌표로 변환
                relative_x = screen_rect.x() - self.frame_x
                relative_y = screen_rect.y() - self.frame_y
                
                # 대 좌표를 비율로 변환 (0.0 ~ 1.0)
                x_ratio = relative_x / self.client_width
                y_ratio = relative_y / self.client_height
                width_ratio = screen_rect.width() / self.client_width
                height_ratio = screen_rect.height() / self.client_height
                
                # 비율 정보를 포함한 캡처 영역 저장
                self.captured_rect = {
                    'x_ratio': x_ratio,
                    'y_ratio': y_ratio,
                    'width_ratio': width_ratio,
                    'height_ratio': height_ratio,
                    'x': relative_x,
                    'y': relative_y,
                    'width': screen_rect.width(),
                    'height': screen_rect.height()
                }
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
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.settings_path = os.path.join(self.base_path, 'settings.json')
        self.captures_dir = os.path.join(self.base_path, 'captures')
        os.makedirs(self.captures_dir, exist_ok=True)
        
        # 저장된 캡처 정보
        self.saved_captures = []
        self.last_capture = None
        
        # UI 초기화 먼저 실행
        self.init_ui()
        
        # 오버레이 초기화
        self.current_overlay = None
        
        # UI 초기화 후에 마지막 저장된 캡처 정보 로드
        self._load_last_capture()
        
        # 시그널 연결 (UI 초기화 후에 호출)
        self._connect_signals()

    def _connect_signals(self):
        """시그널 연결"""
        # 프로세스 관련 버튼
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        
        # 캡처 관련 버튼
        self.capture_btn.clicked.connect(self._capture_area)
        self.reset_btn.clicked.connect(self._reset_capture_area)  # 캡처 초기화 버튼
        
        # 저장/취소 버튼
        self.save_btn.clicked.connect(self._save_area)
        self.cancel_btn.clicked.connect(self.reject)

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
        self.capture_btn.setEnabled(False)
        self.reset_btn = QPushButton("캡처 영역 초기화")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0f0;
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

    def _reset_capture_area(self):
        """캡처 영역 초기화 (UI에서만)"""
        # 로그 시그널 발생 (부모 위젯의 log_message 시그널 사용)
        log_type = "체력" if self.type_ == "hp" else "마력"
        self.parent().advanced_action.emit(f"[고급 기능] {log_type} 캡처 영역 초기화를 시작합니다.")
        
        # 캡처된 이미지 초기화
        self.captured_image = None
        self.captured_rect = None
        
        # 좌표 입력란 초기화
        self.top_left_x.clear()
        self.top_left_y.clear()
        self.top_right_x.clear()
        self.top_right_y.clear()
        self.bottom_left_x.clear()
        self.bottom_left_y.clear()
        self.bottom_right_x.clear()
        self.bottom_right_y.clear()
        
        # 캡처 프레임 초기화
        if self.capture_frame.layout().count() > 0:
            item = self.capture_frame.layout().takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 안내 텍스트 다시 표시
        guide_label = QLabel("캡처된 이미지가 없습니다.\n영역을 지정해주세요.")
        guide_label.setAlignment(Qt.AlignCenter)
        guide_label.setStyleSheet("color: #666;")
        self.capture_frame.layout().addWidget(guide_label)
        
        # 저장 버튼 비활성화
        self.save_btn.setEnabled(False)
        
        # 초기화 완료 로그
        self.parent().advanced_action.emit(f"[고급 기능] {log_type} 캡처 영역이 초기화되었습니다.")

    def _load_last_capture(self):
        """마지막으로 저장된 캡처 정보 로드"""
        try:
            # settings.json 파일 로드
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            gauge_monitor = settings.get('gauge_monitor', {})
            gauge_type = 'hp_gauge' if self.type_ == 'hp' else 'mp_gauge'
            gauge_info = gauge_monitor.get(gauge_type, {})
            
            if gauge_info:
                # 좌표 정보 로드
                if 'coordinates' in gauge_info:
                    coordinates = gauge_info['coordinates']
                    self.captured_rect = {
                        'x': coordinates['x'],
                        'y': coordinates['y'],
                        'width': coordinates['width'],
                        'height': coordinates['height']
                    }
                    
                    # 비율 정보가 있다면 추가
                    if 'ratios' in gauge_info:
                        self.captured_rect.update({
                            'x_ratio': gauge_info['ratios']['x'],
                            'y_ratio': gauge_info['ratios']['y'],
                            'width_ratio': gauge_info['ratios']['width'],
                            'height_ratio': gauge_info['ratios']['height']
                        })
                
                # 이미지 파일 로드
                image_file = gauge_info.get('image_file', '')
                if image_file:
                    # 경로 정규화 - captures가 포함된 모든 부분 제거
                    image_file = os.path.basename(image_file)
                    image_path = os.path.normpath(os.path.join(self.base_path, 'captures', image_file))
                    
                    if os.path.exists(image_path):
                        # QPixmap으로 이미지 로드
                        self.captured_image = QPixmap(image_path)
                        if not self.captured_image.isNull():
                            print(f"이미지 로드 성공: {image_path}")
                            self._update_capture_display()  # UI 업데이트
                        else:
                            print(f"이미지 로드 실패: {image_path}")
                    else:
                        print(f"이미지 파일이 존재하지 않습니다: {image_path}")
            
        except Exception as e:
            print(f"캡처 정보 로드 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

    def _save_capture(self, image, gauge_type):
        """캡처 이미지 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{gauge_type}.png"
        filepath = os.path.normpath(os.path.join(self.captures_dir, filename))
        
        # captures 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            # QPixmap을 QImage로 변환하고 저장
            if isinstance(image, QPixmap):
                image.save(filepath, "PNG")
                print(f"이미지 저장 성공: {filepath}")
            else:
                print("이미지 형식 오류: QPixmap이 아닙니다")
                return None, None
        except Exception as e:
            print(f"이미지 저장 중 오류 발생: {str(e)}")
            return None, None
        
        # settings.json에 저장될 상대 경로
        relative_path = os.path.join('captures', filename)
        return relative_path, timestamp

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
        
        # 캡처 오버레이 표시
        self.current_overlay = CaptureOverlay(hwnd, self)
        self.current_overlay.setAttribute(Qt.WA_DeleteOnClose)
        self.current_overlay.show()
        
        # 모달 실행
        if self.current_overlay.exec_():
            # 상대 좌표와 비율 정보가 포함된 캡처 영역 저장
            self.captured_rect = self.current_overlay.captured_rect
            
            # 윈도우 정보 가져오기
            window_rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 프레임 크기 계산
            frame_x = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
            frame_y = (window_rect[3] - window_rect[1]) - client_rect[3] - frame_x
            
            # 클라이언트 영역의 실제 좌표 계산
            client_x = window_rect[0] + frame_x
            client_y = window_rect[1] + frame_y
            
            # 캡처할 영역 계산 (상대 좌표를 화면 좌표로 변환)
            x = client_x + self.captured_rect['x']
            y = client_y + self.captured_rect['y']
            width = self.captured_rect['width']
            height = self.captured_rect['height']
            
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
        if self.captured_image and not self.captured_image.isNull():
            # 이전 이미지 제거
            if self.capture_frame.layout().count() > 0:
                item = self.capture_frame.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # 새 이미지 표시
            self.capture_label = QLabel()
            scaled_pixmap = self.captured_image.scaled(
                self.capture_frame.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.capture_label.setPixmap(scaled_pixmap)
            self.capture_frame.layout().addWidget(self.capture_label)
            
            # 좌표 표시 (픽셀 단위)
            self.top_left_x.setText(str(self.captured_rect['x']))
            self.top_left_y.setText(str(self.captured_rect['y']))
            self.top_right_x.setText(str(self.captured_rect['x'] + self.captured_rect['width']))
            self.top_right_y.setText(str(self.captured_rect['y']))
            self.bottom_left_x.setText(str(self.captured_rect['x']))
            self.bottom_left_y.setText(str(self.captured_rect['y'] + self.captured_rect['height']))
            self.bottom_right_x.setText(str(self.captured_rect['x'] + self.captured_rect['width']))
            self.bottom_right_y.setText(str(self.captured_rect['y'] + self.captured_rect['height']))
            
            # 저장 버튼 활성화
            self.save_btn.setEnabled(True)

    def _save_area(self):
        """캡처된 영역 저장"""
        try:
            # 현재 settings.json 로드
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            if not self.captured_image:
                # 캡처된 이미지가 없는 경우 (초기화 상태로 저장)
                gauge_type = 'hp_gauge' if self.type_ == 'hp' else 'mp_gauge'
                if 'gauge_monitor' in settings:
                    if gauge_type in settings['gauge_monitor']:
                        del settings['gauge_monitor'][gauge_type]
                
                log_type = "체력" if self.type_ == "hp" else "마력"
                self.parent().advanced_action.emit(f"[고급 기능] {log_type} 캡처 정보가 초기화되었습니다.")
                self.last_capture = None
                
                # 변경된 설정 저장
                with open(self.settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                
                self.close()
                return
            
            # 캡처된 이미지가 있는 경우 새로운 정보 저장
            image_file, timestamp = self._save_capture(self.captured_image, self.type_)
            
            # 캡처 정보 생성 (비율과 픽셀 좌표 모두 저장)
            capture_info = {
                'coordinates': {
                    'x': self.captured_rect['x'],
                    'y': self.captured_rect['y'],
                    'width': self.captured_rect['width'],
                    'height': self.captured_rect['height']
                },
                'ratios': {
                    'x': self.captured_rect['x_ratio'],
                    'y': self.captured_rect['y_ratio'],
                    'width': self.captured_rect['width_ratio'],
                    'height': self.captured_rect['height_ratio']
                },
                'image_file': image_file,
                'timestamp': timestamp
            }
            
            # settings.json 업데이트
            if 'gauge_monitor' not in settings:
                settings['gauge_monitor'] = {}
            
            gauge_type = 'hp_gauge' if self.type_ == 'hp' else 'mp_gauge'
            settings['gauge_monitor'][gauge_type] = capture_info
            
            # 변경된 설정 저장
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            # 저장 성공 메시지
            log_type = "체력" if self.type_ == "hp" else "마력"
            QMessageBox.information(self, "저장 완료", f"{log_type} 캡처 정보가 성공적으로 저장되었습니다.")
            
            # 저장 완료 로그
            self.parent().advanced_action.emit(f"[고급 기능] {log_type} 캡처 정보가 저장되었습니다.")
            
            # 모달을 닫기 전에 last_capture 초기화
            self.last_capture = None
            
            # 저장 후 바로 닫기
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