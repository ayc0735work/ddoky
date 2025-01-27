from PySide6.QtCore import QObject, Signal, Qt
from BE.log.base_log_manager import BaseLogManager
from .Logic_Database_Manager import Logic_Database_Manager
from BE.function.make_logic.logic_list.logic_list_widget import LogicListWidget
import uuid
import copy

class LogicListController(QObject):
    """로직 리스트 컨트롤러
    
    로직 목록의 데이터 관리와 상태를 처리하는 컨트롤러입니다.
    위젯의 UI 이벤트를 처리하고 데이터 저장소와의 상호작용을 관리합니다.
    
    Attributes:
        widget (LogicListWidget): 연결된 로직 리스트 위젯
        clipboard (dict): 복사된 로직 정보 임시 저장
    """
    
    def __init__(self, widget: LogicListWidget):
        """초기화
        
        Args:
            widget (LogicListWidget): 로직 리스트 위젯
            
        초기화 프로세스:
        1. 위젯 연결
        2. 메모리 상태 초기화
        3. 시그널 연결
        4. 저장된 로직 로드
        """
        super().__init__()
        self.logic_list_widget = widget
        self.clipboard = {
            'items': [],  # 복사된 로직들의 리스트
            'source_orders': []  # 각 로직의 원본 순서
        }
        self.logic_database_manager = Logic_Database_Manager()
        self.base_log_manager = BaseLogManager.instance()
        self.logic_list_widget.request_logic_detail.connect(self._load_logic_detail)
        self._connect_signals()
        self.load_saved_logics_list()

    logic_detail_updated = Signal(int, dict)  # 로직 ID와 상세 정보를 전달하는 시그널  

    def _connect_signals(self):
        """시그널 연결 설정
        
        위젯에서 발생하는 다양한 이벤트 시그널을 해당하는 처리 메서드에 연결합니다.
        
        연결되는 시그널:
        - logic_up_move_requested -> process_logic_move_up
        - logic_down_move_requested -> process_logic_move_down
        - logic_edit_requested -> process_logic_update
        - logic_delete_requested -> process_logic_data_delete
        - logic_copy_requested -> process_logic_copy
        - logic_paste_requested -> process_logic_paste
        - reload_logics_requested -> load_saved_logics_list
        - request_logic_detail -> _request_getting_logic_detail_data
        """
        self.logic_list_widget.logic_up_move_requested.connect(self.process_logic_move_up)
        self.logic_list_widget.logic_down_move_requested.connect(self.process_logic_move_down)
        self.logic_list_widget.logic_delete_requested.connect(self.process_logic_data_delete)
        self.logic_list_widget.logic_copy_requested.connect(self.process_logic_copy)
        self.logic_list_widget.logic_paste_requested.connect(self.process_logic_paste)
        self.logic_list_widget.reload_logics_requested.connect(self.load_saved_logics_list)
        self.logic_list_widget.request_logic_detail.connect(self._request_getting_logic_detail_data)
        # self.logic_list_widget.logic_edit_requested.connect(self.process_logic_update) # 기존 로직 정보 업데이트 시그널 연결해야함

    def _load_logic_detail(self, logic_id):
        logic_detail = self.logic_database_manager.get_logic_detail_data(logic_id)
        if logic_detail:
            self.logic_detail_updated.emit(logic_id, logic_detail)
    

    def load_saved_logics_list(self):
        """저장된 로직 리스트를 불러오기
        
        DB에서 로직 리스트를 로드하고 UI를 업데이트합니다.
        """
        try:
            # DB에서 로직 정보 가져오기
            logics = self.logic_database_manager.get_all_logics_list()
            
            # 위젯 업데이트
            self.logic_list_widget.clear_logic_list()
            for logic in logics:
                self.logic_list_widget.add_logic_item({
                    'logic_name': logic['logic_name']
                }, str(logic['id']))
            
            self.base_log_manager.log(
                message="로직 목록을 새로 업데이트 했습니다.",
                level="INFO",
                file_name="logic_list_controller",
                method_name="load_saved_logics_list"
            )

        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 목록 불러오기 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller",
                method_name="load_saved_logics_list"
            )
            
    def process_logic_data_save(self, logic_info):
        """새로운 로직 저장 처리
        
        새로 생성된 로직을 저장하고 UI에 추가합니다.
        
        Args:
            logic_info (dict): 저장할 로직 정보
            
        Returns:
            str: 생성된 로직 ID. 실패 시 None
            
        프로세스:
        1. DB에 로직 저장
        2. UI 업데이트
        """
        try:
            # DB에 저장
            if not self.logic_database_manager.save_logic_detail_data(logic_info):
                raise Exception("DB에 로직 저장 실패")
            
            # UI 업데이트
            self.load_saved_logics_list()  # 전체 목록 새로고침
            
            self.base_log_manager.log(
                message=f"로직 '{logic_info.get('logic_name', '')}'이(가) 저장되었습니다",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_data_save"
            )
            
            return logic_info.get('id')
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_data_save", 
                print_to_terminal=True
            )
            return None
            
    def process_logic_update(self, logic_id, new_info):
        """로직 업데이트 처리
        
        기존 로직의 정보를 업데이트합니다.
        
        Args:
            logic_id (str): 업데이트할 로직의 ID
            new_info (dict): 새로운 로직 정보
            
        프로세스:
        1. DB에서 로직 정보 업데이트
        2. UI 업데이트
        """
        try:
            # 1. DB에서 로직 정보 업데이트
            if not self.logic_database_manager.update_logic_detail_data(logic_id, new_info):
                raise Exception("DB에서 로직 업데이트 실패")
            
            # 2. UI 업데이트
            self.load_saved_logics_list()  # 전체 목록 새로고침
            
            self.base_log_manager.log(
                message=f"로직 '{new_info.get('logic_name', '')}'이(가) 업데이트되었습니다",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_update"
            )
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 업데이트 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_update",
                print_to_terminal=True
            )
            
    def process_logic_data_delete(self, logic_ids):
        """로직 삭제 처리
        
        지정된 로직들을 삭제합니다.
        
        Args:
            logic_ids (list): 삭제할 로직의 ID 리스트
            
        프로세스:
        1. 현재 스크롤 위치 저장
        2. 데이터베이스에서 로직들 삭제
        3. 전체 로직 목록 새로고침
        4. 스크롤 위치 복원
        """
        try:
            # 현재 스크롤 위치 저장
            current_scroll = self.logic_list_widget.get_current_scroll_position()

            # 모든 로직 삭제
            for logic_id in logic_ids:
                # 문자열로 변환하여 전달
                str_logic_id = str(logic_id)
                if not self.logic_database_manager.delete_logic_data(str_logic_id):
                    raise Exception(f"데이터베이스에서 로직 {str_logic_id} 삭제 실패")

            # 전체 로직 목록 새로고침 (한 번만 수행)
            self.load_saved_logics_list()

            # 스크롤 위치 복원
            self.logic_list_widget.set_scroll_position(current_scroll)

        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 삭제 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_data_delete",
                print_to_terminal=True
            )
            
    def process_logic_move_up(self, logic_id):
        """로직을 위로 이동
        
        Args:
            logic_id (str): 이동할 로직의 ID
            
        프로세스:
        1. 현재 스크롤 위치 저장
        2. DB에서 로직 순서 업데이트
        3. 목록 새로고침
        4. 스크롤 위치 복원
        5. 이동된 로직 다시 선택
        """
        # 현재 스크롤 위치 저장
        current_scroll = self.logic_list_widget.get_current_scroll_position()

        try:
            if not self.logic_database_manager.logic_order_minus_one_change(logic_id):
                raise Exception("DB에서 로직 순서 업데이트 실패")
            
            # 목록 새로고침
            self.load_saved_logics_list()
            
            # 스크롤 위치 복원
            self.logic_list_widget.set_scroll_position(current_scroll)
            
            # 이동된 로직 다시 선택
            self.logic_list_widget.select_logic_by_id(logic_id)
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 이동 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_move_up", 
                print_to_terminal=True
            )
            
    def process_logic_move_down(self, logic_id):
        """로직을 아래로 이동
        
        Args:
            logic_id (str): 이동할 로직의 ID
            
        프로세스:
        1. 현재 스크롤 위치 저장
        2. DB에서 로직 순서 업데이트
        3. 목록 새로고침
        4. 스크롤 위치 복원
        5. 이동된 로직 다시 선택
        """
        # 현재 스크롤 위치 저장
        current_scroll = self.logic_list_widget.get_current_scroll_position()

        try:
            if not self.logic_database_manager.logic_order_plus_one_change(logic_id):
                raise Exception("DB에서 로직 순서 업데이트 실패")
            
            # 목록 새로고침
            self.load_saved_logics_list()
            
            # 스크롤 위치 복원
            self.logic_list_widget.set_scroll_position(current_scroll)
            
            # 이동된 로직 다시 선택
            self.logic_list_widget.select_logic_by_id(logic_id)
            
            self.base_log_manager.log(
                message=f"로직을 아래로 이동했습니다 (ID: {logic_id})",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_move_down"
            )
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 이동 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_move_down", 
                print_to_terminal=True
            )
            
    def process_logic_copy(self, logic_ids):
        """로직 복사 처리
        
        선택된 로직들을 클립보드에 복사합니다.
        
        Args:
            logic_ids (list): 복사할 로직들의 ID 리스트
        """
        try:
            # 클립보드 초기화
            self.clipboard = {
                'items': [],
                'source_orders': []
            }
            
            for logic_id in logic_ids:
                # DB에서 로직 정보 조회
                logic_detail = self.logic_database_manager.get_logic_detail_data(logic_id)
                if logic_detail:
                    self.clipboard['items'].append(copy.deepcopy(logic_detail))
                    self.clipboard['source_orders'].append(logic_detail['logic_order'])
            
            if self.clipboard['items']:
                self.base_log_manager.log(
                    message=f"{len(logic_ids)}개의 로직이 복사되었습니다",
                    level="INFO",
                    file_name="logic_list_controller", 
                    method_name="process_logic_copy"
                )
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 복사 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_copy",
                print_to_terminal=True
            )
            
    def process_logic_paste(self):
        """로직 붙여넣기 처리
        
        클립보드에 저장된 로직들을 새로운 로직으로 붙여넣기합니다.
        
        프로세스:
        1. 현재 스크롤 위치 저장
        2. 현재 선택된 로직의 순서 확인
        3. 트랜잭션으로 순서 업데이트
        4. 복사된 로직들을 순서대로 저장
        5. 스크롤 위치 복원
        """
        if not self.clipboard['items']:
            return
            
        try:
            # 1. 현재 스크롤 위치 저장
            current_scroll = self.logic_list_widget.get_current_scroll_position()

            # 2. 현재 선택된 로직의 순서 가져오기
            current_item = self.logic_list_widget.logic_list.currentItem()
            if not current_item:
                return
                
            current_logic_id = current_item.data(Qt.UserRole)
            current_logic = self.logic_database_manager.get_logic_detail_data(current_logic_id)
            target_order = current_logic['logic_order']
            
            # 3. 트랜잭션 시작
            connection = self.logic_database_manager.db.get_connection()
            cursor = connection.cursor()
            
            try:
                connection.execute("BEGIN TRANSACTION")
                
                # 4. 뒤의 로직들 순서 조정 (복사된 로직 개수만큼)
                shift_amount = len(self.clipboard['items'])
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = logic_order + ?
                    WHERE logic_order > ?
                """, (shift_amount, target_order))
                
                # 5. 새 로직들 순서대로 저장
                for idx, logic_data in enumerate(self.clipboard['items'], 1):
                    new_logic = copy.deepcopy(logic_data)
                    new_logic['logic_name'] = f"{new_logic['logic_name']} (복사본)"
                    new_logic['trigger_key'] = None
                    new_logic['isNestedLogicCheckboxSelected'] = True
                    new_logic['logic_order'] = target_order + idx
                    
                    self.process_logic_data_save(new_logic)
                
                # 트랜잭션 커밋
                connection.commit()
                
                # 6. 스크롤 위치 복원
                self.logic_list_widget.set_scroll_position(current_scroll)
                
                self.base_log_manager.log(
                    message=f"{shift_amount}개의 로직이 순서 {target_order + 1}부터 붙여넣기되었습니다",
                    level="INFO",
                    file_name="logic_list_controller", 
                    method_name="process_logic_paste"
                )
                
            except Exception as e:
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 붙여넣기 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_paste",
                print_to_terminal=True
            )
            
    def _format_logic_item_text(self, logic_info):
        """로직 아이템의 표시 텍스트를 생성"""
        if not logic_info:
            return ""
        name = logic_info.get('logic_name', '')  # name을 logic_name으로 수정
        
        if logic_info.get('isNestedLogicCheckboxSelected', False):
            return f"[ {name} ] --- 중첩로직용"
        
        trigger_key = logic_info.get('trigger_key', {})
        if trigger_key and 'key_code' in trigger_key:
            key_text = trigger_key['key_code']
            modifiers_key_flag = trigger_key.get('modifiers_key_flag', 0)
            
            modifier_text = []
            if modifiers_key_flag & 1: modifier_text.append("Alt")
            if modifiers_key_flag & 2: modifier_text.append("Ctrl")
            if modifiers_key_flag & 4: modifier_text.append("Shift")
            if modifiers_key_flag & 8: modifier_text.append("Win")
            
            if modifier_text:
                return f"[ {name} ] --- {' + '.join(modifier_text)} + {key_text}"
            else:
                return f"[ {name} ] --- {key_text}"
        return f"[ {name} ]"
        
    def _get_logic_name_from_text(self, text):
        """표시 텍스트에서 로직 이름을 추출"""
        try:
            start = text.find('[') + 1
            end = text.find(']')
            if start > 0 and end > start:
                return text[start:end].strip()
            return text
        except (AttributeError, IndexError):
            return text

    def get_saved_logics(self):
        """저장된 모든 로직 정보를 반환합니다.
        
        Returns:
            list: 모든 로직의 정보 목록
        """
        try:
            return self.logic_database_manager.get_all_logics_list()
        except Exception as e:
            self.base_log_manager.log(
                message=f"저장된 로직 목록 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller",
                method_name="get_saved_logics",
                print_to_terminal=True
            )
            return []

    def get_logic_by_name(self, logic_name):
        """이름으로 로직 정보 찾기
        
        Args:
            logic_name (str): 찾을 로직의 이름
            
        Returns:
            dict: 찾은 로직 정보. 없으면 None
        """
        try:
            # DB에서 로직 정보 찾기
            logic_info = self.logic_database_manager.get_logic_by_name(logic_name)
            
            if not logic_info:
                self.base_log_manager.log(
                    message=f"로직 '{logic_name}'을(를) 찾을 수 없습니다",
                    level="WARNING",
                    file_name="logic_list_controller", 
                    method_name="get_logic_by_name"
                )
            return logic_info
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 정보 검색 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="get_logic_by_name",
                print_to_terminal=True
            )
            return None

    def _request_getting_logic_detail_data(self, logic_id):
        """로직 상세 정보 요청 처리
        
        Args:
            logic_id (str): 요청된 로직의 ID
        """
        logic_detail = self.logic_database_manager.get_logic_detail_data(logic_id)
        
        if logic_detail:
            # 로직 상세 정보를 위젯으로 전달
            self.logic_list_widget.logic_edit_requested.emit(logic_id, logic_detail)
            
            self.base_log_manager.log(
                message=f"로직 '{logic_detail['logic_name']}'의 상세 정보를 불러왔습니다",
                level="INFO",
                file_name="logic_list_controller",
                method_name="_request_getting_logic_detail_data"
            )
        else:
            self.base_log_manager.log(
                message="로직 상세 정보를 불러오지 못했습니다",
                level="WARNING",
                file_name="logic_list_controller",
                method_name="_request_getting_logic_detail_data"
            )
