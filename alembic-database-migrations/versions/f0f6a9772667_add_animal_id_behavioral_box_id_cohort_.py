"""Add animal_id, behavioral_box_id, cohort_id, and experiment_id to annotations table

Revision ID: f0f6a9772667
Revises: 7ab7c230e70a
Create Date: 2019-11-27 13:49:25.631600

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, Text, ForeignKey


# revision identifiers, used by Alembic.
revision = 'f0f6a9772667'
down_revision = '7ab7c230e70a'
branch_labels = None
depends_on = None

# naming_convention = {
#     "fk":
#     "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
# }

naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
      }

def upgrade():
    with op.batch_alter_table('TimestampedAnnotations', naming_convention=naming_convention) as batch_op:
        batch_op.add_column(Column('behavioral_box_id', Integer, ForeignKey('BehavioralBoxes.numerical_id')))
        batch_op.add_column(Column('experiment_id', Integer, ForeignKey('Experiments.id')))
        batch_op.add_column(Column('cohort_id', Integer, ForeignKey('Cohorts.id')))
        batch_op.add_column(Column('animal_id', Integer, ForeignKey('Animals.id')))
    pass


def downgrade():
    with op.batch_alter_table('TimestampedAnnotations', naming_convention=naming_convention) as batch_op:
        batch_op.drop_column('behavioral_box_id')
        batch_op.drop_column('experiment_id')
        batch_op.drop_column('cohort_id')
        batch_op.drop_column('animal_id')
    pass
