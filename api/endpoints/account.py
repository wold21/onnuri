import csv
import io
import json
from fastapi import APIRouter, File, HTTPException, UploadFile

from models.response import error_response, success_response
from services.account_services import AccountServices

router = APIRouter()

@router.post("/process")
async def process_accounting(rules_file: UploadFile = File(..., description="rules.json 파일"),
                             transactions_file: UploadFile = File(..., description="bank_transactions.csv 파일")):
    
    # 파일 타입 체크
    if rules_file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="올바르지 않은 파일 형식입니다. JSON 파일만 허용됩니다.")
    if transactions_file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="올바르지 않은 파일 형식입니다. CSV 파일만 허용됩니다.")

    try:
        rules_read = await rules_file.read()
        rules_data = json.loads(rules_read.decode('utf-8'))

        csv_read = await transactions_file.read()
        csv_text = csv_read.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        transactions_data = list(csv_reader)

    except json.JSONDecodeError:
        raise error_response(400, "rules.json 파일이 올바른 JSON 형식이 아닙니다.")
    except UnicodeDecodeError:
        raise error_response(400, "CSV 파일이 올바른 형식이 아닙니다.")
    except Exception as e:
        raise error_response(500, f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    

    try: 
        account_services = AccountServices()
        result = account_services.process_file(rules_data, transactions_data)
        return success_response(data=result)
    except Exception as e:
        raise error_response(500, f"파일 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/records")
async def get_accounting_records(companyId: str):
    try:
        account_services = AccountServices()
        result = account_services.get_transaction_by_company_id(companyId)
        return success_response(data=result)
    except Exception as e:
        raise error_response(500, f"거래 내역 조회 중 오류가 발생했습니다: {str(e)}")
    
@router.get("/records/missing")
async def get_accounting_records():
    try:
        account_services = AccountServices()
        result = account_services.get_transaction_missing()
        return success_response(data=result)
    except Exception as e:
        raise error_response(500, f"거래 내역 조회 중 오류가 발생했습니다: {str(e)}")