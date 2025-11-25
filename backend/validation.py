from pydantic import BaseModel, Field, AfterValidator, ValidationError, field_validator
from typing_extensions import Annotated
from typing import Dict, Type
import re

# --- 1. М'ЯКІ ВАЛІДАТОРИ (Виправляють, а не сварять) ---

def validate_pib_soft(v: str) -> str:
    """
    М'яка перевірка ПІБ:
    - Автоматично робить перші літери великими.
    - Видаляє зайві пробіли.
    - Вимагає хоча б 2 слова.
    """
    v = v.strip()
    v = re.sub(r'\s+', ' ', v)
    parts = v.split(' ')

    if len(parts) < 2:
        raise ValueError("Введіть Прізвище та Ім'я (мінімум 2 слова).")

    # Авто-виправлення: робимо кожне слово з великої літери
    return v.title()

def validate_city_soft(v: str) -> str:
    """
    М'яка перевірка міста:
    - Автоматично робить першу літеру великою.
    """
    v = v.strip()
    if not v:
        raise ValueError("Вкажіть назву міста.")

    # Авто-виправлення: Перша літера велика, решта як є (щоб не псувати 'смт. Київ')
    if len(v) > 0:
        v = v[0].upper() + v[1:]

    return v

def validate_address_simple(v: str) -> str:
    v = v.strip()
    if len(v) < 3:
        raise ValueError("Адреса занадто коротка.")
    return v

def validate_edrpou_tin_checksum(v: str | int) -> str:
    """ЄДРПОУ (8) або ІПН (10). Тут залишаємо суворість, бо це офіційний код."""
    v = str(v).strip()
    if not v.isdigit():
        raise ValueError('Код має містити тільки цифри.')

    length = len(v)
    if length not in (8, 10):
        raise ValueError(f'Код має містити 8 (ЄДРПОУ) або 10 (ІПН) цифр. Ви ввели: {length}.')
    return v

def validate_iban_simple(v: str) -> str:
    """
    М'яка перевірка IBAN.
    Перевіряємо тільки довжину та 'UA'. Математичну перевірку прибираємо,
    бо користувачі часто помиляються в одній цифрі, а це блокує роботу.
    """
    v = v.replace(" ", "").upper()
    if not v.startswith("UA"):
         raise ValueError('IBAN має починатися з UA.')

    if len(v) != 29:
        raise ValueError(f'IBAN має містити 29 символів. Ви ввели: {len(v)}.')

    return v

def validate_ua_phone(v: str | int) -> str:
    """Авто-форматування телефону"""
    v = str(v).strip()
    # Залишаємо тільки цифри
    digits = re.sub(r'[^\d]', '', v)

    # Логіка авто-доповнення
    if len(digits) == 10 and digits.startswith('0'): # 0991234567
        return '+38' + digits
    elif len(digits) == 12 and digits.startswith('380'): # 380991234567
        return '+' + digits
    elif len(digits) == 9: # 991234567 (без нуля - рідко, але буває)
        return '+380' + digits

    # Якщо після всіх маніпуляцій формат не +380...
    full_format = '+' + digits if not digits.startswith('+') else digits

    if not re.match(r'^\+380\d{9}$', full_format):
         # Не кидаємо помилку, якщо це схоже на правду, просто повертаємо як є,
         # або кидаємо м'яку помилку
         if len(digits) < 10:
             raise ValueError('Номер телефону занадто короткий.')

    return full_format

# --- 2. ТИПИ ДАНИХ (ANNOTATED) ---

SoftPIB = Annotated[str, AfterValidator(validate_pib_soft)]
SoftCity = Annotated[str, AfterValidator(validate_city_soft)]
SimpleAddress = Annotated[str, AfterValidator(validate_address_simple)]
UaPhoneType = Annotated[str, AfterValidator(validate_ua_phone)]
ValidOrganizationCode = Annotated[str, AfterValidator(validate_edrpou_tin_checksum)]
SimpleIban = Annotated[str, AfterValidator(validate_iban_simple)]

# --- 3. СХЕМА ДОГОВОРУ ---

class NadannyaPoslugSchema(BaseModel):
    # Основні поля
    city: SoftCity = Field(description="Місто укладання")
    # Прибрали pattern і validator для лапок. Тепер приймає будь-який текст > 2 символів.
    enterprise: str = Field(min_length=2, description="Назва підприємства")

    # Учасники
    full_name_customer: SoftPIB = Field(description="ПІБ Замовника")
    full_name_performer: SoftPIB = Field(description="ПІБ Виконавця")

    # Контакти
    customer_phone_number: UaPhoneType
    performer_phone_number: UaPhoneType

    # Реквізити
    customer_edrpou: ValidOrganizationCode = Field(alias="customer_unified_state_register_of_organizations")
    performer_edrpou: ValidOrganizationCode = Field(alias="performer_unified_state_register_of_organizations")

    customer_iban: SimpleIban
    performer_iban: SimpleIban

    # Адреси
    customer_postal_address_and_zip_code: SimpleAddress = Field(description="Адреса Замовника")
    performer_postal_address_and_zip_code: SimpleAddress = Field(description="Адреса Виконавця")

    # Умови договору (числа)
    # Зробили Union[int, str], щоб якщо AI поверне "15", воно схавало
    date_act_signed: int | str = Field(description="День підписання акту")
    money_transfer_deadline: int | str = Field(description="Днів на оплату")
    contract_validity_period: str = Field(min_length=1, description="Строк дії договору")

    # Валідатор для чисел, який перетворює "5 днів" -> 5
    @field_validator('date_act_signed', 'money_transfer_deadline', mode='before')
    @classmethod
    def parse_int_flexible(cls, v):
        if isinstance(v, int): return v
        # Якщо прийшов рядок "до 5 числа", витягуємо цифру
        digits = re.findall(r'\d+', str(v))
        if digits:
            return int(digits[0])
        return v

    class Config:
        extra = "ignore"
        populate_by_name = True # Дозволяє використовувати і аліаси, і реальні назви

# --- 4. РЕЄСТР ШАБЛОНІВ ---

TEMPLATE_REGISTRY: Dict[str, Type[BaseModel]] = {
    "nadannya_poslug": NadannyaPoslugSchema,
    "Надання_послуг": NadannyaPoslugSchema,
}

# --- 5. ГОЛОВНА ФУНКЦІЯ ВАЛІДАЦІЇ ---

def validate_session_answers(template_code: str, answers: dict):
    schema_class = TEMPLATE_REGISTRY.get(template_code)
    if not schema_class:
        return True, []

    errors_list = []

    try:
        schema_class(**answers)
        return True, []
    except ValidationError as e:
        for err in e.errors():
            error_field = str(err['loc'][0]) if err['loc'] else None

            # Ігноруємо, якщо поле не заповнювали
            if error_field and error_field not in answers:
                continue

            # Ігноруємо "Field required", якщо поле пусте в даних (але є ключем)
            # Це дозволяє пропускати пусті поля без криків
            if err['type'] == 'missing':
                continue

            msg = err['msg']
            msg = msg.replace("Value error, ", "")
            msg = msg.replace("String should have at least", "Мінімальна довжина:")

            if error_field:
                errors_list.append({"field": error_field, "message": msg})

    if len(errors_list) > 0:
        return False, errors_list

    return True, []