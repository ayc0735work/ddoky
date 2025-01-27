import sqlite3
from pathlib import Path

def check_database():
    """데이터베이스의 내용을 확인합니다."""
    db_path = Path("BE/settings/setting files/logic_database.db")
    
    if not db_path.exists():
        print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
        
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # logic_data 테이블의 레코드 수 확인
    cursor.execute("SELECT COUNT(*) FROM logic_data")
    logic_count = cursor.fetchone()[0]
    print(f"\n로직 데이터 수: {logic_count}")
    
    # 처음 5개의 로직 데이터 확인
    cursor.execute("""
        SELECT id, logic_order, logic_name, created_at, updated_at, 
               isNestedLogicCheckboxSelected, repeat_count 
        FROM logic_data 
        ORDER BY logic_order 
        LIMIT 5
    """)
    print("\n처음 5개의 로직 데이터:")
    print("ID | 순서 | 이름 | 생성일 | 수정일 | 중첩여부 | 반복횟수")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    
    # logic_detail_items_data 테이블의 레코드 수 확인
    cursor.execute("SELECT COUNT(*) FROM logic_detail_items_data")
    items_count = cursor.fetchone()[0]
    print(f"\n로직 상세 아이템 수: {items_count}")
    
    # 처음 5개의 로직 상세 아이템 데이터 확인
    cursor.execute("""
        SELECT id, logic_id, item_order, item_type
        FROM logic_detail_items_data 
        ORDER BY logic_id, item_order 
        LIMIT 5
    """)
    print("\n처음 5개의 로직 상세 아이템:")
    print("ID | 로직ID | 순서 | 타입")
    print("-" * 40)
    for row in cursor.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
        
    conn.close()

if __name__ == "__main__":
    check_database() 