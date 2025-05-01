"""add_tornado_approval_flow

Revision ID: eed316ac0d2a
Revises: 89bfd60c1009
Create Date: 2025-05-01 13:04:18.478131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eed316ac0d2a'
down_revision: Union[str, None] = '89bfd60c1009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. ایجاد جدول تیم‌ها
    op.create_table(
        'teams',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True),
        sa.Column('is_vendor', sa.Boolean(), default=False)
    )

    # 2. اضافه کردن فیلد team_id به کاربران
    op.add_column('users', 
        sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'))
    )

    # 3. اضافه کردن فیلدهای تأیید
    op.add_column('leave_requests',
        sa.Column('tornado_approval', sa.Boolean(), nullable=True)
    )
    op.add_column('leave_requests',
        sa.Column('zitel_approval', sa.Boolean(), nullable=True)
    )

    # 4. داده‌های اولیه
    op.bulk_insert('teams',
        [
            {'id': 1, 'name': 'زی تل', 'is_vendor': False},
            {'id': 2, 'name': 'تورنادو', 'is_vendor': True}
        ]
    )

def downgrade():
    op.drop_column('leave_requests', 'zitel_approval')
    op.drop_column('leave_requests', 'tornado_approval')
    op.drop_column('users', 'team_id')
    op.drop_table('teams')
