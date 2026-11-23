from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.repositories.categories import CategoryRepository
from app.repositories.seed import SeedRepository
from app.schemas.author import AuthorCreate
from app.schemas.book import BookCreate
from app.schemas.category import CategoryCreate
from app.scripts.seed_data import AUTHORS, BOOKS, CATEGORIES


@dataclass
class SeedResult:
    categories_created: int = 0
    authors_created: int = 0
    books_created: int = 0


class SeedService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.categories = CategoryRepository(db)
        self.repository = SeedRepository(db)

    def run(self) -> SeedResult:
        result = SeedResult()
        try:
            with self.db.begin():
                categories = {}
                for name in CATEGORIES:
                    data = CategoryCreate(name=name)
                    category = self.categories.get_by_name(data.name)

                    if category is None:
                        category = self.categories.add(data.name)
                        result.categories_created += 1

                    categories[name] = category

                authors = {}
                for name in AUTHORS:
                    matches = self.repository.find_authors(name)

                    if len(matches) > 1:
                        raise ConflictError('seed_ambiguous_author', f'Несколько авторов с именем {name}')

                    if matches:
                        author = matches[0]
                    else:
                        author = self.repository.add_author(AuthorCreate(
                            full_name=name, biography='Демонстрационный автор',
                        ))

                        result.authors_created += 1

                    authors[name] = author

                for item in BOOKS:
                    matches = self.repository.find_books(item.title)

                    if len(matches) > 1:
                        raise ConflictError('seed_ambiguous_book', f'Несколько книг {item.title}')

                    if matches:
                        continue

                    book_authors = [authors[name] for name in item.authors]
                    book_categories = [categories[name] for name in item.categories]

                    data = BookCreate(
                        title=item.title, description=item.description, publication_year=item.year,
                        author_ids=[author.id for author in book_authors],
                        category_ids=[category.id for category in book_categories],
                    )

                    self.repository.add_book(data, book_authors, book_categories)

                    result.books_created += 1
            return result
        except IntegrityError as error:
            if error.orig.args[0] == 1062:
                raise ConflictError(
                    'seed_conflict',
                    'Данные изменились одновременно с seed'
                ) from None

            raise
