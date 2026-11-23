"""
Создание таблиц

Идентификатор: 0001
Предыдущая ревизия: нет
Дата создания: 2026-11-21 12:42:11.662752
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = '0001'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'authors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=256), nullable=False),
        sa.Column('birth_year', sa.SmallInteger(), nullable=True),
        sa.Column('biography', sa.Text(), nullable=True),
        sa.CheckConstraint('birth_year IS NULL OR birth_year BETWEEN 1 AND 9999', name=op.f('ck_authors_birth_year_range')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_authors'))
    )
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('isbn', sa.CHAR(length=13), nullable=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('publication_year', sa.SmallInteger(), nullable=True),
        sa.Column('status', sa.Enum('active', 'unavailable', name='book_status'), server_default='active', nullable=False),
        sa.Column('cover_url', sa.String(length=2048), nullable=True),
        sa.Column('content_path', sa.String(length=512), nullable=True),
        sa.Column('deleted_at', mysql.DATETIME(fsp=6), nullable=True),
        sa.Column('updated_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.Column('created_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.CheckConstraint('publication_year IS NULL OR publication_year BETWEEN 1 AND 9999', name=op.f('ck_books_publication_year_range')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_books')),
        sa.UniqueConstraint('isbn', name=op.f('uq_books_isbn'))
    )
    op.create_index('ix_books_created_at', 'books', ['created_at'], unique=False)
    op.create_index(op.f('ix_books_publication_year'), 'books', ['publication_year'], unique=False)
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_categories')),
        sa.UniqueConstraint('name', name=op.f('uq_categories_name'))
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('password', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('role', sa.Enum('admin', 'user', name='user_role'), server_default='user', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('username', name=op.f('uq_users_username'))
    )
    op.create_table(
        'auth_sessions',
        sa.Column('id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('refresh_token_hash', sa.CHAR(length=64), nullable=False),
        sa.Column('expires_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.Column('revoked_at', mysql.DATETIME(fsp=6), nullable=True),
        sa.Column('created_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.CheckConstraint('expires_at > created_at', name=op.f('ck_auth_sessions_expiration_after_creation')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_auth_sessions_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_sessions')),
        sa.UniqueConstraint('refresh_token_hash', name=op.f('uq_auth_sessions_refresh_token_hash'))
    )
    op.create_index(op.f('ix_auth_sessions_user_id'), 'auth_sessions', ['user_id'], unique=False)
    op.create_table(
        'book_authors',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['authors.id'], name=op.f('fk_book_authors_author_id_authors'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_book_authors_book_id_books'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('book_id', 'author_id', name=op.f('pk_book_authors'))
    )
    op.create_index('ix_book_authors_author_id_book_id', 'book_authors', ['author_id', 'book_id'], unique=False)
    op.create_table(
        'book_categories',
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_book_categories_book_id_books'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name=op.f('fk_book_categories_category_id_categories'), ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('book_id', 'category_id', name=op.f('pk_book_categories'))
    )
    op.create_index('ix_book_categories_category_id_book_id', 'book_categories', ['category_id', 'book_id'], unique=False)
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('updated_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.Column('created_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.CheckConstraint('rating BETWEEN 1 AND 5', name=op.f('ck_reviews_rating_range')),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_reviews_book_id_books'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reviews_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews')),
        sa.UniqueConstraint('user_id', 'book_id', name=op.f('uq_reviews_user_id_book_id'))
    )
    op.create_index(op.f('ix_reviews_book_id'), 'reviews', ['book_id'], unique=False)
    op.create_index(op.f('ix_reviews_user_id'), 'reviews', ['user_id'], unique=False)
    op.create_table(
        'user_books',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.Column('is_favorite', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('reading_status', sa.Enum('planned', 'reading', 'finished', name='reading_status'), server_default='planned', nullable=False),
        sa.Column('finished_at', mysql.DATETIME(fsp=6), nullable=True),
        sa.Column('updated_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.Column('created_at', mysql.DATETIME(fsp=6), nullable=False),
        sa.CheckConstraint("(reading_status = 'finished' AND finished_at IS NOT NULL) OR (reading_status <> 'finished' AND finished_at IS NULL)", name=op.f('ck_user_books_finished_at_matches_status')),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name=op.f('fk_user_books_book_id_books'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_books_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'book_id', name=op.f('pk_user_books'))
    )
    op.create_index(op.f('ix_user_books_book_id'), 'user_books', ['book_id'], unique=False)
    op.create_index('ix_user_books_user_id_is_favorite', 'user_books', ['user_id', 'is_favorite'], unique=False)
    op.create_index('ix_user_books_user_id_reading_status', 'user_books', ['user_id', 'reading_status'], unique=False)


def downgrade() -> None:
    op.drop_table('user_books')
    op.drop_table('reviews')
    op.drop_table('book_categories')
    op.drop_table('book_authors')
    op.drop_table('auth_sessions')
    op.drop_table('users')
    op.drop_table('categories')
    op.drop_table('books')
    op.drop_table('authors')
