## 실행 및 테스트 가이드

1. Docker와 Docker compose가 설치된 PC에 소스를 다운 받는다.
2. 터미널로 해당 소스 위치로 이동한다.
3. 프로젝트 루트에서 다음과 같은 명령어를 입력한다.
   - `docker-compose up -d --build` 또는 `docker-compose up --build`
4. 브라우저 주소창에 `127.0.0.1:8000/docs`를 입력하여 스웨거UI에 접근한다.
5. 과제에 명시된 POST, GET API를 테스트 한다.
   - <i>과제 항목 외로 미분류 항목 조회 API를 추가하였습니다.</i>

#### 또는 CURL로 테스트 할 시 예시(Windows CMD 기준)

##### POST(/api/v1/accounting/process)

```SHELL
curl --location "http://localhost:8000/api/v1/accounting/process" --form "rules_file=@{파일위치};type=application/json" --form "transactions_file=@{파일위치};type=text/csv"
```

##### GET(/api/v1/accounting/records?companyId=...)

```SHELL
curl --location "http://localhost:8000/api/v1/accounting/records?companyId=com_1"
```

##### GET(/api/v1/accounting/records/missing)

```SHELL
curl --location "http://localhost:8000/api/v1/accounting/records/missing"
```

## 시스템 아키텍쳐

- 기술스택
  - Python, FastAPI, Sqlite3
- 선택한 이유
  - Python
    - 과제에서 요구했던 첫 번째 문항 중 csv 파일과 json 파일을 읽어야했는데 csv 파일에 대한 프로세싱은 어느 언어보다 파이썬이 빠르고 편하기 때문에 파이썬으로 설정했습니다. 만약 실제 프로젝트였다면 메인 API 서버로는 spring이나 노드 진영의 프레임워크를 베이스로 하고 과제와 같은 파일 프로세싱 서버는 파이썬으로 띄워서 빠르게 문서를 처리하고 요청 트래픽을 내부적으로 분산 시키는 방법으로 진행할 것 입니다.
  - FastAPI
    - 파이썬에서 많이 쓰는 프레임워크 중 flask, Django, FastAPI가 있는데 flask는 단순 개발용으로 최소한의 기능만 있고 추후에도 사용할 일이 적을 것이라 생각하여 후보에서 제외하였고 Django는 풀스택 기반 프레임워크라서 이번 과제와는 맞지 않다고 생각하여 최종적으로 FastAPI를 선정하게 되었습니다.
  - Sqlite3
    - Sqlite는 파이썬에 내장되어있는 서버리스 방식의 DB입니다. 자주 사용하는 PostgreSQL을 사용하려고 했으나 Sqlite로도 충분히 과제에 대해서 구현 가능했으며 작성한 쿼리문에 대해서는 ANSI문법을 지원하기도 하여 Sqlite3를 사용했습니다.

### DB 스키마

```SQL
-- 회사 정보 테이블
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 카테고리(계정과목) 테이블
CREATE TABLE IF NOT EXISTS categories (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    company_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
)

-- 키워드 테이블
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id TEXT NOT NULL,
    keyword TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
)

-- 거래내역 테이블
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
```

## 핵심 자동 분류 로직

rules.json은 회사별 사용되는 계정과목(이하 카테고리)에 대한 정보와 키워드 값을 가지고 있습니다. 각 부분에 대하여 어떻게 분류하고 처리했는지 작성해보겠습니다.

#### 키워드

처음엔 상표 혹은 상호라고 생각되어 어느 값과도 연관관계를 맺지 않으려고 했지만 현재 과제에서는 키워드가 다른 카테고리에도 속할 것인지 아닌지 불분명하여 카테고리 ID와 연관관계를 맺었습니다.

#### 카테고리(계정과목)

카테고리는 한 회사가 가지고 있는 유일한 계정과목에 대한 정보입니다. 그래서 해당 정보는 회사 ID와 연관 관계를 맺고 있습니다. 다만 거래내역에 '개인이체'라고 하는 어느 곳에도 속하지 않는 분류 항목이 있어 카테고리에 모든 회사가 사용할 수 있는 미분류 항목에 대해서 만들었고 'com_0'라는 아이디와 '공통'이라는 회사 정보로 매핑하였습니다. 여기서 작업을 마치면 과제의 2번 문항에서 com_0으로 조회했을 시 실제로 존재하는 회사가 아닌데 조회가 되기 때문에 회사 테이블에 'is_active'라는 컬럼을 만들어 com_0이라는 정보는 조회되지 않게 하였습니다.

### 분류 로직

순서는 간단합니다. 먼저 rules.json의 배열로 반복문을 돌며 `companies` 테이블에 회사 정보를 insert 하는데 이때 존재하는 회사인 경우 `insert or ignore`를 사용하여 중복을 방지합니다. 그 다음 `categories` 테이블에 각 카테고리 ID, 카테고리명을 insert합니다. 마찬가지로 계정과목은 이런식으로 변경될 일이 없기에 `insert or ignore`를 사용했습니다. 다음 키워드는 N개가 속할 수 있는데 키워드 정보는 카테고리 ID를 fk로 잡고 있기 때문에 카테고리 정보를 insert 할때 속해있는 키워드만큼 N번 반복하여 `keywords` 테이블에 insert하게 됩니다.

이렇게 하게 되면 회사별 카테고리(계정과목)에 대한 정보가 DB에 쌓이게 되고 이 정보를 기준으로 은행 거래내역을 분류하게 됩니다. 분류 방법은 다음과 같습니다.

먼저 입력된 csv파일을 컨트롤러 단에서 list로 변환하여 서비스 단으로 넘깁니다. for문을 돌며 `transaction` 테이블에 거래를 쌓게 되는데 루프의 내용은 이렇습니다.

