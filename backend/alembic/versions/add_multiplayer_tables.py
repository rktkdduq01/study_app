"""Add multiplayer tables

Revision ID: add_multiplayer_tables
Revises: 
Create Date: 2025-01-09 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_multiplayer_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("CREATE TYPE guildlevel AS ENUM ('bronze', 'silver', 'gold', 'platinum', 'diamond')")
    op.execute("CREATE TYPE sessiontype AS ENUM ('coop_quest', 'pvp_battle', 'study_group', 'tournament')")
    op.execute("CREATE TYPE sessionstatus AS ENUM ('waiting', 'in_progress', 'completed', 'cancelled')")
    
    # Create guilds table
    op.create_table('guilds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tag', sa.String(length=10), nullable=False),
        sa.Column('level', postgresql.ENUM('bronze', 'silver', 'gold', 'platinum', 'diamond', name='guildlevel'), nullable=True),
        sa.Column('experience', sa.Integer(), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('min_level_requirement', sa.Integer(), nullable=True),
        sa.Column('auto_accept_members', sa.Boolean(), nullable=True),
        sa.Column('emblem', sa.String(length=255), nullable=True),
        sa.Column('banner', sa.String(length=255), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('total_quests_completed', sa.Integer(), nullable=True),
        sa.Column('total_pvp_wins', sa.Integer(), nullable=True),
        sa.Column('weekly_activity_points', sa.Integer(), nullable=True),
        sa.Column('guild_bank_coins', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_guilds_name'), 'guilds', ['name'], unique=True)
    op.create_index(op.f('ix_guilds_tag'), 'guilds', ['tag'], unique=True)
    
    # Create guild_members association table
    op.create_table('guild_members',
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('contribution_points', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('guild_id', 'user_id')
    )
    
    # Create guild_invitations table
    op.create_table('guild_invitations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=True),
        sa.Column('inviter_id', sa.Integer(), nullable=True),
        sa.Column('invitee_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['inviter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['invitee_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create guild_quests table
    op.create_table('guild_quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('quest_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('progress', sa.JSON(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('guild_exp_reward', sa.Integer(), nullable=True),
        sa.Column('guild_coin_reward', sa.Integer(), nullable=True),
        sa.Column('min_participants', sa.Integer(), nullable=True),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('participants', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create guild_announcements table
    op.create_table('guild_announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create friend_requests table
    op.create_table('friend_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sender_id', 'receiver_id', name='_sender_receiver_uc')
    )
    
    # Create friendships table
    op.create_table('friendships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('friendship_level', sa.Integer(), nullable=True),
        sa.Column('interaction_count', sa.Integer(), nullable=True),
        sa.Column('last_interaction', sa.DateTime(), nullable=True),
        sa.Column('favorite', sa.Boolean(), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user1_id', 'user2_id', name='_user1_user2_uc')
    )
    
    # Create user_blocks table
    op.create_table('user_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blocker_id', sa.Integer(), nullable=False),
        sa.Column('blocked_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['blocked_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['blocker_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('blocker_id', 'blocked_id', name='_blocker_blocked_uc')
    )
    
    # Create multiplayer_sessions table
    op.create_table('multiplayer_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_code', sa.String(length=10), nullable=True),
        sa.Column('type', postgresql.ENUM('coop_quest', 'pvp_battle', 'study_group', 'tournament', name='sessiontype'), nullable=False),
        sa.Column('status', postgresql.ENUM('waiting', 'in_progress', 'completed', 'cancelled', name='sessionstatus'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('max_players', sa.Integer(), nullable=True),
        sa.Column('min_players', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=True),
        sa.Column('quest_id', sa.Integer(), nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_start', sa.DateTime(), nullable=True),
        sa.Column('actual_start', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['quest_id'], ['quests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_multiplayer_sessions_session_code'), 'multiplayer_sessions', ['session_code'], unique=True)
    
    # Create chat_rooms table
    op.create_table('chat_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('is_moderated', sa.Boolean(), nullable=True),
        sa.Column('guild_id', sa.Integer(), nullable=True),
        sa.Column('party_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['party_id'], ['multiplayer_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=True),
        sa.Column('edited', sa.Boolean(), nullable=True),
        sa.Column('edited_at', sa.DateTime(), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('reply_to_id', sa.Integer(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('reactions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['reply_to_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_room_created', 'chat_messages', ['room_id', 'created_at'])
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'])
    op.create_index(op.f('ix_chat_messages_room_id'), 'chat_messages', ['room_id'])
    
    # Create chat_participants table
    op.create_table('chat_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('nickname', sa.String(length=50), nullable=True),
        sa.Column('last_read_message_id', sa.Integer(), nullable=True),
        sa.Column('unread_count', sa.Integer(), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=True),
        sa.Column('muted_until', sa.DateTime(), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
        sa.Column('mention_notifications', sa.Boolean(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['last_read_message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create direct_messages table
    op.create_table('direct_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id')
    )
    
    # Add multiplayer columns to users table
    op.add_column('users', sa.Column('pvp_rating', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('pvp_wins', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('pvp_losses', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('total_study_hours', sa.Integer(), nullable=True))
    
    # Create remaining multiplayer tables
    op.create_table('session_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('team', sa.Integer(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('questions_answered', sa.Integer(), nullable=True),
        sa.Column('correct_answers', sa.Integer(), nullable=True),
        sa.Column('experience_earned', sa.Integer(), nullable=True),
        sa.Column('coins_earned', sa.Integer(), nullable=True),
        sa.Column('items_earned', sa.JSON(), nullable=True),
        sa.Column('last_ping', sa.DateTime(), nullable=True),
        sa.Column('connection_quality', sa.String(length=20), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['multiplayer_sessions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('pvp_battles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('battle_mode', sa.String(length=50), nullable=False),
        sa.Column('time_limit_seconds', sa.Integer(), nullable=True),
        sa.Column('question_pool_size', sa.Integer(), nullable=True),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('draw', sa.Boolean(), nullable=True),
        sa.Column('battle_log', sa.JSON(), nullable=True),
        sa.Column('final_scores', sa.JSON(), nullable=True),
        sa.Column('rating_changes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['multiplayer_sessions.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('pvp_battles')
    op.drop_table('session_participants')
    op.drop_table('chat_participants')
    op.drop_table('chat_messages')
    op.drop_table('chat_rooms')
    op.drop_table('multiplayer_sessions')
    op.drop_table('user_blocks')
    op.drop_table('friendships')
    op.drop_table('friend_requests')
    op.drop_table('guild_announcements')
    op.drop_table('guild_quests')
    op.drop_table('guild_invitations')
    op.drop_table('guild_members')
    op.drop_table('guilds')
    
    # Drop columns from users table
    op.drop_column('users', 'total_study_hours')
    op.drop_column('users', 'pvp_losses')
    op.drop_column('users', 'pvp_wins')
    op.drop_column('users', 'pvp_rating')
    
    # Drop enum types
    op.execute('DROP TYPE sessionstatus')
    op.execute('DROP TYPE sessiontype')
    op.execute('DROP TYPE guildlevel')