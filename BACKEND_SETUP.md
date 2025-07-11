# EduRPG 백엔드 서버 설정 가이드

## 빠른 시작 (Quick Start)

### 1. 간단한 테스트 서버 (의존성 불필요)

가상 환경이나 pip 설치 없이 바로 실행할 수 있는 테스트 서버입니다:

```bash
cd backend
python3 simple_server.py
```

서버가 시작되면:
- API 서버: http://localhost:8000
- 헬스 체크: http://localhost:8000/health
- API 목록: http://localhost:8000/

### 2. 통합 테스트

백엔드와 프론트엔드 연동을 테스트합니다:

```bash
# 백엔드 디렉토리에서
python3 test_integration.py
```

## 전체 백엔드 설정 (Full Setup)

### Windows 환경

1. **Python 설치 확인**:
   ```cmd
   python --version
   ```

2. **가상 환경 생성 및 활성화**:
   ```cmd
   cd backend
   python -m venv venv
   venv\Scripts\activate
   ```

3. **의존성 설치**:
   ```cmd
   pip install -r requirements-dev.txt
   ```

4. **서버 실행**:
   ```cmd
   start_server.bat
   ```
   또는
   ```cmd
   python -m uvicorn app.main:app --reload
   ```

### WSL/Linux 환경

WSL에서 pip이 없는 경우:

1. **간단한 서버로 테스트** (권장):
   ```bash
   python3 simple_server.py
   ```

2. **또는 Python 패키지 관리자 설치**:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3-pip python3-venv

   # 또는 pipx 사용 (권장)
   sudo apt install pipx
   pipx install uvicorn[standard]
   ```

## API 테스트

### 1. 서버 상태 확인
```bash
curl http://localhost:8000/health
```

### 2. 사용자 목록 조회
```bash
curl http://localhost:8000/users
```

### 3. 새 사용자 생성
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "email": "new@example.com"}'
```

## 프론트엔드 연동

### 1. 환경 변수 확인

`frontend/.env` 파일:
```env
VITE_API_URL=http://localhost:8000
```

### 2. CORS 설정

백엔드 서버는 다음 origin을 허용합니다:
- http://localhost:3000
- http://localhost:3001
- * (simple_server.py 사용 시)

### 3. 연동 테스트

1. 백엔드 서버 시작:
   ```bash
   cd backend
   python3 simple_server.py
   ```

2. 프론트엔드 시작:
   ```bash
   cd frontend
   npm run dev
   ```

3. 브라우저에서 http://localhost:3000 접속

4. 브라우저 개발자 도구 (F12) > Network 탭에서 API 호출 확인

## 문제 해결

### "Module not found" 오류
- simple_server.py 사용 (외부 의존성 없음)
- 또는 가상 환경 활성화 확인

### 포트 충돌 (Port already in use)
```bash
# 사용 중인 포트 확인
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# 다른 포트로 실행
python3 simple_server.py  # 코드 수정 필요
```

### CORS 오류
- 백엔드가 올바른 origin을 허용하는지 확인
- 프론트엔드의 API URL이 정확한지 확인

## 서버 구성

### 1. Simple Server (simple_server.py)
- 외부 의존성 없음
- 기본 CRUD 기능
- 메모리 저장소
- 테스트 및 개발용

### 2. Mock Server (main.py)
- FastAPI 기반
- 더 많은 기능
- 실제 API와 유사한 구조
- pip 설치 필요

### 3. Main Application (app/main.py)
- 전체 EduRPG 백엔드
- SQLite 데이터베이스
- 인증 및 권한 관리
- 프로덕션 준비

## 다음 단계

1. ✅ 백엔드 서버 실행
2. ✅ API 엔드포인트 테스트
3. ✅ 프론트엔드와 연동 확인
4. 🔲 데이터베이스 초기화 (전체 앱 사용 시)
5. 🔲 인증 기능 구현
6. 🔲 실제 비즈니스 로직 추가