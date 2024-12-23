import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from recommendation_system import load_books_data, generate_recommendations, apply_filters, get_all_genres
import pandas as pd
import json

# Загрузка конфигурации
with open('src/config.json', 'r', encoding='utf-8') as config_file:
    CONFIG = json.load(config_file)

# Глобальные переменные
books_df = None
preferences = {}
recommended_books = pd.DataFrame()
genre_vars = {}
read_list = pd.DataFrame(columns=['title', 'authors', 'genres', 'year', 'match_score', 'description'])

def get_user_preferences():
    selected_genres = [genre for genre, var in genre_vars.items() if var.get()]
    prefs = {
        'genres': [genre.lower() for genre in selected_genres],
        'authors': [author.strip().lower() for author in authors_entry.get().split(',') if author.strip()],
        'keywords': [keyword.strip().lower() for keyword in keywords_entry.get().split(',') if keyword.strip()]
    }
    return prefs

def open_genres_window():
    genres_window = tk.Toplevel(root)
    genres_window.title("Выберите жанры")
    genres_window.geometry("300x400")  # Установим размер окна

    search_var = tk.StringVar()
    tk.Label(genres_window, text="Поиск жанра:").pack(anchor='w', padx=10, pady=5)
    search_entry = tk.Entry(genres_window, textvariable=search_var)
    search_entry.pack(fill='x', padx=10)

    canvas = tk.Canvas(genres_window)
    scrollbar = tk.Scrollbar(genres_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)

    all_genres = get_all_genres()
    top_genres_count = CONFIG.get('top_genres_count', 100)
    top_genres = all_genres[:top_genres_count]

    def update_genre_list(*args):
        search_text = search_var.get().lower()
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        for genre in top_genres:
            if search_text in genre:
                var = genre_vars.get(genre, tk.BooleanVar())
                chk = tk.Checkbutton(scrollable_frame, text=genre.title(), variable=var)
                chk.pack(anchor='w')
                genre_vars[genre] = var

    search_var.trace('w', update_genre_list)

    update_genre_list()

def show_recommendations():
    global recommended_books
    global preferences

    preferences = get_user_preferences()
    if not any(preferences.values()):
        messagebox.showwarning("Предупреждение", "Пожалуйста, введите хотя бы одно предпочтение.")
        return

    recommended_books = generate_recommendations(books_df, preferences)

    if recommended_books.empty:
        messagebox.showinfo("Информация", "По вашим предпочтениям ничего не найдено.")
        for item in recommendations_tree.get_children():
            recommendations_tree.delete(item)
        recommendations_tree.insert('', 'end', values=("Нет книг для отображения.",))
        return

    # Применение фильтров
    filters = {}
    if filter_genres_entry.get():
        filters['genres'] = [genre.strip().lower() for genre in filter_genres_entry.get().split(',') if genre.strip()]
    if filter_year_entry.get().isdigit():
        filters['year'] = int(filter_year_entry.get())

    sort_option = sort_var.get()

    filtered_books = apply_filters(recommended_books, filters, sort_option)
    display_books(filtered_books)

def display_books(books):
    for item in recommendations_tree.get_children():
        recommendations_tree.delete(item)

    if books.empty:
        recommendations_tree.insert('', 'end', values=("Нет книг для отображения.",))
        return

    for idx, row in books.iterrows():
        recommendations_tree.insert('', 'end', values=(
            row['title'],
            ", ".join(row['authors']),
            ", ".join(row['genres']),
            row['year'],
            row['match_score'],
            row['description'][:200] + "..."
        ))

def save_recommendations():
    selected_items = recommendations_tree.selection()
    if not selected_items:
        messagebox.showwarning("Предупреждение", "Нет выбранных рекомендаций для сохранения.")
        return

    selected_books = []
    for item in selected_items:
        values = recommendations_tree.item(item, 'values')
        if values[0] == "Нет книг для отображения.":
            continue
        selected_books.append({
            'title': values[0],
            'authors': values[1],
            'genres': values[2],
            'year': values[3],
            'match_score': values[4],
            'description': values[5]
        })

    if not selected_books:
        messagebox.showwarning("Предупреждение", "Нет валидных рекомендаций для сохранения.")
        return

    # Преобразуем список словарей в DataFrame
    selected_books_df = pd.DataFrame(selected_books)

    filetypes = [('CSV файлы', '*.csv'), ('JSON файлы', '*.json')]
    file = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=filetypes, title="Сохранить рекомендации как")
    if file:
        try:
            if file.endswith('.csv'):
                selected_books_df.to_csv(file, index=False)
            elif file.endswith('.json'):
                selected_books_df.to_json(file, orient='records', force_ascii=False)
            messagebox.showinfo("Информация", "Выбранные рекомендации сохранены.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл.\n{e}")

def save_read_list():
    """
    Сохраняет список прочитать в файл.
    """
    if read_list.empty:
        messagebox.showwarning("Предупреждение", "Список прочитать пуст.")
        return

    filetypes = [('CSV файлы', '*.csv'), ('JSON файлы', '*.json')]
    file = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=filetypes, title="Сохранить список прочитать как")
    if file:
        try:
            if file.endswith('.csv'):
                read_list.to_csv(file, index=False)
            elif file.endswith('.json'):
                read_list.to_json(file, orient='records', force_ascii=False)
            messagebox.showinfo("Информация", "Список прочитать сохранён.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл.\n{e}")

