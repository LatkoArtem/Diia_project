from typing import Dict, List

# Групи полів для кожного шаблону
FIELD_GROUPS: Dict[str, List[Dict]] = {
    "nadannya_poslug": [
        {
            "id": "basic_info",
            "prompt": "Привіт! Я допоможу скласти договір надання послуг. Спочатку кілька базових речей: у якому місті укладається договір, яка назва підприємства і дата укладення?",
            "fields": ["city", "enterprise", "date"],
            "extraction_hint": "Витягни назву міста (city), назву підприємства (enterprise) та дату укладення договору (date)."
        },
        {
            "id": "names",
            "prompt": "Чудово! Тепер мені потрібні повні імена: ПІБ замовника та ПІБ виконавця.",
            "fields": ["full_name_customer", "full_name_performer"],
            "extraction_hint": "Витягни ПІБ замовника (full_name_customer) та ПІБ виконавця (full_name_performer)."
        },
        {
            "id": "phones",
            "prompt": "Добре. Тепер телефони: номер телефону замовника і номер телефону виконавця.",
            "fields": ["customer_phone_number", "performer_phone_number"],
            "extraction_hint": "Витягни номер телефону замовника (customer_phone_number) та номер телефону виконавця (performer_phone_number). Формат: +380XXXXXXXXX або 0XXXXXXXXX"
        },
        {
            "id": "company_ids",
            "prompt": "Далі мені потрібні коди ЄДРПОУ замовника та виконавця.",
            "fields": ["customer_edrpou", "performer_edrpou"],
            "extraction_hint": "Витягни ЄДРПОУ замовника (customer_edrpou) та ЄДРПОУ виконавця (performer_edrpou). Це 8-значні числа."
        },
        {
            "id": "banking",
            "prompt": "Тепер банківські реквізити: IBAN замовника та IBAN виконавця.",
            "fields": ["customer_iban", "performer_iban"],
            "extraction_hint": "Витягни IBAN замовника (customer_iban) та IBAN виконавця (performer_iban). Формат: UA + 27 цифр."
        },
        {
            "id": "addresses",
            "prompt": "Майже все! Мені потрібні поштові адреси замовника та виконавця.",
            "fields": ["customer_postal_address_and_zip_code", "performer_postal_address_and_zip_code"],
            "extraction_hint": "Витягни поштову адресу замовника з індексом (customer_postal_address_and_zip_code) та поштову адресу виконавця з індексом (performer_postal_address_and_zip_code)."
        },
        {
            "id": "terms",
            "prompt": "І останнє — умови договору: до якого числа місяця підписується акт, скільки днів на перерахування грошей, та на який строк укладається договір?",
            "fields": ["date_act_signed", "money_transfer_deadline", "contract_validity_period"],
            "extraction_hint": "Витягни: дату підписання акту щомісяця/число місяця (date_act_signed, ціле число 1-30), дедлайн переказу грошей у днях (money_transfer_deadline, ціле число), та строк дії договору (contract_validity_period, текст типу '1 рік' або 'до 31.12.2025')."
        }
    ]
}

def get_field_groups(template_code: str) -> List[Dict]:
    """Повертає групи полів для заданого шаблону"""
    return FIELD_GROUPS.get(template_code, [])

# --- ВИПРАВЛЕННЯ ТУТ ---
# Додаємо аліас, щоб main.py міг викликати get_group_info
def get_group_info(template_code: str) -> List[Dict]:
    return get_field_groups(template_code)

def get_next_group(template_code: str, filled_fields: set) -> Dict | None:
    """
    Повертає наступну групу полів, яку треба заповнити.
    Якщо всі заповнені — повертає None.
    """
    groups = get_field_groups(template_code)

    for group in groups:
        # Перевіряємо, чи є хоч одне незаповнене поле в групі
        if not all(field in filled_fields for field in group["fields"]):
            return group

    return None

def get_all_required_fields(template_code: str) -> List[str]:
    """Повертає список всіх полів для шаблону"""
    groups = get_field_groups(template_code)
    all_fields = []
    for group in groups:
        all_fields.extend(group["fields"])
    return all_fields