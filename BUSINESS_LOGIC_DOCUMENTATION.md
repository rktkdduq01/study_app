# Business Logic Documentation

## Overview

This document summarizes the complex business logic components that have been documented with detailed comments throughout the codebase.

## Documented Components

### Backend Services (Python)

#### 1. Gamification Service (`/backend/app/services/gamification_service.py`)
**Complex Logic Areas:**
- **Experience Calculation Algorithm**
  - Exponential growth formula: `base_exp * (multiplier^(level-1)) + (increment * (level-1))`
  - Creates balanced progression curve with quick early levels and challenging late game
  - Prevents exploitation through experience boost caps (max 50%)

- **Level Rewards System**
  - Multi-tiered reward structure (gold, items, badges, titles)
  - Milestone-based distribution (every 5, 10, 25 levels)
  - Dynamic scaling based on level achieved

- **Daily Streak Mechanics**
  - 30-day cycle with increasing rewards
  - Bonus milestones at 7, 14, and 30 days
  - Automatic streak reset on missed days

- **Perk System**
  - Unlocks at specific level thresholds
  - Percentage-based boosts with caps
  - Four perk types: XP boost, gold boost, energy regen, bonus hints

#### 2. AI Tutor Service (`/backend/app/services/ai_tutor_service.py`)
**Complex Logic Areas:**
- **Learning Pattern Analysis**
  - 30-day sliding window for meaningful patterns
  - Multi-factor analysis: accuracy, speed, consistency, engagement
  - Learning style identification (visual, auditory, kinesthetic, reading/writing)

- **Content Personalization Engine**
  - Zone of proximal development calculation
  - Adaptive difficulty based on success rates
  - Context-aware content generation with user preferences

- **Real-time Feedback System**
  - Four feedback types with different strategies
  - Scaffolded support based on struggle patterns
  - Progress-based difficulty calibration

- **Recommendation Algorithm**
  - Multi-factor scoring: knowledge gaps (40%), strength building (30%), interest (20%), repetition (10%)
  - Prerequisite mapping for progression
  - Historical effectiveness tracking

#### 3. Multiplayer Service (`/backend/app/services/multiplayer_service.py`)
**Complex Logic Areas:**
- **Session Management**
  - In-memory state cache for real-time performance
  - Three session types with different mechanics
  - Automatic chat room creation and management

- **PvP Battle System**
  - Dynamic scoring formula with time bonuses
  - Streak multipliers and first blood bonuses
  - Anti-cheat measures (server validation, rate limiting)

- **Matchmaking Logic**
  - ELO-based rating system
  - Fair play synchronization
  - Question randomization to prevent cheating

#### 4. Quest Service (`/backend/app/services/quest_service.py`)
**Complex Logic Areas:**
- **Quest Submission Processing**
  - Multi-step validation (progress, time limits, prerequisites)
  - Performance-based reward scaling
  - Achievement trigger integration

- **Daily Quest System**
  - Level-appropriate selection
  - Subject variety enforcement
  - Completion tracking for streaks

- **Recommendation Engine**
  - Five-factor analysis with weighted scoring
  - User performance history analysis
  - Difficulty preference calculation

### Frontend Components (TypeScript)

#### 1. Quest Slice (`/frontend/src/store/slices/questSlice.ts`)
**Complex Logic Areas:**
- **State Management**
  - Comprehensive quest state tracking
  - Daily quest reset handling
  - Result caching for performance

- **Async Operations**
  - Quest lifecycle management (start, submit, complete)
  - Error handling with user-friendly messages
  - Optimistic updates for responsiveness

## Key Business Rules

### Experience & Leveling
1. **Experience Scaling**: Exponential growth ensures balanced progression
2. **Level Cap**: Maximum level 100 with prestigious titles at milestones
3. **Boost Limits**: All percentage boosts capped at 50% to prevent exploitation

### Quest System
1. **Daily Limits**: 3-5 quests per day based on user level
2. **Time Limits**: Optional per quest, automatic failure on expiry
3. **Reward Scaling**: Linear for XP/coins, threshold-based for gems/achievements

### Multiplayer
1. **Session Codes**: 6-character alphanumeric for easy sharing
2. **Battle Duration**: 5-minute time limit for quick matches
3. **Question Pool**: 20 questions per battle for variety

### Learning Analytics
1. **Pattern Window**: 30-day analysis period for accuracy
2. **Style Categories**: Four learning styles identified through interaction patterns
3. **Recommendation Limit**: Top 5 recommendations to avoid choice paralysis

## Performance Considerations

1. **In-Memory Caching**: Active multiplayer sessions cached for real-time performance
2. **Batch Processing**: Multiple level-ups handled in single transaction
3. **Lazy Loading**: Quest content generated on-demand
4. **Rate Limiting**: Answer submissions throttled to prevent spam

## Security Measures

1. **Server Validation**: All answers validated server-side
2. **Time Tracking**: Impossible completion times flagged
3. **Permission Checks**: Role-based access for all operations
4. **Input Sanitization**: All user inputs sanitized before processing

## Future Improvements

1. **Machine Learning**: Implement true ML for recommendation engine
2. **A/B Testing**: Framework for testing reward balances
3. **Analytics Pipeline**: Real-time learning insights dashboard
4. **Microservices**: Extract heavy services for scalability