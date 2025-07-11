#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
테이블 생성 및 초기 데이터 설정
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.core.database import Base, engine, SessionLocal
from app.core.config import settings

# 모든 모델 import (중요!)
from app.models.user import User
from app.models.character import Character, SubjectLevel
from app.models.achievement import Achievement, UserAchievement
from app.models.quest import Quest, QuestProgress


def init_database():
    """데이터베이스 테이블 생성"""
    print("Initializing database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # 기본 데이터 추가 (옵션)
    db = SessionLocal()
    try:
        # 기본 업적 추가
        if db.query(Achievement).count() == 0:
            print("Adding default achievements...")
            default_achievements = [
                {
                    "name": "첫 걸음",
                    "description": "첫 번째 퀘스트를 완료하세요",
                    "category": "quest",
                    "rarity": "common",
                    "points": 10,
                    "max_progress": 1
                },
                {
                    "name": "열정적인 학습자",
                    "description": "하루에 5개의 퀘스트를 완료하세요",
                    "category": "learning",
                    "rarity": "rare",
                    "points": 50,
                    "max_progress": 5
                },
                {
                    "name": "연속 출석",
                    "description": "7일 연속 접속하세요",
                    "category": "streak",
                    "rarity": "rare",
                    "points": 100,
                    "max_progress": 7
                }
            ]
            
            for ach_data in default_achievements:
                achievement = Achievement(**ach_data)
                db.add(achievement)
            
            db.commit()
            print("✅ Default achievements added!")
        
        # 기본 퀘스트 추가
        if db.query(Quest).count() == 0:
            print("Adding default quests...")
            default_quests = [
                {
                    "title": "기초 수학 문제",
                    "description": "간단한 덧셈과 뺄셈 문제를 풀어보세요",
                    "quest_type": "daily",
                    "difficulty": "easy",
                    "subject": "math",
                    "objectives": [{"type": "solve", "count": 5}],
                    "exp_reward": 100,
                    "coin_reward": 50,
                    "gem_reward": 0,
                    "time_limit_minutes": 30,
                    "min_level": 1
                },
                {
                    "title": "과학 탐구",
                    "description": "기초 과학 개념을 학습하세요",
                    "quest_type": "daily",
                    "difficulty": "medium",
                    "subject": "science",
                    "objectives": [{"type": "learn", "count": 3}],
                    "exp_reward": 150,
                    "coin_reward": 75,
                    "gem_reward": 0,
                    "time_limit_minutes": 45,
                    "min_level": 1
                },
                {
                    "title": "영어 단어 마스터",
                    "description": "새로운 영어 단어를 학습하세요",
                    "quest_type": "weekly",
                    "difficulty": "medium",
                    "subject": "english",
                    "objectives": [{"type": "memorize", "count": 10}],
                    "exp_reward": 300,
                    "coin_reward": 150,
                    "gem_reward": 5,
                    "time_limit_minutes": 60,
                    "min_level": 2
                }
            ]
            
            for quest_data in default_quests:
                quest = Quest(**quest_data)
                db.add(quest)
            
            db.commit()
            print("✅ Default quests added!")
        
        print("\n✅ Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error during initialization: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()