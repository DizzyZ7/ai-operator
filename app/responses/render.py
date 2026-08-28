from __future__ import annotations

from app.responses.models import ResponsePlan

_TEMPLATES: dict[str, str] = {
    "appointment_created": "Запись создана.",
    "appointment_rescheduled": "Запись перенесена.",
    "appointment_cancelled": "Запись отменена.",
    "appointment_confirmed": "Запись подтверждена.",
    "handoff_required": (
        "Я передам звонок сотруднику клиники и сохраню уже собранную информацию."
    ),
    "action_not_completed": (
        "Не удалось подтвердить выполнение действия. Я не буду говорить, что оно выполнено."
    ),
    "approved_information_available": "У меня есть подтверждённая информация по вашему вопросу.",
}


class UnknownResponseTemplate(ValueError):
    pass


def render_response(plan: ResponsePlan) -> str:
    if plan.template_key == "slots_available":
        options = plan.facts.get("options")
        if not isinstance(options, list) or not options:
            return "Подтверждённых свободных вариантов сейчас нет."

        safe_options = [str(option) for option in options[:3]]
        return "Есть варианты: " + ", ".join(safe_options) + "."

    try:
        return _TEMPLATES[plan.template_key]
    except KeyError as exc:
        raise UnknownResponseTemplate(plan.template_key) from exc
