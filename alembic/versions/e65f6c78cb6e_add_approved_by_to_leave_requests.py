"""add_approved_by_to_leave_requests

Revision ID: e65f6c78cb6e
Revises: 937e52fb5ae1
Create Date: 2025-05-02 11:51:05.223644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e65f6c78cb6e'
down_revision: Union[str, None] = '937e52fb5ae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # اضافه کردن فیلد approved_by با رابطه ForeignKey
    op.add_column('leave_requests', 
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id'))
    )
    
    # ایجاد ایندکس برای بهبود عملکرد
    op.create_index(op.f('ix_leave_requests_approved_by'), 'leave_requests', ['approved_by'])

def downgrade():
    # حذف ایندکس و فیلد در حالت rollback
    op.drop_index(op.f('ix_leave_requests_approved_by'), table_name='leave_requests')
    op.drop_column('leave_requests', 'approved_by')
