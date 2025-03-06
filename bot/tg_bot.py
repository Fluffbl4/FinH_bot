import os
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

from database.db import User, Income, Category, Expense, Reminder, create_tables
from database.connection_db import get_db, engine

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

create_tables()

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    db = next(get_db())
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        user = User(telegram_id=user_id, username=username)
        db.add(user)
        db.commit()

    update.message.reply_text(
        "Привет! Я FinHelper, твой помощник в управлении финансами.\n\n"
        "Доступные команды:\n"
        "/add_income [сумма] [описание] - добавить доход\n"
        "/add_expense [сумма] [категория] [описание] - добавить расход\n"
        "/remind [дата] [сообщение] - установить напоминание\n"
        "/summary [период] - получить итоговую сумму расходов\n"
        "/categories - просмотреть расходы по категориям"
    )

def add_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        amount = float(context.args[0])
        description = " ".join(context.args[1:]) if len(context.args) > 1 else None

        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            income = Income(
                user_id=user.user_id,
                amount=amount,
                income_date=datetime.now().date(),
                description=description
            )
            db.add(income)
            db.commit()
            update.message.reply_text(f"Доход в размере {amount} успешно добавлен!")
        else:
            update.message.reply_text("Пользователь не найден.")
    except (IndexError, ValueError):
        update.message.reply_text("Используйте эту команду для добавления: /add_income [сумма] [описание]")


def add_expense(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        amount = float(context.args[0])
        category_name = context.args[1] if len(context.args) > 1 else "другое"
        description = " ".join(context.args[2:]) if len(context.args) > 2 else None

        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == category_name).first()
        if user:
            category = db.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                db.add(category)
                db.commit()

            expense = Expense(
                user_id=user.user_id,
                amount=amount,
                expanse_date=datetime.now().date(),
                category_id=category.category_id,
                description=description
            )
            db.add(expense)
            db.commit()
            update.message.reply_text(f"Расход в размере {amount} (категория: {category_name}) успешно добавлен!")
        else:
            update.message.reply_text("Пользователь не найден.")
    except (IndexError, ValueError):
        update.message.reply_text("Используйте эту команду для добавления: /add_expense [сумма] [категория] [описание]")


def set_reminder(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        reminder_date = datetime.strptime(context.args[0], "%d.%m.%Y").date()
        message = " ".join(context.args[1:]) if len(context.args) > 1 else "Не забудьте внести данные о финансах!"

        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            reminder = Reminder(
                user_id=user.user_id,
                reminder_date=reminder_date,
                message=message
            )
            db.add(reminder)
            db.commit()
            update.message.reply_text(f"Напоминание установлено на {reminder_date.strftime('%d.%m.%Y')}!")
        else:
            update.message.reply_text("Пользователь не найден.")
    except (IndexError, ValueError):
        update.message.reply_text("Используйте эту команду: /remind [дата в формате ДД.ММ.ГГГГ] [сообщение]")


def get_summary(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        period = context.args[0] if context.args else "month"

        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            if period == "month":
                start_date = datetime.now().replace(day=1).date()
            else:
                start_date = datetime.now().date()

            total = db.query(Expense.amount).filter(
                Expense.user_id == user.user_id,
                Expense.expanse_date >= start_date
            ).scalar() or 0

            update.message.reply_text(f"Общая сумма расходов за {period}: {total}")
        else:
            update.message.reply_text("Пользователь не найден.")
    except Exception as e:
        logger.error(e)
        update.message.reply_text("Произошла ошибка при расчете суммы расходов.")


def get_categories(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        db = next(get_db())
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            categories = db.query(Category.name, Expense.amount).join(Expense).filter(
                Expense.user_id == user.user_id
            ).all()

            if categories:
                response = "Расходы по категориям:\n" + "\n".join([f"{cat}: {amount}" for cat, amount in categories])
                update.message.reply_text(response)
            else:
                update.message.reply_text("Нет данных о расходах.")
        else:
            update.message.reply_text("Пользователь не найден.")
    except Exception as e:
        logger.error(e)
        update.message.reply_text("Произошла ошибка при получении данных.")


def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    updater = Updater(token)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add_income", add_income))
    dispatcher.add_handler(CommandHandler("add_expense", add_expense))
    dispatcher.add_handler(CommandHandler("remind", set_reminder))
    dispatcher.add_handler(CommandHandler("summary", get_summary))
    dispatcher.add_handler(CommandHandler("categories", get_categories))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()