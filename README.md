# 🎮 AI 기반 교육용 RPG 플랫폼

## 📚 프로젝트 개요

자녀들의 학습을 게임화하여 내재적 동기부여를 높이고, 부모와의 교육적 상호작용을 강화하는 AI 기반 교육 플랫폼입니다.

### 핵심 특징
- 🎯 **RPG 기반 학습 시스템**: 과목별 레벨 업 시스템으로 성장 가시화
- 🤖 **AI 퀘스트 생성**: 맞춤형 학습 과제를 게임 퀘스트로 제공
- 📊 **이해 중심 접근**: 단순 문제 풀이를 넘어 원리와 개념 이해 강조
- 👨‍👩‍👧‍👦 **부모-자녀 연동**: 실시간 학습 현황 공유 및 맞춤형 과제 설정
- 📈 **성장형 콘텐츠**: 아동의 학습 발달에 맞춰 확장되는 콘텐츠

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL, Redis
- **AI/ML**: OpenAI API, Hugging Face
- **Real-time**: WebSocket

### Frontend
- **Web**: React + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Redux Toolkit
- **Charts**: Recharts

## 🚀 시작하기

### 사전 요구사항
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 설치 및 실행

```bash
# 백엔드 실행
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 프론트엔드 실행
cd frontend
npm install
npm start
```

## 📁 프로젝트 구조

```
edu-rpg/
├── backend/          # FastAPI 백엔드
│   ├── app/
│   │   ├── api/      # API 엔드포인트
│   │   ├── core/     # 핵심 설정
│   │   ├── models/   # 데이터베이스 모델
│   │   ├── schemas/  # Pydantic 스키마
│   │   └── services/ # 비즈니스 로직
│   └── tests/        # 테스트
├── frontend/         # React 프론트엔드
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── store/
│   └── public/
└── docs/             # 문서
```

## 🎯 주요 기능

### 자녀용 기능
- 과목별 레벨 시스템 (수학, 국어, 과학, 영어, 프로그래밍)
- AI 생성 퀘스트 및 보상 시스템
- 캐릭터 성장 및 커스터마이징
- 실시간 학습 피드백

### 부모용 기능
- 실시간 학습 현황 대시보드
- 맞춤형 퀘스트 생성
- 상세 학습 분석 리포트
- 보상 설정 및 관리

## 📝 라이선스

This project is licensed under the MIT License.