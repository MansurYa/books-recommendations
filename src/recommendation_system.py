import pandas as pd
import json
import re
import os


with open('src/config.json', 'r', encoding='utf-8') as config_file:
    CONFIG = json.load(config_file)


def load_books_data():
    """
    Загружает данные о книгах из CSV файла.

    :return: DataFrame с данными о книгах.
    """
    df = pd.read_csv(CONFIG['books_data_file'])

    df = df[['Title', 'authors', 'categories', 'description', 'publishedDate']]

    df.rename(columns={
        'Title': 'title',
        'authors': 'authors',
        'categories': 'genres',
        'description': 'description',
        'publishedDate': 'year'
    }, inplace=True)

    df['authors'] = df['authors'].apply(process_authors)
    df['genres'] = df['genres'].apply(process_genres)
    df['year'] = df['year'].apply(process_year)
    df['description'] = df['description'].fillna('')

    genres_file = CONFIG.get('genres_file', 'genres_list.json')
    if not os.path.exists(genres_file):
        prepare_genres_list(df)

    return df


def process_authors(authors_str):
    """
    Преобразует строку авторов в список.

    :param authors_str: Строка с авторами.
    :return: Список авторов.
    """
    if pd.isna(authors_str):
        return []
    authors_list = eval(authors_str)
    return [author.strip().lower() for author in authors_list]


def process_genres(genres_str):
    """
    Обрабатывает жанры, разделяя их по символу '&' и формируя список отдельных жанров.

    :param genres_str: Строка с жанрами.
    :return: Список отдельных жанров.
    """
    if pd.isna(genres_str):
        return []

    # Добавим отладочное сообщение
    # print(f"Обработка жанров: {genres_str}")

    # Предполагаем, что genres_str - это строка, содержащая жанры, разделенные '&'
    genres = [genre.strip().lower() for genre in genres_str.split('&')]

    # Еще одно отладочное сообщение
    # print(f"Результат обработки: {genres}")

    return genres


# def process_genres(genres_list):
#     """
#     Обрабатывает жанры, разделяя их по символам '&' и ', ' и формируя список отдельных жанров.
#
#     :param genres_list: Список, содержащий строки с жанрами.
#     :return: Список отдельных жанров.
#     """
#     result = []
#     if isinstance(genres_list, list):
#         for genre_str in genres_list:
#             if isinstance(genre_str, str):
#                 # Разбиваем строку жанров по '&' и ','
#                 genres_split = re.split(r'[\&,]', genre_str)
#                 genres = [g.strip().lower() for g in genres_split]
#                 result.extend(genres)
#     return result


def process_year(year):
    """
    Преобразует дату публикации в год.

    :param year: Дата публикации.
    :return: Год публикации в виде числа.
    """
    if pd.isna(year):
        return 0
    if isinstance(year, str) and len(year) >= 4 and year[:4].isdigit():
        return int(year[:4])
    elif isinstance(year, int):
        return year
    return 0


def calculate_match_score(book, preferences):
    """
    Вычисляет рейтинг соответствия книги предпочтениям пользователя.

    :param book: Запись о книге.
    :param preferences: Предпочтения пользователя.
    :return: Рейтинг соответствия.
    """
    score = 0

    if any(genre in preferences['genres'] for genre in book['genres']):
        score += 3

    if any(author in preferences['authors'] for author in book['authors']):  # Исправлено
        score += 5

    if book['description']:
        description = book['description'].lower()
        matches = sum(1 for keyword in preferences['keywords'] if keyword in description)
        score += matches * 2

    return score


def generate_recommendations(books_df, preferences):
    """
    Генерирует список рекомендаций с рейтингами соответствия.

    :param books_df: DataFrame с данными о книгах.
    :param preferences: Предпочтения пользователя.
    :return: DataFrame с рекомендациями.
    """
    def calculate_score(row):
        return calculate_match_score(row, preferences)

    books_df['match_score'] = books_df.apply(calculate_score, axis=1)
    recommended_books = books_df[books_df['match_score'] > 0]
    return recommended_books.sort_values(by='match_score', ascending=False)


def apply_filters(books_df, filters, sort_option):
    """
    Применяет фильтры и сортировку к списку книг.

    :param books_df: DataFrame с книгами.
    :param filters: Словарь с фильтрами.
    :param sort_option: Параметр сортировки.
    :return: Отфильтрованный и отсортированный DataFrame.
    """
    if filters.get('genres'):
        genres_list = filters['genres']
        books_df = books_df[books_df['genres'].apply(lambda g: any(genre in g for genre in genres_list))]

    if filters.get('year'):
        books_df = books_df[books_df['year'] >= filters['year']]

    if sort_option == 'Рейтинг':
        books_df = books_df.sort_values(by='match_score', ascending=False)
    elif sort_option == 'Алфавит':
        books_df = books_df.sort_values(by='title')
    elif sort_option == 'Год':
        books_df = books_df.sort_values(by='year', ascending=False)

    return books_df


def prepare_genres_list(books_df):
    """
    Подготавливает список жанров с указанием частоты и сохраняет в файл.

    :param books_df: DataFrame с данными о книгах.
    :return: None
    """
    genres_count = {}
    for genres in books_df['genres']:
        for genre in genres:
            if genre:
                genres_count[genre] = genres_count.get(genre, 0) + 1

    sorted_genres = sorted(genres_count.items(), key=lambda x: x[1], reverse=True)

    sorted_genres_list = [genre for genre, count in sorted_genres]

    genres_file = CONFIG.get('genres_file', 'genres_list.json')
    with open(genres_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_genres_list, f, ensure_ascii=False, indent=4)


def get_all_genres():
    """
    Загружает список жанров из файла.

    :return: Список жанров.
    """
    genres_file = CONFIG.get('genres_file', 'genres_list.json')
    if os.path.exists(genres_file):
        with open(genres_file, 'r', encoding='utf-8') as f:
            genres_list = json.load(f)
        return genres_list
    else:
        return []


def get_all_authors(books_df):
    """
    Возвращает отсортированный список всех уникальных авторов.

    :param books_df: DataFrame с данными о книгах.
    :return: Список уникальных авторов.
    """
    authors_set = set()
    for authors in books_df['authors']:
        authors_set.update(authors)
    return sorted(authors_set)


def get_possible_preferences():

    books_df = load_books_data()

    all_genres = get_all_genres(books_df)
    all_authors = get_all_authors(books_df)

    print("Доступные жанры:")
    print(", ".join(all_genres))

    # print("\nДоступные авторы:")
    # print(", ".join(all_authors))


if __name__ == "__main__":
    get_possible_preferences()
