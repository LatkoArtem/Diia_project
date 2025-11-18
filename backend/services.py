from docx import Document
import os

def generate_contract_docx(template_path: str, answers: dict, output_path: str):
    """
    Бере шаблон, замінює {{KEY}} на values і зберігає.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    doc = Document(template_path)

    # 1. Проходимо по параграфах
    for para in doc.paragraphs:
        replace_text_in_paragraph(para, answers)

    # 2. Проходимо по таблицях (важливо для реквізитів)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    replace_text_in_paragraph(para, answers)

    doc.save(output_path)
    return output_path

def replace_text_in_paragraph(paragraph, answers):
    """Замінює ключі у тексті параграфа"""
    for key, value in answers.items():
        placeholder = f"{{{{{key}}}}}"  # Шукаємо {{KEY}}
        if placeholder in paragraph.text:
            # Проста заміна (може збити форматування, якщо ключ розбитий на run-и)
            # Для MVP цього достатньо. Для PRO версії треба складніший алгоритм.
            paragraph.text = paragraph.text.replace(placeholder, str(value))