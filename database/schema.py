from database.connection import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 회사 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            company_id TEXT PRIMARY KEY,
            company_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
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
    create_tables()