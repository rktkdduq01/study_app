# API Documentation

## Overview

This document provides comprehensive documentation for all REST API endpoints in the Quest Educational Platform. The API is built with FastAPI and follows RESTful principles.

## Base Configuration

- **Base URL**: `https://api.quest-edu.com`
- **API Version**: `v1`
- **API Prefix**: `/api/v1`
- **Authentication**: Bearer token (JWT)
- **Content-Type**: `application/json`

## Authentication

All endpoints except `/health` and authentication endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

## Error Responses

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Technical error message",
    "user_message": "사용자 친화적 메시지",
    "action": "해결 방법",
    "category": "error_category",
    "status_code": 400,
    "request_id": "uuid",
    "data": {}
  }
}
```

## Endpoints

### 🔐 Authentication (`/auth`)

#### Register New User
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!",
  "full_name": "홍길동",
  "username": "gildong123",
  "age": 15,
  "role": "student",  // "student", "parent", "teacher"
  "parent_email": "parent@example.com"  // Required for students under 18
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "gildong123",
    "full_name": "홍길동",
    "role": "student",
    "is_active": true
  }
}
```

#### Login
```http
POST /api/v1/auth/login
```

**Request Body (Form Data):**
```
username: user@example.com
password: securePassword123!
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Get Current User
```http
GET /api/v1/auth/me
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "gildong123",
  "full_name": "홍길동",
  "role": "student",
  "level": 5,
  "experience": 2500,
  "created_at": "2024-01-20T10:00:00Z"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 👤 User Management (`/users`)

#### Get User List
```http
GET /api/v1/users?role=student&limit=20&offset=0
```