1. list에서 거래일시, 입금액, 출금액, 거래 후 잔액, 거래점, 적요를 뽑아냅니다.
2. 현재 거래내역 정보와 회사의 계정과목 정보를 연관 지을 수 있는 데이터는 적요뿐이기 때문에 해당 정보를 가지고 키워드 테이블과 카테고리 테이블을 조인하여 `회사의 ID`와 `카테고리 ID`를 반환합니다.
3. 만약 2번 단계에서 조회 된 값이 없는 경우 해당 거래 내역은 미분류에 해당되기 때문에 해당 정보가 있는 `회사의 ID`와 `카테고리 ID`를 반환합니다.
4. 정리된 데이터 거래일시, 입금액, 출금액, 거래 후 잔액, 거래점, 적요와 회사 ID와 카테고리 ID를 `transaction` 테이블에 insert 하게되면 회사의 카테고리별로 거래내역이 정리가 되게 됩니다.

### 로직 개선 및 확장

제시해주신 금액 구간 및 제외 키워드에 대한 부분을 고민해보니 한 회사에 귀속될 만한 정보가 아니라고 생각이 들었습니다. 혹은 사용자가 필요시 설정할 수 있는 정보라고 판단되어 금액 구간에 대한 공통 테이블과 제외 키워드에 대한 공통 테이블을 만들어두어 커스텀하게 사용자가 사용할 수 있게 하는 방법으로 해당 공통 테이블을 사용해 거래내역을 정리하고 회사별 거래 내역을 조회할 때에도 유용한 파라미터로 사용할 수 있을 것 같습니다.

## 보안 강화 방안

1. API TLS/SSL 통신
2. 유저 or IP별 접근제어 설정
3. 비밀번호 해시 알고리즘 단방향 암호화 처리
4. 파일 관련

   - AWS KMS와 같은 외부 서비스 이용
   - 혹은 양방향 키 기능 구현
   - 다운로드 시 허용된 토큰을 가진 유저만 가능하게 구현

5. 모니터링

   - IDS, IPS를 사용하여 상시 모니터링 가동

6. 그 외

   - 주기적 서버 비밀번호 및 유저 비밀번호 변경
   - root 계정은 접근 못하게 변경

보안에 대해서는 여전히 부족한 지식을 가지고 있음에도 제가 떠올릴 수 있는 방안이 몇가지 있습니다. 파일이나 비밀번호 같은 경우는 TLS/SSL 통신을 기반으로 한 API 수준에서 접근할 수 있게 1차적으로 방어를 해야합니다. 파일 같은 경우는 ssh나 다른 네트워크 침투 방식으로 접근이 가능할텐데 이를 접근 가능한 유저나 허용된 IP만 접근할 수 있게 접근제어를 확실히 셋팅하는 것이 가장 중요할 것 같습니다. 암호화는 가능하다면 AWS KMS처럼 외부 업체를 사용해도 좋을 것 같습니다. 추가로 인증서나 파일을 다운로드 해야할 기능이 있는 경우 허용된 토큰이 있는 유저만 가능하게 구현할 수도 있을 것 같습니다. 비밀번호는 최소한 단방향 해시 암호화가 되어야 한다고 생각합니다. 또 주기적으로 서버 비밀번호를 바꿔야하며 IDS와 IPS를 셋팅하여 추가적으로 문제가 있어보이는 접근이나 행동 등을 모니터링하여 관리하는 것이 중요하다고 생각합니다.

## 문제상황 해결책 제시

문제 상황 : 한 고객사의 거래 데이터가 다른 고객사 대시보드에 노출되었다는 신고가 들어왔습니다.

먼저 신고해주신 고객에게 어느 시기에 그랬는지에 대한 내용과 다른 고객사의 정보를 수정하지 못하게 내용을 전다라고 신고해주셔서 감사하다는 회신을 보낸 뒤에 사태를 분석합니다.

1. 신고 시점을 기반으로 로그 추적
2. 로그에서 파라미터가 발견된다면 동일한 내용으로 쿼리를 날려보고 결과를 확인
3. 만약 동일한 증상이 재현되면 쿼리에 문제가 있을 확률이 높기 때문에 해당 부분을 초점으로 디버깅을 시작하여 원인을 찾아냅니다.
4. 반대로 증상이 동일하지 않으면 그 외의 원인을 찾아야 합니다. 최악의 방법으로 해당 시점의 DB를 백업받고 롤백해가면서 원인을 찾아야할 수도 있을 것 같습니다.

가장 중요한 부분은 이런 상황이 발생하기 전에 미리 방지가 되어있어야 합니다. 제일 먼저 구체적이고 정보를 유실하지 않는 로그 정책을 내부적으로 수립하여 철저히 지켜야하며 기능 개발 시 QA 과정을 확실하게 거쳐 빈 틈이 없는지 N차 점검을 진행해야합니다.

## AI 활용 관련

과제에서 AI가 활용된 부분은 초기 프로젝트 init 셋팅과 테스트 시 활용할 도커 파일 초안 셋팅으로 사용했습니다.
추가로 테이블 설계 과정에서 AI를 사용했으나 미분류에 대한 처리과정이 누락되어 테이블 관련 설계는 필드명과 필드 타입 정도 도움을 받아 작업하였으며 다음과 같은 단순 작업에 대해서도 사용하였습니다.

```PYTHON
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
```

사용하는 과정에서 제가 예상하는 답변을 계속 해주었고 살펴본 결과 이견없이 사용하였습니다.
사용된 AI는 클로드 소넷-4 모델과 GPT-4.1을 사용하였습니다.
