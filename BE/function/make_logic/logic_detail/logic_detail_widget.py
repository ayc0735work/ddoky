from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QLineEdit, QInputDialog, QMessageBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QFont, QGuiApplication, QIntValidator
from datetime import datetime
import uuid
import win32con
import win32api
from BE.settings.settings_data_manager import SettingsManager
from BE.function.manage_logic.logic_manager import LogicManager
from BE.function.constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.function.constants.dimensions import (LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT,
                                 LOGIC_BUTTON_WIDTH)
from BE.function._common_components.modal.entered_key_info_modal.keyboard_hook_handler import create_formatted_key_info
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.function._common_components.modal.text_input_modal.text_input_dialog import TextInputDialog
from BE.log.base_log_manager import BaseLogManager
from BE.function.make_logic.repository.logic_detaill_item_manage_repository import LogicDetailItemsManageRepository

class LogicDetailWidget(QFrame):
    """로직 상세 내용을 표시하고 관리하는 위젯"""
    
    item_moved = Signal()
    item_edited = Signal(str)
    item_deleted = Signal(str)
    logic_name_saved = Signal(str)
    logic_saved = Signal(dict)
    logic_updated = Signal(str, dict)
    
    def __init__(self, repository: LogicDetailItemsManageRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.base_log_manager = BaseLogManager.instance()
        self.init_ui()
        self.edit_mode = False  # 수정 모드 여부
        self.last_formatted_key_info = None
        self.keyboard_hook = None
        self.trigger_key_info = None  # 트리거 키 정보
        self.original_name = None  # 원래 이름
        self.current_logic_id = None  # 현재 로직의 UUID 저장용 추가
        self.copied_items = []  # 복사된 아이템들 저장 (리스트로 변경)
        self.current_logic = None  # 현재 로직 정보
        self.settings_manager = SettingsManager()  # SettingsManager 인스턴스 생성
        self.logic_manager = LogicManager(self.settings_manager)  # LogicManager 인스턴스 추가
        
        # Repository 시그널 연결
        self.repository.logic_detail_item_added.connect(self._update_list_widget)
        self.repository.logic_detail_item_deleted.connect(self._update_list_widget)
        self.repository.logic_detail_item_moved.connect(self._update_list_widget)
        
        # 중첩로직용 체크박스 초기 상태 설정
        self.is_nested_checkbox.setChecked(True)
        
        # 키보드 이벤트 필터 설치
        self.installEventFilter(self)
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        LogicConfigurationLayout__QVBoxLayout = QVBoxLayout()
        LogicConfigurationLayout__QVBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        LogicConfigurationLayout__QVBoxLayout.setContentsMargins(10, 10, 10, 10)
        LogicConfigurationLayout__QVBoxLayout.setSpacing(10)
        
        # 타이틀 레이아웃
        TitleRow__QHBoxLayout = QHBoxLayout()
        
        # 타이틀
        LogicTitleLabel__QLabel = QLabel("로직 정보")
        LogicTitleLabel__QLabel.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        TitleRow__QHBoxLayout.addWidget(LogicTitleLabel__QLabel)
        
        TitleRow__QHBoxLayout.addStretch()
        LogicConfigurationLayout__QVBoxLayout.addLayout(TitleRow__QHBoxLayout)
        
        # 로직 저장 섹션
        LogicSaveSection__QHBoxLayout = QHBoxLayout()
        LogicSaveSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicSaveSection__QHBoxLayout.setSpacing(5)
        
        # 새 로직 버튼
        self.NewLogicButton__QPushButton = QPushButton("새 로직")
        self.NewLogicButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.NewLogicButton__QPushButton.clicked.connect(self._create_new_logic)
        self.NewLogicButton__QPushButton.setEnabled(False)  # 초기에 비활성화
        LogicSaveSection__QHBoxLayout.addWidget(self.NewLogicButton__QPushButton)
        
        # 로직 저장 버튼
        self.LogicSaveButton__QPushButton = QPushButton("로직 저장")
        self.LogicSaveButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.LogicSaveButton__QPushButton.clicked.connect(self._save_logic)
        LogicSaveSection__QHBoxLayout.addWidget(self.LogicSaveButton__QPushButton)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicSaveSection__QHBoxLayout)

        # 로직 이름 레이아웃
        LogicNameSection__QHBoxLayout = QHBoxLayout()
        LogicNameSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicNameSection__QHBoxLayout.setSpacing(5)
        
        # 로직 이름 라벨
        LogicNameLabel__QLabel = QLabel("로직 이름:")
        LogicNameLabel__QLabel.setFixedWidth(60)
        LogicNameSection__QHBoxLayout.addWidget(LogicNameLabel__QLabel)
        
        # 로직 이름 입력
        self.LogicNameInput__QLineEdit = QLineEdit()
        self.LogicNameInput__QLineEdit.setPlaceholderText("로직의 이름을 입력하세요")
        self.LogicNameInput__QLineEdit.textChanged.connect(self._check_data_entered)  # 텍스트 변경 시그널 연결
        LogicNameSection__QHBoxLayout.addWidget(self.LogicNameInput__QLineEdit, 1)  # stretch factor 1을 추가하여 남은 공간을 모 사용
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicNameSection__QHBoxLayout)

        # 트리거 키 입력 레이아웃
        TriggerKeySection__QHBoxLayout = QHBoxLayout()
        TriggerKeySection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        TriggerKeySection__QHBoxLayout.setSpacing(5)
        
        # 트리거 키 라벨
        TriggerKeyLabel__QLabel = QLabel("실행 트리거 키:")
        TriggerKeyLabel__QLabel.setFixedWidth(84)
        TriggerKeySection__QHBoxLayout.addWidget(TriggerKeyLabel__QLabel)
        
        # 트리거 키 입력 필드
        self.TriggerKeyInput__QLineEdit = QLineEdit()
        self.TriggerKeyInput__QLineEdit.setReadOnly(True)
        self.TriggerKeyInput__QLineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.TriggerKeyInput__QLineEdit.mousePressEvent = self._on_trigger_key_input_clicked
        TriggerKeySection__QHBoxLayout.addWidget(self.TriggerKeyInput__QLineEdit)

        # 트리거 키 입력 위젯
        self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog = EnteredKeyInfoDialog(self)
        self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.formatted_key_info_changed.connect(self._check_data_entered)  # 키 입력 변경 시그널 연결

        # 편집 버튼
        self.EditTriggerKeyButton__QPushButton = QPushButton("편집")
        self.EditTriggerKeyButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.EditTriggerKeyButton__QPushButton.setFixedWidth(40)
        self.EditTriggerKeyButton__QPushButton.clicked.connect(self._edit_trigger_key)
        self.EditTriggerKeyButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
        TriggerKeySection__QHBoxLayout.addWidget(self.EditTriggerKeyButton__QPushButton)
        
        # 삭제 버튼
        self.DeleteTriggerKeyButton__QPushButton = QPushButton("삭제")
        self.DeleteTriggerKeyButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.DeleteTriggerKeyButton__QPushButton.setFixedWidth(40)
        self.DeleteTriggerKeyButton__QPushButton.clicked.connect(self._delete_trigger_key)
        self.DeleteTriggerKeyButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
        TriggerKeySection__QHBoxLayout.addWidget(self.DeleteTriggerKeyButton__QPushButton)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(TriggerKeySection__QHBoxLayout)
        
        # 기능 선택 레이아웃
        LogicOptionsSection__QHBoxLayout = QHBoxLayout()
        LogicOptionsSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicOptionsSection__QHBoxLayout.setSpacing(5)
        
        # 반복 횟수 입력 레이아웃
        RepeatCountRow__QHBoxLayout = QHBoxLayout()
        RepeatCountRow__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        RepeatCountRow__QHBoxLayout.setSpacing(5)
        
        # 반복 횟수 입력 필드
        self.RepeatCountInput__QSpinBox = QSpinBox()
        self.RepeatCountInput__QSpinBox.setFixedWidth(70)
        self.RepeatCountInput__QSpinBox.setAlignment(Qt.AlignRight)
        self.RepeatCountInput__QSpinBox.setRange(1, 9999)
        self.RepeatCountInput__QSpinBox.setValue(1)
        self.RepeatCountInput__QSpinBox.valueChanged.connect(self._check_data_entered)
        RepeatCountRow__QHBoxLayout.addWidget(self.RepeatCountInput__QSpinBox)
        
        # 반복 횟수 라벨
        RepeatCountLabel__QLabel = QLabel("회 반복")
        RepeatCountRow__QHBoxLayout.addWidget(RepeatCountLabel__QLabel)
        
        # 중첩로직용 체크박스 추가
        self.is_nested_checkbox = QCheckBox("중첩로직용")
        self.is_nested_checkbox.stateChanged.connect(self._on_nested_checkbox_changed)
        RepeatCountRow__QHBoxLayout.addWidget(self.is_nested_checkbox)
        
        RepeatCountRow__QHBoxLayout.addStretch()
        
        LogicOptionsSection__QHBoxLayout.addLayout(RepeatCountRow__QHBoxLayout)
        LogicOptionsSection__QHBoxLayout.addStretch()
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicOptionsSection__QHBoxLayout)
        
        # 리스트 위젯
        self.LogicItemList__QListWidget = QListWidget()
        self.LogicItemList__QListWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.LogicItemList__QListWidget.setStyleSheet(LIST_STYLE)
        self.LogicItemList__QListWidget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 모드 활성화
        self.LogicItemList__QListWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.LogicItemList__QListWidget.itemDoubleClicked.connect(self._edit_item)  # 더블클릭 시그널 연결
        # 아이템 목록 변경 시 새 로직 버튼 상태 업데이트
        self.LogicItemList__QListWidget.model().rowsInserted.connect(self._check_data_entered)
        self.LogicItemList__QListWidget.model().rowsRemoved.connect(self._check_data_entered)
        LogicConfigurationLayout__QVBoxLayout.addWidget(self.LogicItemList__QListWidget)
        
        # 버튼 그룹 레이아웃
        LogicControlButtonsSection__QHBoxLayout = QHBoxLayout()
        LogicControlButtonsSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicControlButtonsSection__QHBoxLayout.setSpacing(5)
        
        # 위로 버튼
        self.MoveUpButton__QPushButton = QPushButton("위로")
        self.MoveUpButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.MoveUpButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.MoveUpButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.MoveUpButton__QPushButton)
        self.MoveUpButton__QPushButton.clicked.connect(lambda: self._move_selected_item('up'))
        
        # 아래로 버튼
        self.MoveDownButton__QPushButton = QPushButton("아래로")
        self.MoveDownButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.MoveDownButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.MoveDownButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.MoveDownButton__QPushButton)
        self.MoveDownButton__QPushButton.clicked.connect(lambda: self._move_selected_item('down'))

        # 수정 버튼
        self.EditItemButton__QPushButton = QPushButton("항목 수정")
        self.EditItemButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.EditItemButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.EditItemButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.EditItemButton__QPushButton)
        self.EditItemButton__QPushButton.clicked.connect(self._edit_item)

        # 삭제 버튼
        self.DeleteItemButton__QPushButton = QPushButton("항목 삭제")
        self.DeleteItemButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.DeleteItemButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.DeleteItemButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.DeleteItemButton__QPushButton)
        self.DeleteItemButton__QPushButton.clicked.connect(self._delete_selected_items)

        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicControlButtonsSection__QHBoxLayout)
        self.setLayout(LogicConfigurationLayout__QVBoxLayout)
             
        # 초기 데이터 로드 (테스트용)
        self._load_test_data()
        
    def _load_test_data(self):
        """테스트용 데이터 로드"""
        pass  # 더미 데이터 제거
            
    def _on_selection_changed(self):
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.LogicItemList__QListWidget.currentRow()
        self.MoveUpButton__QPushButton.setEnabled(has_selection and current_row > 0)
        self.MoveDownButton__QPushButton.setEnabled(has_selection and current_row < self.LogicItemList__QListWidget.count() - 1)
        self.EditItemButton__QPushButton.setEnabled(len(selected_items) == 1)  # 수정은 단일 선택만 가능
        self.DeleteItemButton__QPushButton.setEnabled(has_selection)  # 삭제는 다중 선택 가능

    def add_item(self, item_info):
        """아이템을 목록에 추가합니다."""
        if isinstance(item_info, dict):
            self.repository.add_logic_detail_item(item_info)
            
    def _delete_selected_items(self):
        """선택된 아이템들을 삭제"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                item_data = item.data(Qt.UserRole)
                if item_data:
                    self.repository.delete_logic_detail_items(item_data)

    def _move_selected_item(self, direction: str):
        """선택된 아이템을 위/아래로 이동"""
        current_item = self.LogicItemList__QListWidget.currentItem()
        if current_item:
            item_data = current_item.data(Qt.UserRole)
            if direction == 'up':
                self.repository.move_logic_detail_item_up(item_data)
            else:
                self.repository.move_logic_detail_item_down(item_data)

    def get_logic_detail_items(self):
        """현재 아이템 목록을 반환합니다."""
        items = self.repository.get_logic_detail_items()
        
        # 키 입력 아이템의 modifiers를 정수로 변환
        for item in items:
            if item.get('type') == 'key' and 'modifiers' in item:
                if not isinstance(item['modifiers'], int):
                    item['modifiers'] = item['modifiers'].value
        
        return items

    def has_items(self):
        """목록에 아이템이 있는지 확인"""
        return self.repository.get_logic_detail_items_count() > 0

    def clear_logic_detail_items(self):
        """모든 아이템을 삭제합니다."""
        self.repository.clear_logic_detail_items()

    def _update_list_widget(self):
        """Repository의 아이템 목록으로 ListWidget을 업데이트"""
        self.LogicItemList__QListWidget.clear()
        items = self.repository.get_logic_detail_items()
        for item in items:
            list_item = QListWidgetItem(item.get('display_text', ''))
            list_item.setData(Qt.UserRole, item)
            self.LogicItemList__QListWidget.addItem(list_item)

    def _check_duplicate_trigger_key(self, key_info):
        """트리거 키 중복 체크"""
        if not key_info:
            return False
            
        # modifiers가 이미 정수값인지 확인하고, 아니라면 int() 변환
        modifiers = key_info['modifiers']
        if not isinstance(modifiers, int):
            modifiers = modifiers.value
            
        # 트리거 키 중복 체크
        logics = self.settings_manager.load_logics(force=True)
        duplicate_logics = []
        
        for logic_id, logic in logics.items():
            if (logic_id != self.current_logic_id and 
                not logic.get('is_nested', False)):
                trigger_key = logic.get('trigger_key', {})
                if (trigger_key and
                    trigger_key.get('virtual_key') == key_info.get('virtual_key') and 
                    trigger_key.get('modifiers') == modifiers):
                    duplicate_logics.append({
                        'name': logic.get('name'),
                        'id': logic_id
                    })

        if duplicate_logics:
            duplicate_info = "\n\n".join([
                f"로직 이름: {logic['name']}\n"
                f"로직 UUID: {logic['id']}"
                for logic in duplicate_logics
            ])
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("트리거 키 중복")
            msg.setText("이미 다른 로직에서 사용 중인 트리거 키입니다.\n\n"
                       "사용 중인 로직 정보\n\n"
                       f"{duplicate_info}")
            msg.setStandardButtons(QMessageBox.Ok)
            
            self.base_log_manager.log(
                message=f"중복된 트리거 키 발견: {len(duplicate_logics)}개의 로직에서 사용 중",
                level="WARNING", 
                file_name="logic_detail_widget"
            )
            
            msg.exec_()
            return True
            
        return False

    def _update_trigger_key_info(self, key_info):
        """트리거 키 정보 업데이트"""
        if key_info:
            self.trigger_key_info = key_info.copy()
            self.TriggerKeyInput__QLineEdit.setText(key_info['simple_display_text'])
            self.EditTriggerKeyButton__QPushButton.setEnabled(True)
            self.DeleteTriggerKeyButton__QPushButton.setEnabled(True)
            
            self.base_log_manager.log(
                message=f"트리거 키 입력 완료(self.trigger_key_info): {self.trigger_key_info}",
                level="DEBUG",
                file_name="logic_detail_widget"
            )

    def _on_trigger_key_input_clicked(self, event):
        """트리거 키 입력 필드 클릭 이벤트 핸들러"""
        # 트리거 키가 없는 경우에만 모달 표시
        if not self.trigger_key_info:
            dialog = self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog
            if dialog.exec():
                result = dialog.get_entered_key_info_result()
                if result and not self._check_duplicate_trigger_key(result):
                    self._update_trigger_key_info(result)

    def _edit_trigger_key(self):
        """트리거 키 편집 다이얼로그를 엽니다."""
        self.base_log_manager.log(
            message="트리거 키 편집 버튼을 클릭했습니다.",
            level="INFO",
            file_name="logic_detail_widget"
        )
        dialog = self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog
        if dialog.exec():
            result = dialog.get_entered_key_info_result()
            if result and not self._check_duplicate_trigger_key(result):
                self._update_trigger_key_info(result)
                self.base_log_manager.log(
                    message=f"트리거 키 변경 완료(self.trigger_key_info): {self.trigger_key_info}",
                    level="DEBUG",
                    file_name="logic_detail_widget"
                )

    def _delete_trigger_key(self):
        """트리거 키 정보를 삭제합니다."""
        self.base_log_manager.log(
            message="트리거 키 삭제 버튼을 클릭했습니다.",
            level="INFO",
            file_name="logic_detail_widget"
        )
        self.clear_key()
        self.TriggerKeyInput__QLineEdit.clear()
        self.TriggerKeyInput__QLineEdit.setPlaceholderText("트리거 키를 설정하세요")

    def _save_logic(self):
        """현재 로직을 저장하는 메서드
        
        현재 로직 데이터를 가져와서 LogicManager를 통해 저장을 시도합니다.
        
        프로세스:
        1. get_logic_data()를 통해 현재 UI에 입력된 로직 데이터를 가져옴
        2. LogicManager의 save_logic() 메서드를 호출하여 저장 시도
        3. 저장 성공 시 로그 메시지 출력 후 True 반환
        4. 저장 실패 시 에러 메시지 표시 후 False 반환
        
        연결된 시그널:
        - logic_saved: MainWindow._on_logic_saved() 메서드로 연결
        - logic_updated: MainWindow._on_logic_updated() 메서드로 연결
        
        Returns:
            bool: 저장 성공 여부
        """
        try:
            logic_data = self.get_logic_data()
            
            success, result = self.logic_manager.save_logic(self.current_logic_id, logic_data)
            
            if success:
                self.base_log_manager.log(
                    message=f"로직 '{logic_data['name']}'이(가) 저장되었습니다",
                    level="INFO",
                    file_name="logic_detail_widget"
                )
                return True
            else:
                # 실패 시 에러 메시지 표시
                QMessageBox.warning(
                    self,
                    "저장 실패",
                    result,  # "동일한 이름의 로직이 이미 존재합니다." 메시지가 표시됨
                    QMessageBox.Ok
                )
                return False
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_detail_widget"
            )
            return False

    def load_logic(self, logic_info):
        """로직 정보를 UI 위젯에 로드하는 메서드
        
        주어진 로직 정보를 바탕으로 UI 위젯들의 상태를 업데이트합니다.
        
        프로세스:
        1. Repository에 로직 로드 요청
        2. 로직 이름과 반복 횟수 UI 업데이트
        3. 중첩로직 여부에 따른 트리거 키 UI 처리
           - 중첩로직일 경우: 트리거 키 비활성화
           - 일반 로직일 경우: 트리거 키 정보 설정 및 UI 업데이트
        
        연결된 메서드:
        - MainWindow._handle_edit_logic()에서 호출됨
        - LogicListWidget의 logic_selected 시그널에 연결
        
        Args:
            logic_info (dict): 로드할 로직 정보
                - name (str): 로직 이름
                - repeat_count (int): 반복 횟수
                - is_nested (bool): 중첩로직 여부
                - trigger_key (dict): 트리거 키 정보
        
        Returns:
            bool: 로드 성공 여부
        """
        # Repository에 로드 요청
        if self.repository.load_logic_detail_items(logic_info):
            # UI 업데이트
            self.LogicNameInput__QLineEdit.setText(logic_info.get('name', ''))
            self.RepeatCountInput__QSpinBox.setValue(logic_info.get('repeat_count', 1))
            
            # Repository에서 받은 logic_info의 is_nested 값에 따라 트리거 키 활성 여부 처리
            # 중첩로직일 경우 트리거 키 비활성화
            is_nested = logic_info.get('is_nested', False)
            self.is_nested_checkbox.setChecked(is_nested)
            
            # 중첩로직이 아닐 경우에만 트리거 키 설정
            if not is_nested:
                trigger_key = logic_info.get('trigger_key', {})
                if isinstance(trigger_key, dict) and trigger_key: # trigger_key가 dict이고 비어있지 않을 경우
                    self.trigger_key_info = trigger_key.copy()
                    self.base_log_manager.log(
                        message=f"load_logic - 트리거 키 정보 불러오기 완료(self.trigger_key_info): {self.trigger_key_info}",
                        level="DEBUG",
                        file_name="logic_detail_widget"
                    )
                    formatted_info = create_formatted_key_info(trigger_key)
                    self.TriggerKeyInput__QLineEdit.setText(formatted_info['simple_display_text'])
                    self.EditTriggerKeyButton__QPushButton.setEnabled(True)
                    self.DeleteTriggerKeyButton__QPushButton.setEnabled(True)
            
            return True
        return False

    def _create_nested_logic_item(self, logic_name, logic_id=None, original_data=None):
        """중첩로직 아이템 생성을 위한 공통 메서드
        
        Args:
            logic_name (str): 로직 이름
            logic_id (str, optional): 이미 알고 있는 로직 ID
            original_data (dict, optional): 원본 데이터 (복사-붙여넣기 시)
            
        Returns:
            tuple: (QListWidgetItem, bool) - 생성된 아이템과 성공 여부
        """
        try:
            # 1. 원본 데이터가 있는 경우 (복사-붙여넣기)
            if original_data:
                item = QListWidgetItem(logic_name)
                new_data = original_data.copy()
                item.setData(Qt.UserRole, new_data)
                return item, True
            
            # 2. 원본 데이터가 없는 경우 (새로 추가)
            # 캐시를 강제로 갱신하여 최신 데이터 가져오기
            logics = self.settings_manager.load_logics(force=True)
            
            # logic_id가 없으면 이름으로 찾기
            if not logic_id:
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        break
            
            # 로직을 찾지 못한 경우
            if not logic_id:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                    "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                )
                return None, False
            
            # 새 아이템 생성
            item = QListWidgetItem(logic_name)
            item_data = {
                'type': 'logic',
                'logic_id': logic_id,
                'logic_name': logic_name,
                'display_text': logic_name,
                'repeat_count': 1,
                'logic_data': {
                    'logic_id': logic_id,
                    'logic_name': logic_name,
                    'repeat_count': 1
                }
            }
            item.setData(Qt.UserRole, item_data)
            self.base_log_manager.log(
                message=f"중첩로직 '{logic_name}'이(가) UUID {logic_id}로 처리되었습니다",
                level="INFO",
                file_name="logic_detail_widget"
            )
            return item, True
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"중첩로직 처리 중 오류 발생: {str(e)}",
                level="ERROR", 
                file_name="logic_detail_widget"
            )
            return None, False
    
    def _add_logic_item(self, item_info):
        """로직 아이템을 리스트에 추가"""
        self.base_log_manager.log(
            message=f"로직 아이템 추가 시작 - 아이템 정보: {item_info}",
            level="DEBUG",
            file_name="logic_detail_widget"
        )
        
        if not isinstance(item_info, dict):
            self.base_log_manager.log(
                message="오류: 잘못된 아이템 정보 형식",
                level="ERROR",
                file_name="logic_detail_widget"
            )
            return
            
        # 현재 리스트의 아이템 개수로 order 설정
        current_order = self.LogicItemList__QListWidget.count() + 1
        item_info['order'] = current_order
        
        # 이미 변환된 형식인 경우 (로직 타입)
        if item_info.get('type') == 'logic':
            logic_name = item_info.get('logic_name')
            logic_id = item_info.get('logic_id')
            self.base_log_manager.log(
                message=f"로직 타입 아이템 처리 - 이름: {logic_name}, ID: {logic_id}",
                level="DEBUG",
                file_name="logic_detail_widget"
            )
            
            # 공통 메서드 사용
            item, success = self._create_nested_logic_item(logic_name, logic_id)
            if not success:
                return
            
            # 순서 설정
            current_count = self.LogicItemList__QListWidget.count()
            item_data = item.data(Qt.UserRole)
            item_data['order'] = current_count + 1
            item.setData(Qt.UserRole, item_data)
            
            self.LogicItemList__QListWidget.addItem(item)
            self.base_log_manager.log(
                message=f"로직 아이템 추가 완료 - 순서: {current_count + 1}",
                level="INFO",
                file_name="logic_detail_widget"
            )
        else:
            # 일반 아이템 처리
            current_count = self.LogicItemList__QListWidget.count()
            item = QListWidgetItem(item_info.get('display_text', ''))
            item_info['order'] = current_count + 1
            item.setData(Qt.UserRole, item_info)
            self.LogicItemList__QListWidget.addItem(item)
            self.base_log_manager.log(
                message=f"일반 아이템 추가 완료 - 타입: {item_info.get('type')}, 순서: {current_count + 1}",
                level="INFO",
                file_name="logic_detail_widget"
            )
    
    def _paste_item(self):
        """복사된 아이템들을 현재 선택된 아이템 아래에 붙여넣기"""
        if not self.copied_items:
            self.base_log_manager.log(
                message="복사된 아이템이 없습니다",
                level="WARNING",
                file_name="logic_detail_widget"
            )
            return
            
        current_row = self.LogicItemList__QListWidget.currentRow()
        if current_row < 0:
            insert_position = self.LogicItemList__QListWidget.count()
        else:
            insert_position = current_row + 1
            
        # 복사된 아이템들을 선택된 아이템 바로 다음에 순서대로 추가
        for idx, copied_item in enumerate(self.copied_items):
            current_insert_position = insert_position + idx
            
            if copied_item['data'] and copied_item['data'].get('type') == 'logic':
                # 중첩로직인 경우 공통 메서드 사용
                item, success = self._create_nested_logic_item(
                    copied_item['text'],
                    original_data=copied_item['data']
                )
                if not success:
                    continue
            else:
                # 일반 아이템의 경우
                item = QListWidgetItem(copied_item['text'])
                if copied_item['data']:
                    new_data = copied_item['data'].copy()
                    item.setData(Qt.UserRole, new_data)
            
            # 순서 업데이트
            item_data = item.data(Qt.UserRole) or {}
            item_data['order'] = current_insert_position + 1
            item.setData(Qt.UserRole, item_data)
            
            # 뒤의 아이템들의 order 업데이트
            for i in range(current_insert_position, self.LogicItemList__QListWidget.count()):
                existing_item = self.LogicItemList__QListWidget.item(i)
                if existing_item:
                    existing_data = existing_item.data(Qt.UserRole) or {}
                    existing_data['order'] = i + 2
                    existing_item.setData(Qt.UserRole, existing_data)
            
            self.LogicItemList__QListWidget.insertItem(current_insert_position, item)
        
        # 마지막으로 붙여넣은 아이템 선택
        last_inserted_item = self.LogicItemList__QListWidget.item(insert_position + len(self.copied_items) - 1)
        if last_inserted_item:
            self.LogicItemList__QListWidget.setCurrentItem(last_inserted_item)
            
        items_count = len(self.copied_items)
        self.base_log_manager.log(
            message=f"{items_count}개의 로직 구성 아이템이 붙여넣기되었습니다",
            level="INFO",
            file_name="logic_detail_widget"
        )

    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if event.type() == QEvent.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            
            # Ctrl+C: 복사
            if modifiers == Qt.ControlModifier and key == Qt.Key_C:
                self._copy_item()
                return True
                
            # Ctrl+V: 붙여넣기
            elif modifiers == Qt.ControlModifier and key == Qt.Key_V:
                self._paste_item()
                return True
                
            # Delete: 삭제
            elif key == Qt.Key_Delete:
                self._delete_logic_detail_items()
                return True
                
        return super().eventFilter(obj, event)

    def _check_data_entered(self, *args):
        """입력된 데이터가 있는지 확인하고 새 로직 버튼 상태를 업데이트"""
        # 새 로직 버튼 활성화 조건:
        # 1. 로직 이름이 입력되어 있는 경우
        # 2. 트리거 키가 설정되어 있는 경우
        # 3. 아이템 목록에 하나 이상의 아이템이 있는 경우
        # 4. 반복 횟수가 1이 아닌 경우
        has_logic_name = bool(self.LogicNameInput__QLineEdit.text().strip())
        has_trigger_key = bool(self.trigger_key_info)
        has_items = self.LogicItemList__QListWidget.count() > 0
        
        # 반복 횟수 확인
        try:
            repeat_count = self.RepeatCountInput__QSpinBox.value()
            has_different_repeat = repeat_count != 1
        except ValueError:
            has_different_repeat = False
        
        # 네 조건 중 하나도 만하면 버튼 활성화
        enable_button = has_logic_name or has_trigger_key or has_items or has_different_repeat
        
        self.NewLogicButton__QPushButton.setEnabled(enable_button)
        
    def _create_new_logic(self):
        """새 로직 버튼 클릭 시 호출되는 메서드"""
        self.clear_all()
        self.is_nested_checkbox.setChecked(True)  # 중첩로직용 체크박스를 선택된 상태로 설정
        self.base_log_manager.log(
            message="새 로직 생성을 시작합니다",
            level="INFO",
            file_name="logic_detail_widget"
        )

    def _edit_item(self):
        """선택된 아이템 수정"""
        current_item = self.LogicItemList__QListWidget.currentItem()
        if current_item:
            item_text = current_item.text()
            user_data = current_item.data(Qt.UserRole)
            
            # 지연시간 아이템인 경우
            if item_text.startswith("지연시간"):
                try:
                    current_delay = float(item_text.split(":")[1].replace("초", "").strip())
                    
                    # QInputDialog 커스터마이징
                    dialog = QInputDialog(self)
                    dialog.setWindowTitle("지연시간 정")
                    dialog.setLabelText("지연시간(초):")
                    dialog.setDoubleDecimals(4)  # 소수점 4자리까지 표시 (0.0001초 단위)
                    dialog.setDoubleValue(current_delay)  # 현재 지연시간을 기본으로 설정
                    dialog.setDoubleRange(0.0001, 10000.0)  # 0.0001초 ~ 10000초
                    dialog.setDoubleStep(0.0001)  # 증가/감소 단위
                    
                    # 버튼 텍스트 변경
                    dialog.setOkButtonText("지연시간 저장")
                    dialog.setCancelButtonText("지시간 입력 취소")
                    
                    if dialog.exec():
                        delay = dialog.doubleValue()
                        delay_text = f"지연시간 : {delay:.4f}초"
                        current_item.setText(delay_text)
                        # 순서와 content 유지
                        current_data = current_item.data(Qt.UserRole)
                        current_data['content'] = delay_text  # content 필드 업데이트
                        current_item.setData(Qt.UserRole, current_data)
                        self.item_edited.emit(delay_text)
                        self.base_log_manager.log(
                            message=f"지연시간이 {delay:.4f}초로 수정되었습니다",
                            level="INFO",
                            file_name="logic_detail_widget"
                        )
                except ValueError:
                    self.base_log_manager.log(
                        message="지연시간 형식이 올바르지 않습니다",
                        level="ERROR",
                        file_name="logic_detail_widget"
                    )
            # 키 입력 아이템인 경우
            elif item_text.startswith("(logic_detail_widget.py) 키 입력:"):
                key_parts = item_text.split(" --- ")
                if len(key_parts) == 2:
                    key_text = key_parts[0]
                    current_action = key_parts[1]  # 현재 액션 ("누르기" 또는 "떼기")
                    
                    # 액션 선택 대화상
                    dialog = QMessageBox(self)
                    dialog.setWindowTitle("선택된 키의 키 입력 정보 수정")
                    dialog.setText("선택된 키의 입력 정보를 수정하세요")
                    dialog.setIcon(QMessageBox.Question)
                    
                    # 버튼 추가
                    press_button = dialog.addButton("누르기", QMessageBox.ActionRole)
                    release_button = dialog.addButton("떼기", QMessageBox.ActionRole)
                    cancel_button = dialog.addButton("취소", QMessageBox.RejectRole)
                    
                    # 현재 액션에 따라 기본 버튼 설정
                    if current_action == "누르기":
                        dialog.setDefaultButton(press_button)
                    else:
                        dialog.setDefaultButton(release_button)
                    
                    dialog.exec()
                    clicked_button = dialog.clickedButton()
                    
                    if clicked_button in [press_button, release_button]:
                        new_action = "누르기" if clicked_button == press_button else "떼기"
                        if new_action != current_action:
                            new_text = f"{key_text} --- {new_action}"
                            current_item.setText(new_text)
                            # 순서 값과 content 유지
                            current_data = current_item.data(Qt.UserRole)
                            current_data['content'] = new_text  # content 필드 업데이트
                            current_item.setData(Qt.UserRole, current_data)
                            self.item_edited.emit(new_text)
                            self.base_log_manager.log(
                                message=f"키 입력 액션이 '{new_action}'으로 변경되었습니다",
                                level="INFO",
                                file_name="logic_detail_widget"
                            )
            # 텍스트 입력 아이템인 경우
            elif user_data and user_data.get('type') == 'write_text':
                dialog = TextInputDialog(self)
                dialog.text_input.setText(user_data.get('text', ''))
                if dialog.exec():
                    new_text = dialog.get_text()
                    current_item.setText(new_text['display_text'])
                    # 기존 데이터의 순서 정보 유지
                    current_data = current_item.data(Qt.UserRole)
                    # 새로운 텍스트 정보로 업데이트하되 order는 유지
                    current_data.update(new_text)
                    current_item.setData(Qt.UserRole, current_data)
                    self.item_edited.emit(new_text['display_text'])
                    self.base_log_manager.log(
                        message="텍스트 입력 아이템이 수정되었습니다",
                        level="INFO",
                        file_name="logic_detail_widget"
                    )

    def _on_nested_checkbox_changed(self, state):
        """중첩로직용 체크박스 상태 변경 시 호출"""
        is_nested = state == Qt.CheckState.Checked.value
        
        # 로그 추가
        self.base_log_manager.log(
            message=f"중첩로직용 체크박스가 {'활성화' if is_nested else '비활성화'}되었습니다",
            level="INFO",
            file_name="logic_detail_widget"
        )
        
        # 트리거 키 입력 UI 비활성화/활성화
        self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.setEnabled(not is_nested)
        self.TriggerKeyInput__QLineEdit.setEnabled(not is_nested)
        self.EditTriggerKeyButton__QPushButton.setEnabled(not is_nested and bool(self.trigger_key_info))
        self.DeleteTriggerKeyButton__QPushButton.setEnabled(not is_nested and bool(self.trigger_key_info))
        
        # 중첩로직일 경우 클릭 이벤트 제거, 아닐 경우 클릭 이벤트 설정
        if is_nested:
            self.TriggerKeyInput__QLineEdit.mousePressEvent = None
            self.TriggerKeyInput__QLineEdit.setPlaceholderText("중첩로직용")
            # 중첩로직용일 경우 트리거 키 초기화
            self.trigger_key_info = None
            self.TriggerKeyInput__QLineEdit.clear()
            # 트리거 키 입력 위젯 초기화
            self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.clear_key()
        else:
            self.TriggerKeyInput__QLineEdit.mousePressEvent = self._on_trigger_key_input_clicked
            self.TriggerKeyInput__QLineEdit.setPlaceholderText("트리거 키를 설정하세요")

    def get_logic_data(self):
        """기존 메서드 수정"""
        # 가장 큰 order 값 찾기
        logics = self.settings_manager.load_logics(force=True)
        max_order = 0
        for logic in logics.values():
            order = logic.get('order', 0)
            if order > max_order:
                max_order = order

        data = {
            'order': max_order + 1,  # 가장 큰 order + 1
            'name': self.LogicNameInput__QLineEdit.text(),
            'repeat_count': self.RepeatCountInput__QSpinBox.value(),
            'items': self.get_logic_detail_items(),
            'is_nested': self.is_nested_checkbox.isChecked()
        }
        
        # 중첩로직이 아닐 경우에만 트리거 키 추가
        if not data['is_nested']:
            # trigger_key_info가 있고 modifiers가 정수가 아닌 경우 변환
            if self.trigger_key_info and 'modifiers' in self.trigger_key_info:
                trigger_key = self.trigger_key_info.copy()
                if not isinstance(trigger_key['modifiers'], int):
                    trigger_key['modifiers'] = trigger_key['modifiers'].value
                data['trigger_key'] = trigger_key
            else:
                data['trigger_key'] = self.trigger_key_info
            
        return data

    def set_logic_data(self, logic_data):
        """기존 메서드 수정"""
        self.LogicNameInput__QLineEdit.setText(logic_data.get('name', ''))
        self.RepeatCountInput__QSpinBox.setValue(logic_data.get('repeat_count', 1))
        self.LogicItemList__QListWidget.set_items(logic_data.get('items', []))
        
        # 중첩로직 여부 설정
        is_nested = logic_data.get('is_nested', False)
        self.is_nested_checkbox.setChecked(is_nested)
        
        # 중첩로직이 아닐 경우에만 트리거 키 설정
        if not is_nested:
            self.trigger_key_info = logic_data.get('trigger_key')
            if self.trigger_key_info:
                self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.set_key_info(self.trigger_key_info)

    def clear_logic_info(self):
        """로직 정보 초기화"""
        try:
            # 로직 이름 초기화
            self.LogicNameInput__QLineEdit.clear()
            
            # 트리거 키 초기화
            self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.clear_key()
            self.trigger_key_info = {}
            
            # 반복 횟수 초기화
            self.RepeatCountInput__QSpinBox.setValue(1)
            
            # 중첩로직용 체크박스 초기화
            self.is_nested_checkbox.setChecked(False)
            
            # 로직 아이템 목록 초기화
            self.LogicItemList__QListWidget.clear()
            
            # 로직 아이템 정보 초기화
            self.logic_items.clear()
            
            # 현재 편집 중인 로직 ID 초기화
            self.current_logic_id = None
            
            self.base_log_manager.log(
                message="로직 정보가 초기화되었습니다",
                level="INFO",
                file_name="logic_detail_widget"
            )
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 정보 초기화 중 오류 발생: {str(e)}",
                level="ERROR", 
                file_name="logic_detail_widget"
            )

    def _copy_item(self):
        """선택된 아이템들을 복사"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        if selected_items:
            # 텍스트와 함께 전체 데이터를 사용
            self.copied_items = []
            for item in selected_items:
                item_data = {
                    'text': item.text(),
                    'data': item.data(Qt.UserRole)
                }
                self.copied_items.append(item_data)
            items_count = len(self.copied_items)
            self.base_log_manager.log(
                message=f"{items_count}개의 로직 구성 아이템이 복사되었습니다",
                level="INFO",
                file_name="logic_detail_widget"
            )

    def clear_key(self):
        """트리거 키 정보 초기화"""
        self.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.clear_key()
        self.TriggerKeyInput__QLineEdit.clear()
        self.TriggerKeyInput__QLineEdit.setPlaceholderText("트리거 키를 설정하세요")
        self.trigger_key_info = None
        self.base_log_manager.log(
            message="트리거 키 정보가 초기화되었습니다",
            level="DEBUG",
            file_name="logic_detail_widget"
        )

    def _delete_logic_detail_items(self):
        """선택된 아이템을 삭제"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                item_data = item.data(Qt.UserRole)
                if item_data:
                    self.repository.delete_logic_detail_items(item_data)

    def clear_all(self):
        """모든 UI 필드 초기화"""
        self.LogicNameInput__QLineEdit.clear()
        self.RepeatCountInput__QSpinBox.setValue(1)
        self.is_nested_checkbox.setChecked(False)
        self.clear_key()
        self.repository.clear_logic_detail_items()  # Repository를 통해 아이템 목록 초기화