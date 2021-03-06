"""Add invoice details

Revision ID: b0ad3831068d
Revises: 7f59125777ef
Create Date: 2016-02-23 13:24:11.103228

"""

# revision identifiers, used by Alembic.
revision = 'b0ad3831068d'
down_revision = '7f59125777ef'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('invoice_details', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Users', 'invoice_details')
    ### end Alembic commands ###
