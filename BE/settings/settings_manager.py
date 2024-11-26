import json
import os
from pathlib import Path
import uuid

class SettingsManager:
    """설정 파일 관리 클래스"""
    
    def __init__(self):
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_file = Path(current_dir) / "settings.json"
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """설정 파일 로드"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # UUID 마이그레이션 수행
                    return self._migrate_to_uuid(settings)
            except json.JSONDecodeError:
                return self._get_default_settings()
        return self._get_default_settings()
    
    def _save_settings(self):
        """설정 파일에 현재 설정을 저장합니다."""
        try:
            # 로직 데이터에서 uuid 필드 제거 및 필드 순서 정리
            if 'logics' in self.settings:
                ordered_logics = {}
                for logic_id, logic_data in self.settings['logics'].items():
                    # items 리스트 내부의 아이템들도 필드 순서 정렬
                    ordered_items = []
                    for item in logic_data.get('items', []):
                        if 'type' in item:
                            if item['type'] == 'delay':
                                # 딜레이 아이템의 경우
                                ordered_item = {
                                    'type': 'delay',
                                    'display_text': item.get('display_text', f"지연시간 : {item.get('duration', 0)}초"),
                                    'duration': item.get('duration', 0),
                                    'order': item.get('order', 0)
                                }
                            elif item['type'] == 'key_input':
                                # 키 입력 아이템의 경우
                                ordered_item = self._create_ordered_key_input_item(item)
                            elif item['type'] == 'logic':
                                ordered_item = self._create_ordered_logic_item(item)
                        else:
                            # 이전 형식의 아이템의 경우
                            ordered_item = {
                                'content': item.get('content', ''),
                                'order': item.get('order', 0)
                            }
                        ordered_items.append(ordered_item)

                    # 필드 순서 정렬
                    ordered_logic = {
                        'order': logic_data.get('order', 0),
                        'name': logic_data.get('name', ''),
                        'created_at': logic_data.get('created_at', ''),
                        'updated_at': logic_data.get('updated_at', ''),
                        'trigger_key': logic_data.get('trigger_key', {}),
                        'repeat_count': logic_data.get('repeat_count', 1),
                        'items': ordered_items
                    }
                    ordered_logics[logic_id] = ordered_logic
                self.settings['logics'] = ordered_logics

            # 설정 파일 저장 (파일을 직접 열고 닫음)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
                f.flush()  # 버퍼 내용을 즉시 디스크에 쓰기
                os.fsync(f.fileno())  # 파일 디스크립터를 동기화
                
            # 파일이 제대로 저장되었는지 확인
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                if saved_settings != self.settings:
                    print("설정 파일이 제대로 저장되지 않았습니다.")
                    return False
                
            return True
                
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {str(e)}")
            return False
    
    def _get_default_settings(self):
        """기본 설정값 반환"""
        return {
            "window": {
                "position": {
                    "x": 100,
                    "y": 100
                },
                "size": {
                    "width": 800,
                    "height": 600
                }
            },
            "logics": {}  # UUID를 키로 사용하는 로직 저장소
        }
    
    def _migrate_to_uuid(self, settings):
        """기존 로직들에 UUID를 부여하고 마이그레이션
        
        Args:
            settings (dict): 마이그레이션할 설정 데이터
            
        Returns:
            dict: 마이그레이션된 설정 데이터
        """
        try:
            if not isinstance(settings, dict):
                print("설정 데이터가 딕셔너리 형식이 아닙니다. 기본값으로 초기화합니다.")
                return self._get_default_settings()
                
            if 'logics' not in settings:
                print("로직 데이터가 없습니다. 새로운 구조로 초기화합니다.")
                settings['logics'] = {}
                return settings
                
            if not isinstance(settings['logics'], dict):
                print("로직 데이터가 올바른 형식이 아닙니다. 초기화합니다.")
                settings['logics'] = {}
                return settings

            # logic_names 필드가 있다면 제거
            if 'logic_names' in settings:
                del settings['logic_names']

            # 로직 데이터 검증 및 정리
            validated_logics = {}
            for logic_id, logic in settings['logics'].items():
                if not isinstance(logic, dict):
                    print(f"경고: 잘못된 형식의 로직을 건너뜁니다.")
                    continue

                # UUID 형식 검증
                try:
                    uuid.UUID(logic_id)
                except ValueError:
                    # 잘못된 UUID면 새로 생성
                    new_id = str(uuid.uuid4())
                    print(f"잘못된 UUID 형식 감지: 새 UUID를 생성합니다.")
                    logic_id = new_id

                # 필수 필드 확인
                if 'name' not in logic:
                    print(f"경고: 이름이 없는 로직을 건너뜁니다.")
                    continue

                validated_logics[logic_id] = logic

            settings['logics'] = validated_logics
            return settings

        except Exception as e:
            print(f"마이그레이션 중 오류 발생: {str(e)}")
            return self._get_default_settings()
    
    def _create_ordered_key_input_item(self, item):
        """키 입력 아이템의 필드를 정해진 순서로 정렬합니다."""
        return {
            'order': item.get('order', 0),
            'display_text': item.get('display_text', ''),
            'action': item.get('action', ''),
            'type': 'key_input',
            'key_code': item.get('key_code', ''),
            'scan_code': item.get('scan_code', 0),
            'virtual_key': item.get('virtual_key', 0),
            'modifiers': item.get('modifiers', 0)
        }

    def _create_ordered_delay_item(self, item):
        """딜레이 아이템의 필드를 정해진 순서로 정렬합니다."""
        return {
            'type': 'delay',
            'display_text': item.get('display_text', ''),
            'duration': item.get('duration', 0),
            'order': item.get('order', 0)
        }

    def _create_ordered_logic_item(self, item):
        """로직 타입 아이템 생성"""
        return {
            'order': item.get('order', 0),
            'type': 'logic',
            'display_text': f"{item.get('logic_name', '')}",
            'logic_id': item.get('logic_id', ''),
            'logic_name': item.get('logic_name', ''),
            'repeat_count': item.get('repeat_count', 1)
        }

    def _create_ordered_trigger_key(self, trigger_key):
        """트리거 키의 필드를 정해진 순서로 정렬합니다."""
        return {
            'display_text': trigger_key.get('display_text', ''),
            'key_code': trigger_key.get('key_code', ''),
            'modifiers': trigger_key.get('modifiers', 0),
            'scan_code': trigger_key.get('scan_code', 0),
            'virtual_key': trigger_key.get('virtual_key', 0)
        }

    def get_window_settings(self):
        """윈도우 설정 반환"""
        return self.settings.get("window", self._get_default_settings()["window"])
    
    def set_window_position(self, x, y):
        """윈도우 위치 설정"""
        # 현재 설정 파일의 최신 내용을 로드
        current_settings = self._load_settings()
        
        # window 설정 업데이트
        current_settings.setdefault("window", {})["position"] = {"x": x, "y": y}
        self.settings = current_settings
        
        # 업데이트된 설정 저장
        self._save_settings()
    
    def set_window_size(self, width, height):
        """윈도우 크기 설정"""
        # 현재 설정 파일의 최신 내용을 로드
        current_settings = self._load_settings()
        
        # window 설정 업데이트
        current_settings.setdefault("window", {})["size"] = {"width": width, "height": height}
        self.settings = current_settings
        
        # 업데이트된 설정 저장
        self._save_settings()

    def reload_settings(self):
        """설정을 다시 로드합니다."""
        self.settings = self._load_settings()
        
    def save_logic(self, logic_id, logic_info):
        """로직 정보를 저장합니다."""
        try:
            # 현재 설정을 다시 로드
            self.reload_settings()
            
            if 'logics' not in self.settings:
                self.settings['logics'] = {}
            
            # items 필드의 순서 정리
            ordered_items = []
            if 'items' in logic_info:
                for item in logic_info['items']:
                    if item.get('type') == 'key_input':
                        ordered_item = self._create_ordered_key_input_item(item)
                    elif item.get('type') == 'delay':
                        ordered_item = self._create_ordered_delay_item(item)
                    elif item.get('type') == 'logic':
                        ordered_item = self._create_ordered_logic_item(item)
                    elif 'content' in item:  # 이전 형식의 아이템인 경우 로직 타입으로 변환
                        content = item.get('content', '')
                        ordered_item = {
                            'type': 'logic',
                            'logic_name': content,
                            'display_text': f"만들어진 다른 로직: {content}",
                            'logic_id': str(uuid.uuid4()),  # 새로운 UUID 생성
                            'repeat_count': 1,
                            'order': item.get('order', 0)
                        }
                    ordered_items.append(ordered_item)
            
            # 트리거 키 정리
            trigger_key = self._create_ordered_trigger_key(logic_info.get('trigger_key', {}))
            
            # 로직 정보의 필드 순서 정리
            ordered_logic = {
                'name': logic_info.get('name', ''),
                'order': logic_info.get('order', 1),  # order 값을 그대로 사용
                'created_at': logic_info.get('created_at', ''),
                'updated_at': logic_info.get('updated_at', ''),
                'trigger_key': trigger_key,
                'repeat_count': logic_info.get('repeat_count', 1),
                'items': ordered_items
            }
            
            # 설정에 저장
            self.settings['logics'][logic_id] = ordered_logic
            
            # 설정 파일에 저장
            self._save_settings()
            
            # 설정을 다시 로드하여 최신 상태 유지
            self.reload_settings()
            
            return ordered_logic
            
        except Exception as e:
            print(f"로직 저장 중 오류 발생: {str(e)}")
            return None

    def load_logics(self):
        """저장된 모든 로직을 불러옵니다."""
        return self.settings.get('logics', {})

    def save_logics(self, logics):
        """모든 로직을 저장합니다."""
        ordered_logics = {}
        for logic_id, logic_data in logics.items():
            # 아이템 순서 정렬
            ordered_items = []
            for item in logic_data.get('items', []):
                if 'type' in item:
                    if item['type'] == 'delay':
                        # 딜레이 아이템의 경우
                        ordered_item = {
                            'type': 'delay',
                            'display_text': item.get('display_text', f"지연시간 : {item.get('duration', 0)}초"),
                            'duration': item.get('duration', 0),
                            'order': item.get('order', 0)
                        }
                    elif item['type'] == 'key_input':
                        # 키 입력 아이템의 경우
                        ordered_item = self._create_ordered_key_input_item(item)
                    elif item['type'] == 'logic':
                        ordered_item = self._create_ordered_logic_item(item)
                else:
                    # 이전 형식의 아이템의 경우
                    ordered_item = {
                        'content': item.get('content', ''),
                        'order': item.get('order', 0)
                    }
                ordered_items.append(ordered_item)
                
            ordered_logic = {
                'name': logic_data.get('name', ''),
                'order': logic_data.get('order', 0),
                'created_at': logic_data.get('created_at', ''),
                'updated_at': logic_data.get('updated_at', ''),
                'trigger_key': logic_data.get('trigger_key', {}),
                'repeat_count': logic_data.get('repeat_count', 1),
                'items': ordered_items
            }
            ordered_logics[logic_id] = ordered_logic
        
        self.settings['logics'] = ordered_logics
        self._save_settings()