**Query Parameters:**
- `role` (optional): Filter by role
- `limit` (optional): Number of results (default: 20)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "users": [
    {
      "id": 1,
      "username": "gildong123",
      "full_name": "홍길동",
      "level": 5,
      "role": "student"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### Update User
```http
PATCH /api/v1/users/{user_id}
```

**Request Body:**
```json
{
  "full_name": "홍길동 Updated",
  "preferences": {
    "language": "ko",
    "theme": "dark"
  }
}
```

#### Parent - Get Children
```http
GET /api/v1/users/parent/children
```

**Response:**
```json
{
  "children": [
    {
      "id": 2,
      "username": "child1",
      "full_name": "자녀1",
      "level": 3,
      "last_active": "2024-01-20T15:30:00Z"
    }
  ]
}
```

### 🤖 AI Tutor (`/ai-tutor`)

#### Analyze Learning Style
```http
POST /api/v1/ai-tutor/analyze-style
```

**Request Body:**
```json
{
  "session_data": [
    {
      "subject": "math",
      "duration": 30,
      "score": 85,
      "interaction_patterns": ["viewed_diagrams", "used_visual_aids"]
    }
  ]
}
```

**Response:**
```json
{
  "learning_style": "visual",
  "characteristics": [
    "선호하는 학습 방식: 시각적 자료",
    "다이어그램과 차트를 통한 이해도 높음"
  ],
  "recommendations": [
    "마인드맵 활용을 추천합니다",
    "비디오 강의가 효과적일 것입니다"
  ]
}
```

#### Generate Personalized Content
```http
POST /api/v1/ai-tutor/generate-content
```

**Request Body:**
```json
{
  "subject": "math",
  "topic": "fractions",
  "difficulty": "beginner",
  "context": {
    "learning_style": "visual",
    "interests": ["게임", "스포츠"]
  }
}
```

**Response:**
```json
{
  "title": "분수 이해하기 - 피자로 배우는 수학",
  "content": "피자를 나눠먹는 것처럼 분수를 이해해봅시다...",
  "learning_objectives": [
    "분수의 개념 이해",
    "분수의 덧셈과 뺄셈"
  ],
  "estimated_duration": 15,
  "interactive_elements": [
    {
      "type": "visual",
      "description": "피자 분할 인터랙티브 도구"
    }
  ],
  "practice_problems": [
    {
      "question": "8조각 피자 중 3조각을 먹었다면 몇 분의 몇을 먹었나요?",
      "options": ["3/8", "5/8", "3/5", "8/3"],
      "correct_answer": "3/8",
      "explanation": "전체 8조각 중 3조각이므로 3/8입니다"
    }
  ]
}
```

#### Provide Feedback
```http
POST /api/v1/ai-tutor/feedback
```

**Request Body:**
```json
{
  "question": "What is 2 + 2?",
  "user_answer": "5",
  "correct_answer": "4",
  "subject": "math",
  "topic": "addition"
}
```

**Response:**
```json
{
  "is_correct": false,
  "feedback": "거의 맞았어요! 2 + 2는 4입니다. 손가락으로 세어보세요.",
  "hints": [
    "2개에 2개를 더하면?",
    "●● + ●● = ?"
  ],
  "next_steps": [
    "더 작은 숫자로 연습해보세요",
    "구체물을 사용해서 계산해보세요"
  ],
  "confidence_score": 0.7,
  "misconceptions": ["계산 실수"]
}
```

### 🎮 Gamification (`/gamification`)

#### Get Gamification Profile
```http
GET /api/v1/gamification/profile
```

**Response:**
```json
{
  "level": {
    "current_level": 15,
    "current_experience": 3250,
    "experience_for_next_level": 5000,
    "progress_percentage": 65.0,
    "title": "수학 탐험가"
  },
  "stats": {
    "total_experience": 28250,
    "quests_completed": 156,
    "perfect_scores": 23,
    "study_streak": 7,
    "gold": 2500,
    "gems": 150
  },
  "recent_achievements": [
    {
      "id": 1,
      "name": "일주일 연속 학습",
      "description": "7일 연속으로 학습했습니다",
      "earned_at": "2024-01-20T10:00:00Z",
      "points": 100
    }
  ]
}
```

#### Claim Daily Reward
```http
POST /api/v1/gamification/daily-reward/claim
```

**Response:**
```json
{
  "success": true,
  "day": 7,
  "streak": 7,
  "rewards": {
    "gold": 70,
    "gems": 3,
    "experience": 140,
    "items": ["xp_boost_1h"]
  },
  "is_milestone": true,
  "milestone_bonus": {
    "extra_gold": 100,
    "badge": "week_warrior"
  },
  "next_reward_available_at": "2024-01-21T00:00:00Z"
}
```

#### Get Leaderboard
```http
GET /api/v1/gamification/leaderboard?type=weekly&limit=10
```

**Query Parameters:**
- `type`: "daily", "weekly", "monthly", "all_time"
- `limit`: Number of entries (default: 10)
- `offset`: Pagination offset

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": 123,
      "username": "mathmaster",
      "display_name": "수학왕",
      "score": 15420,
      "level": 25,
      "avatar_url": "/avatars/123.png"
    }
  ],
  "user_rank": {
    "rank": 42,
    "score": 8750,
    "percentile": 15.3
  },
  "total_participants": 2845
}
```

### 🎯 Multiplayer (`/multiplayer`)

#### Create Battle
```http
POST /api/v1/multiplayer/battles
```

**Request Body:**
```json
{
  "title": "수학 대결",
  "subject": "math",
  "difficulty": "medium",
  "max_rounds": 5,
  "time_per_round": 30,
  "is_private": false
}
```

**Response:**
```json
{
  "id": 1,
  "title": "수학 대결",
  "status": "waiting",
  "join_code": "ABC123",
  "creator": {
    "id": 1,
    "username": "player1"
  },
  "settings": {
    "subject": "math",
    "difficulty": "medium",
    "max_rounds": 5,
    "time_per_round": 30
  },
  "current_participants": 1,
  "max_participants": 2
}
```

#### Join Battle
```http
POST /api/v1/multiplayer/battles/{battle_id}/join
```

**Response:**
```json
{
  "success": true,
  "battle": {
    "id": 1,
    "status": "ready",
    "participants": [
      {"id": 1, "username": "player1", "is_ready": true},
      {"id": 2, "username": "player2", "is_ready": false}
    ]
  }
}
```

#### Submit Answer in Battle
```http
POST /api/v1/multiplayer/battles/{battle_id}/answer
```

**Request Body:**
```json
{
  "question_id": "q123",
  "answer": "B",
  "time_taken": 4.5
}
```

**Response:**
```json
{
  "correct": true,
  "points_earned": 100,
  "time_bonus": 20,
  "current_score": 520,
  "opponent_answered": true,
  "round_complete": true,
  "round_winner": "you"
}
```

### 💳 Payments (`/payments`)

#### Get Subscription Plans
```http
GET /api/v1/payments/plans
```

**Response:**
```json
{
  "plans": [
    {
      "id": "basic_monthly",
      "name": "베이직 월간",
      "price": 9900,
      "currency": "KRW",
      "interval": "month",
      "features": [
        "AI 튜터 기본 기능",
        "일일 퀘스트 3개",
        "친구 10명까지"
      ]
    },
    {
      "id": "premium_monthly",
      "name": "프리미엄 월간",
      "price": 19900,
      "currency": "KRW",
      "interval": "month",
      "features": [
        "AI 튜터 전체 기능",
        "무제한 퀘스트",
        "무제한 친구",
        "고급 분석 리포트",
        "1:1 튜터링"
      ]
    }
  ]
}
```

#### Create Subscription
```http
POST /api/v1/payments/subscription
```

**Request Body:**
```json
{
  "plan_id": "premium_monthly",
  "payment_method_id": "pm_1234567890"
}
```

**Response:**
```json
{
  "subscription": {
    "id": "sub_1234567890",
    "status": "active",
    "current_period_start": "2024-01-20T00:00:00Z",
    "current_period_end": "2024-02-20T00:00:00Z",
    "plan": {
      "id": "premium_monthly",
      "name": "프리미엄 월간"
    }
  },
  "invoice": {
    "id": "inv_1234567890",
    "amount": 19900,
    "status": "paid"
  }
}
```

### 📚 Content Management (`/cms`)

#### Create Content
```http
POST /api/v1/cms/content
```

**Request Body:**
```json
{
  "title": "분수의 덧셈",
  "description": "분수를 더하는 방법을 배웁니다",
  "content_type": "lesson",
  "body": "## 분수의 덧셈\n\n분모가 같은 분수의 덧셈은...",
  "subject_id": 1,
  "difficulty_level": "beginner",
  "estimated_duration": 20,
  "learning_objectives": [
    "분모가 같은 분수의 덧셈",
    "분모가 다른 분수의 덧셈"
  ],
  "tags": ["math", "fractions", "addition"]
}
```

**Response:**
```json
{
  "id": 1,
  "title": "분수의 덧셈",
  "slug": "bunsu-ui-deotssem",
  "status": "draft",
  "author": {
    "id": 1,
    "name": "김선생"
  },
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

#### Get Content Analytics
```http
GET /api/v1/cms/content/{content_id}/analytics
```

**Response:**
```json
{
  "content_id": 1,
  "metrics": {
    "total_views": 1523,
    "unique_learners": 892,
    "completion_rate": 0.73,
    "average_time_spent": 18.5,
    "average_score": 82.3,
    "effectiveness_score": 0.85
  },
  "engagement": {
    "likes": 234,
    "bookmarks": 89,
    "shares": 12,
    "comments": 45
  },
  "performance_by_difficulty": {
    "beginner": {"completion_rate": 0.89, "average_score": 91.2},
    "intermediate": {"completion_rate": 0.72, "average_score": 78.5},
    "advanced": {"completion_rate": 0.58, "average_score": 71.3}
  }
}
```

### 📊 Analytics (`/analytics`)

#### Track Custom Event
```http
POST /api/v1/analytics/track/event
```

**Request Body:**
```json
{
  "event_name": "video_watched",
  "event_data": {
    "video_id": "math_101",
    "duration_watched": 300,
    "total_duration": 420,
    "completion_percentage": 71.4
  }
}
```

#### Get User Analytics
```http
GET /api/v1/analytics/user/me?period=week
```

**Query Parameters:**
- `period`: "day", "week", "month", "year", "all"

**Response:**
```json
{
  "period": "week",
  "summary": {
    "total_study_time": 1250,
    "sessions_count": 12,
    "average_session_duration": 104.2,
    "subjects_studied": ["math", "science"],
    "quests_completed": 8,
    "achievements_earned": 3
  },
  "progress": {
    "experience_gained": 850,
    "levels_gained": 1,
    "current_streak": 7,
    "accuracy_rate": 0.82
  },
  "performance_by_subject": {
    "math": {
      "time_spent": 650,
      "accuracy": 0.85,
      "topics_covered": ["fractions", "algebra"]
    },
    "science": {
      "time_spent": 600,
      "accuracy": 0.79,
      "topics_covered": ["biology", "chemistry"]
    }
  }
}
```

### 🌐 Internationalization (`/i18n`)

#### Get Translation
```http
GET /api/v1/i18n/translate/welcome_message?language=ko
```

**Response:**
```json
{
  "key": "welcome_message",
  "value": "환영합니다!",
  "language": "ko"
}
```

#### Batch Translation
```http
POST /api/v1/i18n/translate/batch
```

**Request Body:**
```json
{
  "keys": ["welcome_message", "start_quest", "level_up"],
  "language": "ko"
}
```

**Response:**
```json
{
  "translations": {
    "welcome_message": "환영합니다!",
    "start_quest": "퀘스트 시작",
    "level_up": "레벨 업!"
  }
}
```

### 🔒 Security (`/security`)

#### Setup 2FA
```http
POST /api/v1/security/2fa/setup
```

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "backup_codes": [
    "12345678",
    "87654321",
    "13579246"
  ]
}
```

#### Verify 2FA
```http
POST /api/v1/security/2fa/verify
```

**Request Body:**
```json
{
  "code": "123456"
}
```

**Response:**
```json
{
  "verified": true,
  "message": "2FA가 성공적으로 활성화되었습니다"
}
```

## Rate Limiting

API endpoints have the following rate limits:

- **General endpoints**: 100 requests per minute
- **Authentication endpoints**: 5 requests per minute
- **AI Tutor endpoints**: 30 requests per minute
- **Payment endpoints**: 10 requests per minute

Rate limit headers:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Pagination

List endpoints support pagination using:
- `limit`: Number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip

Response includes:
- `total`: Total number of items
- `limit`: Items per page
- `offset`: Current offset

## Webhooks

The platform sends webhooks for:
- Payment events (Stripe webhooks)
- Achievement unlocked
- Level up
- Friend request received
- Battle invitation

Webhook payload structure:
```json
{
  "event_type": "achievement.unlocked",
  "timestamp": "2024-01-20T10:00:00Z",
  "data": {
    "user_id": 1,
    "achievement_id": 5,
    "achievement_name": "수학 마스터"
  }
}
```

## SDK Examples

### JavaScript/TypeScript
```typescript
import { QuestAPI } from '@quest-edu/sdk';

const api = new QuestAPI({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.quest-edu.com'
});

// Login
const { token } = await api.auth.login({
  email: 'user@example.com',
  password: 'password123'
});

// Get user profile
const profile = await api.users.getProfile();

// Start a battle
const battle = await api.multiplayer.createBattle({
  subject: 'math',
  difficulty: 'medium'
});
```

### Python
```python
from quest_edu import QuestAPI

api = QuestAPI(
    api_key='your-api-key',
    base_url='https://api.quest-edu.com'
)

# Login
token = api.auth.login(
    email='user@example.com',
    password='password123'
)

# Track progress
api.analytics.track_progress(
    subject='math',
    topic='fractions',
    score=85
)
```

## Testing

Test environment available at:
- Base URL: `https://api-test.quest-edu.com`
- Use test API keys for development
- Test data is reset daily

## Support

- Documentation: https://docs.quest-edu.com
- API Status: https://status.quest-edu.com
- Support Email: api-support@quest-edu.com
- Discord: https://discord.gg/quest-edu