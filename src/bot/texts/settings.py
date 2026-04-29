from __future__ import annotations

from src.schemas.dataclasses.settings import StopWordDTO, StreamGoalDTO


class SettingsText:
    @staticmethod
    def menu() -> str:
        return "⚙️ <b>Настройки</b>\n\nВыбери раздел:"

    @staticmethod
    def streamer_only() -> str:
        return "❌ Настройки доступны только для стримеров."

    # ── Стоп-слова ────────────────────────────────────────────────────────────

    @staticmethod
    def stopwords_list(words: list[StopWordDTO]) -> str:
        if not words:
            return (
                "🚫 <b>Стоп-слова</b>\n\n"
                "Список пуст. Донаты с любыми словами разрешены.\n\n"
                "Добавь слова, которые хочешь запретить в сообщениях."
            )
        lines = [f"🚫 <b>Стоп-слова</b> ({len(words)}):\n"]
        for w in words:
            lines.append(f"• {w.word}")
        lines.append("\nДонаты с этими словами автоматически отклоняются.")
        return "\n".join(lines)

    @staticmethod
    def stopword_ask() -> str:
        return "✏️ Введи слово для добавления в стоп-список:"

    @staticmethod
    def stopword_added(word: str) -> str:
        return f'✅ Слово "<b>{word}</b>" добавлено в стоп-список.'

    @staticmethod
    def stopword_duplicate(word: str) -> str:
        return f'⚠️ Слово "<b>{word}</b>" уже есть в стоп-списке.'

    @staticmethod
    def stopword_empty() -> str:
        return "❌ Слово не может быть пустым. Введи слово:"

    @staticmethod
    def stopword_deleted() -> str:
        return "🗑 Слово удалено."

    # ── Цель сбора ────────────────────────────────────────────────────────────

    @staticmethod
    def goal_info(goal: StreamGoalDTO) -> str:
        if goal.target_amount == 0:
            return (
                "🎯 <b>Цель сбора</b>\n\n"
                "Цель не задана.\n\n"
                "Установи цель, чтобы зрители видели прогресс сбора."
            )
        percent = (
            round(goal.current_amount / goal.target_amount * 100)
            if goal.target_amount > 0 else 0
        )
        title = goal.title or "Без названия"
        return (
            f"🎯 <b>Цель сбора</b>\n\n"
            f"📌 {title}\n"
            f"Собрано: <b>{goal.current_amount}</b> / {goal.target_amount} монет ({percent}%)"
        )

    @staticmethod
    def goal_ask_title() -> str:
        return (
            "✏️ Введи название цели сбора:\n"
            "(например: <i>На новый микрофон</i>)"
        )

    @staticmethod
    def goal_ask_amount(title: str) -> str:
        return (
            f'📌 Название: "<b>{title}</b>"\n\n'
            "💰 Теперь введи целевую сумму в монетах:"
        )

    @staticmethod
    def goal_updated(title: str, amount: int) -> str:
        return (
            f'✅ Цель обновлена!\n\n'
            f'📌 "{title}"\n'
            f"💰 Цель: {amount} монет"
        )

    @staticmethod
    def goal_invalid_amount() -> str:
        return "❌ Введи целое число больше нуля:"

    @staticmethod
    def cancelled() -> str:
        return "❌ Отменено."
