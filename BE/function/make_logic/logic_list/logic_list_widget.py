from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont
from BE.log.base_log_manager import BaseLogManager
import json
import os
import uuid
from datetime import datetime
import copy

from BE.function.constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.function.constants.dimensions import LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT, LOGIC_BUTTON_WIDTH
from BE.settings.logics_data_settingfiles_manager import LogicsDataSettingFilesManager

class LogicListWidget(QFrame):
    """로직 목록 UI 위젯
    
    로직 목록을 표시하고 사용자 상호작용을 처리하는 UI 컴포넌트입니다.
    
    Signals:
        logic_move_requested (str, int): 로직 이동 요청 (logic_id, new_position)
        logic_edit_requested (str, dict): 로직 수정 요청 (logic_id, new_data)
        logic_delete_requested (str): 로직 삭제 요청 (logic_id)
        logic_copy_requested (str): 로직 복사 요청 (logic_id)
        logic_paste_requested: 로직 붙여넣기 요청
        logic_selected (str): 로직 선택 시 (로직 이름)
        edit_logic (dict): 로직 불러오기 (로직 정보)
        reload_logics_requested: 로직 다시 불러오기 요청
    """
    
    # 시그널 정의
    logic_move_requested = Signal(str, int)  # logic_id, new_position
    logic_edit_requested = Signal(str, dict)  # logic_id, new_data
    logic_delete_requested = Signal(str)  # logic_id
    logic_copy_requested = Signal(str)  # logic_id
    logic_paste_requested = Signal()
    logic_selected = Signal(str)  # 로직이 선택되었을 때 (로직 이름)
    edit_logic = Signal(dict)  # 로직 불러오기 시그널 (로직 정보)
    reload_logics_requested = Signal()  # 로직 다시 불러오기 요청
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_log_manager = BaseLogManager.instance()
        self.init_ui()
        
        # 이벤트 필터 설치
        self.logic_list.installEventFilter(self)
        
    def init_ui(self):
        """UI 초기화
        
        위젯의 시각적 요소들을 초기화하고 배치합니다.
        
        구성요소:
        1. 타이틀 레이블
        2. 로직 다시 불러오기 버튼
        3. 로직 목록 위젯 (QListWidget)
        4. 제어 버튼들:
           - 위로 이동
           - 아래로 이동
           - 로직 불러오기
           - 로직 삭제
        
        스타일:
        - 프레임 스타일 적용
        - 고정 크기 설정
        - 버튼 스타일 적용
        """
        # 기본 설정
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃 설정
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 1. 타이틀 섹션
        title = QLabel("로직 리스트")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 2. 로직 다시 불러오기 버튼 섹션
        self.reload_button = QPushButton("로직 다시 불러오기")
        self.reload_button.setStyleSheet(BUTTON_STYLE)
        self.reload_button.clicked.connect(self._on_reload_button_clicked)
        layout.addWidget(self.reload_button)
        
        # 3. 로직 리스트 섹션
        self.logic_list = QListWidget()
        self.logic_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logic_list.setStyleSheet(LIST_STYLE)
        self.logic_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.logic_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.logic_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.logic_list)
        
        # 4. 제어 버튼 섹션
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # 위로 이동 버튼
        self.move_up_btn = QPushButton("위로")
        self.move_up_btn.setFixedWidth(40)
        self.move_up_btn.setStyleSheet(BUTTON_STYLE)
        self.move_up_btn.setEnabled(False)
        self.move_up_btn.clicked.connect(self._on_move_up_clicked)
        button_layout.addWidget(self.move_up_btn)
        
        # 아래로 이동 버튼
        self.move_down_btn = QPushButton("아래로")
        self.move_down_btn.setFixedWidth(50)
        self.move_down_btn.setStyleSheet(BUTTON_STYLE)
        self.move_down_btn.setEnabled(False)
        self.move_down_btn.clicked.connect(self._on_move_down_clicked)
        button_layout.addWidget(self.move_down_btn)
        
        # 로직 불러오기 버튼
        self.edit_btn = QPushButton("선택한 로직 불러오기")
        self.edit_btn.setFixedWidth(130)
        self.edit_btn.setStyleSheet(BUTTON_STYLE)
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(self.edit_btn)
        
        # 로직 삭제 버튼
        self.delete_btn = QPushButton("로직 삭제")
        self.delete_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.delete_btn.setStyleSheet(BUTTON_STYLE)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def _on_selection_changed(self):
        """선택 상태 변경 처리
        
        리스트 아이템 선택이 변경될 때 호출됩니다.
        
        처리내용:
        1. 현재 선택된 아이템 확인
        2. 버튼 활성화/비활성화 상태 업데이트:
           - 위로 이동: 첫 번째 아이템이 아닐 때
           - 아래로 이동: 마지막 아이템이 아닐 때
           - 수정: 단일 선택일 때
           - 삭제: 선택된 아이템이 있을 때
        """
        selected_items = self.logic_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.logic_list.currentRow()
        self.move_up_btn.setEnabled(has_selection and current_row > 0)
        self.move_down_btn.setEnabled(has_selection and current_row < self.logic_list.count() - 1)
        self.edit_btn.setEnabled(len(selected_items) == 1)
        self.delete_btn.setEnabled(has_selection)
        
    def _on_move_up_clicked(self):
        """위로 이동 버튼 처리
        
        선택된 아이템을 한 칸 위로 이동합니다.
        
        프로세스:
        1. 현재 선택된 아이템 확인
        2. 이동 가능 여부 확인 (첫 번째 아이템이 아닌지)
        3. 이동 요청 시그널 발생 (logic_move_requested)
        """
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        current_row = self.logic_list.currentRow()
        logic_id = current_item.data(Qt.UserRole)
        self.logic_move_requested.emit(logic_id, current_row - 1)
        
    def _on_move_down_clicked(self):
        """아래로 이동 버튼 처리
        
        선택된 아이템을 한 칸 아래로 이동합니다.
        
        프로세스:
        1. 현재 선택된 아이템 확인
        2. 이동 가능 여부 확인 (마지막 아이템이 아닌지)
        3. 이동 요청 시그널 발생 (logic_move_requested)
        """
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        current_row = self.logic_list.currentRow()
        logic_id = current_item.data(Qt.UserRole)
        self.logic_move_requested.emit(logic_id, current_row + 1)
        
    def _on_edit_clicked(self):
        """로직 불러오기 버튼 처리
        
        선택된 로직을 수정하기 위해 불러옵니다.
        
        프로세스:
        1. 현재 선택된 아이템 확인
        2. 설정에서 로직 정보 로드
        3. 로직 정보가 있으면 edit_logic 시그널 발생
        """
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        # 설정 매니저를 통해 로직 정보 가져오기
        settings_manager = LogicsDataSettingFilesManager()
        logics = settings_manager.load_logics()
        logic_id = current_item.data(Qt.UserRole)
        
        if logic_id in logics:
            self.edit_logic.emit(logics[logic_id])
        
    def _on_item_double_clicked(self, item):
        """아이템 더블클릭 처리
        
        로직 아이템이 더블클릭되었을 때 처리합니다.
        
        Args:
            item (QListWidgetItem): 더블클릭된 아이템
            
        프로세스:
        1. 아이템 유효성 확인
        2. 설정에서 로직 정보 로드
        3. 로직 정보가 있으면 edit_logic 시그널 발생
        """
        if not item:
            return
            
        # 설정 매니저를 통해 로직 정보 가져오기
        settings_manager = LogicsDataSettingFilesManager()
        logics = settings_manager.load_logics()
        logic_id = item.data(Qt.UserRole)
        
        if logic_id in logics:
            self.edit_logic.emit(logics[logic_id])
        
    def _on_delete_clicked(self):
        """삭제 버튼 처리
        
        선택된 로직(들)을 삭제합니다.
        
        프로세스:
        1. 선택된 아이템 확인
        2. 삭제 확인 대화상자 표시
        3. 사용자 확인 시 각 아이템에 대해:
           - logic_delete_requested 시그널 발생
        """
        selected_items = self.logic_list.selectedItems()
        if not selected_items:
            return
            
        # 삭제 확인 메시지
        if len(selected_items) == 1:
            message = f'로직 "{selected_items[0].text()}"을(를) 삭제하시겠습니까?'
        else:
            message = f'선택된 {len(selected_items)}개의 로직을 삭제하시겠습니까?'
            
        reply = QMessageBox.question(
            self, 
            '로직 삭제', 
            message,
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                logic_id = item.data(Qt.UserRole)
                self.logic_delete_requested.emit(logic_id)
                
    def _on_reload_button_clicked(self):
        """로직 다시 불러오기 버튼 클릭 시 호출되는 메서드"""
        self.reload_logics_requested.emit()
        
    def eventFilter(self, obj, event):
        """이벤트 필터
        
        키보드 단축키 등의 이벤트를 처리합니다.
        
        Args:
            obj: 이벤트가 발생한 객체
            event: 발생한 이벤트
            
        처리하는 이벤트:
        - Ctrl+C: 복사 (logic_copy_requested)
        - Ctrl+V: 붙여넣기 (logic_paste_requested)
        - Delete: 삭제 (_on_delete_clicked)
        
        Returns:
            bool: 이벤트 처리 여부
        """
        if obj == self.logic_list and event.type() == QEvent.KeyPress:
            modifiers_key_flag = event.modifiers_key_flag()
            key = event.key()
            
            # Ctrl+C: 복사
            if modifiers_key_flag == Qt.ControlModifier and key == Qt.Key_C:
                current_item = self.logic_list.currentItem()
                if current_item:
                    logic_id = current_item.data(Qt.UserRole)
                    self.logic_copy_requested.emit(logic_id)
                return True
                
            # Ctrl+V: 붙여넣기
            elif modifiers_key_flag == Qt.ControlModifier and key == Qt.Key_V:
                self.logic_paste_requested.emit()
                return True
                
            # Delete: 삭제
            elif key == Qt.Key_Delete:
                self._on_delete_clicked()
                return True
                
        return super().eventFilter(obj, event)
        
    def clear_logic_list(self):
        """로직 목록 초기화
        
        목록의 모든 아이템을 제거합니다.
        """
        self.logic_list.clear()
        
    def add_logic_item(self, logic_info, logic_id):
        """로직 아이템 추가
        
        새로운 로직 아이템을 목록에 추가합니다.
        
        Args:
            logic_info (dict): 로직 정보 (이름 등)
            logic_id (str): 로직의 고유 ID
        """
        item = QListWidgetItem(logic_info.get('name', ''))
        item.setData(Qt.UserRole, logic_id)
        self.logic_list.addItem(item)
        
    def update_logic_item(self, logic_id, logic_info):
        """로직 아이템 업데이트
        
        기존 로직 아이템의 정보를 업데이트합니다.
        
        Args:
            logic_id (str): 업데이트할 로직의 ID
            logic_info (dict): 새로운 로직 정보
        """
        for i in range(self.logic_list.count()):
            item = self.logic_list.item(i)
            if item and item.data(Qt.UserRole) == logic_id:
                item.setText(logic_info.get('name', ''))
                break
                
    def remove_logic_item(self, logic_id):
        """로직 아이템 제거
        
        지정된 로직 아이템을 목록에서 제거합니다.
        
        Args:
            logic_id (str): 제거할 로직의 ID
        """
        for i in range(self.logic_list.count()):
            item = self.logic_list.item(i)
            if item and item.data(Qt.UserRole) == logic_id:
                self.logic_list.takeItem(i)
                break
                
    def get_logic_count(self):
        """로직 아이템 개수 반환"""
        return self.logic_list.count()
        
    def get_logic_id_at(self, index):
        """특정 인덱스의 로직 ID 반환"""
        item = self.logic_list.item(index)
        return item.data(Qt.UserRole) if item else None
