from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QGuiApplication

from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_widget import EnteredKeyInfoWidget
from BE.function._common_components.modal.entered_key_info_modal.keyboard_hook_handler import KeyboardHook
from BE.log.manager.base_log_manager import BaseLogManager

class EnteredKeyInfoDialog(QDialog):
    """키 입력 모달 창을 제공하고 키를 입력 받고 처리하는 다이얼로그
    
    이 다이얼로그는:
    1. EnteredKeyInfoWidget을 통한 UI 표시
    2. KeyboardHook을 통한 키 입력 처리
    3. 키 데이터의 유효성 검사와 저장
    를 담당합니다.
    """
    
    key_input_changed = Signal(dict)  # 키 입력이 변경되었을 때
    
    def __init__(self, parent=None, show_details=True):
        """EnteredKeyInfoDialog 초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
            show_details (bool): 키 입력 상세 정보 표시 여부
        """
        super().__init__(parent)
        self.setWindowTitle("키 입력")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # ESC 키로 닫히는 것을 방지하기 위한 플래그 설정
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowStaysOnTopHint 
            | Qt.CustomizeWindowHint 
            | Qt.WindowTitleHint 
            | Qt.WindowCloseButtonHint
        )
        
        self.last_key_info = None
        self.keyboard_hook = None
        self.modal_log_manager = BaseLogManager.instance()
        
        self._setup_ui(show_details)
        self._setup_connections()
    
    def _setup_ui(self, show_details):
        """UI 컴포넌트 초기화 및 배치"""
        KeyInputLayout__QVBoxLayout = QVBoxLayout()
        
        # 안내 메시지
        GuideLabel__QLabel = QLabel("입력하려는 키를 누르세요")
        GuideLabel__QLabel.setAlignment(Qt.AlignCenter)
        KeyInputLayout__QVBoxLayout.addWidget(GuideLabel__QLabel)
        
        # NumLock 경고 메시지
        self.NumLockWarning__QLabel = QLabel()
        self.NumLockWarning__QLabel.setStyleSheet("color: red;")
        self.NumLockWarning__QLabel.setAlignment(Qt.AlignCenter)
        self.NumLockWarning__QLabel.setWordWrap(True)
        KeyInputLayout__QVBoxLayout.addWidget(self.NumLockWarning__QLabel)
        
        # 키 입력 위젯
        self.entered_key_info_widget = EnteredKeyInfoWidget(self, show_details)
        KeyInputLayout__QVBoxLayout.addWidget(self.entered_key_info_widget)
        
        # 키 정보 라벨
        self.KeyInfoLabel__QLabel = QLabel()
        self.KeyInfoLabel__QLabel.setWordWrap(True)
        KeyInputLayout__QVBoxLayout.addWidget(self.KeyInfoLabel__QLabel)
        
        # 버튼 레이아웃
        KeyInputButtonSection__QHBoxLayout = QHBoxLayout()
        
        # 확인 버튼
        self.ConfirmButton__QPushButton = QPushButton("입력된 키 정보 저장")
        self.ConfirmButton__QPushButton.clicked.connect(self._on_confirm)
        KeyInputButtonSection__QHBoxLayout.addWidget(self.ConfirmButton__QPushButton)
        
        # 취소 버튼
        self.CancelButton__QPushButton = QPushButton("키 입력 취소")
        self.CancelButton__QPushButton.clicked.connect(self.reject)
        KeyInputButtonSection__QHBoxLayout.addWidget(self.CancelButton__QPushButton)
        
        KeyInputLayout__QVBoxLayout.addLayout(KeyInputButtonSection__QHBoxLayout)
        self.setLayout(KeyInputLayout__QVBoxLayout)
    
    def _setup_connections(self):
        """시그널/슬롯 연결"""
        self.entered_key_info_widget.key_input_area_focused.connect(self._start_keyboard_hook)
        self.entered_key_info_widget.key_input_area_unfocused.connect(self._stop_keyboard_hook)
    
    def _start_keyboard_hook(self):
        """키보드 훅 시작"""
        if not self.keyboard_hook:
            self.keyboard_hook = KeyboardHook()
            self.keyboard_hook.key_pressed.connect(self._on_key_pressed)
            self.keyboard_hook.start()
    
    def _stop_keyboard_hook(self):
        """키보드 훅 중지"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
    
    def _on_key_pressed(self, formatted_key_info):
        """키가 눌렸을 때의 처리
        
        Args:
            formatted_key_info (dict): 구조화된 키 정보
        """
        # 이전 키 정보와 동일한 경우 무시
        if (self.last_key_info and 
            self.last_key_info['key_code'] == formatted_key_info['key_code'] and
            self.last_key_info['modifiers'] == formatted_key_info['modifiers'] and
            self.last_key_info['scan_code'] == formatted_key_info['scan_code']):
            return
        
        # 키 정보 업데이트
        self.last_key_info = formatted_key_info.copy()
        
        # UI 업데이트
        self.entered_key_info_widget.update_key_info(formatted_key_info)
        
        # NumLock 상태 체크 및 경고
        self._check_numlock_state()
        
        # 키 정보 변경 시그널 발생
        self.key_input_changed.emit(formatted_key_info)
    
    def _check_numlock_state(self):
        """NumLock 상태를 체크하고 경고 메시지를 표시"""
        if self.last_key_info and self.last_key_info.get('is_numpad'):
            self.NumLockWarning__QLabel.setText(
                "주의: 숫자 패드 키를 입력했습니다. NumLock 상태에 따라 키가 다르게 동작할 수 있습니다."
            )
        else:
            self.NumLockWarning__QLabel.clear()
    
    def keyPressEvent(self, event: QKeyEvent):
        """키 이벤트 처리"""
        # ESC와 Enter 키를 무시
        if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
            event.ignore()
        else:
            super().keyPressEvent(event)
    
    def get_entered_key_info(self):
        """현재 입력된 키 정보를 반환합니다.
        
        이 메서드는 키보드 훅을 통해 캡처된 raw_key_info를 create_formatted_key_info()를 통해
        구조화한 formatted_key_info를 반환합니다.
        
        Returns:
            dict or None: 구조화된 키 정보를 포함하는 딕셔너리. 또는 키 정보가 없으면 None
        
        Note:
            이 메서드는 캡슐화를 통해 키 정보에 대한 안전한 접근을 제공합니다.
            외부에서는 last_key_info 속성에 직접 접근하지 않고 이 메서드를 통해
            구조화된 키 정보를 얻을 수 있습니다.
        """
        return self.last_key_info
    
    def set_formatted_key_info(self, formatted_key_info):
        """구조화된 키 정보를 설정하고 관련 UI를 업데이트합니다.
        
        Args:
            formatted_key_info (dict): 구조화된 키 정보 딕셔너리
                None이거나 빈 딕셔너리인 경우 무시됩니다.
                
        동작:
            1. 키 정보를 내부 상태(last_key_info)에 저장
            2. UI 위젯 업데이트
            3. NumLock 상태 확인
            4. key_input_changed 시그널 발생
        """
        if not formatted_key_info:  # None이거나 빈 딕셔너리인 경우 설정하지 않음
            return
        
        self.last_key_info = formatted_key_info
        self.entered_key_info_widget.set_key_info(formatted_key_info)
        self._check_numlock_state()
        self.key_input_changed.emit(formatted_key_info)  # 시그널 발생
    
    def clear_key(self):
        """키 입력 초기화"""
        self.last_key_info = None
        self.entered_key_info_widget.clear_key()
        self.NumLockWarning__QLabel.clear()
        self.key_input_changed.emit({})
    
    def _on_confirm(self):
        """확인 버튼 클릭 시"""
        confirmed_key_info = self.get_entered_key_info()
        if confirmed_key_info: # 키 정보가 있는 경우
            self.accept()  # 다이얼로그가 성공적으로 완료되면 창을 닫고 데이터를 사용해도 좋다는 이벤트 전달
            self.modal_log_manager.log(
                message="키 입력 모달의 확인버튼이 클릭되었습니다.<br>",
                level="INFO",
                modal_name="키입력모달"
            )
    
    def closeEvent(self, event):
        """다이얼로그가 닫힐 때 키보드 훅 정리"""
        self._stop_keyboard_hook()
        super().closeEvent(event)