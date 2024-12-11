from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QSpinBox, QFrame, QRadioButton,
                              QButtonGroup, QLineEdit, QApplication)
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize, QTimer
from PySide6.QtGui import QScreen, QPixmap, QColor, QPainter, QPen, QBrush, QImage
from win32api import GetCursorPos
import win32gui
import win32con
from ..process_selector.process_selector_dialog import ProcessSelectorDialog


class CaptureOverlay(QDialog):
    """마우스 좌표 선택을 위한 오버레이 다이얼로그"""
    
    def __init__(self, parent=None, process_info=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.process_info = process_info
        self.mouse_pos = None
        self.window_image = None
        self.client_rect = None
        self.magnifier_size = QSize(150, 150)
        self.magnifier_scale = 2
        self.parent = parent
        
        # 반투명 오버레이 설정
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: transparent;")
        
        # 마우스 추적 활성화
        self.setMouseTracking(True)
        
        # 초기화 타이머 설정
        self.init_timer = QTimer(self)
        self.init_timer.setSingleShot(True)
        self.init_timer.timeout.connect(self._capture_window)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 초기화"""
        self.setCursor(Qt.CrossCursor)
        
    def _capture_window(self):
        """프로세스 창 캡처"""
        if not self.process_info or 'hwnd' not in self.process_info:
            self.parent._append_log("오류: 프로세스 정보가 없거나 잘못되었습니다.")
            self.reject()
            return
            
        hwnd = self.process_info['hwnd']
        self.parent._append_log(f"창 캡처 시작 - HWND: {hwnd}")
        
        try:
            # 창이 최소화되어 있다면 복원
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                self.parent._append_log("최소화된 창을 복원했습니다.")
            
            # 창을 활성화
            win32gui.SetForegroundWindow(hwnd)
            
            # 창의 클라이언트 영역 정보 가져오기
            rect = win32gui.GetWindowRect(hwnd)
            client_rect = win32gui.GetClientRect(hwnd)
            
            # 스크린 좌표로 변환
            point = win32gui.ClientToScreen(hwnd, (0, 0))
            self.client_x = point[0]
            self.client_y = point[1]
            self.client_width = client_rect[2]
            self.client_height = client_rect[3]
            
            self.parent._append_log(f"창 정보 - 클라이언트 영역: ({self.client_width}x{self.client_height}), 위치: ({self.client_x}, {self.client_y})")
            
            # 창 이미지 캡처
            screen = QApplication.primaryScreen()
            self.window_image = screen.grabWindow(0, self.client_x, self.client_y, 
                                                self.client_width, self.client_height)
            
            # 오버레이 위치 설정
            self.setGeometry(QRect(self.client_x, self.client_y, 
                                 self.client_width, self.client_height))
            
            self.parent._append_log("창 캡처 및 오버레이 설정 완료")
            
        except Exception as e:
            self.parent._append_log(f"창 캡처 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.reject()
            
    def paintEvent(self, event):
        """화면 그리기 이벤트"""
        if not self.window_image:
            return
            
        painter = QPainter(self)
        
        # 배경 이미지 그리기
        if not self.window_image.isNull():
            painter.drawPixmap(0, 0, self.window_image)
            
            # 반투명 어두운 오버레이
            overlay = QColor(0, 0, 0, 128)
            painter.fillRect(self.rect(), overlay)
            
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
        if not source_rect.intersected(self.rect()).isEmpty():
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
        
    def mouseMoveEvent(self, event):
        """마우스 이동 이벤트"""
        self.mouse_pos = event.pos()
        self.update()
        
    def mousePressEvent(self, event):
        """마우스 클릭 이벤트"""
        if event.button() == Qt.LeftButton:
            # 클릭 위치의 상대 좌표와 비율 계산
            pos = event.pos()
            relative_x = pos.x()
            relative_y = pos.y()
            
            # 좌표를 비율로 변환 (0.0 ~ 1.0)
            x_ratio = relative_x / self.client_width
            y_ratio = relative_y / self.client_height
            
            self.parent._append_log(f"마우스 클릭 감지 - 상대좌표: ({relative_x}, {relative_y})")
            self.parent._append_log(f"클라이언트 영역 크기: {self.client_width}x{self.client_height}")
            self.parent._append_log(f"계산된 비율 - X: {x_ratio:.3f}, Y: {y_ratio:.3f}")
            
            self.click_info = {
                'coordinates': {
                    'x': relative_x,
                    'y': relative_y
                },
                'ratios': {
                    'x': x_ratio,
                    'y': y_ratio
                }
            }
            
            self.parent._append_log(f"클릭 정보 생성 완료: {self.click_info}")
            self.accept()
            
    def get_click_info(self):
        """클릭 정보 반환"""
        return getattr(self, 'click_info', None)
    
    def showEvent(self, event):
        """오버레이가 표시될 때 호출"""
        super().showEvent(event)
        # 950ms 후에 캡처 시작
        self.init_timer.start(950)


class MouseInputDialog(QDialog):
    """마우스 입력을 받는 다이얼로그"""
    
    mouse_input_selected = Signal(dict)  # 선택된 마우스 입력 정보를 전송하는 시그널
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("마우스 입력")
        self.setFixedSize(400, 600)
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowStaysOnTopHint
        )
        
        self.selected_process = None
        self.click_ratios = None
        self.init_ui()
        
    def _append_log(self, message):
        """로그 메시지를 출력합니다."""
        formatted_message = f"<span style='color: #666666;'>[MouseInputDialog]</span> {message}"
        self.log_message.emit(formatted_message)
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 프로세스 선택 섹션
        process_section = QFrame()
        process_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        process_layout = QVBoxLayout(process_section)
        
        process_title = QLabel("프로세스")
        process_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        process_layout.addWidget(process_title)
        
        # 프로세스 정보 표시
        self.process_info = QLabel("선택된 프로세스 없음")
        self.process_info.setWordWrap(True)
        process_layout.addWidget(self.process_info)
        
        # 프로세스 선택/초기화 버튼
        process_button_layout = QHBoxLayout()
        process_button_layout.setSpacing(10)
        
        self.process_select_btn = QPushButton("프로세스 선택")
        self.process_reset_btn = QPushButton("프로세스 초기화")
        
        button_style = """
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3d8ce4;
            }
        """
        self.process_select_btn.setStyleSheet(button_style)
        self.process_reset_btn.setStyleSheet(button_style)
        
        process_button_layout.addWidget(self.process_select_btn)
        process_button_layout.addWidget(self.process_reset_btn)
        process_layout.addLayout(process_button_layout)
        
        layout.addWidget(process_section)
        
        # 마우스 동작 선택 섹션
        action_section = QFrame()
        action_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        action_layout = QVBoxLayout(action_section)
        
        action_title = QLabel("마우스 동작")
        action_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        action_layout.addWidget(action_title)
        
        # 마우스 동작 라디오 버튼 그룹
        self.action_group = QButtonGroup()
        
        click_radio = QRadioButton("클릭")
        click_radio.setChecked(True)
        self.action_group.addButton(click_radio, 1)
        action_layout.addWidget(click_radio)
        
        move_radio = QRadioButton("이동")
        self.action_group.addButton(move_radio, 2)
        action_layout.addWidget(move_radio)
        
        drag_radio = QRadioButton("드래그")
        self.action_group.addButton(drag_radio, 3)
        action_layout.addWidget(drag_radio)
        
        layout.addWidget(action_section)
        
        # 마우스 버튼 선택 섹션
        button_section = QFrame()
        button_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        button_layout = QVBoxLayout(button_section)
        
        button_title = QLabel("마우스 버튼")
        button_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        button_layout.addWidget(button_title)
        
        self.button_combo = QComboBox()
        self.button_combo.addItems(["왼쪽 버튼", "오른쪽 버튼", "가운데 버튼"])
        self.button_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        button_layout.addWidget(self.button_combo)
        
        layout.addWidget(button_section)
        
        # 좌표 입력 섹션
        coord_section = QFrame()
        coord_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        coord_layout = QVBoxLayout(coord_section)
        
        coord_title = QLabel("좌표")
        coord_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        coord_layout.addWidget(coord_title)
        
        # X 좌표
        x_layout = QHBoxLayout()
        x_label = QLabel("X:")
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(-9999, 9999)
        self.x_spinbox.setValue(0)
        self.x_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_spinbox)
        coord_layout.addLayout(x_layout)
        
        # Y 좌표
        y_layout = QHBoxLayout()
        y_label = QLabel("Y:")
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(-9999, 9999)
        self.y_spinbox.setValue(0)
        self.y_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_spinbox)
        coord_layout.addLayout(y_layout)
        
        # 좌표 선택/초기화 버튼
        coord_button_layout = QHBoxLayout()
        coord_button_layout.setSpacing(10)
        
        self.coord_select_btn = QPushButton("마우스 좌표 선택하기")
        self.coord_reset_btn = QPushButton("좌표 입력 초기화")
        
        button_style = """
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3d8ce4;
            }
        """
        self.coord_select_btn.setStyleSheet(button_style)
        self.coord_reset_btn.setStyleSheet(button_style)
        
        coord_button_layout.addWidget(self.coord_select_btn)
        coord_button_layout.addWidget(self.coord_reset_btn)
        coord_layout.addLayout(coord_button_layout)
        
        layout.addWidget(coord_section)
        
        # 마우스 동작 이름 섹션
        name_section = QFrame()
        name_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        name_layout = QVBoxLayout(name_section)
        
        name_title = QLabel("마우스 동작 이름")
        name_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_layout.addWidget(name_title)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("마우스 동작 이름을 입력하세요")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)
        name_layout.addWidget(self.name_input)
        
        layout.addWidget(name_section)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        confirm_btn = QPushButton("마우스 입력 정보 저장")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        cancel_btn = QPushButton("마우스 입력 취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 시그널 연결
        confirm_btn.clicked.connect(self._on_confirm)
        cancel_btn.clicked.connect(self.reject)
        self.coord_select_btn.clicked.connect(self._select_coordinates)
        self.coord_reset_btn.clicked.connect(self._reset_coordinates)
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        
    def _select_process(self):
        """프로세스 선택 다이얼로그 표시"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec():
            self.selected_process = dialog.selected_process
            if self.selected_process:
                process_info_text = f"[ PID : {self.selected_process['pid']} ] {self.selected_process['name']} - {self.selected_process['title']}"
                self.process_info.setText(process_info_text)
            
    def _reset_process(self):
        """프로세스 선택 초기화"""
        self.selected_process = None
        self.process_info.setText("선택된 프로세스 없음")
        
    def _select_coordinates(self):
        """마우스 좌표 선택"""
        if not self.selected_process:
            self._append_log("프로세스가 선택되지 않았습니다.")
            return
            
        self._append_log(f"좌표 선택 시작 - 선택된 프로세스: {self.selected_process}")
        overlay = CaptureOverlay(self, self.selected_process)
        
        if overlay.exec() == QDialog.Accepted:
            click_info = overlay.get_click_info()
            self._append_log(f"클릭 정보 수신: {click_info}")
            
            if click_info:
                # 좌표 정보 저장
                coordinates = click_info['coordinates']
                self._append_log(f"좌표 정보 저장 시도 - X: {coordinates['x']}, Y: {coordinates['y']}")
                self.x_spinbox.setValue(coordinates['x'])
                self.y_spinbox.setValue(coordinates['y'])
                
                # 비율 정보 저장
                ratios = click_info['ratios']
                self._append_log(f"비율 정보 저장 시도 - X비율: {ratios['x']:.3f}, Y비율: {ratios['y']:.3f}")
                self.click_ratios = ratios
                
                self._append_log("좌표 및 비율 정보 저장 완료")
            else:
                self._append_log("오류: 클릭 정보가 없습니다.")
        else:
            self._append_log("좌표 선택이 취소되었습니다.")
                
    def _reset_coordinates(self):
        """좌표 입력 초기화"""
        self._append_log("좌표 입력 초기화 시작")
        self.x_spinbox.setValue(0)
        self.y_spinbox.setValue(0)
        self.click_ratios = None
        self._append_log("좌표 및 비율 정보 초기화 완료")
        
    def _on_confirm(self):
        """확인 버튼 클릭 시 호출"""
        self._append_log("마우스 입력 정보 저장 시작")
        
        if not self.name_input.text().strip():
            self._append_log("오류: 이름이 입력되지 않았습니다.")
            return
            
        # 선택된 정보 수집
        action_id = self.action_group.checkedId()
        action_map = {1: "클릭", 2: "이동", 3: "드래그"}
        action = action_map.get(action_id, "클릭")
        
        button = self.button_combo.currentText()
        x = self.x_spinbox.value()
        y = self.y_spinbox.value()
        name = self.name_input.text().strip()
        
        self._append_log(f"수집된 정보 - 동작: {action}, 버튼: {button}, 좌표: ({x}, {y}), 이름: {name}")
        self._append_log(f"선택된 프로세스 정보: {self.selected_process}")
        
        if not hasattr(self, 'click_ratios') or self.click_ratios is None:
            self._append_log("경고: 비율 정보가 없습니다.")
            self.click_ratios = {'x': 0, 'y': 0}
        else:
            self._append_log(f"비율 정보: {self.click_ratios}")
        
        # 마우스 입력 정보 생성
        mouse_info = {
            'type': 'mouse_input',
            'name': name,
            'action': action,
            'button': button,
            'coordinates': {'x': x, 'y': y},
            'ratios': self.click_ratios,
            'process': self.selected_process,
            'display_text': f"마우스 입력: {name} ({x}, {y})",
            'order': 0  # 순서는 LogicDetailWidget에서 설정됨
        }
        
        self._append_log(f"생성된 마우스 입력 정보: {mouse_info}")
        
        # 시그널 발생
        self._append_log("마우스 입력 정보 전송 시작")
        self.mouse_input_selected.emit(mouse_info)
        self._append_log("마우스 입력 정보 전송 완료")
        self.accept() 