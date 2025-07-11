# Windows 환경에서 백엔드 실행 가이드

## 사전 요구사항
- Python 3.8 이상 설치
- Visual Studio Code 또는 다른 IDE
- Git Bash 또는 PowerShell

## 설치 및 실행 단계

### 1. 가상환경 생성 및 활성화

PowerShell에서:
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Git Bash에서:
```bash
cd backend
python -m venv venv
source venv/Scripts/activate
```

### 2. 개발용 패키지 설치

```bash
pip install -r requirements-dev.txt
```

만약 psycopg2 설치 오류가 발생하면:
```bash
# psycopg2를 제외하고 설치
pip install fastapi uvicorn[standard] sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart email-validator pydantic pydantic-settings alembic httpx pytest pytest-asyncio python-dotenv
```

### 3. 환경 변수 설정

`.env` 파일이 이미 생성되어 있습니다. 필요시 수정:
```
DATABASE_URL=sqlite:///./edurpg.db
SECRET_KEY=your-secret-key-here-change-this-in-production
```

### 4. 데이터베이스 초기화

```bash
python init_db.py
```

### 5. 서버 실행

방법 1 - 실행 스크립트 사용:
```bash
python run_server.py
```

방법 2 - uvicorn 직접 실행:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. API 테스트

서버가 실행되면:
- API 문서: http://localhost:8000/docs
- 대체 문서: http://localhost:8000/redoc
- 헬스체크: http://localhost:8000/

새 터미널에서 API 테스트:
```bash
python test_api.py
```

## 일반적인 문제 해결

### 1. "Module not found" 오류
가상환경이 활성화되어 있는지 확인:
```bash
# 프롬프트에 (venv)가 표시되어야 함
(venv) C:\...\backend>
```

### 2. 포트 8000 사용 중
다른 포트로 실행:
```bash
uvicorn app.main:app --reload --port 8001
```

### 3. SQLite 파일 권한 오류
데이터베이스 파일 삭제 후 재생성:
```bash
del edurpg.db
python init_db.py
```

### 4. PowerShell 실행 정책 오류
관리자 권한으로 PowerShell 실행 후:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 개발 워크플로우

1. **코드 수정**: VS Code에서 파일 편집
2. **서버 재시작**: uvicorn의 --reload 옵션으로 자동 재시작
3. **API 테스트**: /docs에서 직접 테스트 또는 test_api.py 실행
4. **데이터베이스 확인**: SQLite 브라우저 또는 DBeaver 사용

## 유용한 명령어

```bash
# 패키지 목록 확인
pip list

# 데이터베이스 재설정
del edurpg.db && python init_db.py

# 로그 레벨 조정하여 실행
uvicorn app.main:app --log-level debug

# 특정 호스트/포트로 실행
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

## VS Code 추천 확장

- Python
- Pylance
- SQLite Viewer
- Thunder Client (API 테스트)
- GitLens

## 추가 리소스

- FastAPI 문서: https://fastapi.tiangolo.com/
- SQLAlchemy 문서: https://www.sqlalchemy.org/
- Pydantic 문서: https://docs.pydantic.dev/