#!/usr/bin/env python3
"""
Initialize default achievements in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.achievement import Achievement
from app.services.achievement_service import AchievementService
from app.services.achievement_data import get_default_achievements
from app.schemas.achievement import AchievementCreate


def init_achievements():
    """Initialize default achievements"""
    db = SessionLocal()
    
    try:
        print("Initializing default achievements...")
        
        achievements = get_default_achievements()
        created_count = 0
        updated_count = 0
        
        for achievement_data in achievements:
            # Check if achievement already exists
            existing = db.query(Achievement).filter_by(
                name=achievement_data["name"]
            ).first()
            
            if not existing:
                try:
                    # Create new achievement
                    achievement = AchievementService.create_achievement(
                        db,
                        AchievementCreate(**achievement_data)
                    )
                    created_count += 1
                    print(f"✓ Created achievement: {achievement.name}")
                except Exception as e:
                    print(f"✗ Failed to create achievement {achievement_data['name']}: {e}")
            else:
                # Update existing achievement
                try:
                    for key, value in achievement_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    db.commit()
                    updated_count += 1
                    print(f"↻ Updated achievement: {existing.name}")
                except Exception as e:
                    print(f"✗ Failed to update achievement {achievement_data['name']}: {e}")
                    db.rollback()
        
        print(f"\nSummary:")
        print(f"- Created: {created_count} achievements")
        print(f"- Updated: {updated_count} achievements")
        print(f"- Total: {len(achievements)} achievements")
        
        # Display achievement stats
        total_achievements = db.query(Achievement).count()
        active_achievements = db.query(Achievement).filter_by(is_active=True).count()
        
        print(f"\nDatabase stats:")
        print(f"- Total achievements: {total_achievements}")
        print(f"- Active achievements: {active_achievements}")
        
    except Exception as e:
        print(f"Error initializing achievements: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_achievements()