from BE.database.connection import DatabaseConnection
from BE.log.base_log_manager import BaseLogManager

class LogicDatabaseManager:
    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        self.db = DatabaseConnection()

    def get_all_logics(self):
        """DB에서 모든 로직 데이터를 조회합니다.
        
        Returns:
            list: 로직 데이터 리스트. 각 로직은 딕셔너리 형태.
                 실패 시 빈 리스트 반환.
        """
        try:
            query = """
                SELECT ld.id, ld.logic_order, ld.logic_name, ld.created_at, ld.updated_at,
                       ld.repeat_count, ld.is_nested_logic
                FROM logic_data ld
                ORDER BY ld.logic_order
            """
            cursor = self.db.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            logics = []
            for row in rows:
                logic = {
                    'id': row[0],
                    'logic_order': row[1],
                    'logic_name': row[2],
                    'created_at': row[3],
                    'updated_at': row[4],
                    'repeat_count': row[5],
                    'isNestedLogicCheckboxSelected': bool(row[6])
                }
                logics.append(logic)
                
            self.base_log_manager.log(
                message=f"{len(logics)}개의 로직을 불러왔습니다.",
                level="INFO",
                file_name="LogicDatabaseManager",
                method_name="get_all_logics"
            )
            return logics
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 데이터 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="LogicDatabaseManager",
                method_name="get_all_logics"
            )
            return [] 