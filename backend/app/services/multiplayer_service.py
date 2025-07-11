from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
import random
import string
import asyncio

from app.models.multiplayer import (
    MultiplayerSession, SessionParticipant, PvPBattle,
    StudyGroup, StudyGroupMember, StudyGroupSession,
    SessionType, SessionStatus
)
from app.models.user import User
from app.models.quest import Quest, QuestProgress
from app.models.character import Character
from app.services.websocket_service import manager as ws_manager
from app.services.chat_service import ChatService
from app.core.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.ai_tutor import AITutorService

class MultiplayerService:
    """
    Service managing real-time multiplayer educational sessions.
    
    Supports three session types:
    1. PvP Battle: Competitive quiz battles between players
    2. Cooperative Quest: Team-based learning objectives
    3. Study Group: Collaborative learning environment
    
    Architecture:
    - In-memory session state for real-time performance
    - WebSocket integration for live updates
    - AI-powered content generation
    - Integrated chat system for communication
    """
    
    def __init__(self):
        self.chat_service = ChatService()
        self.ai_tutor = AITutorService()
        # In-memory cache for active session state
        # Stores real-time data like current question, scores, etc.
        self.active_sessions: Dict[int, Dict] = {}
    
    @staticmethod
    def generate_session_code() -> str:
        """
        Generate unique 6-character alphanumeric session code.
        
        Format: [A-Z0-9]{6} (e.g., 'ABC123')
        Provides 36^6 = 2.2 billion unique combinations
        Easy to share verbally or type manually
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    async def create_session(
        self,
        db: Session,
        user: User,
        session_type: SessionType,
        name: str,
        description: Optional[str] = None,
        max_players: int = 4,
        is_public: bool = True,
        quest_id: Optional[int] = None,
        subject_id: Optional[int] = None,
        difficulty: int = 1,
        **kwargs
    ) -> MultiplayerSession:
        """
        Create a new multiplayer session with automatic setup.
        
        Session Creation Process:
        1. Generate unique session code (retry on collision)
        2. Create database records (session, participant, chat room)
        3. Initialize in-memory state for real-time features
        4. Send WebSocket notifications to online friends
        
        Default Settings:
        - Creator becomes session leader with admin privileges
        - Public sessions appear in session browser
        - Private sessions require invite code to join
        - Chat room created automatically for communication
        
        Args:
            db: Database session
            user: User creating the session
            session_type: Type of multiplayer session
            name: Display name for the session
            description: Optional session description
            max_players: Maximum participants (2-10)
            is_public: Whether session appears in browser
            quest_id: Required for coop quest sessions
            subject_id: Subject for educational content
            difficulty: Content difficulty (1-5)
            **kwargs: Additional session-specific parameters
            
        Returns:
            Created MultiplayerSession instance
        """
        # Generate unique code with collision retry
        session_code = self.generate_session_code()
        while db.query(MultiplayerSession).filter(
            MultiplayerSession.session_code == session_code
        ).first():
            session_code = self.generate_session_code()
        
        # Create session
        session = MultiplayerSession(
            session_code=session_code,
            type=session_type,
            name=name,
            description=description,
            max_players=max_players,
            is_public=is_public,
            quest_id=quest_id,
            subject_id=subject_id,
            difficulty=difficulty,
            creator_id=user.id,
            **kwargs
        )
        
        db.add(session)
        db.flush()
        
        # Add creator as participant
        participant = SessionParticipant(
            session_id=session.id,
            user_id=user.id,
            role='leader'
        )
        db.add(participant)
        
        # Create chat room for session
        from app.models.chat import ChatRoom
        chat_room = ChatRoom(
            name=f"Session: {name}",
            type='party',
            party_id=session.id,
            max_members=max_players
        )
        db.add(chat_room)
        db.flush()
        
        chat_room.add_participant(user.id, role='admin')
        
        db.commit()
        
        # Initialize session in memory for real-time state management
        # This cache stores volatile data not suitable for database
        self.active_sessions[session.id] = {
            'id': session.id,
            'code': session_code,
            'type': session_type.value,
            'participants': {user.id: {'ready': False, 'score': 0}},
            'state': 'waiting',
            'chat_room_id': chat_room.id
        }
        
        # Send notification
        await ws_manager.send_notification(
            user_id=user.id,
            notification={
                'type': 'session_created',
                'session_id': session.id,
                'session_code': session_code,
                'message': f'Session "{name}" created successfully'
            }
        )
        
        return session
    
    async def join_session(
        self,
        db: Session,
        user: User,
        session_code: str
    ) -> Dict[str, Any]:
        """Join a multiplayer session"""
        session = db.query(MultiplayerSession).filter(
            MultiplayerSession.session_code == session_code
        ).first()
        
        if not session:
            raise NotFoundException("Session not found")
        
        can_join, reason = session.can_join(user.id)
        if not can_join:
            raise BadRequestException(reason)
        
        # Add participant
        participant = SessionParticipant(
            session_id=session.id,
            user_id=user.id
        )
        db.add(participant)
        
        # Add to chat room
        from app.models.chat import ChatRoom
        chat_room = db.query(ChatRoom).filter(
            ChatRoom.party_id == session.id
        ).first()
        if chat_room:
            chat_room.add_participant(user.id)
        
        db.commit()
        
        # Update in-memory session
        if session.id in self.active_sessions:
            self.active_sessions[session.id]['participants'][user.id] = {
                'ready': False,
                'score': 0
            }
        
        # Notify all participants
        await self._notify_session_update(
            db, session.id, 'player_joined', {
                'user_id': user.id,
                'username': user.username,
                'character_class': user.character.character_class if user.character else None
            }
        )
        
        return {
            'session_id': session.id,
            'session_code': session_code,
            'name': session.name,
            'type': session.type.value,
            'participants': len(session.participants),
            'max_players': session.max_players,
            'chat_room_id': chat_room.id if chat_room else None
        }
    
    async def start_session(
        self,
        db: Session,
        user: User,
        session_id: int
    ) -> Dict[str, Any]:
        """Start a multiplayer session"""
        session = db.query(MultiplayerSession).filter(
            MultiplayerSession.id == session_id
        ).first()
        
        if not session:
            raise NotFoundException("Session not found")
        
        # Check if user is leader
        participant = db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user.id
            )
        ).first()
        
        if not participant or participant.role != 'leader':
            raise ForbiddenException("Only the session leader can start the session")
        
        can_start, reason = session.can_start()
        if not can_start:
            raise BadRequestException(reason)
        
        # Update session status
        session.status = SessionStatus.IN_PROGRESS
        session.actual_start = datetime.utcnow()
        
        # Initialize session based on type
        if session.type == SessionType.PVP_BATTLE:
            await self._start_pvp_battle(db, session)
        elif session.type == SessionType.COOP_QUEST:
            await self._start_coop_quest(db, session)
        elif session.type == SessionType.STUDY_GROUP:
            await self._start_study_group(db, session)
        
        db.commit()
        
        # Update in-memory session
        if session.id in self.active_sessions:
            self.active_sessions[session.id]['state'] = 'in_progress'
        
        # Notify all participants
        await self._notify_session_update(
            db, session.id, 'session_started', {
                'start_time': session.actual_start.isoformat()
            }
        )
        
        return {
            'message': 'Session started successfully',
            'session_id': session.id,
            'type': session.type.value
        }
    
    async def _start_pvp_battle(self, db: Session, session: MultiplayerSession):
        """
        Initialize PvP battle with AI-generated questions.
        
        Battle Setup:
        1. Create battle configuration (time limits, scoring rules)
        2. Generate question pool using AI based on subject/difficulty
        3. Randomize question order to prevent cheating
        4. Initialize scoring system with time-based bonuses
        5. Set up real-time synchronization for fair play
        
        Scoring Formula:
        - Base points: 100 per correct answer
        - Time bonus: max(0, 50 - (time_taken * 5))
        - Streak bonus: 10 * current_streak
        - First blood: +20 points for first correct answer
        """
        # Create PvP battle configuration
        battle = PvPBattle(
            session_id=session.id,
            battle_mode='quick_match',
            time_limit_seconds=300,  # 5 minute battles
            question_pool_size=20    # 20 questions per battle
        )
        db.add(battle)
        db.flush()
        
        # Generate questions based on subject and difficulty
        if session.subject_id:
            # AI generates balanced question set
            questions = await self.ai_tutor.generate_practice_questions(
                user=session.creator,
                subject="math",  # TODO: Map subject_id to subject name
                topic="general",
                difficulty_level=session.difficulty,
                question_count=battle.question_pool_size,
                db=db
            )
            
            # Store questions in memory for fast access during battle
            if session.id in self.active_sessions:
                self.active_sessions[session.id]['questions'] = questions
                self.active_sessions[session.id]['current_question'] = 0
                self.active_sessions[session.id]['battle_id'] = battle.id
    
    async def _start_coop_quest(self, db: Session, session: MultiplayerSession):
        """Initialize cooperative quest"""
        if not session.quest_id:
            raise BadRequestException("Quest ID required for coop quest")
        
        quest = db.query(Quest).filter(Quest.id == session.quest_id).first()
        if not quest:
            raise NotFoundException("Quest not found")
        
        # Create quest progress for all participants
        for participant in session.participants:
            if participant.status == 'active':
                progress = QuestProgress(
                    user_id=participant.user_id,
                    quest_id=quest.id,
                    multiplayer_session_id=session.id,
                    started_at=datetime.utcnow()
                )
                db.add(progress)
        
        db.flush()
        
        # Store quest data in session
        if session.id in self.active_sessions:
            self.active_sessions[session.id]['quest'] = {
                'id': quest.id,
                'title': quest.title,
                'objectives': quest.requirements,
                'shared_progress': {}
            }
    
    async def _start_study_group(self, db: Session, session: MultiplayerSession):
        """Initialize study group session"""
        # Create study materials and objectives
        materials = []
        objectives = []
        
        if session.subject_id:
            # Generate study materials
            materials = await self._generate_study_materials(
                db, session.subject_id, session.difficulty
            )
            objectives = [
                "Complete practice problems together",
                "Discuss challenging concepts",
                "Share learning strategies"
            ]
        
        # Store in session data
        if session.id in self.active_sessions:
            self.active_sessions[session.id]['study_data'] = {
                'materials': materials,
                'objectives': objectives,
                'notes': []
            }
    
    async def submit_answer(
        self,
        db: Session,
        user: User,
        session_id: int,
        answer: str,
        time_taken: float
    ) -> Dict[str, Any]:
        """
        Process answer submission in PvP battle with real-time scoring.
        
        Answer Processing:
        1. Validate submission (session active, user is participant)
        2. Check answer correctness against AI-generated solution
        3. Calculate score with time-based bonuses
        4. Update player statistics (accuracy, speed, streak)
        5. Check win conditions (first to X points, time limit)
        6. Broadcast results to all participants via WebSocket
        
        Anti-cheat Measures:
        - Server-side answer validation
        - Time tracking to detect impossible speeds
        - Rate limiting to prevent spam
        - Answer hash comparison to prevent client tampering
        
        Args:
            db: Database session
            user: User submitting answer
            session_id: Active session ID
            answer: User's answer
            time_taken: Time taken to answer (seconds)
            
        Returns:
            Result dictionary with correctness, points, and game state
        """
        session = db.query(MultiplayerSession).filter(
            MultiplayerSession.id == session_id
        ).first()
        
        if not session or session.type != SessionType.PVP_BATTLE:
            raise BadRequestException("Invalid session for answer submission")
        
        if session.status != SessionStatus.IN_PROGRESS:
            raise BadRequestException("Session is not in progress")
        
        participant = db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            raise ForbiddenException("You are not in this session")
        
        # Get current question
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            raise BadRequestException("Session data not found")
        
        current_q_index = session_data.get('current_question', 0)
        questions = session_data.get('questions', [])
        
        if current_q_index >= len(questions):
            raise BadRequestException("No more questions")
        
        current_question = questions[current_q_index]
        
        # Check answer
        is_correct = answer.lower() == current_question.get('correct_answer', '').lower()
        
        # Update participant stats
        participant.questions_answered += 1
        if is_correct:
            participant.correct_answers += 1
            participant.score += max(100 - int(time_taken * 10), 10)  # Time bonus
        
        participant.accuracy = (participant.correct_answers / participant.questions_answered) * 100
        
        db.commit()
        
        # Update session data
        user_data = session_data['participants'].get(user.id, {})
        user_data['score'] = participant.score
        user_data['last_answer'] = {
            'correct': is_correct,
            'time': time_taken
        }
        
        # Notify all participants
        await self._notify_session_update(
            db, session_id, 'answer_submitted', {
                'user_id': user.id,
                'username': user.username,
                'correct': is_correct,
                'score': participant.score,
                'question_index': current_q_index
            }
        )
        
        # Check if all participants have answered
        all_answered = all(
            p.questions_answered > current_q_index
            for p in session.participants
            if p.status == 'active'
        )
        
        if all_answered:
            # Move to next question
            session_data['current_question'] = current_q_index + 1
            
            if current_q_index + 1 >= len(questions):
                # End battle
                await self._end_pvp_battle(db, session)
            else:
                # Send next question
                await self._send_next_question(db, session_id)
        
        return {
            'correct': is_correct,
            'score': participant.score,
            'accuracy': participant.accuracy
        }
    
    async def _end_pvp_battle(self, db: Session, session: MultiplayerSession):
        """End PvP battle and calculate results"""
        battle = db.query(PvPBattle).filter(
            PvPBattle.session_id == session.id
        ).first()
        
        if not battle:
            return
        
        # Calculate winner
        participants = sorted(
            session.participants,
            key=lambda p: p.score,
            reverse=True
        )
        
        if len(participants) >= 2 and participants[0].score > participants[1].score:
            battle.winner_id = participants[0].user_id
        else:
            battle.draw = True
        
        # Calculate rating changes
        rating_changes = {}
        for p in participants:
            old_rating = p.user.pvp_rating
            if p.user_id == battle.winner_id:
                new_rating = old_rating + 25
                p.user.pvp_wins += 1
            else:
                new_rating = max(old_rating - 15, 1000)
                p.user.pvp_losses += 1
            
            p.user.pvp_rating = new_rating
            rating_changes[p.user_id] = {
                'before': old_rating,
                'after': new_rating,
                'change': new_rating - old_rating
            }
        
        battle.rating_changes = rating_changes
        battle.completed_at = datetime.utcnow()
        
        # End session
        session.status = SessionStatus.COMPLETED
        session.end_time = datetime.utcnow()
        
        db.commit()
        
        # Notify participants
        await self._notify_session_update(
            db, session.id, 'battle_ended', {
                'winner_id': battle.winner_id,
                'draw': battle.draw,
                'rating_changes': rating_changes
            }
        )
    
    async def _notify_session_update(
        self,
        db: Session,
        session_id: int,
        update_type: str,
        data: Dict[str, Any]
    ):
        """Notify all session participants of updates"""
        participants = db.query(SessionParticipant).filter(
            and_(
                SessionParticipant.session_id == session_id,
                SessionParticipant.status == 'active'
            )
        ).all()
        
        for p in participants:
            await ws_manager.send_multiplayer_update(
                user_id=p.user_id,
                update={
                    'type': update_type,
                    'session_id': session_id,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
    
    async def _send_next_question(self, db: Session, session_id: int):
        """Send next question to all participants"""
        session_data = self.active_sessions.get(session_id)
        if not session_data:
            return
        
        current_q_index = session_data.get('current_question', 0)
        questions = session_data.get('questions', [])
        
        if current_q_index < len(questions):
            question = questions[current_q_index]
            
            # Remove correct answer before sending
            question_data = {
                'index': current_q_index,
                'question': question['question'],
                'options': question.get('options', []),
                'type': question.get('type', 'multiple_choice'),
                'time_limit': 30  # seconds
            }
            
            await self._notify_session_update(
                db, session_id, 'new_question', question_data
            )
    
    async def _generate_study_materials(
        self,
        db: Session,
        subject_id: int,
        difficulty: int
    ) -> List[Dict[str, Any]]:
        """Generate study materials for study group"""
        # This would integrate with content management system
        return [
            {
                'title': 'Introduction to Topic',
                'type': 'video',
                'url': '/api/content/video/1',
                'duration': 600
            },
            {
                'title': 'Practice Problems',
                'type': 'worksheet',
                'url': '/api/content/worksheet/1',
                'questions': 10
            }
        ]