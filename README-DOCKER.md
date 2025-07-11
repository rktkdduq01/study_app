# EduRPG Docker 실행 가이드

이 가이드는 지금까지 구현한 EduRPG 프로젝트를 Docker를 사용하여 실행하는 방법을 설명합니다.

## 구현된 주요 기능들

### 1. 🎮 기본 시스템
- **사용자 인증 시스템**: 학생, 부모, 관리자 역할별 로그인
- **캐릭터 시스템**: 캐릭터 생성, 스탯, 레벨업
- **퀘스트 시스템**: 일일/주간/이벤트 퀘스트
- **업적 시스템**: 업적 달성 및 보상

### 2. 🛍️ 상점 시스템
- **기본 상점**: 코인/젬으로 아이템 구매
- **리워드 상점**: 퀘스트 보상으로 특별 아이템 구매
- **번들 상점**: 할인 패키지
- **일일 상점**: 매일 갱신되는 특별 아이템

### 3. 🏆 리더보드 시스템
- **다양한 랭킹**: 전체, 주간, 월간, 과목별
- **경쟁 시스템**: 실시간 경쟁 이벤트
- **길드 랭킹**: 길드 간 경쟁

### 4. 🔔 실시간 알림 시스템
- **WebSocket 기반**: 실시간 알림 전송
- **카테고리별 알림**: 업적, 소셜, 상점 등
- **브라우저 알림**: 팝업 알림 지원

### 5. 👥 친구 & 소셜 시스템
- **친구 관리**: 친구 추가, 목록, 추천
- **실시간 채팅**: 1:1 및 그룹 채팅
- **길드 시스템**: 길드 생성 및 관리
- **스터디 그룹**: 협력 학습 그룹

### 6. 🎯 멘토-멘티 매칭 시스템
- **지능형 매칭**: AI 기반 멘토-멘티 매칭
- **멘토링 세션**: 일정 관리 및 진행
- **목표 추적**: 학습 목표 설정 및 진행도 관리
- **리뷰 시스템**: 상호 평가 및 피드백

### 7. 📱 모바일 최적화
- **반응형 디자인**: 모든 디바이스 지원
- **터치 최적화**: 44px 최소 터치 타겟
- **모바일 네비게이션**: 드로어 메뉴

## 필요 사항

- Docker Desktop (Windows/Mac) 또는 Docker Engine (Linux)
- Docker Compose
- 최소 4GB RAM
- 10GB 이상의 디스크 공간

## 빠른 시작

### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

### 2. 프로젝트 빌드 및 실행
```bash
# 프로젝트 루트 디렉토리로 이동
cd /mnt/c/Users/PC/Desktop/vscode/study

# Docker 컨테이너 빌드 및 실행
docker-compose up --build
```

### 3. 서비스 접속
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 개별 서비스 실행

### Frontend만 실행
```bash
docker-compose up frontend
```

### Backend만 실행
```bash
docker-compose up backend db redis
```

## 개발 모드 실행

### 1. Frontend 개발 모드
```bash
cd frontend
npm install
npm start
```

### 2. Backend 개발 모드
```bash
cd backend
pip install -r requirements.txt
python main.py
```

## 환경 변수 설정

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/edurpg
JWT_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

## 유용한 Docker 명령어

### 컨테이너 상태 확인
```bash
docker-compose ps
```

### 로그 확인
```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs frontend
docker-compose logs backend
```

### 컨테이너 중지
```bash
docker-compose down
```

### 컨테이너 및 볼륨 완전 삭제
```bash
docker-compose down -v
```

### 컨테이너 재시작
```bash
docker-compose restart
```

## 문제 해결

### 1. 포트 충돌
다른 프로세스가 포트를 사용 중인 경우:
```bash
# Windows
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :3000
lsof -i :8000
```

### 2. 빌드 오류
캐시 없이 다시 빌드:
```bash
docker-compose build --no-cache
```

### 3. 데이터베이스 연결 오류
데이터베이스 컨테이너가 완전히 시작될 때까지 기다린 후 다시 시도:
```bash
docker-compose up -d db
# 30초 대기
docker-compose up
```

## 프로덕션 배포

### 1. 환경 변수 업데이트
프로덕션 환경에 맞게 .env 파일 수정

### 2. SSL 인증서 설정
nginx.conf에 SSL 설정 추가

### 3. 컨테이너 최적화
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 데이터 백업

### PostgreSQL 백업
```bash
docker exec edurpg-db pg_dump -U postgres edurpg > backup.sql
```

### PostgreSQL 복원
```bash
docker exec -i edurpg-db psql -U postgres edurpg < backup.sql
```

## 모니터링

### 리소스 사용량 확인
```bash
docker stats
```

### 컨테이너 내부 접속
```bash
# Frontend 컨테이너
docker exec -it edurpg-frontend sh

# Backend 컨테이너
docker exec -it edurpg-backend bash

# Database 컨테이너
docker exec -it edurpg-db psql -U postgres
```

## 테스트 계정

### 학생 계정
- ID: student@test.com
- PW: password123

### 부모 계정
- ID: parent@test.com
- PW: password123

### 관리자 계정
- ID: admin@test.com
- PW: password123

## 추가 리소스

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [React 문서](https://reactjs.org/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)

## 지원

문제가 발생하면 다음을 확인하세요:
1. Docker Desktop이 실행 중인지 확인
2. 모든 포트가 사용 가능한지 확인
3. 충분한 시스템 리소스가 있는지 확인
4. 로그를 확인하여 구체적인 오류 메시지 찾기