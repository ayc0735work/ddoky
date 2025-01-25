from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QGuiApplication

from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_widget import EnteredKeyInfoWidget
from BE.function._common_components.modal.entered_key_info_modal.keyboard_hook_handler import KeyboardHook
from BE.log.base_log_manager import BaseLogManager

class EnteredKeyInfoDialog(QDialog):
    """키 입력 모달 창을 제공하고 키를 입력 받고 처리하는 다이얼로그
    
    이 다이얼로그는:
    1. EnteredKeyInfoWidget을 통한 UI 표시
    2. KeyboardHook을 통한 키 입력 처리
    3. 키 데이터의 유효성 검사와 저장
    를 담당합니다.
    
    Returns:
        dict or None: 다이얼로그가 accept로 닫힌 경우 키 정보를, reject로 닫힌 경우 None을 반환
    """
    
    formatted_key_info_changed = Signal(dict)  # 키 입력이 변경되었을 때
    
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
        
        self.keyboard_hook = None
        self.modal_log_manager = BaseLogManager.instance()
        self._result_key_info = None  # 다이얼로그 결과값 저장
        self._current_formatted_key_info = None  # 현재 입력된 키 정보
        
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
        self.ConfirmButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
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
            self.keyboard_hook.key_pressed.connect(self._on_key_pressed) # key_pressed만 사용. 즉 키가 눌린 시점에 정보가 전달됨. key_released는 현재는 사용하지 않음.
            self.keyboard_hook.start()
    
    def _stop_keyboard_hook(self):
        """키보드 훅 중지"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
    
    def _on_key_pressed(self, formatted_key_info):
        """키가 눌렸을 때 formatted_key_info를 받아와서 처리 하는 로직
        UI 업데이트를 하고, Numlock 상태 체크를 하고, 키 정보 변경 시그널을 보내고, 확인 버튼 활성화 상태 업데이트를 한다
        """
        self.modal_log_manager.log(
            message=f"_on_key_pressed - 입력받은 데이터(formatted_key_info): {formatted_key_info}",
            level="DEBUG",
            file_name="entered_key_info_dialog"
        )
        
        # 키 정보 저장
        self._current_formatted_key_info = formatted_key_info
        
        # UI 업데이트
        self.entered_key_info_widget.update_key_info(formatted_key_info)
        
        # NumLock 상태 체크 및 경고
        if formatted_key_info and formatted_key_info.get('is_numpad'):
            self.NumLockWarning__QLabel.setText(
                "주의: 숫자 패드 키를 입력했습니다. NumLock 상태에 따라 키가 다르게 동작할 수 있습니다."
            )
        else:
            self.NumLockWarning__QLabel.clear()
        
        # 확인 버튼 활성화 상태 업데이트
        self.ConfirmButton__QPushButton.setEnabled(bool(formatted_key_info))
    
    def keyPressEvent(self, event: QKeyEvent):
        """키 이벤트 처리"""
        # ESC와 Enter 키를 무시
        if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def clear_key(self):
        """키 입력 초기화"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
        self.entered_key_info_widget.clear_key()
        self.NumLockWarning__QLabel.clear()
        self.formatted_key_info_changed.emit({})
    
    def get_entered_key_info_result(self):
        """다이얼로그의 결과값을 반환합니다.
        
        Returns:
            dict or None: 
            _on_confirm을 통해 확인 버튼으로 닫힌 경우 _result_key_info에 저장된 키 정보를, 
            취소된 경우 None을 반환합니다.
        """
        return self._result_key_info if self.result() == QDialog.Accepted else None
    
    def _on_confirm(self):
        """확인 버튼 클릭 시"""
        self.modal_log_manager.log(
            message=f"_on_confirm - 확인 버튼 클릭 시 현재 키 정보 저장(current_key_info): {self._current_formatted_key_info}",
            level="DEBUG",
            file_name="entered_key_info_dialog"
        )
        
        if self._current_formatted_key_info:  # 키 정보가 있는 경우
            self.modal_log_manager.log(
                message="_on_confirm - 키 입력 모달의 확인버튼이 클릭되었습니다.",
                level="INFO",
                file_name="entered_key_info_dialog"
            )
            # 결과값 저장
            self._result_key_info = self._current_formatted_key_info

            self.modal_log_manager.log(
                message=f"_on_confirm - 키 입력 모달 닫히기 전 최종으로 저장된 키 정보(result_key_info): {self._result_key_info}",
                level="DEBUG",
                file_name="entered_key_info_dialog"
            )

            # 키보드 훅 정리
            self._stop_keyboard_hook()
            
            # 다이얼로그 닫기
            super().accept()  # QDialog의 accept() 메서드 직접 호출
    
    def reject(self):
        """취소 버튼 클릭 또는 창이 닫힐 때"""
        self._result_key_info = None
        super().reject()
    
    def closeEvent(self, event):
        """다이얼로그가 닫힐 때 키보드 훅 정리"""
        self._stop_keyboard_hook()
        super().closeEvent(event)

    def set_key_info(self, formatted_key_info: dict):
        """키 정보를 설정합니다.
        
        Args:
            formatted_key_info (dict): 구조화된 키 정보
        """
        self.entered_key_info_widget.set_key_info(formatted_key_info)
        
    def get_current_key_info(self) -> dict:
        """현재 설정된 키 정보를 반환합니다.
        
        Returns:
            dict: 현재 설정된 키 정보
        """
        return self.entered_key_info_widget.get_current_key_info()