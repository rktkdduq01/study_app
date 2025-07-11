"""Add CMS tables

Revision ID: add_cms_tables
Revises: add_multiplayer_tables
Create Date: 2025-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_cms_tables'
down_revision = 'add_multiplayer_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types for CMS
    op.execute("CREATE TYPE contenttype AS ENUM ('lesson', 'quiz', 'exercise', 'video', 'article', 'interactive', 'game', 'assessment')")
    op.execute("CREATE TYPE contentstatus AS ENUM ('draft', 'review', 'published', 'archived')")
    op.execute("CREATE TYPE difficultylevel AS ENUM ('beginner', 'intermediate', 'advanced', 'expert')")
    
    # Create subjects table first
    op.create_table('subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=255), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_subjects_id'), 'subjects', ['id'], unique=False)
    op.create_index(op.f('ix_subjects_name'), 'subjects', ['name'], unique=True)
    op.create_index(op.f('ix_subjects_code'), 'subjects', ['code'], unique=True)
    
    # Create contents table
    op.create_table('contents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=250), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', postgresql.ENUM('lesson', 'quiz', 'exercise', 'video', 'article', 'interactive', 'game', 'assessment', name='contenttype'), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('assets', sa.JSON(), nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('difficulty_level', postgresql.ENUM('beginner', 'intermediate', 'advanced', 'expert', name='difficultylevel'), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('prerequisites', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'review', 'published', 'archived', name='contentstatus'), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('total_ratings', sa.Integer(), nullable=True),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('editor_id', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['editor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contents_id'), 'contents', ['id'], unique=False)
    op.create_index(op.f('ix_contents_slug'), 'contents', ['slug'], unique=True)
    op.create_index(op.f('ix_contents_title'), 'contents', ['title'], unique=False)
    op.create_index(op.f('ix_contents_content_type'), 'contents', ['content_type'], unique=False)
    op.create_index(op.f('ix_contents_subject_id'), 'contents', ['subject_id'], unique=False)
    op.create_index(op.f('ix_contents_status'), 'contents', ['status'], unique=False)
    
    # Create content_versions table
    op.create_table('content_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create content_comments table
    op.create_table('content_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['content_comments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create content_categories table
    op.create_table('content_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['content_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_categories_name'), 'content_categories', ['name'], unique=True)
    op.create_index(op.f('ix_content_categories_slug'), 'content_categories', ['slug'], unique=True)
    
    # Create content_templates table
    op.create_table('content_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content_type', postgresql.ENUM('lesson', 'quiz', 'exercise', 'video', 'article', 'interactive', 'game', 'assessment', name='contenttype'), nullable=False),
        sa.Column('template_body', sa.Text(), nullable=True),
        sa.Column('default_metadata', sa.JSON(), nullable=True),
        sa.Column('required_fields', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create content_analytics table
    op.create_table('content_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('views', sa.Integer(), nullable=True),
        sa.Column('unique_views', sa.Integer(), nullable=True),
        sa.Column('completions', sa.Integer(), nullable=True),
        sa.Column('time_spent', sa.Integer(), nullable=True),
        sa.Column('bounce_rate', sa.Float(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True),
        sa.Column('shares', sa.Integer(), nullable=True),
        sa.Column('comments_count', sa.Integer(), nullable=True),
        sa.Column('downloads', sa.Integer(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('completion_time', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_analytics_date'), 'content_analytics', ['date'], unique=False)
    
    # Create curriculums table
    op.create_table('curriculums',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('difficulty_level', postgresql.ENUM('beginner', 'intermediate', 'advanced', 'expert', name='difficultylevel'), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('is_sequential', sa.Boolean(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'review', 'published', 'archived', name='contentstatus'), nullable=True),
        sa.Column('is_premium', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create curriculum_items table
    op.create_table('curriculum_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('curriculum_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.Column('unlock_criteria', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ),
        sa.ForeignKeyConstraint(['curriculum_id'], ['curriculums.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('curriculum_items')
    op.drop_table('curriculums')
    op.drop_table('content_analytics')
    op.drop_table('content_templates')
    op.drop_table('content_categories')
    op.drop_table('content_comments')
    op.drop_table('content_versions')
    op.drop_table('contents')
    op.drop_table('subjects')
    
    # Drop enum types
    op.execute('DROP TYPE difficultylevel')
    op.execute('DROP TYPE contentstatus')
    op.execute('DROP TYPE contenttype')