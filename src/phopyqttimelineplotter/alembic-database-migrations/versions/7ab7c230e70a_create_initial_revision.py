"""create initial revision

Revision ID: 7ab7c230e70a
Revises: 
Create Date: 2019-11-27 13:45:50.311430

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ab7c230e70a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # op.create_table(
    #     'account',
    #     sa.Column('id', sa.Integer, primary_key=True),
    #     sa.Column('name', sa.String(50), nullable=False),
    #     sa.Column('description', sa.Unicode(200)),
    # )
    pass


def downgrade():
    # op.drop_table('account')
    pass
