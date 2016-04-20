"""Add mollie id to Payment

Revision ID: 47172e76faa4
Revises: 2d045afae57e
Create Date: 2016-04-20 10:42:58.981529

"""

# revision identifiers, used by Alembic.
revision = '47172e76faa4'
down_revision = '2d045afae57e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Payments', sa.Column('mollie_id', sa.String(length=20), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Payments', 'mollie_id')
    ### end Alembic commands ###
