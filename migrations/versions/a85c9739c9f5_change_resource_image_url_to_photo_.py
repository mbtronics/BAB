"""Change resource image_url to photo upload

Revision ID: a85c9739c9f5
Revises: 1932d1816dbb
Create Date: 2016-01-14 10:57:09.744243

"""

# revision identifiers, used by Alembic.
revision = 'a85c9739c9f5'
down_revision = '1932d1816dbb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('Resources') as batch_op:
        batch_op.add_column(sa.Column('photo_filename', sa.String(length=100), nullable=True))
        batch_op.drop_column('image_url')

def downgrade():
    with op.batch_alter_table('Resources') as batch_op:
        batch_op.add_column(sa.Column('image_url', sa.VARCHAR(), nullable=True))
        batch_op.drop_column('photo_filename')

