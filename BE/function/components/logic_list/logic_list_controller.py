from PySide6.QtCore import QObject, Signal
from BE.settings.settings_data_manager import SettingsManager
import uuid
import copy

class LogicListController(QObject):
    """로직 리스트 컨트롤러"""
    
    log_message = Signal(str)
    
    def __init__(self, widget):
        """초기화
        
        Args:
            widget (LogicListWidget): 로직 리스트 위젯
        """
        super().__init__()
        self.widget = widget
        self.settings_manager = SettingsManager()
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리
        self.clipboard = None  # 복사된 로직 저장용
        self._connect_signals()
        self.load_saved_logics()
        
    def _connect_signals(self):
        """시그널 연결"""
        self.widget.logic_move_requested.connect(self.process_logic_move)
        self.widget.logic_edit_requested.connect(self.process_logic_update)
        self.widget.logic_delete_requested.connect(self.process_logic_delete)
        self.widget.logic_copy_requested.connect(self.process_logic_copy)
        self.widget.logic_paste_requested.connect(self.process_logic_paste)
        
        self.widget.log_message.connect(self.log_message)
        
    def load_saved_logics(self):
        """저장된 로직 정보 불러오기"""
        try:
            # 설정 다시 로드
            self.settings_manager.reload_settings()
            
            # 로직 정보 가져오기
            logics = self.settings_manager.settings.get('logics', {})
            
            # order 값으로 정렬
            sorted_logics = sorted(logics.items(), key=lambda x: x[1].get('order', 0))
            
            # 위젯 업데이트
            self.widget.clear_logic_list()
            for logic_id, logic_info in sorted_logics:
                self.widget.add_logic_item(logic_info, logic_id)
                
            self.log_message.emit("로직 목록을 불러왔습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 목록 불러오기 중 오류 발생: {str(e)}")
            
    def save_logics_to_settings(self):
        """현재 로직 목록을 설정에 저장"""
        try:
            self.log_message.emit("[로직 저장 시작] 현재 로직 목록을 설정에 저장합니다.")
            logics = {}
            
            # 모든 로직 정보 수집
            for i in range(self.widget.get_logic_count()):
                logic_id = self.widget.get_logic_id_at(i)
                if not logic_id:
                    self.log_message.emit(f"[경고] 아이템 {i}에 로직 ID가 없습니다.")
                    continue
                
                self.log_message.emit(f"[로직 처리] 로직 ID: {logic_id} 처리 시작")
                
                # 로직 정보 가져오기
                logic_info = self.settings_manager.load_logics(force=True).get(logic_id)
                if not logic_info:
                    self.log_message.emit(f"[경고] 로직 ID {logic_id}에 해당하는 로직 정보를 찾을 수 없습니다.")
                    continue
                
                # 순서 업데이트
                logic_info['order'] = i
                logics[logic_id] = logic_info
            
            # 설정에 저장
            settings = self.settings_manager._load_settings() or {}
            settings['logics'] = logics
            self.settings_manager._save_settings(settings)
            self.log_message.emit("[설정 저장 완료] 로직 정보가 성공적으로 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"[오류] 로직 저장 중 오류 발생: {str(e)}")
            
    def process_logic_save(self, logic_info):
        """새로운 로직 저장 처리"""
        try:
            # 새 UUID 생성
            logic_id = str(uuid.uuid4())
            logic_info['id'] = logic_id
            
            # 설정에 저장
            logics = self.settings_manager.load_logics()
            logics[logic_id] = logic_info
            self.settings_manager.save_logics(logics)
            
            # UI 업데이트
            self.widget.add_logic_item(logic_info, logic_id)
            self.log_message.emit(f"로직 '{logic_info.get('name', '')}'이(가) 저장되었습니다.")
            
            return logic_id
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")
            return None
            
    def process_logic_update(self, logic_id, new_info):
        """로직 업데이트 처리"""
        try:
            logics = self.settings_manager.load_logics()
            if logic_id in logics:
                logics[logic_id].update(new_info)
                self.settings_manager.save_logics(logics)
                self.widget.update_logic_item(logic_id, logics[logic_id])
                self.log_message.emit(f"로직 '{new_info.get('name', '')}'이(가) 업데이트되었습니다.")
                
        except Exception as e:
            self.log_message.emit(f"로직 업데이트 중 오류 발생: {str(e)}")
            
    def process_logic_delete(self, logic_id):
        """로직 삭제 처리"""
        try:
            # 설정 다시 로드하여 최신 상태 확인
            self.settings_manager.reload_settings()
            logics = self.settings_manager.settings.get('logics', {})
            
            if logic_id in logics:
                logic_name = logics[logic_id].get('name', '')
                
                # 로직 삭제
                del logics[logic_id]
                
                # 설정 저장
                settings = self.settings_manager._load_settings() or {}
                settings['logics'] = logics
                self.settings_manager._save_settings(settings)
                
                # 메모리상의 saved_logics 업데이트
                self.saved_logics = logics.copy()
                
                # UI에서 해당 아이템만 제거
                self.widget.remove_logic_item(logic_id)
                
                self.log_message.emit(f"로직 '{logic_name}'이(가) 삭제되었습니다.")
                
        except Exception as e:
            self.log_message.emit(f"로직 삭제 중 오류 발생: {str(e)}")
            import traceback
            self.log_message.emit(traceback.format_exc())
            
    def process_logic_move(self, logic_id, new_position):
        """로직 이동 처리"""
        try:
            logics = self.settings_manager.load_logics()
            if logic_id in logics:
                # 순서 업데이트
                for id, logic in logics.items():
                    if logic.get('order', 0) >= new_position:
                        logic['order'] += 1
                logics[logic_id]['order'] = new_position
                
                self.settings_manager.save_logics(logics)
                self.load_saved_logics()  # 전체 목록 새로고침
                
        except Exception as e:
            self.log_message.emit(f"로직 이동 중 오류 발생: {str(e)}")
            
    def process_logic_copy(self, logic_id):
        """로직 복사 처리"""
        try:
            logics = self.settings_manager.load_logics()
            if logic_id in logics:
                self.clipboard = copy.deepcopy(logics[logic_id])
                self.clipboard['id'] = logic_id
                self.log_message.emit(f"로직 '{self.clipboard.get('name', '')}'이(가) 복사되었습니다.")
                
        except Exception as e:
            self.log_message.emit(f"로직 복사 중 오류 발생: {str(e)}")
            
    def process_logic_paste(self):
        """로직 붙여넣기 처리"""
        if not self.clipboard:
            return
            
        try:
            new_logic = copy.deepcopy(self.clipboard)
            new_logic['name'] = f"{new_logic['name']} (복사본)"
            new_logic['trigger_key'] = None
            new_logic['is_nested'] = True
            
            # 새로운 UUID로 저장
            self.process_logic_save(new_logic)
            
        except Exception as e:
            self.log_message.emit(f"로직 붙여넣기 중 오류 발생: {str(e)}")
            
    def _format_logic_item_text(self, logic_info):
        """로직 아이템의 표시 텍스트를 생성"""
        if not logic_info:
            return ""
        name = logic_info.get('name', '')
        
        if logic_info.get('is_nested', False):
            return f"[ {name} ] --- 중첩로직용"
        
        trigger_key = logic_info.get('trigger_key', {})
        if trigger_key and 'key_code' in trigger_key:
            key_text = trigger_key['key_code']
            modifiers = trigger_key.get('modifiers', 0)
            
            modifier_text = []
            if modifiers & 1: modifier_text.append("Alt")
            if modifiers & 2: modifier_text.append("Ctrl")
            if modifiers & 4: modifier_text.append("Shift")
            if modifiers & 8: modifier_text.append("Win")
            
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
        """저장된 로직 정보 반환"""
        return self.saved_logics

    def get_logic_by_name(self, logic_name):
        """이름으로 로직 정보 찾기"""
        try:
            # 설정에서 최신 로직 정보 가져오기
            logics = self.settings_manager.load_logics()
            
            # 이름으로 로직 찾기
            for logic_id, logic_info in logics.items():
                if logic_info.get('name') == logic_name:
                    return logic_info
            return None
            
        except Exception as e:
            self.log_message.emit(f"로직 정보 검색 중 오류 발생: {str(e)}")
            return None

    def on_logic_saved(self, logic_info):
        """로직이 저장되었을 때의 처리"""
        logic_id = logic_info.get('id') or str(uuid.uuid4())
        self.saved_logics[logic_id] = logic_info
        self.widget.add_logic_item(logic_info, logic_id)
        self.log_message.emit(f"로직 '{logic_info.get('name')}'이(가) 저장되었습니다.")

    def on_logic_updated(self, logic_info):
        """로직이 수정되었을 때의 처리"""
        logic_id = logic_info.get('id')
        if logic_id in self.saved_logics:
            self.saved_logics[logic_id].update(logic_info)
            self.widget.update_logic_item(logic_id, self.saved_logics[logic_id])
            self.log_message.emit(f"로직 '{logic_info.get('name')}'이(가) 업데이트되었습니다.")
