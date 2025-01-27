from BE.database.connection import DatabaseConnection
from BE.log.base_log_manager import BaseLogManager

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
                    message=f"{len(logics)}개의 로직을 불러왔습니다.",
                    level="INFO",
                    file_name="Logic_Database_Manager",
                    method_name="get_all_logics_list"
                )
            else:
                self.base_log_manager.log(
                    message="로직을 불러오지 못했습니다.",
                    level="ERROR",
                    file_name="Logic_Database_Manager",
                    method_name="get_all_logics_list",
                    print_to_terminal=True
                )
            return logics
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 데이터 조회 중 오류 발생: {str(e)}",
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
                'trigger_key': row[7],  # JSON 문자열로 저장된 트리거 키 정보
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
            
            self.base_log_manager.log(
                message=f"로직 '{logic_detail['logic_name']}'의 상세 정보를 불러왔습니다. \n 불러온 로직: {logic_detail}",
                level="INFO",
                file_name="Logic_Database_Manager",
                method_name="get_logic_detail_data"
            )
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