# API 엔드포인트 테스트 가이드

## 개요
이 문서는 백엔드 API 엔드포인트를 테스트하는 방법을 설명합니다.

## 테스트 파일 구조
```
backend/
├── tests/
│   ├── conftest.py          # Pytest fixtures 및 설정
│   ├── test_characters.py   # 캐릭터 관련 테스트
│   ├── test_achievements.py # 업적 관련 테스트
│   └── test_quests.py       # 퀘스트 관련 테스트
├── test_api.py              # 수동 API 테스트 스크립트
└── run_server.py            # 서버 실행 스크립트
```

## 환경 설정

### 1. 가상환경 생성 및 활성화
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
`.env` 파일 생성:
```env
DATABASE_URL=postgresql://user:password@localhost/testdb
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 테스트 실행 방법

### 1. 단위 테스트 (Pytest)
```bash
# 모든 테스트 실행
pytest

# 특정 파일의 테스트만 실행
pytest tests/test_characters.py

# 상세한 출력과 함께 실행
pytest -v

# 커버리지 리포트와 함께 실행
pytest --cov=app tests/
```

### 2. 수동 API 테스트

#### 서버 시작
```bash
# 방법 1: 실행 스크립트 사용
python run_server.py

# 방법 2: uvicorn 직접 사용
uvicorn app.main:app --reload
```

#### API 테스트 실행
새 터미널에서:
```bash
python test_api.py
```

### 3. API 문서 확인
서버 실행 후 브라우저에서:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트 범위

### Character API
- ✅ 캐릭터 생성 (POST /api/v1/characters/)
- ✅ 캐릭터 조회 (GET /api/v1/characters/{id})
- ✅ 내 캐릭터 조회 (GET /api/v1/characters/me)
- ✅ 캐릭터 업데이트 (PUT /api/v1/characters/{id})
- ✅ 경험치 추가 (POST /api/v1/characters/{id}/experience)
- ✅ 랭킹 조회 (GET /api/v1/characters/rankings)

### Achievement API
- ✅ 업적 목록 조회 (GET /api/v1/achievements/)
- ✅ 업적 상세 조회 (GET /api/v1/achievements/{id})
- ✅ 내 업적 조회 (GET /api/v1/achievements/me)
- ✅ 업적 진행도 업데이트 (PUT /api/v1/achievements/{id}/progress)
- ✅ 업적 통계 조회 (GET /api/v1/achievements/stats)
- ✅ 업적 생성 [관리자] (POST /api/v1/achievements/)

### Quest API
- ✅ 퀘스트 목록 조회 (GET /api/v1/quests/)
- ✅ 퀘스트 상세 조회 (GET /api/v1/quests/{id})
- ✅ 퀘스트 시작 (POST /api/v1/quests/{id}/start)
- ✅ 퀘스트 진행상황 조회 (GET /api/v1/quests/progress)
- ✅ 퀘스트 제출 (POST /api/v1/quests/submit)
- ✅ 일일 퀘스트 조회 (GET /api/v1/quests/daily)
- ✅ 퀘스트 추천 (GET /api/v1/quests/recommendations)
- ✅ 퀘스트 통계 (GET /api/v1/quests/stats)
- ✅ 퀘스트 생성 [관리자] (POST /api/v1/quests/)

## 테스트 시나리오

### 기본 사용자 플로우
1. 사용자 등록
2. 로그인 (토큰 획득)
3. 캐릭터 생성
4. 퀘스트 목록 조회
5. 퀘스트 시작
6. 퀘스트 제출
7. 경험치 및 보상 획득
8. 업적 확인

### 서비스 레이어 테스트
- 비즈니스 로직 검증
- 예외 처리 테스트
- 데이터 무결성 확인
- 권한 검증

## 문제 해결

### 서버가 시작되지 않을 때
1. 포트 8000이 사용 중인지 확인
2. 필요한 패키지가 모두 설치되었는지 확인
3. 환경 변수가 올바르게 설정되었는지 확인

### 테스트가 실패할 때
1. 데이터베이스 연결 확인
2. 마이그레이션 실행 여부 확인
3. 의존성 버전 확인

### 권한 오류 발생 시
1. JWT 토큰이 올바른지 확인
2. 사용자 역할(role)이 적절한지 확인
3. 토큰 만료 시간 확인

## 개발 팁

### 새로운 엔드포인트 추가 시
1. 스키마 정의 (schemas/)
2. 서비스 로직 구현 (services/)
3. API 엔드포인트 구현 (api/v1/endpoints/)
4. 테스트 작성 (tests/)
5. API 문서 확인 (/docs)

### 테스트 작성 시
- Given-When-Then 패턴 사용
- 엣지 케이스 고려
- 독립적인 테스트 작성
- 의미있는 테스트 이름 사용