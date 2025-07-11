# ERD 개선 및 마이그레이션 가이드

## 🔴 주요 문제점 및 해결방안

### 1. **순환 참조 문제**

**문제점:**
- User ↔ Character 간 양방향 참조
- User ↔ Guild 간 복잡한 순환 관계
- Quest ↔ QuestReward 간 순환 참조

**해결방안:**
```python
# Character 테이블 제거, UserGameStats로 통합
class UserGameStats(Base):
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    character_class = Column(String(50))
    character_level = Column(Integer)
    # 중복 데이터 통합
```

### 2. **인덱스 누락**

**문제점:**
- 외래키에 인덱스 없음 (성능 저하)
- 자주 조회되는 컬럼에 인덱스 부재

**해결방안:**
```python
# 모든 외래키에 index=True 추가
user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

# 복합 인덱스 추가
__table_args__ = (
    Index('idx_user_subject', 'user_id', 'subject_id'),
    Index('idx_user_status', 'user_id', 'status'),
)
```

### 3. **데이터 중복**

**문제점:**
- User, Character, UserStats에 동일 데이터 중복
- 레벨, XP, 코인 등이 여러 테이블에 존재

**해결방안:**
```python
# 단일 진실 공급원 (Single Source of Truth)
class UserGameStats(Base):
    # 모든 게임 통계를 한 곳에서 관리
    character_level = Column(Integer)
    total_xp = Column(Integer)
    coins = Column(Integer)
    gems = Column(Integer)
```

### 4. **JSON 컬럼 남용**

**문제점:**
- 대용량 JSON 데이터 저장 (쿼리 성능 저하)
- 정규화 가능한 데이터를 JSON으로 저장

**해결방안:**
```python
# JSON 대신 정규화된 테이블 사용
class UserSubjectPreference(Base):
    profile_id = Column(Integer, ForeignKey("user_profiles.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    preference_level = Column(Integer)
```

## 📊 개선된 ERD 구조

### 1. **User 관련 테이블 분리**
```
User (인증 정보만)
├── UserProfile (프로필 정보)
├── UserGameStats (게임 통계)
└── UserLearningProfile (학습 통계)
```

### 2. **Subject 시스템 정규화**
```
Subject (과목 마스터)
├── SubjectProgress (사용자별 진행도)
└── UserSubjectPreference (선호도)
```

### 3. **Quest 시스템 개선**
```
Quest (퀘스트 정의)
├── QuestProgress (진행 상황)
└── QuestReward (보상 - 별도 테이블)
```

## 🚀 마이그레이션 전략

### Phase 1: 준비 단계
1. 현재 데이터 백업
2. 새 스키마 생성 (병렬 운영)
3. 데이터 무결성 검증

### Phase 2: 데이터 마이그레이션
```sql
-- 1. User 데이터 분리
INSERT INTO user_game_stats (user_id, character_level, total_xp, coins, gems, pvp_rating)
SELECT u.id, c.level, c.total_xp, c.coins, c.gems, u.pvp_rating
FROM users u
LEFT JOIN characters c ON u.id = c.user_id;

-- 2. Subject Progress 통합
INSERT INTO subject_progress (user_id, subject_id, level, total_xp)
SELECT sl.character_id, s.id, sl.level, sl.total_xp
FROM subject_levels sl
JOIN characters c ON sl.character_id = c.id
JOIN subjects s ON sl.subject = s.code;

-- 3. JSON 데이터 정규화
INSERT INTO user_subject_preferences (profile_id, subject_id, preference_level)
SELECT up.id, s.id, 3
FROM user_profiles up
CROSS JOIN LATERAL jsonb_array_elements_text(up.preferred_subjects::jsonb) AS subj
JOIN subjects s ON s.code = subj;
```

### Phase 3: 애플리케이션 업데이트
1. ORM 모델 업데이트
2. Repository 패턴 수정
3. API 엔드포인트 조정

### Phase 4: 검증 및 전환
1. 데이터 일관성 검증
2. 성능 테스트
3. 구 스키마 제거

## 📈 예상 성능 개선

### 쿼리 성능
- **Before**: User 정보 조회 시 5개 테이블 JOIN
- **After**: 필요한 테이블만 선택적 JOIN (50% 성능 향상)

### 인덱스 효율
- **Before**: 전체 테이블 스캔 빈번
- **After**: 인덱스 활용으로 10-100배 속도 향상

### 데이터 일관성
- **Before**: 동일 데이터 여러 곳 업데이트 필요
- **After**: 단일 업데이트로 일관성 보장

## 🔧 추가 최적화 제안

### 1. 파티셔닝
```sql
-- 일별 활동 테이블 파티셔닝
CREATE TABLE daily_user_activity_2024_01 PARTITION OF daily_user_activity
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 2. Materialized View
```sql
-- 자주 사용되는 통계를 위한 Materialized View
CREATE MATERIALIZED VIEW user_stats_summary AS
SELECT 
    u.id,
    ugs.character_level,
    ugs.total_xp,
    ulp.total_study_minutes,
    ulp.overall_accuracy
FROM users u
JOIN user_game_stats ugs ON u.id = ugs.user_id
JOIN user_learning_profiles ulp ON u.id = ulp.user_id;

CREATE INDEX idx_user_stats_summary_level ON user_stats_summary(character_level);
```

### 3. 캐싱 전략
```python
# Redis 캐싱 레이어
@cache.memoize(timeout=300)
def get_user_stats(user_id: int):
    return db.query(UserGameStats).filter_by(user_id=user_id).first()
```

## 📝 체크리스트

- [ ] 모든 외래키에 인덱스 추가
- [ ] 복합 인덱스 생성 (자주 사용되는 조합)
- [ ] CHECK 제약조건 추가 (데이터 무결성)
- [ ] UNIQUE 제약조건 추가 (중복 방지)
- [ ] 정규화 (1NF, 2NF, 3NF 준수)
- [ ] 역정규화 검토 (성능 필요 시)
- [ ] 파티셔닝 적용 (대용량 테이블)
- [ ] 트리거/프로시저 최소화
- [ ] 적절한 데이터 타입 사용
- [ ] NULL 허용 최소화