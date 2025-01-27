from BE.database.connection import DatabaseConnection
from BE.log.base_log_manager import BaseLogManager
import json

class Logic_Database_Manager:
    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        self.db = DatabaseConnection.get_instance()

    def get_all_logics_list(self):
        """DB에서 모든 로직의 기본 정보를 조회합니다.
        
        Returns:
            list: 로직 기본 정보 리스트 (id, order, name).
                 실패 시 빈 리스트 반환.
        """
        try:
            query = """
                SELECT ld.id, ld.logic_order, ld.logic_name
                FROM logic_data ld
                ORDER BY ld.logic_order
            """
            connection = self.db.get_connection()
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            logics = []
            for row in rows:
                logic = {
                    'id': row[0],
                    'logic_order': row[1],
                    'logic_name': row[2]
                }
                logics.append(logic)
            
            if logics:  # 데이터를 성공적으로 가져왔을 때만 로그 출력
                self.base_log_manager.log(
                    message=f"DB에서 {len(logics)}개의 로직을 불러왔습니다.",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="get_all_logics_list"
                )
            else:
                self.base_log_manager.log(
                    message="DB에서 로직을 불러오지 못했습니다.",
                    level="ERROR",
                    file_name="Logic_Database_Manager",
                    method_name="get_all_logics_list",
                    print_to_terminal=True
                )
            return logics
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"DB에서 로직 데이터 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="get_all_logics_list",
                print_to_terminal=True
            )
            return []

    def get_logic_detail_data(self, logic_id: int):
        """특정 로직의 상세 정보를 조회합니다.
        
        Args:
            logic_id (int): 조회할 로직의 ID
            
        Returns:
            dict: 로직 상세 정보를 담은 딕셔너리.
                 실패 시 None 반환.
        """
        try:
            # 1. 로직 기본 정보 조회
            query = """
                SELECT id, logic_name, logic_order, created_at, updated_at,
                       repeat_count, isNestedLogicCheckboxSelected, trigger_key
                FROM logic_data
                WHERE id = ?
            """
            connection = self.db.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (logic_id,))
            row = cursor.fetchone()
            
            if not row:
                self.base_log_manager.log(
                    message=f"로직 ID {logic_id}를 찾을 수 없습니다.",
                    level="ERROR",
                    file_name="Logic_Database_Manager",
                    method_name="get_logic_detail_data",
                    print_to_terminal=True
                )
                return None
                
            # 2. 로직 상세 아이템 조회
            items_query = """
                SELECT id, item_order, item_type, item_data
                FROM logic_detail_items_data
                WHERE logic_id = ?
                ORDER BY item_order
            """
            cursor.execute(items_query, (logic_id,))
            items = cursor.fetchall()
            
            # 3. 결과 데이터 구성
            logic_detail = {
                'id': row[0],
                'logic_name': row[1],
                'logic_order': row[2],
                'created_at': row[3],
                'updated_at': row[4],
                'repeat_count': row[5],
                'isNestedLogicCheckboxSelected': bool(row[6]),
                'trigger_key': json.loads(row[7]) if row[7] else None,  # JSON 문자열을 파싱하여 디코딩
                'items': []
            }
            
            # 아이템 정보 추가
            for item in items:
                item_data = {
                    'id': item[0],
                    'item_order': item[1],
                    'type': item[2],
                    'item_data': item[3]  # JSON 문자열로 저장된 아이템 상세 정보
                }
                logic_detail['items'].append(item_data)

            return logic_detail
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 상세 정보 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="get_logic_detail_data",
                print_to_terminal=True
            )
            return None 

    def save_logic_detail_data(self, logic_data):
        try:
            # trigger_key를 JSON으로 직렬화
            trigger_key_json = json.dumps(logic_data.get('trigger_key'), ensure_ascii=False)
            
            query = """
                INSERT INTO logic_data (
                    logic_name, logic_order, created_at, updated_at,
                    repeat_count, isNestedLogicCheckboxSelected, trigger_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                query,
                (
                    logic_data.get('logic_name'),
                    logic_data.get('logic_order'),
                    logic_data.get('created_at'),
                    logic_data.get('updated_at'),
                    logic_data.get('repeat_count', 1),
                    logic_data.get('isNestedLogicCheckboxSelected', False),
                    trigger_key_json
                )
            )
            connection.commit()
            
            self.base_log_manager.log(
                message=f"로직 '{logic_data['logic_name']}'의 상세 정보를 저장했습니다.",
                level="INFO",
                file_name="Logic_Database_Manager",
                method_name="save_logic_detail_data"
            )
            return True
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 상세 정보 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="save_logic_detail_data",
                print_to_terminal=True
            )
            return False 

    def delete_logic_data(self, logic_id: int):
        """로직과 관련된 모든 데이터를 삭제합니다.
        
        Args:
            logic_id (int): 삭제할 로직의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # 트랜잭션 시작
            connection.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 삭제할 로직의 순서와 이름 조회 (로깅용)
                cursor.execute("SELECT logic_name, logic_order FROM logic_data WHERE id = ?", (logic_id,))
                row = cursor.fetchone()
                if not row:
                    raise Exception(f"로직 ID {logic_id}를 찾을 수 없습니다")
                    
                logic_name, deleted_order = row
                
                # 2. 로직 상세 아이템 삭제
                cursor.execute("""
                    DELETE FROM logic_detail_items_data
                    WHERE logic_id = ?
                """, (logic_id,))
                
                # 3. 로직 기본 정보 삭제
                cursor.execute("""
                    DELETE FROM logic_data
                    WHERE id = ?
                """, (logic_id,))
                
                # 4. 삭제된 순서보다 큰 순서를 가진 로직들의 순서를 -1
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = logic_order - 1
                    WHERE logic_order > ?
                """, (deleted_order,))
                
                # 트랜잭션 커밋
                connection.commit()
                
                self.base_log_manager.log(
                    message=f"ID가 {logic_id}인 로직 '{logic_name}'이(가) 삭제되었습니다.",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="delete_logic"
                )

                return True
                
            except Exception as e:
                # 오류 발생 시 롤백
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 삭제 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="delete_logic",
                print_to_terminal=True
            )
            return False

    def update_logic_detail_data(self, logic_id: int, logic_data: dict):
        """기존 로직의 상세 정보를 업데이트합니다.
        
        Args:
            logic_id (int): 업데이트할 로직의 ID
            logic_data (dict): 업데이트할 로직 데이터
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            # trigger_key를 JSON으로 직렬화
            trigger_key_json = json.dumps(logic_data.get('trigger_key'), ensure_ascii=False)
            
            query = """
                UPDATE logic_data
                SET logic_name = ?,
                    logic_order = ?,
                    updated_at = ?,
                    repeat_count = ?,
                    isNestedLogicCheckboxSelected = ?,
                    trigger_key = ?
                WHERE id = ?
            """
            
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # 트랜잭션 시작
            connection.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 로직 기본 정보 업데이트
                cursor.execute(
                    query,
                    (
                        logic_data.get('logic_name'),
                        logic_data.get('logic_order'),
                        logic_data.get('updated_at'),
                        logic_data.get('repeat_count', 1),
                        logic_data.get('isNestedLogicCheckboxSelected', False),
                        trigger_key_json,
                        logic_id
                    )
                )
                
                # 2. 기존 로직 상세 아이템 삭제
                cursor.execute("DELETE FROM logic_detail_items_data WHERE logic_id = ?", (logic_id,))
                
                # 3. 새로운 로직 상세 아이템 추가
                items = logic_data.get('items', [])
                for item in items:
                    cursor.execute("""
                        INSERT INTO logic_detail_items_data (
                            logic_id, item_order, item_type, item_data
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        logic_id,
                        item.get('item_order'),
                        item.get('type'),
                        item.get('item_data')
                    ))
                
                # 트랜잭션 커밋
                connection.commit()
                
                self.base_log_manager.log(
                    message=f"로직 '{logic_data.get('logic_name')}'의 상세 정보가 업데이트되었습니다.",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="update_logic_detail_data"
                )
                return True
                
            except Exception as e:
                # 오류 발생 시 롤백
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 상세 정보 업데이트 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="update_logic_detail_data",
                print_to_terminal=True
            )
            return False 

    def update_logic_data_order(self, logic_id: int, new_order: int):
        """로직의 순서를 업데이트합니다.
        
        Args:
            logic_id (int): 업데이트할 로직의 ID
            new_order (int): 새로운 순서 번호
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # 트랜잭션 시작
            connection.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 현재 로직의 이름과 순서 조회 (로깅용)
                cursor.execute("""
                    SELECT logic_name, logic_order 
                    FROM logic_data 
                    WHERE id = ?
                """, (logic_id,))
                row = cursor.fetchone()
                if not row:
                    raise Exception(f"로직 ID {logic_id}를 찾을 수 없습니다.")
                
                logic_name, current_order = row
                
                # 2. 로직 순서 업데이트
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = ?
                    WHERE id = ?
                """, (new_order, logic_id))
                
                # 3. 전체 로직 순서 검증
                cursor.execute("SELECT COUNT(*) FROM logic_data")
                total_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT MAX(logic_order) FROM logic_data")
                max_order = cursor.fetchone()[0]
                
                if total_count != max_order:
                    raise Exception("로직 순서가 불연속적입니다.")
                
                # 트랜잭션 커밋
                connection.commit()
                
                self.base_log_manager.log(
                    message=f"로직 '{logic_name}'의 순서가 {current_order}에서 {new_order}로 변경되었습니다.",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="update_logic_data_order"
                )
                return True
                
            except Exception as e:
                # 오류 발생 시 롤백
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 순서 업데이트 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="update_logic_data_order",
                print_to_terminal=True
            )
            return False
            
    def get_logic_by_order(self, logic_order: int):
        """특정 순서의 로직 정보를 조회합니다.
        
        Args:
            logic_order (int): 조회할 로직의 순서
            
        Returns:
            dict: 로직 정보 (id, logic_order)
            None: 조회 실패 시
        """
        try:
            query = """
                SELECT id, logic_order
                FROM logic_data
                WHERE logic_order = ?
            """
            connection = self.db.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (logic_order,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'logic_order': row[1]
                }
            return None
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 순서 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="get_logic_by_order",
                print_to_terminal=True
            )
            return None
            

    def logic_order_plus_one_change(self, selected_logic_id: int):
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # 트랜잭션 시작
            connection.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 선택된 로직의 현재 순서 조회
                cursor.execute("""
                    SELECT logic_name, logic_order 
                    FROM logic_data 
                    WHERE id = ?
                """, (selected_logic_id,))
                row = cursor.fetchone()
                if not row:
                    raise Exception(f"로직 ID {selected_logic_id}를 찾을 수 없습니다.")
                
                selected_logic_name, selected_order = row
                
                # 2. 다음 순서의 로직 조회
                cursor.execute("""
                    SELECT id, logic_name, logic_order
                    FROM logic_data
                    WHERE logic_order = ?
                """, (selected_order + 1,))
                target_row = cursor.fetchone()
                if not target_row:
                    # 마지막 로직인 경우 변경하지 않음
                    connection.rollback()
                    self.base_log_manager.log(
                        message=f"로직 '{selected_logic_name}'은(는) 이미 마지막 순서입니다.",
                        level="INFO",
                        file_name="Logic_Database_Manager",
                        method_name="logic_order_plus_one_change"
                    )
                    return True
                
                target_id, target_name, target_order = target_row
                
                # 3. 순서 변경
                # 3-1. 대상 로직의 순서를 -1
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = ?
                    WHERE id = ?
                """, (selected_order, target_id))
                
                # 3-2. 선택된 로직의 순서를 +1
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = ?
                    WHERE id = ?
                """, (target_order, selected_logic_id))
                
                # 트랜잭션 커밋
                connection.commit()
                
                self.base_log_manager.log(
                    message=f"로직 순서 변경 완료: {selected_logic_name}({selected_order} → {target_order}), {target_name}({target_order} → {selected_order})",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="logic_order_plus_one_change"
                )
                return True
                
            except Exception as e:
                # 오류 발생 시 롤백
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 순서 변경 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="logic_order_plus_one_change",
                print_to_terminal=True
            )
            return False
            
    def logic_order_minus_one_change(self, selected_logic_id: int):
        try:
            connection = self.db.get_connection()
            cursor = connection.cursor()
            
            # 트랜잭션 시작
            connection.execute("BEGIN TRANSACTION")
            
            try:
                # 1. 선택된 로직의 현재 순서 조회
                cursor.execute("""
                    SELECT logic_name, logic_order 
                    FROM logic_data 
                    WHERE id = ?
                """, (selected_logic_id,))
                row = cursor.fetchone()
                if not row:
                    raise Exception(f"로직 ID {selected_logic_id}를 찾을 수 없습니다.")
                
                selected_logic_name, selected_order = row
                
                # 2. 이전 순서의 로직 조회
                cursor.execute("""
                    SELECT id, logic_name, logic_order
                    FROM logic_data
                    WHERE logic_order = ?
                """, (selected_order - 1,))
                target_row = cursor.fetchone()
                if not target_row:
                    # 첫 번째 로직인 경우 변경하지 않음
                    connection.rollback()
                    self.base_log_manager.log(
                        message=f"로직 '{selected_logic_name}'은(는) 이미 첫 번째 순서입니다.",
                        level="INFO",
                        file_name="Logic_Database_Manager",
                        method_name="logic_order_minus_one_change"
                    )
                    return True
                
                target_id, target_name, target_order = target_row
                
                # 3. 순서 변경
                # 3-1. 대상 로직의 순서를 +1
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = ?
                    WHERE id = ?
                """, (selected_order, target_id))
                
                # 3-2. 선택된 로직의 순서를 -1
                cursor.execute("""
                    UPDATE logic_data
                    SET logic_order = ?
                    WHERE id = ?
                """, (target_order, selected_logic_id))
                
                # 트랜잭션 커밋
                connection.commit()
                
                self.base_log_manager.log(
                    message=f"로직 순서 변경 완료: {selected_logic_name}({selected_order} → {target_order}), {target_name}({target_order} → {selected_order})",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="logic_order_minus_one_change"
                )
                return True
                
            except Exception as e:
                # 오류 발생 시 롤백
                connection.rollback()
                raise e
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 순서 변경 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="Logic_Database_Manager",
                method_name="logic_order_minus_one_change",
                print_to_terminal=True
            )
            return False
            
