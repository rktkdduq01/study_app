-- Performance Optimization SQL Scripts
-- 성능 최적화를 위한 SQL 스크립트

-- ============================================
-- 1. 인덱스 최적화
-- ============================================

-- User 관련 인덱스
CREATE INDEX CONCURRENTLY idx_users_email_active ON users(email, is_active) WHERE is_active = true;
CREATE INDEX CONCURRENTLY idx_users_created_at ON users(created_at DESC);
CREATE INDEX CONCURRENTLY idx_users_last_login ON users(last_login_at DESC) WHERE last_login_at IS NOT NULL;

-- Game Stats 인덱스
CREATE INDEX CONCURRENTLY idx_game_stats_level_xp ON user_game_stats(character_level DESC, total_xp DESC);
CREATE INDEX CONCURRENTLY idx_game_stats_pvp_rating ON user_game_stats(pvp_rating DESC) WHERE pvp_rating > 0;
CREATE INDEX CONCURRENTLY idx_game_stats_guild ON user_game_stats(guild_id) WHERE guild_id IS NOT NULL;

-- Subject Progress 복합 인덱스
CREATE INDEX CONCURRENTLY idx_subject_progress_user_level ON subject_progress(user_id, level DESC);
CREATE INDEX CONCURRENTLY idx_subject_progress_mastery ON subject_progress(mastery_level DESC) WHERE mastery_level > 50;
CREATE INDEX CONCURRENTLY idx_subject_progress_last_activity ON subject_progress(last_activity_at DESC NULLS LAST);

-- Quest Progress 인덱스
CREATE INDEX CONCURRENTLY idx_quest_progress_active ON quest_progress(user_id, status) WHERE status = 'active';
CREATE INDEX CONCURRENTLY idx_quest_progress_completed ON quest_progress(completed_at DESC) WHERE status = 'completed';

-- Battle 인덱스
CREATE INDEX CONCURRENTLY idx_battles_recent ON battles(started_at DESC);
CREATE INDEX CONCURRENTLY idx_battles_user_history ON battles(challenger_id, started_at DESC);
CREATE INDEX CONCURRENTLY idx_battles_ranked ON battles(battle_type, started_at DESC) WHERE battle_type = 'ranked';

-- Content 인덱스
CREATE INDEX CONCURRENTLY idx_content_active_by_subject ON contents(subject_id, content_type, difficulty_level) WHERE is_active = true;

-- Analytics 인덱스
CREATE INDEX CONCURRENTLY idx_daily_activity_recent ON daily_user_activity(activity_date DESC);
CREATE INDEX CONCURRENTLY idx_daily_activity_user_week ON daily_user_activity(user_id, activity_date DESC);

-- ============================================
-- 2. 파티셔닝 설정
-- ============================================

-- Daily Activity 테이블 파티셔닝 (월별)
CREATE TABLE daily_user_activity_partitioned (LIKE daily_user_activity INCLUDING ALL) PARTITION BY RANGE (activity_date);

-- 2024년 파티션 생성
CREATE TABLE daily_user_activity_2024_01 PARTITION OF daily_user_activity_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE daily_user_activity_2024_02 PARTITION OF daily_user_activity_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... 계속

-- Battle 테이블 파티셔닝 (월별)
CREATE TABLE battles_partitioned (LIKE battles INCLUDING ALL) PARTITION BY RANGE (started_at);

-- Activity Monitoring 파티셔닝 (주별)
CREATE TABLE activity_monitoring_partitioned (LIKE activity_monitoring INCLUDING ALL) PARTITION BY RANGE (start_time);

-- ============================================
-- 3. Materialized Views
-- ============================================

-- 사용자 종합 통계 View
CREATE MATERIALIZED VIEW mv_user_summary AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    ugs.character_level,
    ugs.total_xp,
    ugs.coins,
    ugs.gems,
    ugs.pvp_rating,
    ulp.total_study_minutes,
    ulp.total_problems_solved,
    ulp.overall_accuracy,
    ulp.current_streak_days,
    COUNT(DISTINCT sp.subject_id) as subjects_studied,
    COUNT(DISTINCT ua.achievement_id) as achievements_earned,
    MAX(u.last_login_at) as last_login_at
FROM users u
LEFT JOIN user_game_stats ugs ON u.id = ugs.user_id
LEFT JOIN user_learning_profiles ulp ON u.id = ulp.user_id
LEFT JOIN subject_progress sp ON u.id = sp.user_id
LEFT JOIN user_achievements ua ON u.id = ua.user_id
WHERE u.is_active = true
GROUP BY u.id, u.username, u.email, ugs.character_level, ugs.total_xp, 
         ugs.coins, ugs.gems, ugs.pvp_rating, ulp.total_study_minutes,
         ulp.total_problems_solved, ulp.overall_accuracy, ulp.current_streak_days;