def add_to_read_list():
    global read_list  # Объявляем, что будем изменять глобальную переменную read_list
    selected_items = recommendations_tree.selection()
    if not selected_items:
        messagebox.showwarning("Предупреждение", "Нет выбранных рекомендаций для добавления в список прочитать.")
        return

    new_books = []
    for item in selected_items:
        values = recommendations_tree.item(item, 'values')
        if values[0] == "Нет книг для отображения.":
            continue
        new_books.append({
            'title': values[0],
            'authors': values[1],
            'genres': values[2],
            'year': values[3],
            'match_score': values[4],
            'description': values[5]
        })

    if new_books:
        # Используем pd.concat вместо append, так как append устарел
        read_list = pd.concat([read_list, pd.DataFrame(new_books)], ignore_index=True)
        messagebox.showinfo("Информация", "Выбранные книги добавлены в список прочитать.")
    else:
        messagebox.showwarning("Предупреждение", "Нет валидных книг для добавления.")

def show_read_list():
    read_window = tk.Toplevel(root)
    read_window.title("Список прочитать")
    read_window.geometry("800x600")  # Увеличиваем размер окна для удобства

    read_tree = ttk.Treeview(read_window, columns=columns, show='headings', selectmode='none')

    for col in columns:
        read_tree.heading(col, text=col)
        read_tree.column(col, width=150, anchor='w')  # Увеличиваем ширину колонок

    read_tree.pack(fill="both", expand=True)

    for idx, row in read_list.iterrows():
        read_tree.insert('', 'end', values=(
            row['title'],
            row['authors'],
            row['genres'],
            row['year'],
            row['match_score'],
            row['description'][:200] + "..."
        ))

# Инициализация данных
books_df = load_books_data()

# Создание окна приложения
root = tk.Tk()
root.title("Рекомендательная система книг")
root.geometry("1000x700")  # Увеличиваем размер окна для удобства

# Настройка стилей
style = ttk.Style()
style.theme_use('clam')  # Используем современную тему

# Предпочтения пользователя
prefs_frame = tk.LabelFrame(root, text="Предпочтения пользователя", padx=10, pady=10)
prefs_frame.pack(fill="both", expand="yes", padx=10, pady=5)

tk.Label(prefs_frame, text="Любимые жанры:").grid(row=0, column=0, sticky='w', pady=5)
tk.Button(prefs_frame, text="Выбрать жанры", command=open_genres_window).grid(row=0, column=1, padx=5, pady=5, sticky='w')

tk.Label(prefs_frame, text="Любимые авторы:").grid(row=1, column=0, sticky='w', pady=5)
authors_entry = tk.Entry(prefs_frame, width=50)
authors_entry.grid(row=1, column=1, pady=5, padx=5)

tk.Label(prefs_frame, text="Ключевые слова:").grid(row=2, column=0, sticky='w', pady=5)
keywords_entry = tk.Entry(prefs_frame, width=50)
keywords_entry.grid(row=2, column=1, pady=5, padx=5)

# Фильтры и сортировка
filters_frame = tk.LabelFrame(root, text="Фильтры и сортировка", padx=10, pady=10)
filters_frame.pack(fill="both", expand="yes", padx=10, pady=5)

tk.Label(filters_frame, text="Фильтр по жанрам (через запятую):").grid(row=0, column=0, sticky='w', pady=5)
filter_genres_entry = tk.Entry(filters_frame, width=50)
filter_genres_entry.grid(row=0, column=1, pady=5, padx=5)

tk.Label(filters_frame, text="Книги после года:").grid(row=1, column=0, sticky='w', pady=5)
filter_year_entry = tk.Entry(filters_frame, width=10)
filter_year_entry.grid(row=1, column=1, sticky='w', pady=5, padx=5)

tk.Label(filters_frame, text="Сортировка:").grid(row=2, column=0, sticky='w', pady=5)
sort_var = tk.StringVar(value='Рейтинг')
sort_options = ['Рейтинг', 'Алфавит', 'Год']
sort_menu = tk.OptionMenu(filters_frame, sort_var, *sort_options)
sort_menu.grid(row=2, column=1, sticky='w', pady=5, padx=5)

# Кнопки
buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=5)

tk.Button(buttons_frame, text="Показать рекомендации", command=show_recommendations).grid(row=0, column=0, padx=5)
tk.Button(buttons_frame, text="Сохранить рекомендации", command=save_recommendations).grid(row=0, column=1, padx=5)
tk.Button(buttons_frame, text="Добавить в список прочитать", command=add_to_read_list).grid(row=0, column=2, padx=5)
tk.Button(buttons_frame, text="Просмотр списка прочитать", command=show_read_list).grid(row=0, column=3, padx=5)
tk.Button(buttons_frame, text="Сохранить список прочитать", command=save_read_list).grid(row=0, column=4, padx=5)  # Новая кнопка

# Отображение рекомендаций с использованием Treeview
recommendations_frame = tk.LabelFrame(root, text="Рекомендованные книги")
recommendations_frame.pack(fill="both", expand="yes", padx=10, pady=5)

columns = ('Название', 'Авторы', 'Жанры', 'Год', 'Рейтинг', 'Описание')
recommendations_tree = ttk.Treeview(recommendations_frame, columns=columns, show='headings', selectmode='extended')

for col in columns:
    recommendations_tree.heading(col, text=col)
    recommendations_tree.column(col, width=150, anchor='w')  # Увеличиваем ширину колонок

recommendations_tree.pack(fill="both", expand=True)

root.mainloop()
