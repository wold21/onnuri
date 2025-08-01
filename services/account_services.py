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
                cursor.execute("""
                    insert into transactions (
                        transaction_date, deposit_amount, withdrawal_amount, balance, branch, description, company_id, category_id
                    ) values (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        transaction_date, deposit, withdrawal, balance, branch, description, company_id, category_id
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
            try:
                cursor.execute("""
                        select c.company_id, c.category_id
                        from categories c
                        where c.category_name = '미분류'
                        order by c.company_id
                        limit 1
                    """)
                result = cursor.fetchone()
                return result['company_id'], result['category_id']
            except Exception as e:
                raise Exception(f"미분류 계정과목 조회 오류: {str(e)}")

    def get_transaction_by_company_id(self, companyId: str):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                select * from companies where company_id = ? and is_active = 1
            """, (companyId,))
            
            company = cursor.fetchone()
            if not company:
                raise Exception(f"해당 회사가 존재하지 않습니다.")

            cursor.execute("""
                select c.category_id as 'categoryID',
                    c.category_name as 'categoryName',
                    t.description as 'description',
                    t.deposit_amount as 'depositAmount',
                    t.withdrawal_amount as 'withdrawalAmount',
                    t.balance as 'balance',
                    t.branch as 'branch',
                    t.transaction_date as 'transactionDate'
                from transactions t
                join categories c on t.category_id = c.category_id
                join companies co on t.company_id = co.company_id
                where t.company_id = ? and co.is_active = 1
                order by t.transaction_date desc
            """, (companyId,))

            results = cursor.fetchall()
            return list(map(dict, results))
        except Exception as e:
            raise Exception(f"거래 내역 조회 오류: {str(e)}")
        finally:
            conn.close()

    def get_transaction_missing(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                select t.description as 'description',
                    t.deposit_amount as 'depositAmount',
                    t.withdrawal_amount as 'withdrawalAmount',
                    t.balance as 'balance',
                    t.branch as 'branch',
                    t.transaction_date as 'transactionDate'
                from transactions t
                join companies c on t.company_id = c.company_id
                where c.is_active = 0
                order by t.transaction_date desc
            """)

            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            raise Exception(f"거래 내역 조회 오류: {str(e)}")
        finally:
            conn.close()