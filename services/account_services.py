from datetime import datetime
from database.connection import get_connection

class AccountServices:
    def process_file(self, rules_data: dict, transactions_data: list) -> str:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. 회사 입력 및 계정과목 insert
        try:
            self._insert_rules_data(cursor, rules_data)
            self._insert_transactions_data(cursor, transactions_data)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise Exception(f"데이터 저장 오류: {str(e)}")
        finally:
            conn.close()

        return "저장완료"

    def _insert_rules_data(self, cursor, rules_data: dict):
        try:
            companies = rules_data.get("companies", [])
            
            # 회사 저장
            for company in companies:
                cursor.execute("""
                    insert or ignore into companies (company_id, company_name)
                    values (?, ?)
                            """, (company["company_id"], company["company_name"]))
                # 계정과목 저장
                for category in company.get("categories", []):
                    cursor.execute("""
                        insert or ignore into categories (company_id, category_id, category_name)
                        values (?, ?, ?)
                                """, (company["company_id"], category["category_id"], category["category_name"]))
                    # 키워드 저장
                    for keyword in category.get('keywords', []):
                        cursor.execute("""
                            insert or ignore into keywords (category_id, keyword)
                            values (?, ?)
                        """, (category['category_id'], keyword))
        except Exception as e:
            raise Exception(f"Rules 데이터 저장 오류: {str(e)}")

    def _insert_transactions_data(self, cursor, transactions_data: list):
        try:
            for transaction in transactions_data:
                transaction_date = datetime.strptime(transaction["거래일시"], '%Y-%m-%d %H:%M:%S')
                deposit = transaction.get("입금액", 0)
                withdrawal = transaction.get("출금액", 0)
                balance = transaction.get("거래후잔액", 0)
                branch = transaction.get("거래점", "")
                description = transaction.get("적요", "")

                company_id, category_id = self._classify_transaction(cursor, description)
                is_classified = 1 if company_id and category_id else 0
                cursor.execute("""
                    insert into transactions (
                        transaction_date, deposit_amount, withdrawal_amount, balance, branch, description, company_id, category_id, is_classified
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction_date, deposit, withdrawal, balance, branch, description, company_id, category_id, is_classified
                ))

        except Exception as e:
            raise Exception(f"Transactions 데이터 저장 오류: {str(e)}")

    def _classify_transaction(self, cursor, description: str):
        cursor.execute("""
            select k.category_id, c.company_id
            from keywords k
            join categories c on k.category_id = c.category_id
            where ? like '%' || k.keyword || '%'
            order by length(keyword) desc
            limit 1
        """, (description,))

        result = cursor.fetchone()
        if result:
            return result['company_id'], result['category_id']
        else:
            return None, None

    def get_transaction_by_company_id(self, company_id: str):
        return "complete"