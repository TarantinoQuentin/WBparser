from datetime import datetime
from sqlmodel import Field, SQLModel, create_engine


class WBPosition(SQLModel, table=True):
    """
    Класс-модель таблицы с карточками товаров,
    полученных в ходе парсинга, для базы данных.
    Содержит описания и типы данных столбцов, название таблицы
    """

    __tablename__ = "wb_positions"

    id: int | None = Field(default=None, primary_key=True)  # Первичный ключ
    timestamp: datetime = Field(default_factory=datetime.now)  # Время парса
    key: str  # Ключ поиска
    position: int  # Порядковый номер
    sku: str  # Артикул
    link: str  # Ссылка

DB_PASS = ''
DB_NAME = ''

DB_URL = f"postgresql://postgres:{DB_PASS}@localhost:5432/{DB_NAME}"
engine = create_engine(DB_URL)

def create_db_and_tables() -> None:
    """
    Метод, создающий таблицу в базе данных по модели 'WBPosition'

    :return: None
    """

    # Аналог команды 'python manage.py migrate'
    # Эта строчка посмотрит на класс WBPosition и создаст таблицу в Postgres
    SQLModel.metadata.create_all(engine)
