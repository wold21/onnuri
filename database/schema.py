from database.connection import get_connection
import sqlite3

def init_tables(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 회사 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO companies (company_id, company_name, is_active)
        VALUES ('com_0', '공통', 0)
    """)
    
    # 계정과목 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id TEXT PRIMARY KEY,
            category_name TEXT NOT NULL,
            company_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id)
        )
    """)

    cursor.execute("""
        INSERT OR IGNORE INTO categories (category_id, category_name, company_id)
        VALUES ('cat_0', '미분류', 'com_0')
    """)
    
    # 키워드 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)
    
    # 거래내역 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date DATETIME NOT NULL,
            description TEXT NOT NULL,
            deposit_amount INTEGER DEFAULT 0,
            withdrawal_amount INTEGER DEFAULT 0,
            balance INTEGER NOT NULL,
            branch TEXT,
            company_id TEXT NULL,
            category_id TEXT NULL,
            is_classified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(company_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("Tables created successfully.")

if __name__ == "__main__":
    init_tables("database/onnuri.db")