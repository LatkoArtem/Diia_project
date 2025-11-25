"""
Метадані про поля для AI-driven розмов.
Замість жорстких промптів, AI отримує контекст і сам веде діалог.
"""

from typing import Dict, List

# Метадані для кожного поля
FIELD_METADATA = {
    "city": {
        "description": "Місто, де укладається договір",
        "purpose": "Вказується в шапці договору для фіксації місця укладення",
        "example": "Київ, Львів, Одеса"
    },
    "enterprise": {
        "description": "Повна назва підприємства",
        "purpose": "Офіційна назва організації для договору",
        "example": "ТОВ 'Епік Софт', ПП 'Диджитал Лаб'"
    },
    "date": {
        "description": "Дата укладення договору",
        "purpose": "Офіційна дата підписання договору",
        "example": "15 січня 2025 року, 15.01.2025"
    },
    "full_name_customer": {
        "description": "ПІБ замовника (в родовому відмінку)",
        "purpose": "Хто отримує послуги",
        "example": "Іванова Івана Івановича"
    },
    "full_name_performer": {
        "description": "ПІБ виконавця (в називному відмінку)",
        "purpose": "Хто надає послуги",
        "example": "Петрова Петра Петровича"
    },
    "customer_phone_number": {
        "description": "Номер телефону замовника",
        "purpose": "Для контактів",
        "example": "+380991234567"
    },
    "performer_phone_number": {
        "description": "Номер телефону виконавця",
        "purpose": "Для контактів",
        "example": "+380997654321"
    },
    "customer_edrpou": {
        "description": "Код ЄДРПОУ замовника (8 цифр)",
        "purpose": "Унікальний ідентифікатор організації в державному реєстрі",
        "example": "12345678"
    },
    "performer_edrpou": {
        "description": "Код ЄДРПОУ виконавця (8 цифр)",
        "purpose": "Унікальний ідентифікатор організації в державному реєстрі",
        "example": "87654321"
    },
    "customer_iban": {
        "description": "IBAN замовника",
        "purpose": "Банківський рахунок для переказу коштів",
        "example": "UA123456789012345678901234567"
    },
    "performer_iban": {
        "description": "IBAN виконавця",
        "purpose": "Банківський рахунок для отримання оплати",
        "example": "UA987654321098765432109876543"
    },
    "customer_postal_address_and_zip_code": {
        "description": "Поштова адреса замовника з індексом",
        "purpose": "Юридична адреса для листування та документів",
        "example": "01001, м. Київ, вул. Хрещатик, 1"
    },
    "performer_postal_address_and_zip_code": {
        "description": "Поштова адреса виконавця з індексом",
        "purpose": "Юридична адреса для листування та документів",
        "example": "02000, м. Київ, вул. Шевченка, 10"
    },
    "date_act_signed": {
        "description": "Число місяця для підписання акту (1-30)",
        "purpose": "Щомісячний дедлайн для підписання акту виконаних робіт",
        "example": "15 (тобто до 15-го числа кожного місяця)"
    },
    "money_transfer_deadline": {
        "description": "Кількість днів на оплату",
        "purpose": "Термін, протягом якого замовник повинен оплатити послуги після підписання акту",
        "example": "5 (днів)"
    },
    "contract_validity_period": {
        "description": "Строк дії договору",
        "purpose": "Визначає, на який період укладається договір",
        "example": "1 рік, до 31.12.2025, безстроково"
    }
}

# Логічні групи для збору (щоб AI знав, що краще питати разом)
FIELD_GROUPS_INFO: Dict[str, List[Dict]] = {
    "nadannya_poslug": [
        {
            "name": "Базова інформація",
            "fields": ["city", "enterprise", "date"],
            "initial_prompt": "Спочатку кілька базових речей: у якому місті укладається договір, яка назва підприємства і дата укладення."
        },
        {
            "name": "Імена",
            "fields": ["full_name_customer", "full_name_performer"],
            "initial_prompt": "Тепер мені потрібні повні імена: ПІБ замовника та ПІБ виконавця."
        },
        {
            "name": "Телефони",
            "fields": ["customer_phone_number", "performer_phone_number"],
            "initial_prompt": "Номери телефонів замовника і виконавця."
        },
        {
            "name": "Коди ЄДРПОУ",
            "fields": ["customer_edrpou", "performer_edrpou"],
            "initial_prompt": "Коди ЄДРПОУ замовника та виконавця."
        },
        {
            "name": "Банківські реквізити",
            "fields": ["customer_iban", "performer_iban"],
            "initial_prompt": "IBAN замовника та IBAN виконавця."
        },
        {
            "name": "Адреси",
            "fields": ["customer_postal_address_and_zip_code", "performer_postal_address_and_zip_code"],
            "initial_prompt": "Поштові адреси замовника та виконавця."
        },
        {
            "name": "Умови договору",
            "fields": ["date_act_signed", "money_transfer_deadline", "contract_validity_period"],
            "initial_prompt": "Умови договору: до якого числа місяця підписується акт, скільки днів на перерахування грошей, та на який строк укладається договір."
        }
    ]
}

def get_field_description(field_name: str) -> str:
    """Повертає опис поля для AI"""
    meta = FIELD_METADATA.get(field_name, {})
    desc = meta.get("description", field_name)
    purpose = meta.get("purpose", "")
    example = meta.get("example", "")

    result = f"- {field_name}: {desc}"
    if purpose:
        result += f" (Призначення: {purpose})"
    if example:
        result += f" [Приклад: {example}]"

    return result

def get_group_info(template_code: str) -> List[Dict]:
    """Повертає інформацію про групи полів"""
    return FIELD_GROUPS_INFO.get(template_code, [])

def get_fields_context(field_names: List[str]) -> str:
    """Створює контекст про поля для AI"""
    return "\n".join([get_field_description(f) for f in field_names])