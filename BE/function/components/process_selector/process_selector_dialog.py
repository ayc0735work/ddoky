from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt

from BE.process.window_process_finder import ProcessManager
from BE.function.constants.styles import BUTTON_STYLE, LIST_STYLE

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
        ProcessSelectorLayout__QVBoxLayout = QVBoxLayout()
        self.setLayout(ProcessSelectorLayout__QVBoxLayout)
        
        # 검색 영역
        SearchSection__QHBoxLayout = QHBoxLayout()
        self.SearchInput__QLineEdit = QLineEdit()
        self.SearchInput__QLineEdit.setPlaceholderText("검색어를 입력하세요")
        self.SearchInput__QLineEdit.setText("maple")  # 기본 검색어 설정
        self.SearchButton__QPushButton = QPushButton("검색")
        self.SearchButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        
        SearchSection__QHBoxLayout.addWidget(self.SearchInput__QLineEdit)
        SearchSection__QHBoxLayout.addWidget(self.SearchButton__QPushButton)
        ProcessSelectorLayout__QVBoxLayout.addLayout(SearchSection__QHBoxLayout)
        
        # 프로세스 목록
        self.ProcessList__QListWidget = QListWidget()
        self.ProcessList__QListWidget.setStyleSheet(LIST_STYLE)
        ProcessSelectorLayout__QVBoxLayout.addWidget(self.ProcessList__QListWidget)
        
        # 버튼 그룹
        DialogButtonSection__QHBoxLayout = QHBoxLayout()
        self.SelectButton__QPushButton = QPushButton("선택")
        self.SelectButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.CancelButton__QPushButton = QPushButton("취소")
        self.CancelButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        
        DialogButtonSection__QHBoxLayout.addWidget(self.SelectButton__QPushButton)
        DialogButtonSection__QHBoxLayout.addWidget(self.CancelButton__QPushButton)
        ProcessSelectorLayout__QVBoxLayout.addLayout(DialogButtonSection__QHBoxLayout)
    
    def _connect_signals(self):
        self.SearchButton__QPushButton.clicked.connect(self._search_processes)
        self.SelectButton__QPushButton.clicked.connect(self._on_select)
        self.CancelButton__QPushButton.clicked.connect(self.reject)
        self.SearchInput__QLineEdit.returnPressed.connect(self._search_processes)
    
    def _search_processes(self):
        """프로세스 검색 및 결과 표시"""
        search_text = self.SearchInput__QLineEdit.text().lower()
        self.ProcessList__QListWidget.clear()
        
        processes = ProcessManager.get_processes(search_text)
        for process in processes:
            item_text = f"[ PID : {process['pid']} ] {process['name']} - {process['title']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, process)
            self.ProcessList__QListWidget.addItem(item)
        
        # 검색 결과에 따른 포커스 처리
        if self.ProcessList__QListWidget.count() > 0:
            # 검색 결과가 있으면 첫 번째 항목 선택
            self.ProcessList__QListWidget.setCurrentRow(0)
            self.ProcessList__QListWidget.setFocus()
        else:
            # 검색 결과가 없으면 검색어 입력창에 포커스
            self.SearchInput__QLineEdit.setFocus()
    
    def _on_select(self):
        current_item = self.ProcessList__QListWidget.currentItem()
        if current_item:
            self.selected_process = current_item.data(Qt.UserRole)
            self.accept()
    
    def keyPressEvent(self, event):
        """키 입력 이벤트 처리"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 프로세스 목록에 포커스가 있고 항목이 선택되어 있으면 선택 버튼 클릭
            if (self.ProcessList__QListWidget.hasFocus() and 
                self.ProcessList__QListWidget.currentItem() is not None):
                self._on_select()
        else:
            super().keyPressEvent(event)
