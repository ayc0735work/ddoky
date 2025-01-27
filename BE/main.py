import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from BE.function.main_window import MainWindow
from BE.database.connection import DatabaseConnection
from BE.database.migrations.json_to_db_migration import JsonToDbMigration

def initialize_database():
    """데이터베이스 초기화 및 마이그레이션을 수행합니다."""
    # DB 초기화
    db = DatabaseConnection.get_instance()
    db.initialize_database()
    
    # 마이그레이션 체크 및 실행
    migration = JsonToDbMigration()
    if migration.should_migrate():
        if migration.confirm_migration():
            success, message = migration.migrate()
            if success:
                QMessageBox.information(None, "마이그레이션 완료", message)
            else:
                QMessageBox.critical(None, "마이그레이션 실패", message)

def main():
    app = QApplication(sys.argv)
    
    # DB 초기화 및 마이그레이션
    initialize_database()
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
