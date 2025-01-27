import json
import os
from pathlib import Path
import uuid
from datetime import datetime
from BE.log.base_log_manager import BaseLogManager

class LogicsDataSettingFilesManager:
    """설정 파일 관리 클래스"""

    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        
        # BE 폴더 경로를 기준으로 설정 파일 경로 지정
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_file = Path(current_dir).resolve() / "settings" / "setting files" / "logics_data_settingfiles_manager.json"

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

    def _save_settings(self, settings):
        """설정 파일에 현재 설정을 저장합니다."""
        try:
            # 로직 데이터에서 uuid 필드 제거 및 필드 순서 정리
            if 'logics' in settings:
                ordered_logics = {}
                # 현재 order 값들을 모두 수집하고 정렬
                logic_orders = [(logic_id, logic_data.get('order', 0)) 
                              for logic_id, logic_data in settings['logics'].items()]
                logic_orders.sort(key=lambda x: x[1])
                # 순서 재할당 (1부터 시작)
                new_order = 1
                for logic_id, _ in logic_orders:
                    settings['logics'][logic_id]['order'] = new_order
                    new_order += 1

                for logic_id, logic_data in settings['logics'].items():
                    # items 리스트 내부의 아이템들도 필드 순서 정렬
                    ordered_items = []
                    for item in logic_data.get('items', []):
                        if 'type' in item:
                            if item['type'] == 'delay':
                                ordered_item = self._create_ordered_delay_item(item)
                            elif item['type'] == 'key_input':
                                ordered_item = self._create_ordered_key_input_item(item)
                            elif item['type'] == 'logic':
                                ordered_item = self._create_ordered_logic_item(item)
                            elif item['type'] == 'mouse_input':
                                ordered_item = self._create_ordered_mouse_input_item(item)
                            else:
                                ordered_item = item  # 알 수 없는 타입은 그대로 유지
                        else:
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
                        'isNestedLogicCheckboxSelected': logic_data.get('isNestedLogicCheckboxSelected', False),
                        'items': ordered_items
                    }
                    ordered_logics[logic_id] = ordered_logic
                settings['logics'] = ordered_logics

            # 설정 파일 저장
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())

            return True
        except Exception as e:
            self.base_log_manager.log(
                message=f"설정 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logics_data_settingfiles_manager",
                method_name="save_settings",
                print_to_terminal=True
            )
            return False

    def _get_default_settings(self):
        """기본 설정값 반환"""
        return {
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
                self.base_log_manager.log(
                    message="설정 데이터가 딕셔너리 형식이 아닙니다. 기본값으로 초기화합니다.",
                    level="ERROR",
                    file_name="logics_data_settingfiles_manager",
                    method_name="_migrate_to_uuid",
                    print_to_terminal=True
                )
                return self._get_default_settings()

            if 'logics' not in settings:
                self.base_log_manager.log(
                    message="로직 데이터가 없습니다. 새로운 구조로 초기화합니다.",
                    level="ERROR",
                    file_name="logics_data_settingfiles_manager",
                    method_name="_migrate_to_uuid",
                    print_to_terminal=True
                )
                settings['logics'] = {}
                return settings

            if not isinstance(settings['logics'], dict):
                self.base_log_manager.log(
                    message="로직 데이터가 올바른 형식이 아닙니다. 초기화합니다.",
                    level="ERROR",
                    file_name="logics_data_settingfiles_manager",
                    method_name="_migrate_to_uuid",
                    print_to_terminal=True
                )
                settings['logics'] = {}
                return settings

            # logic_names 필드가 있다면 제거
            if 'logic_names' in settings:
                del settings['logic_names']

            # 로직 데이터 검증 및 정리
            validated_logics = {}
            for logic_id, logic in settings['logics'].items():
                if not isinstance(logic, dict):
                    self.base_log_manager.log(
                        message="경고: 잘못된 형식의 로직을 건너뜁니다.",
                        level="WARNING",
                        file_name="logics_data_settingfiles_manager",
                        method_name="_migrate_to_uuid"
                    )
                    continue
                # UUID 형식 검증
                try:
                    uuid.UUID(logic_id)
                except ValueError:
                    # 잘못된 UUID면 새로 생성
                    new_id = str(uuid.uuid4())
                    self.base_log_manager.log(
                        message="잘못된 UUID 형식 감지: 새 UUID를 생성합니다.",
                        level="ERROR",
                        file_name="logics_data_settingfiles_manager",
                        method_name="_migrate_to_uuid",
                        print_to_terminal=True
                    )
                    logic_id = new_id

                # 필수 필드 확인
                if 'name' not in logic:
                    self.base_log_manager.log(
                        message="경고: 이름이 없는 로직을 건너뜁니다.",
                        level="WARNING",
                        file_name="logics_data_settingfiles_manager",
                        method_name="_migrate_to_uuid"
                    )
                    continue

                validated_logics[logic_id] = logic

            settings['logics'] = validated_logics
            return settings

        except Exception as e:
            self.base_log_manager.log(
                message=f"마이그레이션 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logics_data_settingfiles_manager",
                method_name="_migrate_to_uuid",
                print_to_terminal=True
            )
            return self._get_default_settings()

    def _create_ordered_key_input_item(self, item):
        """키 입력 아이템의 필드를 정해진 순서로 정렬합니다."""
        return {
            'order': item.get('order', 0),
            'logic_detail_item_dp_text': item.get('logic_detail_item_dp_text', ''),
            'action': item.get('action', ''),
            'type': 'key_input',
            'key_code': item.get('key_code', ''),
            'scan_code': item.get('scan_code', 0),
            'virtual_key': item.get('virtual_key', 0),
            'modifiers_key_flag': item.get('modifiers_key_flag', 0)
        }

    def _create_ordered_delay_item(self, item):
        """딜레이 아이템의 필드를 정해진 순서로 정렬합니다."""
        return {
            'type': 'delay',
            'logic_detail_item_dp_text': item.get('logic_detail_item_dp_text', ''),
            'duration': item.get('duration', 0),
            'order': item.get('order', 0)
        }

    def _create_ordered_logic_item(self, item):
        """로직 타입 아이템 생성"""
        return {
            'order': item.get('order', 0),
            'type': 'logic',
            'logic_detail_item_dp_text': f"{item.get('logic_name', '')}",
            'logic_id': item.get('logic_id', ''),
            'logic_name': item.get('logic_name', ''),
            'repeat_count': item.get('repeat_count', 1)
        }

    def _create_ordered_trigger_key(self, trigger_key):
        """트리거 키의 필드를 정해진 순서로 정렬합니다."""
        return {
            'logic_detail_item_dp_text': trigger_key.get('logic_detail_item_dp_text', ''),
            'key_code': trigger_key.get('key_code', ''),
            'scan_code': trigger_key.get('scan_code', 0),
            'virtual_key': trigger_key.get('virtual_key', 0),
            'modifiers_key_flag': trigger_key.get('modifiers_key_flag', 0),
        }

    def _create_ordered_mouse_input_item(self, item):
        """마우스 입력 아이템의 필드 순서를 정렬"""
        return {
            'order': item.get('order', 0),
            'type': 'mouse_input',
            'logic_detail_item_dp_text': item.get('logic_detail_item_dp_text', ''),
            'name': item.get('name', ''),
            'action': item.get('action', '클릭'),
            'button': item.get('button', '왼쪽 버튼'),
            'coordinates_x': item.get('coordinates_x', 0),
            'coordinates_y': item.get('coordinates_y', 0),
            'ratios_x': item.get('ratios_x', 0),
            'ratios_y': item.get('ratios_y', 0)
        }

    def reload_settings(self, force=False):
        """설정을 다시 로드합니다.

        Args:
            force (bool): 강제로 파일에서 다시 로드할지 여부
        """
        if force:
            # 파일에서 직접 로드
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
                return self._migrate_to_uuid(self.settings)
        else:
            # 기존 방식대로 로드
            self.settings = self._load_settings()
        return self.settings

    def save_logic(self, logic_id, logic_data):
        """로직 저장

        Args:
            logic_id (str): 로직 ID
            logic_data (dict): 로직 데이터

        Returns:
            dict: 저장된 로직 데이터
        """
        try:
            # 기존 설정 로드
            settings = self._load_settings()

            # logics 섹션이 없으면 생성
            if 'logics' not in settings:
                settings['logics'] = {}

            # 필수 필드 확인
            required_fields = ['name', 'items', 'repeat_count']
            for field in required_fields:
                if field not in logic_data:
                    raise ValueError(f"필수 필드 '{field}'가 누락되었습니다.")

            # 중첩로직용 여부 저장
            isNestedLogicCheckboxSelected = logic_data.get('isNestedLogicCheckboxSelected', False)

            # order 값 처리 - 항상 1 이상의 값 보장
            if 'order' in logic_data:
                # 입력된 order 값이 있는 경우
                current_order = max(1, logic_data['order'])  # 최소값 1 보장
            else:
                # order 값이 없는 경우 새로운 order 할당
                current_order = max([l.get('order', 0) for l in settings['logics'].values() if l.get('order', 0) > 0], default=0) + 1

            # 기본 로직 정보 구성
            logic_info = {
                'order': current_order,  # 계산된 order 값 사용
                'name': logic_data['name'],
                'created_at': logic_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'trigger_key': logic_data.get('trigger_key', {}),
                'repeat_count': logic_data['repeat_count'],
                'items': logic_data['items'],
                'isNestedLogicCheckboxSelected': isNestedLogicCheckboxSelected
            }

            # 기존 로직의 이름과 ID를 가져옴
            old_logic = settings['logics'].get(logic_id, {})
            old_name = old_logic.get('name')

            # 이름이나 UUID가 변경되었는지 확인
            name_changed = old_name and old_name != logic_info['name']

            # 모든 로직을 순회하면서 중첩된 로직의 UUID와 이름을 업데이트
            if name_changed or logic_id:
                for existing_logic_id, existing_logic in settings['logics'].items():
                    if 'items' in existing_logic:
                        updated_items = []
                        for item in existing_logic['items']:
                            if item.get('type') == 'logic' and item.get('logic_id') == logic_id:
                                # UUID가 일치하는 경우 이름정보 업데이트
                                item = item.copy()
                                item['logic_name'] = logic_info['name']
                                item['logic_detail_item_dp_text'] = logic_info['name']
                            updated_items.append(item)
                        existing_logic['items'] = updated_items

            # 로직 저장
            settings['logics'][logic_id] = logic_info

            # 설정 파일 저장
            self._save_settings(settings)

            # 캐시 갱신
            self.settings = settings

            return logic_info

        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logic",
                print_to_terminal=True
            )
            raise

    def load_logics(self, force=False):
        """저장된 로직들을 로드합니다.

        Args:
            force (bool): 강제로 설정을 다시 로드할지 여부
        """
        # 강제 로드가 요청된 경우 설정을 다시 로드
        if force:
            self.reload_settings(force=True)
        # 로직 데이터를 반환하되, 없으면 빈 딕셔너리 반환
        return self.settings.get('logics', {})

    def save_logics(self, logics):
        """모든 로직을 저장합니다."""
        try:
            self.base_log_manager.log(
                message="로직 저장 시작",
                level="DEBUG",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logics"
            )
            ordered_logics = {}
            for logic_id, logic_data in logics.items():
                self.base_log_manager.log(
                    message=f"로직 ID: {logic_id} 처리 시작",
                    level="DEBUG",
                    file_name="logics_data_settingfiles_manager",
                    method_name="save_logics"
                )

                # 아이템 순서 정렬
                ordered_items = []
                for item in logic_data.get('items', []):
                    self.base_log_manager.log(
                        message=f"아이템 데이터: {item}",
                        level="DEBUG",
                        file_name="logics_data_settingfiles_manager",
                        method_name="save_logics"
                    )

                    try:
                        if 'type' in item:
                            if item['type'] == 'delay':
                                # 딜레이 아이템의 경우
                                ordered_item = {
                                    'type': 'delay',
                                    'logic_detail_item_dp_text': item.get('logic_detail_item_dp_text', f"지연시간 : {item.get('duration', 0)}초"),
                                    'duration': item.get('duration', 0),
                                    'order': item.get('order', 0)
                                }
                                self.base_log_manager.log(
                                    message=f"딜레이 아이템 처리: {ordered_item}",
                                    level="DEBUG",
                                    file_name="logics_data_settingfiles_manager",
                                    method_name="save_logics"
                                )

                            elif item['type'] == 'key_input':
                                # 키 입력 아이템의 경우
                                ordered_item = self._create_ordered_key_input_item(item)
                                self.base_log_manager.log(
                                    message=f"키 입력 아이템 처리: {ordered_item}",
                                    level="DEBUG",
                                    file_name="logics_data_settingfiles_manager",
                                    method_name="save_logics"
                                )

                            elif item['type'] == 'logic':
                                ordered_item = self._create_ordered_logic_item(item)
                                self.base_log_manager.log(
                                    message=f"로직 타입 아이템 처리: {ordered_item}",
                                    level="DEBUG",
                                    file_name="logics_data_settingfiles_manager",
                                    method_name="save_logics"
                                )

                        else:
                            # 이전 형식의 아이템의 경우
                            ordered_item = {
                                'content': item.get('content', ''),
                                'order': item.get('order', 0)
                            }
                            self.base_log_manager.log(
                                message=f"이전 형식 아이템 처리: {ordered_item}",
                                level="DEBUG",
                                file_name="logics_data_settingfiles_manager",
                                method_name="save_logics"
                            )

                        ordered_items.append(ordered_item)

                    except Exception as e:
                        self.base_log_manager.log(
                            message=f"아이템 처리 중 오류 발생: {str(e)}",
                            level="ERROR",
                            file_name="logics_data_settingfiles_manager",
                            method_name="save_logics",
                            print_to_terminal=True
                        )
                        import traceback
                        self.base_log_manager.log(
                            message=f"오류 상세: {traceback.format_exc()}",
                            level="ERROR",
                            file_name="logics_data_settingfiles_manager",
                            method_name="save_logics",
                            print_to_terminal=True
                        )
                        continue

                ordered_logic = {
                    'name': logic_data.get('name', ''),
                    'order': logic_data.get('order', 0),
                    'created_at': logic_data.get('created_at', ''),
                    'updated_at': logic_data.get('updated_at', ''),
                    'trigger_key': logic_data.get('trigger_key', {}),
                    'repeat_count': logic_data.get('repeat_count', 1),
                    'items': ordered_items
                }
                self.base_log_manager.log(
                    message=f"로직 처리: {ordered_logic}",
                    level="DEBUG",
                    file_name="logics_data_settingfiles_manager",
                    method_name="save_logics"
                )

                ordered_logics[logic_id] = ordered_logic

            # 설정에 저장
            self.base_log_manager.log(
                message="수집된 로직 정보를 설정에 저장합니다.",
                level="DEBUG",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logics"
            )
            settings = self.load_settings() or {}
            settings['logics'] = ordered_logics
            self.save_settings(settings)
            self.base_log_manager.log(
                message="로직 정보가 성공적으로 저장되었습니다.",
                level="DEBUG",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logics"
            )

        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logics",
                print_to_terminal=True
            )
            import traceback
            self.base_log_manager.log(
                message=f"오류 상세: {traceback.format_exc()}",
                level="ERROR",
                file_name="logics_data_settingfiles_manager",
                method_name="save_logics",
                print_to_terminal=True
            )
            raise
        