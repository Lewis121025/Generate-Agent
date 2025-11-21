"""Initial database schema

Revision ID: init_schema
Revises: 
Create Date: 2025-01-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'init_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建初始数据库表"""
    
    # ==================== Users 表 ====================
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('credits_usd', sa.Float(), nullable=False, server_default='10.0'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_external_id', 'users', ['external_id'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # ==================== Creative Projects 表 ====================
    op.create_table(
        'creative_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('prompt_hash', sa.String(length=64), nullable=True),
        
        # 核心业务字段
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('brief', sa.Text(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('aspect_ratio', sa.String(length=10), nullable=False, server_default='16:9'),
        sa.Column('style', sa.String(length=50), nullable=False, server_default='cinematic'),
        sa.Column('video_provider', sa.String(length=50), nullable=True, server_default='runway'),
        
        # 状态字段
        sa.Column('status', sa.String(length=50), nullable=False, server_default='initiated'),
        sa.Column('pause_reason', sa.String(length=50), nullable=True),
        sa.Column('paused_at', sa.DateTime(), nullable=True),
        sa.Column('pre_pause_state', sa.String(length=50), nullable=True),
        sa.Column('auto_resume_enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # 预算字段
        sa.Column('budget_usd', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('auto_pause_enabled', sa.Boolean(), nullable=False, server_default='true'),
        
        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(), nullable=False),
        
        # 扩展配置
        sa.Column('config_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index('ix_creative_projects_external_id', 'creative_projects', ['external_id'])
    op.create_index('ix_creative_projects_user_id', 'creative_projects', ['user_id'])
    op.create_index('ix_creative_projects_status', 'creative_projects', ['status'])
    op.create_index('ix_creative_projects_created_at', 'creative_projects', ['created_at'])
    
    # ==================== Scripts 表 ====================
    op.create_table(
        'scripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('reviewed_by_user', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['creative_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scripts_project_id', 'scripts', ['project_id'])
    
    # ==================== Storyboards 表 ====================
    op.create_table(
        'storyboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('shot_number', sa.Integer(), nullable=False),
        sa.Column('duration_sec', sa.Integer(), nullable=False),
        sa.Column('camera_angle', sa.String(length=100), nullable=True),
        sa.Column('visual_prompt', sa.Text(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['creative_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_storyboards_project_id', 'storyboards', ['project_id'])
    
    # ==================== Project Assets 表 ====================
    op.create_table(
        'project_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('s3_key', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['creative_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_project_assets_project_id', 'project_assets', ['project_id'])
    
    # ==================== Generated Shots 表 ====================
    op.create_table(
        'generated_shots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('storyboard_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('video_url', sa.String(length=512), nullable=True),
        sa.Column('generation_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['storyboard_id'], ['storyboards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_generated_shots_storyboard_id', 'generated_shots', ['storyboard_id'])
    
    # ==================== General Sessions 表 ====================
    op.create_table(
        'general_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('memory_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_active_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index('ix_general_sessions_external_id', 'general_sessions', ['external_id'])
    op.create_index('ix_general_sessions_user_id', 'general_sessions', ['user_id'])


def downgrade():
    """删除所有表"""
    op.drop_index('ix_general_sessions_user_id', table_name='general_sessions')
    op.drop_index('ix_general_sessions_external_id', table_name='general_sessions')
    op.drop_table('general_sessions')
    
    op.drop_index('ix_generated_shots_storyboard_id', table_name='generated_shots')
    op.drop_table('generated_shots')
    
    op.drop_index('ix_project_assets_project_id', table_name='project_assets')
    op.drop_table('project_assets')
    
    op.drop_index('ix_storyboards_project_id', table_name='storyboards')
    op.drop_table('storyboards')
    
    op.drop_index('ix_scripts_project_id', table_name='scripts')
    op.drop_table('scripts')
    
    op.drop_index('ix_creative_projects_created_at', table_name='creative_projects')
    op.drop_index('ix_creative_projects_status', table_name='creative_projects')
    op.drop_index('ix_creative_projects_user_id', table_name='creative_projects')
    op.drop_index('ix_creative_projects_external_id', table_name='creative_projects')
    op.drop_table('creative_projects')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_external_id', table_name='users')
    op.drop_table('users')
