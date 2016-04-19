"""Change payment paid to state

Revision ID: 2d045afae57e
Revises: 44ab77c55d85
Create Date: 2016-04-17 17:47:20.477872

"""

# revision identifiers, used by Alembic.
revision = '2d045afae57e'
down_revision = '44ab77c55d85'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Payments', sa.Column('status', sa.Enum('Open', 'Pending', 'Paid', 'Cancelled'), nullable=False))
    op.drop_column('Payments', 'paid')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Payments', sa.Column('paid', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_column('Payments', 'status')
    ### end Alembic commands ###