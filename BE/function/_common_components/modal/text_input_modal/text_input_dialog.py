from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QLineEdit, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt

class TextInputDialog(QDialog):
    """텍스트 입력 모달 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("텍스트 입력")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 설명 레이블
        description = QLabel("입력할 텍스트를 입력하세요:")
        description.setStyleSheet("font-weight: bold;")
        layout.addWidget(description)
        
        # 텍스트 입력 필드
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("여기에 텍스트를 입력하세요")
        self.text_input.textChanged.connect(self._validate_input)
        layout.addWidget(self.text_input)
        
        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        self.save_button = button_box.button(QDialogButtonBox.Save)
        self.save_button.setText("저장")
        self.save_button.setEnabled(False)  # 초기에는 비활성화
        
        button_box.button(QDialogButtonBox.Cancel).setText("취소")
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _validate_input(self, text):
        """입력 텍스트 유효성 검사"""
        # 빈 문자열이 아닌 경우에만 저장 버튼 활성화
        self.save_button.setEnabled(bool(text.strip()))
        
    def _on_accept(self):
        """저장 버튼 클릭 시 처리"""
        text = self.text_input.text().strip()
        if not text:
            QMessageBox.warning(
                self,
                "입력 오류",
                "텍스트를 입력해주세요."
            )
            return
            
        self.accept()
        
    def get_text(self):
        """입력된 텍스트와 메타데이터 반환"""
        text = self.text_input.text().strip()
        return {
            'type': 'write_text',
            'text': text,
            'logic_detail_item_dp_text': f'텍스트 입력: {text}'
    }
