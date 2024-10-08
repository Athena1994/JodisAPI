"""Initial migration#

Revision ID: 5d7ea004e2a0
Revises: 
Create Date: 2024-09-15 15:54:28.645519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d7ea004e2a0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Client',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('Name', sa.String(length=64), nullable=True),
    sa.Column('State', sa.Enum('ACTIVE', 'SUSPENDED', name='state'), nullable=False),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('Job',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('Configuration', sa.JSON(), nullable=False),
    sa.Column('CreationTimestamp', sa.DateTime(), nullable=False),
    sa.Column('Name', sa.String(length=64), nullable=True),
    sa.Column('Description', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('JobScheduleEntry',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('JobId', sa.Integer(), nullable=False),
    sa.Column('ClientId', sa.Integer(), nullable=False),
    sa.Column('Rank', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ClientId'], ['Client.Id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['JobId'], ['Job.Id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('Id')
    )
    op.create_table('JobStatus',
    sa.Column('Id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('JobId', sa.Integer(), nullable=False),
    sa.Column('State', sa.Enum('UNASSIGNED', 'ASSIGNED', 'FINISHED', name='state'), nullable=False),
    sa.Column('SubState', sa.Enum('CREATED', 'RETURNED', 'SCHEDULED', 'RUNNING', 'FAILED', 'FINISHED', 'ABORTED', name='substate'), nullable=False),
    sa.Column('Timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['JobId'], ['Job.Id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('Id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('JobStatus')
    op.drop_table('JobScheduleEntry')
    op.drop_table('Job')
    op.drop_table('Client')
    # ### end Alembic commands ###