CREATE UNIQUE INDEX idx_mv_user_summary_id ON mv_user_summary(user_id);
CREATE INDEX idx_mv_user_summary_level ON mv_user_summary(character_level DESC);
CREATE INDEX idx_mv_user_summary_streak ON mv_user_summary(current_streak_days DESC);

-- 과목별 성과 통계 View
CREATE MATERIALIZED VIEW mv_subject_performance AS
SELECT 
    sp.subject_id,
    s.code as subject_code,
    s.name as subject_name,
    COUNT(DISTINCT sp.user_id) as total_users,
    AVG(sp.level) as avg_level,
    AVG(sp.mastery_level) as avg_mastery,
    AVG(CASE WHEN sp.problems_solved > 0 
        THEN sp.problems_correct::float / sp.problems_solved * 100 
        ELSE 0 END) as avg_accuracy,
    SUM(sp.total_time_minutes) as total_time_minutes,
    SUM(sp.problems_solved) as total_problems_solved
FROM subject_progress sp
JOIN subjects s ON sp.subject_id = s.id
WHERE s.is_active = true
GROUP BY sp.subject_id, s.code, s.name;

CREATE UNIQUE INDEX idx_mv_subject_performance_id ON mv_subject_performance(subject_id);

-- 길드 랭킹 View
CREATE MATERIALIZED VIEW mv_guild_rankings AS
SELECT 
    g.id as guild_id,
    g.name,
    g.tag,
    g.level,
    g.experience,
    COUNT(DISTINCT ugs.user_id) as member_count,
    AVG(ugs.character_level) as avg_member_level,
    SUM(ugs.guild_contribution_points) as total_contribution_points,
    COUNT(DISTINCT gq.id) FILTER (WHERE gq.status = 'completed') as quests_completed
FROM guilds g
LEFT JOIN user_game_stats ugs ON g.id = ugs.guild_id
LEFT JOIN guild_quests gq ON g.id = gq.guild_id
GROUP BY g.id, g.name, g.tag, g.level, g.experience
ORDER BY g.level DESC, g.experience DESC;

CREATE UNIQUE INDEX idx_mv_guild_rankings_id ON mv_guild_rankings(guild_id);
CREATE INDEX idx_mv_guild_rankings_level ON mv_guild_rankings(level DESC, experience DESC);

-- ============================================
-- 4. 함수 기반 인덱스
-- ============================================

-- JSON 필드에 대한 함수 인덱스
CREATE INDEX idx_quest_requirements_type ON quests((requirements->>'type'));
CREATE INDEX idx_content_data_difficulty ON contents((metadata->>'estimated_difficulty'));
CREATE INDEX idx_user_profile_lang ON user_profiles((ui_preferences->>'language'));

-- 계산된 값에 대한 인덱스
CREATE INDEX idx_subject_progress_accuracy ON subject_progress(
    (CASE WHEN problems_solved > 0 
     THEN problems_correct::float / problems_solved * 100 
     ELSE 0 END) DESC
);

-- ============================================
-- 5. 통계 업데이트 및 Vacuum 설정
-- ============================================

-- 자동 vacuum 설정 조정 (자주 업데이트되는 테이블)
ALTER TABLE user_game_stats SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE subject_progress SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE quest_progress SET (autovacuum_vacuum_scale_factor = 0.1);
ALTER TABLE daily_user_activity SET (autovacuum_vacuum_scale_factor = 0.05);

-- 통계 수집 빈도 증가
ALTER TABLE battles SET (autovacuum_analyze_scale_factor = 0.05);
ALTER TABLE activity_monitoring SET (autovacuum_analyze_scale_factor = 0.05);

-- ============================================
-- 6. 쿼리 최적화 힌트
-- ============================================

-- 느린 쿼리 로깅 활성화
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1초 이상 쿼리 로깅
ALTER SYSTEM SET log_statement = 'mod'; -- INSERT, UPDATE, DELETE 로깅

-- 병렬 쿼리 설정
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;

-- ============================================
-- 7. 주기적 유지보수 스크립트
-- ============================================

-- Materialized View 새로고침 (크론잡으로 실행)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_summary;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_subject_performance;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_guild_rankings;

-- 오래된 파티션 삭제 (3개월 이상)
DROP TABLE IF EXISTS daily_user_activity_2023_01;
DROP TABLE IF EXISTS daily_user_activity_2023_02;

-- 인덱스 재구성 (월 1회 실행)
REINDEX INDEX CONCURRENTLY idx_users_email_active;
REINDEX INDEX CONCURRENTLY idx_quest_progress_active;

-- ============================================
-- 8. 모니터링 쿼리
-- ============================================

-- 인덱스 사용률 확인
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC
LIMIT 20;

-- 테이블 크기 및 성장률 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_live_tup AS row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 느린 쿼리 분석
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time
FROM pg_stat_statements
WHERE mean_time > 100 -- 100ms 이상
ORDER BY mean_time DESC
LIMIT 20;