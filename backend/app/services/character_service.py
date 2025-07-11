from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.character import Character, SubjectLevel
from app.models.user import User
from app.schemas.character import (
    CharacterCreate,
    CharacterUpdate,
    SubjectLevelCreate,
    SubjectLevelUpdate,
    ExperienceGain,
    CurrencyUpdate,
    SubjectType
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)


class CharacterService:
    @staticmethod
    def create_character(
        db: Session,
        user_id: int,
        character_data: CharacterCreate
    ) -> Character:
        # Check if user already has a character
        existing_character = db.query(Character).filter(
            Character.user_id == user_id
        ).first()
        
        if existing_character:
            raise ConflictException("User already has a character")
        
        # Create new character
        db_character = Character(
            user_id=user_id,
            name=character_data.name,
            avatar_url=character_data.avatar_url
        )
        
        try:
            db.add(db_character)
            db.commit()
            db.refresh(db_character)
            
            # Initialize subject levels
            subjects = [subject.value for subject in SubjectType]
            for subject in subjects:
                subject_level = SubjectLevel(
                    character_id=db_character.id,
                    subject=subject
                )
                db.add(subject_level)
            
            db.commit()
            db.refresh(db_character)
            
            return db_character
            
        except IntegrityError:
            db.rollback()
            raise ConflictException("Failed to create character")
    
    @staticmethod
    def get_character(db: Session, character_id: int) -> Character:
        character = db.query(Character).filter(
            Character.id == character_id
        ).first()
        
        if not character:
            raise NotFoundException(f"Character with id {character_id} not found")
        
        return character
    
    @staticmethod
    def get_character_by_user_id(db: Session, user_id: int) -> Optional[Character]:
        return db.query(Character).filter(
            Character.user_id == user_id
        ).first()
    
    @staticmethod
    def update_character(
        db: Session,
        character_id: int,
        character_update: CharacterUpdate
    ) -> Character:
        character = CharacterService.get_character(db, character_id)
        
        update_data = character_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(character, field, value)
        
        character.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(character)
            return character
        except IntegrityError:
            db.rollback()
            raise BadRequestException("Failed to update character")
    
    @staticmethod
    def add_experience(
        db: Session,
        character_id: int,
        exp_gain: ExperienceGain
    ) -> SubjectLevel:
        character = CharacterService.get_character(db, character_id)
        
        # Find subject level
        subject_level = db.query(SubjectLevel).filter(
            SubjectLevel.character_id == character_id,
            SubjectLevel.subject == exp_gain.subject
        ).first()
        
        if not subject_level:
            raise NotFoundException(f"Subject level for {exp_gain.subject} not found")
        
        # Add experience
        subject_level.experience += exp_gain.experience_gained
        
        # Check for level up
        while subject_level.experience >= subject_level.exp_to_next_level:
            subject_level.experience -= subject_level.exp_to_next_level
            subject_level.level += 1
            subject_level.exp_to_next_level = CharacterService._calculate_exp_to_next_level(
                subject_level.level
            )
            
            # Update character total level
            character.total_level = sum(
                sl.level for sl in character.subject_levels
            )
        
        # Update character total experience
        character.total_experience += exp_gain.experience_gained
        character.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(subject_level)
        
        return subject_level
    
    @staticmethod
    def update_currency(
        db: Session,
        character_id: int,
        currency_update: CurrencyUpdate
    ) -> Character:
        character = CharacterService.get_character(db, character_id)
        
        if currency_update.coins is not None:
            if character.coins + currency_update.coins < 0:
                raise BadRequestException("Insufficient coins")
            character.coins += currency_update.coins
        
        if currency_update.gems is not None:
            if character.gems + currency_update.gems < 0:
                raise BadRequestException("Insufficient gems")
            character.gems += currency_update.gems
        
        character.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(character)
        
        return character
    
    @staticmethod
    def update_streak(db: Session, character_id: int) -> Character:
        character = CharacterService.get_character(db, character_id)
        
        today = datetime.utcnow().date()
        
        if character.last_active_date:
            last_active = character.last_active_date.date()
            days_diff = (today - last_active).days
            
            if days_diff == 1:
                # Continue streak
                character.streak_days += 1
            elif days_diff > 1:
                # Reset streak
                character.streak_days = 1
            # If days_diff == 0, already updated today
        else:
            # First time
            character.streak_days = 1
        
        character.last_active_date = datetime.utcnow()
        character.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(character)
        
        return character
    
    @staticmethod
    def get_rankings(
        db: Session,
        limit: int = 100,
        offset: int = 0
    ) -> List[Character]:
        return db.query(Character).order_by(
            Character.total_level.desc(),
            Character.total_experience.desc()
        ).offset(offset).limit(limit).all()
    
    @staticmethod
    def _calculate_exp_to_next_level(level: int) -> int:
        # Simple exponential growth formula
        base_exp = 100
        growth_rate = 1.2
        return int(base_exp * (growth_rate ** (level - 1)))