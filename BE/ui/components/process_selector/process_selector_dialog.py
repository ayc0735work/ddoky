from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from BE.process.process_manager import ProcessManager
from BE.ui.constants.styles import BUTTON_STYLE, LIST_STYLE

class ProcessSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("프로세스 선택")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.selected_process = None
        
        self._init_ui()
        self._connect_signals()
        
        # 초기 검색 실행
        self._search_processes()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 검색 영역
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어를 입력하세요")
        self.search_input.setText("maple")  # 기본 검색어 설정
        self.search_button = QPushButton("검색")
        self.search_button.setStyleSheet(BUTTON_STYLE)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)
        
        # 프로세스 목록
        self.process_list = QListWidget()
        self.process_list.setStyleSheet(LIST_STYLE)
        layout.addWidget(self.process_list)
        
        # 버튼 그룹
        button_group = QHBoxLayout()
        self.select_button = QPushButton("선택")
        self.select_button.setStyleSheet(BUTTON_STYLE)
        self.cancel_button = QPushButton("취소")
        self.cancel_button.setStyleSheet(BUTTON_STYLE)
        
        button_group.addWidget(self.select_button)
        button_group.addWidget(self.cancel_button)
        layout.addLayout(button_group)
    
    def _connect_signals(self):
        self.search_button.clicked.connect(self._search_processes)
        self.select_button.clicked.connect(self._on_select)
        self.cancel_button.clicked.connect(self.reject)
        self.search_input.returnPressed.connect(self._search_processes)
    
    def _search_processes(self):
        """프로세스 검색 및 결과 표시"""
        search_text = self.search_input.text().lower()
        self.process_list.clear()
        
        processes = ProcessManager.get_processes(search_text)
        for process in processes:
            item_text = f"[ PID : {process['pid']} ] {process['name']} - {process['title']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, process)
            self.process_list.addItem(item)
        
        # 검색 결과에 따른 포커스 처리
        if self.process_list.count() > 0:
            # 검색 결과가 있으면 첫 번째 항목 선택
            self.process_list.setCurrentRow(0)
            self.process_list.setFocus()
        else:
            # 검색 결과가 없으면 검색어 입력창에 포커스
            self.search_input.setFocus()
    
    def _on_select(self):
        current_item = self.process_list.currentItem()
        if current_item:
            self.selected_process = current_item.data(Qt.UserRole)
            self.accept()
    
    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 프로세스 목록에 포커스가 있고 항목이 선택되어 있으면 선택 버튼 클릭
            if (self.process_list.hasFocus() and 
                self.process_list.currentItem() is not None):
                self._on_select()
        else:
            super().keyPressEvent(event)
