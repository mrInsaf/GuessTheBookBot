import os
import re

# Настрой: путь к папке с .txt файлами
folder_path = '.'  # Текущая папка. Измени на нужный путь, например: 'C:/мои_тексты'

# Регулярное выражение для поиска концов предложений
sentence_endings = re.compile(r'[.!?]+')


def count_sentences(text):
    # Находим все концы предложений
    matches = sentence_endings.findall(text)
    return len(matches)


# Обработка всех .txt файлов в папке
for filename in os.listdir(folder_path):
    if filename.lower().endswith('.txt'):
        filepath = os.path.join(folder_path, filename)

        try:
            # Читаем файл с кодировкой UTF-8
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

            # Считаем предложения
            num_sentences = count_sentences(content)

            # Формируем новое содержимое
            new_content = f"Предложений: {num_sentences}\n\n{content}"

            # Перезаписываем файл
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(new_content)

            print(f"Обработано: {filename} — {num_sentences} предложений")

        except Exception as e:
            print(f"Ошибка при обработке {filename}: {e}")