"""empty message

Revision ID: 237d59044303
Revises: 0de5ec0cb554
Create Date: 2023-11-29 05:50:56.118095

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '237d59044303'
down_revision = '0de5ec0cb554'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.BIGINT(),
               nullable=False,
               autoincrement=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.alter_column('timestamp',
               existing_type=sa.BIGINT(),
               nullable=True,
               autoincrement=True)

    # ### end Alembic commands ###