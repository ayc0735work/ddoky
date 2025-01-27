import sqlite3
from pathlib import Path
import logging
from typing import Optional

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    
    @classmethod
    def get_instance(cls) -> 'DatabaseConnection':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.db_path = Path("./data/logic_database.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
        
    def get_connection(self) -> sqlite3.Connection:
        """DB 연결을 반환하거나 새로 생성합니다."""
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
        return self.connection
        
    def close(self):
        """DB 연결을 종료합니다."""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def initialize_database(self):
        """DB 스키마를 초기화합니다."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # logics 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_nested BOOLEAN DEFAULT FALSE,
                    trigger_key TEXT,
                    repeat_count INTEGER DEFAULT 1,
                    display_order INTEGER NOT NULL
                )
            """)
            
            # logic_items 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logic_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    logic_id INTEGER NOT NULL,
                    item_order INTEGER NOT NULL,
                    item_type TEXT NOT NULL,
                    item_data JSON NOT NULL,
                    FOREIGN KEY (logic_id) REFERENCES logics(id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to initialize database: {str(e)}")
            raise 