from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import string
import random

from app.models.guild import Guild, GuildQuest, GuildAnnouncement, GuildLevel
from app.models.user import User
from app.models.quest import Quest
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.websocket_service import manager as ws_manager

class GuildService:
    @staticmethod
    def generate_guild_tag() -> str:
        """Generate a unique guild tag"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    
    @staticmethod
    async def create_guild(
        db: Session,
        user: User,
        name: str,
        description: str,
        tag: Optional[str] = None,
        is_public: bool = True,
        **kwargs
    ) -> Guild:
        """Create a new guild"""
        # Check if user already owns a guild
        if user.owned_guild:
            raise BadRequestException("You already own a guild")
        
        # Check if user is already in a guild
        if user.guild:
            raise BadRequestException("You must leave your current guild first")
        
        # Generate tag if not provided
        if not tag:
            tag = GuildService.generate_guild_tag()
            # Ensure uniqueness
            while db.query(Guild).filter(Guild.tag == tag).first():
                tag = GuildService.generate_guild_tag()
        
        # Create guild
        guild = Guild(
            name=name,
            description=description,
            tag=tag,
            is_public=is_public,
            owner_id=user.id,
            **kwargs
        )
        
        db.add(guild)
        db.commit()
        
        # Add owner as member
        guild.add_member(user, role="leader")
        db.commit()
        
        # Send notification
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "guild_created",
                "guild_id": guild.id,
                "guild_name": guild.name,
                "message": f"You have created the guild '{guild.name}'"
            }
        )
        
        return guild
    
    @staticmethod
    async def join_guild(
        db: Session,
        user: User,
        guild_id: int
    ) -> Dict[str, Any]:
        """Join a guild"""
        guild = db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            raise NotFoundException("Guild not found")
        
        # Check if can join
        can_join, reason = guild.can_join(user)
        if not can_join:
            raise BadRequestException(reason)
        
        # Add member
        guild.add_member(user)
        db.commit()
        
        # Update guild stats
        await GuildService.update_guild_stats(db, guild)
        
        # Send notifications
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "guild_joined",
                "guild_id": guild.id,
                "guild_name": guild.name,
                "message": f"You have joined '{guild.name}'"
            }
        )
        
        # Notify guild members
        for member in guild.members:
            if member.id != user.id:
                await ws_manager.send_notification(
                    user_id=member.id,
                    notification={
                        "type": "new_guild_member",
                        "guild_id": guild.id,
                        "user_id": user.id,
                        "username": user.username,
                        "message": f"{user.username} has joined the guild"
                    }
                )
        
        return {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "member_count": guild.get_member_count()
        }
    
    @staticmethod
    async def leave_guild(
        db: Session,
        user: User,
        guild_id: int
    ) -> Dict[str, Any]:
        """Leave a guild"""
        guild = db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            raise NotFoundException("Guild not found")
        
        if user not in guild.members:
            raise BadRequestException("You are not a member of this guild")
        
        if guild.owner_id == user.id:
            raise BadRequestException("Guild owner cannot leave. Transfer ownership first.")
        
        # Remove member
        guild.remove_member(user)
        db.commit()
        
        # Send notifications
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                "type": "guild_left",
                "guild_id": guild.id,
                "guild_name": guild.name,
                "message": f"You have left '{guild.name}'"
            }
        )
        
        return {"message": "Successfully left the guild"}
    
    @staticmethod
    async def create_guild_quest(
        db: Session,
        user: User,
        guild_id: int,
        quest_id: int,
        min_participants: int = 3,
        max_participants: int = 10
    ) -> GuildQuest:
        """Create a guild quest"""
        guild = db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            raise NotFoundException("Guild not found")
        
        if user not in guild.members:
            raise ForbiddenException("You must be a guild member")
        
        quest = db.query(Quest).filter(Quest.id == quest_id).first()
        if not quest:
            raise NotFoundException("Quest not found")
        
        # Check if quest is already active
        active_quest = db.query(GuildQuest).filter(
            and_(
                GuildQuest.guild_id == guild_id,
                GuildQuest.quest_id == quest_id,
                GuildQuest.status == 'active'
            )
        ).first()
        
        if active_quest:
            raise BadRequestException("This quest is already active for the guild")
        
        # Create guild quest
        guild_quest = GuildQuest(
            guild_id=guild_id,
            quest_id=quest_id,
            min_participants=min_participants,
            max_participants=max_participants,
            guild_exp_reward=quest.experience * 2,  # Double exp for guild
            guild_coin_reward=quest.reward * 2,  # Double coins for guild
            participants=[user.id]
        )
        
        db.add(guild_quest)
        db.commit()
        
        # Notify guild members
        for member in guild.members:
            await ws_manager.send_notification(
                user_id=member.id,
                notification={
                    "type": "guild_quest_created",
                    "guild_id": guild.id,
                    "quest_id": quest.id,
                    "quest_title": quest.title,
                    "message": f"New guild quest available: {quest.title}"
                }
            )
        
        return guild_quest
    
    @staticmethod
    async def update_guild_stats(db: Session, guild: Guild) -> None:
        """Update guild statistics"""
        # Calculate weekly activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count completed quests this week
        weekly_quests = db.query(GuildQuest).filter(
            and_(
                GuildQuest.guild_id == guild.id,
                GuildQuest.status == 'completed',
                GuildQuest.end_time >= week_ago
            )
        ).count()
        
        guild.weekly_activity_points = weekly_quests * 100
        
        # Check for level up
        level_thresholds = {
            GuildLevel.BRONZE: 0,
            GuildLevel.SILVER: 1000,
            GuildLevel.GOLD: 5000,
            GuildLevel.PLATINUM: 15000,
            GuildLevel.DIAMOND: 50000
        }
        
        for level, threshold in reversed(list(level_thresholds.items())):
            if guild.experience >= threshold and guild.level != level:
                guild.level = level
                guild.max_members = 50 + (list(GuildLevel).index(level) * 25)
                
                # Notify members of level up
                for member in guild.members:
                    await ws_manager.send_notification(
                        user_id=member.id,
                        notification={
                            "type": "guild_level_up",
                            "guild_id": guild.id,
                            "new_level": level.value,
                            "message": f"Guild leveled up to {level.value}!"
                        }
                    )
                break
        
        db.commit()
    
    @staticmethod
    def get_guild_leaderboard(
        db: Session,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get guild leaderboard"""
        guilds = db.query(Guild).order_by(
            Guild.experience.desc(),
            Guild.weekly_activity_points.desc()
        ).limit(limit).offset(offset).all()
        
        return [{
            "rank": offset + idx + 1,
            "id": guild.id,
            "name": guild.name,
            "tag": guild.tag,
            "level": guild.level.value,
            "experience": guild.experience,
            "member_count": guild.get_member_count(),
            "weekly_activity": guild.weekly_activity_points
        } for idx, guild in enumerate(guilds)]
    
    @staticmethod
    async def create_announcement(
        db: Session,
        user: User,
        guild_id: int,
        title: str,
        content: str,
        priority: str = "normal",
        expires_at: Optional[datetime] = None
    ) -> GuildAnnouncement:
        """Create guild announcement"""
        guild = db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            raise NotFoundException("Guild not found")
        
        # Check permissions (only owner and officers)
        member_data = db.execute(
            "SELECT role FROM guild_members WHERE guild_id = :guild_id AND user_id = :user_id",
            {"guild_id": guild_id, "user_id": user.id}
        ).first()
        
        if not member_data or member_data.role not in ['leader', 'officer']:
            raise ForbiddenException("Only guild leaders and officers can create announcements")
        
        announcement = GuildAnnouncement(
            guild_id=guild_id,
            author_id=user.id,
            title=title,
            content=content,
            priority=priority,
            expires_at=expires_at
        )
        
        db.add(announcement)
        db.commit()
        
        # Notify all members
        for member in guild.members:
            await ws_manager.send_notification(
                user_id=member.id,
                notification={
                    "type": "guild_announcement",
                    "guild_id": guild.id,
                    "announcement_id": announcement.id,
                    "title": title,
                    "priority": priority,
                    "message": f"New guild announcement: {title}"
                }
            )
        
        return announcement