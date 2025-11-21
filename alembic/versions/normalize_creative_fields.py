"""
数据库字段规范化迁移脚本
将 config_json 中的核心字段提升为一级列
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'normalize_creative_fields'
down_revision = None  # 替换为上一个迁移的 revision
branch_labels = None
depends_on = None


def upgrade():
    """将核心业务字段从 config_json 提升为一级列"""
    
    # 1. 添加新列 (允许 NULL,稍后填充数据)
    op.add_column('creative_projects', sa.Column('title', sa.String(length=200), nullable=True))
    op.add_column('creative_projects', sa.Column('brief', sa.Text(), nullable=True))
    op.add_column('creative_projects', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('creative_projects', sa.Column('aspect_ratio', sa.String(length=10), nullable=True))
    op.add_column('creative_projects', sa.Column('style', sa.String(length=50), nullable=True))
    op.add_column('creative_projects', sa.Column('video_provider', sa.String(length=50), nullable=True))
    op.add_column('creative_projects', sa.Column('auto_pause_enabled', sa.Boolean(), nullable=True))
    
    # 2. 从 config_json 迁移数据到新列
    # PostgreSQL 示例 (MySQL 和 SQLite 需要调整 JSON 语法)
    op.execute("""
        UPDATE creative_projects
        SET 
            title = config_json->>'title',
            brief = config_json->>'brief',
            duration_seconds = (config_json->>'duration_seconds')::integer,
            aspect_ratio = COALESCE(config_json->>'aspect_ratio', '16:9'),
            style = COALESCE(config_json->>'style', 'cinematic'),
            video_provider = COALESCE(config_json->>'video_provider', 'runway'),
            auto_pause_enabled = COALESCE((config_json->>'auto_pause_enabled')::boolean, true)
        WHERE config_json IS NOT NULL
    """)
    
    # 3. 为没有 config_json 的旧数据设置默认值
    op.execute("""
        UPDATE creative_projects
        SET 
            title = COALESCE(title, 'Untitled Project'),
            brief = COALESCE(brief, ''),
            duration_seconds = COALESCE(duration_seconds, 5),
            aspect_ratio = COALESCE(aspect_ratio, '16:9'),
            style = COALESCE(style, 'cinematic'),
            video_provider = COALESCE(video_provider, 'runway'),
            auto_pause_enabled = COALESCE(auto_pause_enabled, true)
        WHERE title IS NULL OR brief IS NULL
    """)
    
    # 4. 修改列为 NOT NULL (数据已填充)
    op.alter_column('creative_projects', 'title', nullable=False)
    op.alter_column('creative_projects', 'brief', nullable=False)
    op.alter_column('creative_projects', 'duration_seconds', nullable=False)
    op.alter_column('creative_projects', 'aspect_ratio', nullable=False)
    op.alter_column('creative_projects', 'style', nullable=False)
    
    # 5. 添加索引 (加速查询)
    op.create_index('ix_creative_projects_status', 'creative_projects', ['status'])
    op.create_index('ix_creative_projects_created_at', 'creative_projects', ['created_at'])
    
    # 6. (可选) 从 config_json 中删除已迁移的字段,减少冗余
    # 注意: 这一步不可逆!
    # op.execute("""
    #     UPDATE creative_projects
    #     SET config_json = config_json - 'title' - 'brief' - 'duration_seconds' 
    #                      - 'aspect_ratio' - 'style' - 'video_provider' 
    #                      - 'auto_pause_enabled'
    # """)


def downgrade():
    """回滚:将一级列的数据写回 config_json"""
    
    # 1. 将数据写回 config_json
    op.execute("""
        UPDATE creative_projects
        SET config_json = COALESCE(config_json, '{}'::json) || 
            json_build_object(
                'title', title,
                'brief', brief,
                'duration_seconds', duration_seconds,
                'aspect_ratio', aspect_ratio,
                'style', style,
                'video_provider', video_provider,
                'auto_pause_enabled', auto_pause_enabled
            )
    """)
    
    # 2. 删除索引
    op.drop_index('ix_creative_projects_created_at', table_name='creative_projects')
    op.drop_index('ix_creative_projects_status', table_name='creative_projects')
    
    # 3. 删除列
    op.drop_column('creative_projects', 'auto_pause_enabled')
    op.drop_column('creative_projects', 'video_provider')
    op.drop_column('creative_projects', 'style')
    op.drop_column('creative_projects', 'aspect_ratio')
    op.drop_column('creative_projects', 'duration_seconds')
    op.drop_column('creative_projects', 'brief')
    op.drop_column('creative_projects', 'title')
