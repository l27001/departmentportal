"""Add rating system tables (7 publication types, conferences, trainings, templates)

Revision ID: f7a2b3c4d5e6
Revises: 3ea0cd686485
Create Date: 2026-05-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


revision: str = 'f7a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] =     '3ea0cd686485'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(name: str) -> bool:
    inspector = reflection.Inspector.from_engine(op.get_bind())
    return name in inspector.get_table_names()


def upgrade() -> None:
    op.execute('DROP TABLE IF EXISTS publications')

    if not table_exists('publication_books'):
        op.create_table('publication_books',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('authors', sa.String(500), nullable=True),
            sa.Column('edition', sa.String(50), nullable=True),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('publisher', sa.String(255), nullable=True),
            sa.Column('pages', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_journal_articles'):
        op.create_table('publication_journal_articles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('authors', sa.String(500), nullable=True),
            sa.Column('journal_name', sa.String(255), nullable=True),
            sa.Column('issue', sa.String(50), nullable=True),
            sa.Column('pages', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_collection_articles'):
        op.create_table('publication_collection_articles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('authors', sa.String(500), nullable=True),
            sa.Column('collection_title', sa.String(500), nullable=True),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('publisher', sa.String(255), nullable=True),
            sa.Column('pages', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_dissertations'):
        op.create_table('publication_dissertations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('author_single', sa.String(255), nullable=True),
            sa.Column('degree', sa.String(50), nullable=True),
            sa.Column('field', sa.String(100), nullable=True),
            sa.Column('specialty_code', sa.String(20), nullable=True),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('pages', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_abstracts'):
        op.create_table('publication_abstracts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('author_single', sa.String(255), nullable=True),
            sa.Column('degree', sa.String(50), nullable=True),
            sa.Column('field', sa.String(100), nullable=True),
            sa.Column('specialty_code', sa.String(20), nullable=True),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('pages', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_internets'):
        op.create_table('publication_internets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('authors', sa.String(500), nullable=True),
            sa.Column('site_name', sa.String(255), nullable=True),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('access_date', sa.String(20), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('publication_newspaper_articles'):
        op.create_table('publication_newspaper_articles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('publication_date', sa.Date(), nullable=True),
            sa.Column('gost_string', sa.Text(), nullable=True),
            sa.Column('doi', sa.String(100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('authors', sa.String(500), nullable=True),
            sa.Column('newspaper_name', sa.String(255), nullable=True),
            sa.Column('newspaper_date', sa.String(20), nullable=True),
            sa.Column('issue', sa.String(50), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('conferences'):
        op.create_table('conferences',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('name', sa.String(255), nullable=False, index=True),
            sa.Column('role', sa.String(50), nullable=False),
            sa.Column('paper_title', sa.String(255), nullable=True),
            sa.Column('conference_date', sa.Date(), nullable=False, index=True),
            sa.Column('location', sa.String(255), nullable=True),
            sa.Column('conference_url', sa.String(500), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True),
            sa.Column('coauthors', sa.String(255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )

    if not table_exists('trainings'):
        op.create_table('trainings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False, index=True),
            sa.Column('title', sa.String(255), nullable=False, index=True),
            sa.Column('organization', sa.String(255), nullable=False),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('training_type', sa.String(50), nullable=False),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=False, index=True),
            sa.Column('duration_hours', sa.Integer(), nullable=True),
            sa.Column('certificate_number', sa.String(255), nullable=True),
            sa.Column('certificate_url', sa.String(500), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(20), nullable=True),
            sa.Column('level', sa.String(50), nullable=True),
            sa.Column('state_issued', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
        )
    else:
        op.execute('ALTER TABLE trainings ADD COLUMN IF NOT EXISTS state_issued BOOLEAN')

    if not table_exists('rating_templates'):
        op.create_table('rating_templates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('entity_type', sa.String(50), nullable=False),
            sa.Column('sub_type', sa.String(50), nullable=True),
            sa.Column('template_data', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade() -> None:
    op.drop_table('rating_templates')
    op.drop_table('trainings')
    op.drop_table('conferences')
    op.drop_table('publication_newspaper_articles')
    op.drop_table('publication_internets')
    op.drop_table('publication_abstracts')
    op.drop_table('publication_dissertations')
    op.drop_table('publication_collection_articles')
    op.drop_table('publication_journal_articles')
    op.drop_table('publication_books')
