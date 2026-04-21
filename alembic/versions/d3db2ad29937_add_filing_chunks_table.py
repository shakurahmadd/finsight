"""add_filing_chunks_table

Revision ID: d3db2ad29937
Revises: f2d763462c00
Create Date: 2026-04-21 11:21:54.958006

"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3db2ad29937'
down_revision: Union[str, Sequence[str], None] = 'f2d763462c00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'filing_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),                                                                                                
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),                                                                                                 
        sa.Column('filing_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),                                                                             
    )        
    
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
