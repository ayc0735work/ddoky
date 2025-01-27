from BE.database.connection import DatabaseConnection
from BE.log.base_log_manager import BaseLogManager

class LogicDatabaseManager:
    def __init__(self):
        self.base_log_manager = BaseLogManager.instance()
        self.db = DatabaseConnection()

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
            cursor = self.db.cursor()
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
                
            self.base_log_manager.log(
                message=f"{len(logics)}개의 로직을 불러왔습니다.",
                level="INFO",
                file_name="LogicDatabaseManager",
                method_name="get_all_logics_list"
            )
            return logics
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 데이터 조회 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="LogicDatabaseManager",
                method_name="get_all_logics_list"
            )
            return [] 