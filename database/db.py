from sqlalchemy import Column, Integer, String, Date, Time, DECIMAL, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base

from connection_db import engine

Base = declarative_base()


# Таблица пользователей
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    salary_day = Column(Integer, nullable=True)
    reminder_time = Column(Time, nullable=True)

    incomes = relationship('Income', back_populates='user')
    expenses = relationship('Expense', back_populates='user')
    reminders = relationship('Reminder', back_populates='user')


# Таблица поступлений
class Income(Base):
    __tablename__ = 'incomes'
    income_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    income_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)

    user = relationship('User', back_populates='incomes')


# Таблица категорий расходов
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    expenses = relationship('Expense', back_populates='category')


# Таблица расходов
class Expense(Base):
    __tablename__ = 'expenses'
    expense_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    expanse_date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id', ondelete='SET NULL'), nullable=True)
    description = Column(Text, nullable=True)

    user = relationship('User', back_populates='expenses')
    category = relationship('Category', back_populates='expenses')


# Таблица напоминаний
class Reminder(Base):
    __tablename__ = 'reminders'
    reminder_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    reminder_date = Column(Date, nullable=False)
    message = Column(Text, nullable=False)  # Текст напоминания
    is_sent = Column(Boolean, default=False)  # Флаг отправки напоминания

    user = relationship('User', back_populates='reminders')


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
    print("Таблицы успешно созданы!")
