"""Update resource table

Revision ID: 6fa3823b89a8
Revises: 0c30600413ab
Create Date: 2016-01-06 20:14:19.297164

"""

# revision identifiers, used by Alembic.
revision = '6fa3823b89a8'
down_revision = '0c30600413ab'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('Resources') as batch_op:
        batch_op.drop_column('cons_unit')
        batch_op.drop_column('cons_cost')
        batch_op.drop_column('cons_name')

def downgrade():
    with op.batch_alter_table('Resources') as batch_op:
        batch_op.add_column(sa.Column('cons_name', sa.VARCHAR(length=64), nullable=True))
        batch_op.add_column(sa.Column('cons_cost', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('cons_unit', sa.VARCHAR(length=64), nullable=True))

