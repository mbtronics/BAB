"""Change Payment

Revision ID: 92f3ef29d5a9
Revises: b51909f47d3a
Create Date: 2016-01-26 13:09:56.799820

"""

# revision identifiers, used by Alembic.
revision = '92f3ef29d5a9'
down_revision = 'b51909f47d3a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Payments', 'user_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Payments', 'user_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    ### end Alembic commands ###