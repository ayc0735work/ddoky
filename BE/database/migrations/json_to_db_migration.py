import json
import logging
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

from ..connection import DatabaseConnection
from ..models import Logic, LogicDetailItem

class JsonToDbMigration:
    """JSON 파일의 데이터를 DB로 마이그레이션하는 클래스"""
    
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        self.json_file_path = Path("BE") / "settings" / "setting files" / "logics_data_settingfiles_manager.json"
        
    def should_migrate(self) -> bool:
        """마이그레이션이 필요한지 확인"""
        cursor = self.db.get_connection().cursor()
        
        # logic_data 테이블의 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM logic_data")
        count = cursor.fetchone()[0]
        
        return count == 0  # 테이블이 비어있으면 마이그레이션 필요
        
    def migrate(self) -> tuple[bool, str]:
        """JSON 파일의 데이터를 DB로 마이그레이션
        
        Returns:
            tuple[bool, str]: (성공 여부, 메시지)
        """
        try:
            # 1. JSON 파일 읽기
            if not self.json_file_path.exists():
                return False, "JSON 파일을 찾을 수 없습니다."
                
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 2. DB 연결
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # 3. 트랜잭션 시작
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # 4. 데이터 마이그레이션
                for logic in json_data.get('logics', {}).values():
                    # logic_data 테이블에 데이터 삽입
                    cursor.execute("""
                        INSERT INTO logic_data (
                            logic_order, logic_name, created_at, updated_at,
                            isNestedLogicCheckboxSelected, trigger_key,
                            repeat_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        logic.get('order', 0),
                        logic.get('name'),
                        logic.get('created_at'),
                        logic.get('updated_at'),
                        logic.get('isNestedLogicCheckboxSelected', False),
                        json.dumps(logic.get('trigger_key')),
                        logic.get('repeat_count', 1)
                    ))
                    
                    # 방금 삽입된 logic의 id 가져오기
                    logic_id = cursor.lastrowid
                    
                    # logic_detail_items_data 테이블에 아이템 데이터 삽입
                    for item in logic.get('items', []):
                        cursor.execute("""
                            INSERT INTO logic_detail_items_data (
                                logic_id, item_order, item_type, item_data
                            ) VALUES (?, ?, ?, ?)
                        """, (
                            logic_id,
                            item.get('order', 0),
                            item.get('type', 'key_input'),  # 기본값 설정
                            json.dumps(item)
                        ))
                
                # 5. 트랜잭션 커밋
                conn.commit()
                
                # 6. 백업 생성
                backup_path = self.json_file_path.with_suffix('.json.bak')
                import shutil
                shutil.copy2(self.json_file_path, backup_path)
                
                logging.info("Migration completed successfully")
                return True, "마이그레이션이 성공적으로 완료되었습니다."
                
            except Exception as e:
                # 오류 발생 시 롤백
                conn.rollback()
                logging.error(f"Migration failed: {str(e)}")
                return False, f"마이그레이션 실패: {str(e)}"
                
        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            return False, f"마이그레이션 실패: {str(e)}"
            
    def confirm_migration(self) -> bool:
        """사용자에게 마이그레이션 실행 여부를 확인"""
        # key_input_delays_data.json 파일 존재 여부 확인
        key_input_delays_path = Path("BE") / "settings" / "setting files" / "key_input_delays_data.json"
        
        # DB가 비어있는지 확인
        cursor = self.db.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM logic_data")
        is_db_empty = cursor.fetchone()[0] == 0
        
        message = "기존 JSON 데이터를 DB로 마이그레이션하시겠습니까?"
        
        # key_input_delays_data.json 파일이 존재하고 DB가 비어있는 경우
        if key_input_delays_path.exists() and is_db_empty:
            message = (
                "이전 버전의 데이터 파일(key_input_delays_data.json)이 발견되었습니다.\n"
                "이 데이터를 새로운 DB 형식으로 마이그레이션하시겠습니까?\n\n"
                "※ 마이그레이션 후에도 원본 파일은 보존됩니다."
            )
        
        response = QMessageBox.question(
            None,
            "데이터 마이그레이션",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return response == QMessageBox.Yes 