from sqlalchemy import Column, ForeignKey, Index, Integer, Table

from app.db.base import Base

book_authors = Table(
    'book_authors', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='RESTRICT'), primary_key=True),
    Index('ix_book_authors_author_id_book_id', 'author_id', 'book_id'),
)

book_categories = Table(
    'book_categories', Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='RESTRICT'), primary_key=True),
    Index('ix_book_categories_category_id_book_id', 'category_id', 'book_id'),
)
