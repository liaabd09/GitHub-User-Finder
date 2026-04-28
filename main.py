import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Файл для избранных
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()

        # Создание интерфейса
        self.create_widgets()

        # Загрузка избранных при старте
        self.update_favorites_list()

    def create_widgets(self):
        # Верхняя панель поиска
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="Введите имя пользователя GitHub:").pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self.search_users())

        ttk.Button(search_frame, text="Поиск", command=self.search_users).pack(side=tk.LEFT, padx=(0, 10))

        # Панель вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Вкладка результатов поиска
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Результаты поиска")

        # Таблица результатов
        columns = ("username", "user_id", "repos", "followers", "url")
        self.search_tree = ttk.Treeview(self.search_tab, columns=columns, show="headings", height=15)

        self.search_tree.heading("username", text="Имя пользователя")
        self.search_tree.heading("user_id", text="ID")
        self.search_tree.heading("repos", text="Репозитории")
        self.search_tree.heading("followers", text="Подписчики")
        self.search_tree.heading("url", text="URL профиля")

        self.search_tree.column("username", width=150)
        self.search_tree.column("user_id", width=80)
        self.search_tree.column("repos", width=100)
        self.search_tree.column("followers", width=100)
        self.search_tree.column("url", width=250)

        scrollbar = ttk.Scrollbar(self.search_tab, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)

        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Контекстное меню для добавления в избранное
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Добавить в избранное", command=self.add_to_favorites_from_search)
        self.search_tree.bind("<Button-3>", self.show_context_menu)

        # Вкладка избранного
        self.favorites_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.favorites_tab, text="Избранное")

        columns_fav = ("username", "user_id", "repos", "followers", "added_date")
        self.favorites_tree = ttk.Treeview(self.favorites_tab, columns=columns_fav, show="headings", height=15)

        self.favorites_tree.heading("username", text="Имя пользователя")
        self.favorites_tree.heading("user_id", text="ID")
        self.favorites_tree.heading("repos", text="Репозитории")
        self.favorites_tree.heading("followers", text="Подписчики")
        self.favorites_tree.heading("added_date", text="Дата добавления")

        self.favorites_tree.column("username", width=150)
        self.favorites_tree.column("user_id", width=80)
        self.favorites_tree.column("repos", width=100)
        self.favorites_tree.column("followers", width=100)
        self.favorites_tree.column("added_date", width=150)

        scrollbar_fav = ttk.Scrollbar(self.favorites_tab, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        self.favorites_tree.configure(yscrollcommand=scrollbar_fav.set)

        self.favorites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_fav.pack(side=tk.RIGHT, fill=tk.Y)

        # Контекстное меню для удаления из избранного
        self.context_menu_fav = tk.Menu(self.root, tearoff=0)
        self.context_menu_fav.add_command(label="Удалить из избранного", command=self.remove_from_favorites)
        self.favorites_tree.bind("<Button-3>", self.show_context_menu_fav)

        # Кнопка обновления избранного
        ttk.Button(self.favorites_tab, text="Обновить список", command=self.update_favorites_list).pack(pady=5)

    def search_users(self):
        username = self.search_entry.get().strip()

        # Проверка на пустое поле
        if not username:
            messagebox.showwarning("Ошибка", "Поле поиска не может быть пустым!")
            return

        # Очистка предыдущих результатов
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        try:
            # Поиск пользователей через GitHub API
            url = f"https://api.github.com/search/users?q={username}&per_page=20"
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            users = data.get("items", [])

            if not users:
                messagebox.showinfo("Результат", "Пользователи не найдены")
                return

            # Загрузка дополнительной информации о каждом пользователе
            for user in users:
                user_url = user["url"]
                user_response = requests.get(user_url)
                user_response.raise_for_status()
                user_data = user_response.json()

                self.search_tree.insert("", tk.END, values=(
                    user_data.get("login", "N/A"),
                    user_data.get("id", "N/A"),
                    user_data.get("public_repos", 0),
                    user_data.get("followers", 0),
                    user_data.get("html_url", "N/A")
                ), tags=(user_data.get("login", ""),))

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить запрос к API:\n{str(e)}")

    def show_context_menu(self, event):
        item = self.search_tree.identify_row(event.y)
        if item:
            self.search_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def add_to_favorites_from_search(self):
        selected = self.search_tree.selection()
        if not selected:
            return

        item = selected[0]
        values = self.search_tree.item(item, "values")
        username = values[0]

        # Проверка, не добавлен ли уже пользователь
        if username in self.favorites:
            messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном")
            return

        # Получение полной информации о пользователе
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url)
            response.raise_for_status()
            user_data = response.json()

            fav_data = {
                "username": user_data.get("login"),
                "user_id": user_data.get("id"),
                "repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
                "added_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            self.favorites[username] = fav_data
            self.save_favorites()
            self.update_favorites_list()
            messagebox.showinfo("Успех", f"Пользователь {username} добавлен в избранное")

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Не удалось получить данные пользователя:\n{str(e)}")

    def update_favorites_list(self):
        # Очистка списка избранного
        for item in self.favorites_tree.get_children():
            self.favorites_tree.delete(item)

        # Заполнение списка избранного
        for username, data in self.favorites.items():
            self.favorites_tree.insert("", tk.END, values=(
                data.get("username", "N/A"),
                data.get("user_id", "N/A"),
                data.get("repos", 0),
                data.get("followers", 0),
                data.get("added_date", "N/A")
            ))

    def show_context_menu_fav(self, event):
        item = self.favorites_tree.identify_row(event.y)
        if item:
            self.favorites_tree.selection_set(item)
            self.context_menu_fav.post(event.x_root, event.y_root)

    def remove_from_favorites(self):
        selected = self.favorites_tree.selection()
        if not selected:
            return

        item = selected[0]
        values = self.favorites_tree.item(item, "values")
        username = values[0]

        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {username} из избранного?"):
            del self.favorites[username]
            self.save_favorites()
            self.update_favorites_list()
            messagebox.showinfo("Успех", f"Пользователь {username} удалён из избранного")

    def load_favorites(self):
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_favorites(self):
        with open(self.favorites_file, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()