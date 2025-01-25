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
from BE.function._common_components.modal.window_process_selector.window_process_selector_modal import ProcessSelectorDialog

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
        
        # 클라이언트 영역 정보 가져오기
        client_info = self._get_client_rect(target_hwnd)
        if not client_info:
            raise Exception("클라이언트 영역 정보를 가져올 수 없습니다.")
        
        # 클라이언트 영역 정보 저장
        self.client_x = client_info['x']
        self.client_y = client_info['y']
        self.client_width = client_info['width']
        self.client_height = client_info['height']
        
        # 오버레이 위치와 크기 설정 (전체 창 기준)
        self.setGeometry(
            client_info['window_x'],
            client_info['window_y'],
            client_info['window_width'],
            client_info['window_height']
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
        
    def _get_client_rect(self, hwnd):
        """클라이언트 영역 정보 가져오기"""
        try:
            # 윈도우 전체 영역
            window_rect = win32gui.GetWindowRect(hwnd)
            # 클라이언트 영역
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 프레임 크기 계산
            frame_x = ((window_rect[2] - window_rect[0]) - client_rect[2]) // 2
            frame_y = (window_rect[3] - window_rect[1]) - client_rect[3] - frame_x
            
            return {
                'window_x': window_rect[0],
                'window_y': window_rect[1],
                'window_width': window_rect[2] - window_rect[0],
                'window_height': window_rect[3] - window_rect[1],
                'x': frame_x,
                'y': frame_y,
                'width': client_rect[2],
                'height': client_rect[3]
            }
        except Exception as e:
            self.base_log_manager.log(
                message=f"클라이언트 영역 정보 가져오기 실패: {str(e)}",
                level="ERROR",
                file_name="image_search_area_dialog",
                method_name="_get_client_rect",
                print_to_terminal=True
            )
            return None
        
    def showEvent(self, event):
        """오버레이가 표시될 때 호출"""
        super().showEvent(event)
        # 지정된 시간 후에 초기화 함수 호출
        self.init_timer.start(950)
        
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
        """마우스 클릭 이벤트"""
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
        """마우스 릴리즈 이벤트"""
        if event.button() == Qt.LeftButton and self.is_capturing:
            self.is_capturing = False
            if self.start_pos and self.current_pos:
                capture_rect = QRect(self.start_pos, self.current_pos).normalized()
                
                # 상대 좌표 계산
                relative_rect = {
                    'x': capture_rect.x(),
                    'y': capture_rect.y(),
                    'width': capture_rect.width(),
                    'height': capture_rect.height(),
                    'x_ratio': capture_rect.x() / self.client_width,
                    'y_ratio': capture_rect.y() / self.client_height,
                    'width_ratio': capture_rect.width() / self.client_width,
                    'height_ratio': capture_rect.height() / self.client_height
                }
                
                self.captured_rect = relative_rect
                self.accept()

class ImageSearchAreaDialog(QDialog):
    """이미지 서치 체크 설정 모달"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle("이미지 서치 체크 설정 모달")
        self.setFixedSize(600, 500)
        
        # 변수 초기화
        self.selected_process = None
        self.captured_image = None
        self.captured_rect = None
        
        # 설정 파일 경로
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.captures_dir = os.path.join(self.base_path, 'captures')
        os.makedirs(self.captures_dir, exist_ok=True)
        
        # UI 초기화
        self.init_ui()
        
        # 오버레이 초기화
        self.current_overlay = None
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 프로세스 선택 영역
        process_frame = QFrame()
        process_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 5px; }")
        process_layout = QHBoxLayout(process_frame)
        
        self.process_label = QLabel("선택된 프로세스: 없음")
        self.process_select_btn = QPushButton("프로세스 선택")
        self.process_reset_btn = QPushButton("초기화")
        
        process_layout.addWidget(self.process_label)
        process_layout.addWidget(self.process_select_btn)
        process_layout.addWidget(self.process_reset_btn)
        
        layout.addWidget(process_frame)
        
        # 캡처 영역
        capture_frame = QFrame()
        capture_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-radius: 5px; }")
        capture_layout = QVBoxLayout(capture_frame)
        
        # 캡처 정보 표시
        self.capture_info = QLabel("캡처된 영역: 없음")
        capture_layout.addWidget(self.capture_info)
        
        # 캡처 이미지 표시
        self.capture_image_label = QLabel()
        self.capture_image_label.setFixedSize(200, 100)
        self.capture_image_label.setStyleSheet("QLabel { background-color: white; border: 1px solid #ccc; }")
        self.capture_image_label.setAlignment(Qt.AlignCenter)
        capture_layout.addWidget(self.capture_image_label)
        
        # 캡처 버튼
        self.capture_btn = QPushButton("영역 캡처")
        capture_layout.addWidget(self.capture_btn)
        
        layout.addWidget(capture_frame)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("저장")
        self.cancel_btn = QPushButton("취소")
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 시그널 연결
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        self.capture_btn.clicked.connect(self._capture_area)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def _select_process(self):
        """프로세스 선택"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_process = dialog.selected_process
            self.process_label.setText(f"선택된 프로세스: {self.selected_process['name']}")
            self.capture_btn.setEnabled(True)
        
    def _reset_process(self):
        """프로세스 초기화"""
        self.selected_process = None
        self.process_label.setText("선택된 프로세스: 없음")
        self.capture_btn.setEnabled(False)
        self._reset_capture_area()
        
    def _reset_capture_area(self):
        """캡처 영역 초기화"""
        self.captured_rect = None
        self.captured_image = None
        self.capture_info.setText("캡처된 영역: 없음")
        self.capture_image_label.clear()
        self.capture_image_label.setText("캡처된 이미지 없음")
        
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
        if self.current_overlay.exec_() == QDialog.Accepted:
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
        if self.captured_rect and self.captured_image:
            # 캡처 정보 업데이트
            self.capture_info.setText(
                f"캡처된 영역: ({self.captured_rect['x']}, {self.captured_rect['y']}) "
                f"{self.captured_rect['width']}x{self.captured_rect['height']}"
            )
            
            # 이미지 표시
            scaled_image = self.captured_image.scaled(
                self.capture_image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.capture_image_label.setPixmap(scaled_image)
            
    def closeEvent(self, event):
        """다이얼로그가 닫힐 때 호출되는 이벤트"""
        if self.current_overlay:
            self.current_overlay.close()
        event.accept()
