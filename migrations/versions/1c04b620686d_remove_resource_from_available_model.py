"""Remove resource from Available model

Revision ID: 1c04b620686d
Revises: e8e00d6a0ee6
Create Date: 2016-01-20 12:56:51.664531

"""

# revision identifiers, used by Alembic.
revision = '1c04b620686d'
down_revision = 'e8e00d6a0ee6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('Availability_ibfk_1', 'Availability', type_='foreignkey')
    op.drop_index('ix_Availability_resource_id', table_name='Availability')
    op.drop_column('Availability', 'resource_id')


def downgrade():
    op.add_column('Availability', sa.Column('resource_id', sa.INTEGER(), nullable=True))
    op.create_foreign_key('Availability_ibfk_1', 'Availability', 'Resources', ['resource_id'], ['id'])
    op.create_index('ix_Availability_resource_id', 'Availability', ['resource_id'], unique=False)
