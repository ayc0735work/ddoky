from PySide6.QtCore import QObject, Signal
from BE.log.base_log_manager import BaseLogManager
from .Logic_Database_Manager import Logic_Database_Manager
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
    
    def __init__(self, widget):
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
        self.widget = widget
        self.widget.set_controller(self)  # 위젯에 컨트롤러 설정
        self.clipboard = None  # 복사된 로직 저장용
        self.logic_database_manager = Logic_Database_Manager()
        self.base_log_manager = BaseLogManager.instance()
        self._connect_signals()
        self.load_saved_logics()
        
    def _connect_signals(self):
        """시그널 연결 설정
        
        위젯에서 발생하는 다양한 이벤트 시그널을 해당하는 처리 메서드에 연결합니다.
        
        연결되는 시그널:
        - logic_up_move_requested -> process_logic_move_up
        - logic_down_move_requested -> process_logic_move_down
        - logic_edit_requested -> process_logic_update
        - logic_delete_requested -> process_logic_delete
        - logic_copy_requested -> process_logic_copy
        - logic_paste_requested -> process_logic_paste
        - reload_logics_requested -> load_saved_logics
        """
        self.widget.logic_up_move_requested.connect(self.process_logic_move_up)
        self.widget.logic_down_move_requested.connect(self.process_logic_move_down)
        self.widget.logic_edit_requested.connect(self.process_logic_update)
        self.widget.logic_delete_requested.connect(self.process_logic_delete)
        self.widget.logic_copy_requested.connect(self.process_logic_copy)
        self.widget.logic_paste_requested.connect(self.process_logic_paste)
        self.widget.reload_logics_requested.connect(self.load_saved_logics)
        
    def load_saved_logics(self):
        """저장된 로직 정보 불러오기
        
        DB에서 로직 기본 정보를 로드하고 UI를 업데이트합니다.
        스크롤 위치를 보존합니다.
        """
        try:
            # 현재 스크롤 위치 저장
            current_scroll = self.widget.get_scroll_position()
            
            # DB에서 로직 정보 가져오기
            logics = self.logic_database_manager.get_all_logics_list()
            
            # 위젯 업데이트
            self.widget.clear_logic_list()
            for logic in logics:
                self.widget.add_logic_item({
                    'logic_name': logic['logic_name']
                }, str(logic['id']))
                
            # 스크롤 위치 복원
            self.widget.refresh_logic_list(current_scroll)
            
            self.base_log_manager.log(
                message="로직 목록을 DB에서 불러왔습니다",
                level="INFO",
                file_name="logic_list_controller",
                method_name="load_saved_logics"
            )
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 목록 불러오기 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller",
                method_name="load_saved_logics"
            )
            
    def process_logic_save(self, logic_info):
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
            if not self.logic_database_manager.save_logic_detail(logic_info):
                raise Exception("DB에 로직 저장 실패")
            
            # UI 업데이트
            self.load_saved_logics()  # 전체 목록 새로고침
            
            self.base_log_manager.log(
                message=f"로직 '{logic_info.get('logic_name', '')}'이(가) 저장되었습니다",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_save"
            )
            
            return logic_info.get('id')
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_save", 
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
            if not self.logic_database_manager.update_logic_detail(logic_id, new_info):
                raise Exception("DB에서 로직 업데이트 실패")
            
            # 2. UI 업데이트
            self.load_saved_logics()  # 전체 목록 새로고침
            
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
            
    def process_logic_delete(self, logic_id):
        """로직 삭제 처리
        
        지정된 로직을 삭제합니다.
        
        Args:
            logic_id (str): 삭제할 로직의 ID
            
        프로세스:
        1. 데이터베이스에서 로직 삭제
        2. 설정에서 로직 삭제
        3. 전체 로직 목록 새로고침
        """
        try:
            # 현재 스크롤 위치 저장
            current_scroll = self.widget.get_scroll_position()
            
            # 1. 데이터베이스에서 삭제
            if not self.logic_database_manager.delete_logic(logic_id):
                raise Exception("데이터베이스에서 로직 삭제 실패")
               
            # 2. 전체 로직 목록 새로고침
            self.load_saved_logics()
            
            # 스크롤 위치 복원
            self.widget.refresh_logic_list(current_scroll)
                
            self.base_log_manager.log(
                message="로직 목록을 새로고침했습니다",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_delete"
            )

        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 삭제 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller", 
                method_name="process_logic_delete",
                print_to_terminal=True
            )
            
    def process_logic_move_up(self, logic_id):
        """로직을 위로 이동
        
        Args:
            logic_id (str): 이동할 로직의 ID
        """
        try:
            if not self.logic_database_manager.logic_order_minus_one_change(logic_id):
                raise Exception("DB에서 로직 순서 업데이트 실패")
            
            self.load_saved_logics()
            
            self.base_log_manager.log(
                message=f"로직을 위로 이동했습니다 (ID: {logic_id})",
                level="INFO",
                file_name="logic_list_controller", 
                method_name="process_logic_move_up"
            )
                
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
        """
        try:
            if not self.logic_database_manager.logic_order_plus_one_change(logic_id):
                raise Exception("DB에서 로직 순서 업데이트 실패")
            
            self.load_saved_logics()
            
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
            
    def process_logic_copy(self, logic_id):
        """로직 복사 처리
        
        선택된 로직을 클립보드에 복사합니다.
        
        Args:
            logic_id (str): 복사할 로직의 ID
            
        프로세스:
        1. DB에서 로직 정보 조회
        2. 로직 정보 깊은 복사
        3. 클립보드에 저장
        """
        try:
            # 1. DB에서 로직 정보 조회
            logic_detail = self.logic_database_manager.get_logic_detail_data(logic_id)
            if not logic_detail:
                raise Exception("DB에서 로직 정보를 찾을 수 없습니다")
            
            # 2. 로직 정보 깊은 복사 및 클립보드에 저장
            self.clipboard = copy.deepcopy(logic_detail)
            self.clipboard['id'] = logic_id
            
            self.base_log_manager.log(
                message=f"로직 '{logic_detail.get('logic_name', '')}'이(가) 복사되었습니다",
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
        
        클립보드에 저장된 로직을 새로운 로직으로 붙여넣기합니다.
        
        프로세스:
        1. 클립보드 데이터 깊은 복사
        2. 새 이름 설정 (복사본)
        3. 트리거 키 초기화
        4. 새 로직으로 저장
        """
        if not self.clipboard:
            return
            
        try:
            new_logic = copy.deepcopy(self.clipboard)
            new_logic['logic_name'] = f"{new_logic['logic_name']} (복사본)"
            new_logic['trigger_key'] = None
            new_logic['isNestedLogicCheckboxSelected'] = True
            
            # 새로운 UUID로 저장
            self.process_logic_save(new_logic)
            
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

    def load_logic_detail(self, logic_id):
        """로직 상세 정보를 불러옵니다.
        
        Args:
            logic_id (str): 불러올 로직의 ID
            
        Returns:
            dict: 로직 상세 정보. 실패 시 None
        """
        try:
            # DB에서 로직 상세 정보 조회
            logic_detail = self.logic_database_manager.get_logic_detail_data(logic_id)
            
            if logic_detail:
                self.base_log_manager.log(
                    message=f"로직 '{logic_detail['logic_name']}'의 상세 정보를 불러왔습니다. \n 불러온 로직: {logic_detail}",
                    level="INFO",
                    file_name="logic_list_controller",
                    method_name="load_logic_detail"
                )
            else:
                self.base_log_manager.log(
                    message=f"로직 ID {logic_id}의 상세 정보를 불러오지 못했습니다.",
                    level="WARNING",
                    file_name="logic_list_controller",
                    method_name="load_logic_detail"
                )
                
            return logic_detail
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 상세 정보 불러오기 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_list_controller",
                method_name="load_logic_detail",
                print_to_terminal=True
            )
            return None
