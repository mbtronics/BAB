"""Add organisation info

Revision ID: 7f59125777ef
Revises: 92f3ef29d5a9
Create Date: 2016-02-17 15:10:59.036402

"""

# revision identifiers, used by Alembic.
revision = '7f59125777ef'
down_revision = '92f3ef29d5a9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('organisation', sa.String(length=50), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Users', 'organisation')
    ### end Alembic commands ###
