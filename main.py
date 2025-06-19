from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from datetime import datetime
from functools import partial
import smtplib
from email.message import EmailMessage
import json, os
import random




class MainScreen(MDScreen):
    pass

class ReportScreen(MDScreen):
    pass

class FinanceApp(MDApp):
    def populate_tasks_screen(self):
        screen = self.root.get_screen("tasks_screen")
        container = screen.ids.tasks_container
        container.clear_widgets()

        for task in self.tasks:
            card = MDCard(
                orientation="vertical",
                padding="12dp",
                radius=[12],
                size_hint_y=None,
                height="100dp",
            )

            btn = MDRaisedButton(
                text="Завершено" if task["completed"] else "Выполнить",
                disabled=task["completed"],
                pos_hint={"center_x": 0.5},
                on_release=lambda x, task_id=task["id"]: self.complete_task(task_id)
            )

            card.add_widget(MDLabel(text=task["title"], font_style="Body1", halign="left"))
            card.add_widget(MDLabel(text=f"Тип: {task['type']}  |  Награда: {task['reward']}", font_style="Caption", halign="left"))
            card.add_widget(btn)

            container.add_widget(card)

    # Обнови метод complete_task() чтобы вызывать populate_tasks_screen()
    # И добавь переход на tasks_screen из главного экрана
    def build(self):
        self.title = "Финансовое Обучение"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"
        self.progress_file = "data/progress.json"
        self.test_widgets = []  # сюда будем сохранять виджеты с ответами
        self.tasks = []
        self.profile = {"currency": 0, "last_login_date": ""}
        self.users_file = "data/users.json"
        self.temp_user_data = {}
        self.load_users()
        self.load_words()

        self.modules = [
            {"title": "1. Личное финансовое планирование", "desc": "Бюджет и цели", "key": "Планирование"},
            {"title": "2. Депозиты", "desc": "Как копить и сохранять", "key": "Депозиты"},
            {"title": "3. Кредиты", "desc": "Деньги взаймы и проценты", "key": "Кредиты"},
            {"title": "4. Банковские операции", "desc": "Карты, переводы, проценты", "key": "Операции"},
            {"title": "5. Страхование", "desc": "Как защититься от рисков", "key": "Страхование"},
            {"title": "6. Инвестиции", "desc": "Приумножение средств", "key": "Инвестиции"},
            {"title": "7. Пенсии", "desc": "Забота о будущем", "key": "Пенсии"},
            {"title": "8. Налоги", "desc": "Платим государству", "key": "Налоги"},
            {"title": "9. Мошенничество", "desc": "Финансовая безопасность", "key": "Мошенничество"},
        ]

        self.load_progress()
        self.current_module = None
        return Builder.load_file("main.kv")

    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r", encoding="utf-8") as f:
                self.module_progress = json.load(f)
        else:
            self.module_progress = {
                m["key"]: {"progress": 0 if i != 0 else 10, "locked": i != 0}
                for i, m in enumerate(self.modules)
            }
            
            self.save_progress()

    def save_progress(self):
        os.makedirs("data", exist_ok=True)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(self.module_progress, f, ensure_ascii=False, indent=4)

    def on_start(self):
        current_user = self.users_data.get("current_user")
        if current_user and current_user in self.users_data["users"]:
            self.change_screen("main")
        else:
            self.change_screen("login")
        container = self.root.get_screen("main").ids.modules_container
        container.clear_widgets() 
        self.load_tasks()
        self.reset_daily_tasks_if_needed()
        self.populate_tasks_screen()
        
        self.populate_tasks_tab()
        self.update_currency_in_appbar()
        self.load_words()

        for module in self.modules:
            key = module["key"]
            progress = self.module_progress[key]["progress"]
            locked = self.module_progress[key]["locked"]

            card = MDCard(
                radius=[16],
                elevation=1,
                padding=dp(12),
                size_hint_y=None,
                height=dp(120),
                ripple_behavior=True,
                md_bg_color=(0.8, 0.9, 0.8, 1) if locked else (1, 1, 1, 1),
                on_release=lambda x, k=key: self.show_module(k) if not self.module_progress[k]["locked"] else None
            )

            box = MDBoxLayout(orientation="horizontal", spacing=dp(12))
            text_box = MDBoxLayout(orientation="vertical", spacing=dp(4))
            text_box.add_widget(MDLabel(text=module["title"], font_style="H6", theme_text_color="Primary"))
            text_box.add_widget(MDLabel(text=module["desc"], font_style="Caption", theme_text_color="Secondary"))

            progress_value = round(progress)
            bar = MDProgressBar(value=progress_value, color=self.theme_cls.primary_color)
            bar.height = dp(6)
            bar.radius = [8]
            text_box.add_widget(bar)
            text_box.add_widget(MDLabel(text=f"{progress_value}%", font_style="Caption", halign="right"))

            icon = MDIconButton(
                icon="lock" if locked else "check",
                theme_text_color="Hint",
                icon_size="32sp"
            )

            box.add_widget(text_box)
            box.add_widget(icon)
            card.add_widget(box)
            container.add_widget(card)
            

    def show_module(self, module_key):
        self.current_module = module_key
        module_info = next((m for m in self.modules if m["key"] == module_key), None)
        if not module_info:
            print(f"[Ошибка] Модуль не найден: {module_key}")
            return

        screen = self.root.get_screen("module_screen")
        screen.ids.module_title.text = module_info["title"]
        screen.ids.module_desc.text = module_info["desc"]
        self.root.current = "module_screen"

    def go_back(self):
        self.root.current = "main"

    def go_back_module(self):
        self.root.current = "module_screen"

    def start_lesson(self):
        key = self.current_module
        screen = self.root.get_screen("lesson_screen")
        content_box = screen.ids.lesson_content
        content_box.clear_widgets()

        lesson_path = f"data/lessons/{key}.txt"
        if not os.path.exists(lesson_path):
            content_box.add_widget(MDLabel(text="Урок не найден", halign="center"))
            return

        with open(lesson_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        prev_type = None
        for line in lines:
            line = line.strip()
            if not line:
                continue  # пропускаем пустые строки

            # Добавляем отступ между разными типами блоков
            current_type = "text"
            if line.startswith("# "):
                current_type = "h1"
            elif line.startswith("## "):
                current_type = "h2"
            elif line.startswith("- "):
                current_type = "bullet"
            elif line.startswith("![") and "](" in line:
                current_type = "image"

            if prev_type and current_type != prev_type:
                content_box.add_widget(Widget(size_hint_y=None, height=dp(12)))
            prev_type = current_type

            if current_type == "h1":
                content_box.add_widget(MDLabel(
                    text=line[2:], font_style="H6",
                    halign="left", theme_text_color="Primary",
                    size_hint_y=None, height=dp(32)
                ))
            elif current_type == "h2":
                content_box.add_widget(MDLabel(
                    text=line[3:], font_style="Subtitle1",
                    halign="left", theme_text_color="Primary",
                    size_hint_y=None, height=dp(28)
                ))
            elif current_type == "bullet":
                content_box.add_widget(MDLabel(
                    text="• " + line[2:], halign="left",
                    theme_text_color="Secondary",
                    size_hint_y=None, height=dp(24)
                ))
            elif current_type == "image":
                alt = line.split("![")[1].split("]")[0]
                path = line.split("](")[1].split(")")[0]
                if os.path.exists(path):
    
                    img = Image(
                        source=path,
                        size_hint=(1, None),  # ширина 100%, высота фиксированная
                        height=dp(200),
                        allow_stretch=True,
                        keep_ratio=True
                    )
                    content_box.add_widget(img)
                    
                else:
                    content_box.add_widget(MDLabel(
                        text=f"[Изображение не найдено: {alt}]", halign="left"
                    ))
            else:
                content_box.add_widget(MDLabel(
                    text=line,
                    halign="left",
                    theme_text_color="Secondary",
                    text_size=(self.root.width - dp(32), None),
                    size_hint_y=None,
                    height=dp(28)
                ))

        self.root.current = "lesson_screen"
        
    def finish_lesson(self):
        key = self.current_module
        if self.module_progress[key]["progress"] < 100:
            self.module_progress[key]["progress"] = 100
            idx = next((i for i, m in enumerate(self.modules) if m["key"] == key), -1)
            if idx + 1 < len(self.modules):
                next_key = self.modules[idx + 1]["key"]
                self.module_progress[next_key]["locked"] = False
            self.save_progress()
            self.on_start()
        self.root.current = "main"
        
        
    def start_test(self):
        
        key = self.current_module
        test_path = f"data/tests/{key}.json"

        container = self.root.get_screen("test_screen").ids.test_container
        container.clear_widgets()
        self.test_widgets = []

        if not os.path.exists(test_path):
            container.add_widget(MDLabel(text="Тест не найден", halign="center"))
            return

        with open(test_path, "r", encoding="utf-8") as f:
            questions = json.load(f)

        for q_idx, q in enumerate(questions):
            q_widgets = []

            # карточка вопроса
            card = MDCard(
                orientation="vertical",
                padding=dp(12),
                radius=[16],
                size_hint_y=None,
                height=dp(48 + 40 * len(q["options"])),
                md_bg_color=(0.95, 0.97, 0.98, 1),
                elevation=4,
            )

            # Заголовок вопроса
            question_label = MDLabel(
                text=f"{q_idx + 1}. {q['question']}",
                font_style="Subtitle1",
                halign="left",
                theme_text_color="Primary",
                size_hint_y=None,
                height=dp(32)
            )
            card.add_widget(question_label)

            for opt_idx, option in enumerate(q["options"]):
                checkbox = MDCheckbox(
                    size_hint=(None, None),
                    size=("24dp", "24dp"),
                    pos_hint={"center_y": 0.5},
                    group=str(q_idx) if q["type"] == "single" else None
                )

                label = MDLabel(
                    text=option,
                    halign="left",
                    valign="middle",
                    theme_text_color="Secondary"
                )
                label.bind(width=lambda instance, value: setattr(label, 'text_size', (value, None)))

                row = MDBoxLayout(
                    orientation="horizontal",
                    spacing=dp(12),
                    padding=[dp(8), dp(4), dp(8), dp(4)],
                    size_hint_y=None,
                    height=dp(36)
                )
                row.add_widget(checkbox)
                row.add_widget(label)
                card.add_widget(row)
                q_widgets.append(checkbox)

            container.add_widget(card)
            container.add_widget(Widget(size_hint_y=None, height=dp(12)))  # отступ между карточками
            self.test_widgets.append((q["type"], q_widgets, q["correct"]))

        self.root.current = "test_screen"
        
    def check_test(self):
        correct_count = 0
        for q_type, checkboxes, correct_indexes in self.test_widgets:
            selected = [i for i, c in enumerate(checkboxes) if c.active]
            if q_type == "single":
                if selected == correct_indexes:
                    correct_count += 1
            elif q_type == "multiple":
                if set(selected) == set(correct_indexes):
                    correct_count += 1

        total = len(self.test_widgets)
        percent = int(correct_count / total * 100)

        from kivymd.uix.dialog import MDDialog
        if percent >= 70:
            self.module_progress[self.current_module]["progress"] = 100
            idx = next((i for i, m in enumerate(self.modules) if m["key"] == self.current_module), -1)
            if idx + 1 < len(self.modules):
                next_key = self.modules[idx + 1]["key"]
                self.module_progress[next_key]["locked"] = False
            self.save_progress()
            self.on_start()
            dialog = MDDialog(title="Успешно!", text=f"Вы прошли тест на {percent}%. Модуль завершён.")
        else:
            dialog = MDDialog(title="Попробуйте снова", text=f"Результат: {percent}%. Нужно минимум 70%.")

        dialog.open()
        self.root.current = "main"
        self.update_currency_in_appbar()
        
        
    def load_tasks(self):
        try:
            with open("data/tasks.json", "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
        except FileNotFoundError:
            self.tasks = []
            
    def load_profile(self):
        try:
            with open("data/profile.json", "r", encoding="utf-8") as f:
                self.profile = json.load(f)
        except FileNotFoundError:
            self.profile = {"currency": 0, "last_login_date": ""}
            
    

    def reset_daily_tasks_if_needed(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.profile.get("last_login_date") != today:
            for task in self.tasks:
                if task["type"] == "daily":
                    task["completed"] = False
            self.profile["last_login_date"] = today
            self.save_tasks()
            self.save_profile()
            
    def save_tasks(self):
        with open("data/tasks.json", "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def save_profile(self):
        with open("data/profile.json", "w", encoding="utf-8") as f:
            json.dump(self.profile, f, ensure_ascii=False, indent=4)
            
        
            
    def populate_tasks_tab(self):
        screen = self.root.get_screen("main")
        container = screen.ids.tasks_container
        container.clear_widgets()

        for task in self.tasks:
            card = MDCard(
                orientation="vertical",
                padding="12dp",
                radius=[12],
                size_hint_y=None,
                height="110dp"
            )

            card.add_widget(MDLabel(text=task["title"], font_style="Body1", halign="left"))
            card.add_widget(MDLabel(text=f"Тип: {task['type']} | Награда: {task['reward']}", font_style="Caption", halign="left"))

            if not task["completed"]:
                btn = MDRaisedButton(
                    text="Выполнить",
                    pos_hint={"center_x": 0.5},
                    on_release=partial(self.complete_task, task["id"])
                )
                card.add_widget(btn)
            else:
                card.add_widget(MDLabel(text="[Выполнено]", halign="center", theme_text_color="Hint"))

            container.add_widget(card)
            
    def complete_task_from_tab(self, task_id):
        self.complete_task(task_id)
        self.populate_tasks_tab()
        self.update_currency_in_appbar()       
        
    def update_currency_in_appbar(self):
        amount = self.profile.get("currency", 0)
        current_screen = self.root.current

        try:
            screen = self.root.get_screen(current_screen)
            topbar = screen.ids.get("topbar")

            if topbar:
                topbar.right_action_items = [["cash", lambda x: None, f"{amount} кешиков"]]
            else:
                print(f"[!] Не найден topbar на экране '{current_screen}'")

        except Exception as e:
            print(f"[Ошибка обновления кешиков]: {e}")
        
    def add_currency(self, amount):
        self.profile["currency"] += amount
        self.save_users()
        self.update_currency_in_appbar()
    
    def update_currency_display(self):
        try:
            currency_widget = self.root.ids.currency_widget
            currency_label = self.root.ids.currency_amount

            # Скрывать валюту в профиле
            current = self.root.current
            currency_widget.opacity = 0 if current == "profile" else 1
            currency_widget.disabled = current == "profile"

            currency_label.text = str(self.profile.get("currency", 0))
        except Exception as e:
            print("[Ошибка отображения валюты]:", e)
    
    def complete_task(self, task_id, *args):
        try:
            for task in self.tasks:
                if task["id"] == task_id and not task["completed"]:
                    # Проверка модулей
                    if task_id.startswith("module_"):
                        mod_num = int(task_id.split("_")[1])
                        mod_key = self.modules[mod_num - 1]["key"]
                        if self.module_progress[mod_key]["progress"] < 100:
                            self.handle_app_error("Сначала пройдите модуль!")
                            return

                    if task["id"] == "daily_game":
                        self.handle_app_error("Игры пока нет в приложении!")
                        return

                    task["completed"] = True
                    self.profile["currency"] += task["reward"]
                    self.save_tasks()
                    self.save_profile()
                    self.update_currency_display()
                    break

            if self.root.current == "main":
                self.populate_tasks_tab()
            elif self.root.current == "tasks_screen":
                self.populate_tasks_screen()

        except Exception as e:
            self.handle_app_error(f"Ошибка при выполнении задания: {e}")

    def handle_app_error(self, message):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        print(f"[ОШИБКА] {message}")
        dialog = MDDialog(
            title="Ошибка",
            text=message,
            buttons=[MDFlatButton(text="ОК", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()
        
    def change_screen(self, screen_name):
        self.root.current = screen_name

    def show_error(self, message):
        dialog = MDDialog(
            title="Ошибка",
            text=message,
            buttons=[MDFlatButton(text="ОК", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def load_users(self):
        if os.path.exists(self.users_file):
            with open(self.users_file, "r", encoding="utf-8") as f:
                self.users_data = json.load(f)
        else:
            self.users_data = {"users": {}, "current_user": None}

    def save_users(self):
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(self.users_data, f, ensure_ascii=False, indent=4)

    def login(self, username, password):
        user = self.users_data["users"].get(username)
        if not user or user["password"] != password:
            self.show_error("Неверный логин или пароль")
            return
        self.users_data["current_user"] = username
        self.save_users()
        self.change_screen("main")

    def register_step1(self, username, password, confirm):
        if not username or not password:
            self.show_error("Заполните все поля")
            return
        if username in self.users_data["users"]:
            self.show_error("Пользователь уже существует")
            return
        if password != confirm:
            self.show_error("Пароли не совпадают")
            return
        self.temp_user_data = {"username": username, "password": password}
        self.change_screen("register_step2")

    def register_step2(self, last, first, middle, age):
        if not all([last, first, age]):
            self.show_error("Введите ФИО и возраст")
            return
        self.temp_user_data.update({
            "last_name": last,
            "first_name": first,
            "middle_name": middle,
            "age": int(age)
        })
        self.change_screen("register_step3")

    def register_finish(self, school, grade):
        if not school or not grade:
            self.show_error("Введите школу и класс")
            return

        self.temp_user_data.update({
            "school": school,
            "grade": grade,
            "currency": 0,
        })

        username = self.temp_user_data["username"]
        user_data = self.temp_user_data.copy()
        del user_data["username"]

        self.users_data["users"][username] = user_data
        self.users_data["current_user"] = username
        self.save_users()
        self.change_screen("main")

    def show_profile_tab(self):
        user = self.users_data["users"].get(self.users_data["current_user"])
        if not user:
            return

        try:
            screen = self.root.get_screen("main")
            ids = screen.ids

            ids.profile_name.text = f"{user.get('first_name', '')} {user.get('last_name', '')}"
            ids.profile_currency.text = f"Баланс: {self.profile.get('currency', 0)} кешиков"

            total_modules = 9
            completed = sum(1 for m in self.module_progress.values() if m["progress"] >= 100)
            percent = round(completed / total_modules * 100)
            ids.profile_progress.text = f"Прогресс: {percent}%"
        except Exception as e:
            print("[Профиль] Ошибка отображения:", e)

    def logout(self):
        self.users_data["current_user"] = None
        self.save_users()
        self.change_screen("login")

    def edit_profile(self):
        user = self.users_data["users"].get(self.users_data["current_user"])
        if not user:
            return

        screen = self.root.get_screen("edit_profile")

        screen.ids.first_name.text = user.get("first_name", "")
        screen.ids.last_name.text = user.get("last_name", "")
        screen.ids.middle_name.text = user.get("middle_name", "")
        screen.ids.school.text = user.get("school", "")
        screen.ids.grade.text = user.get("grade", "")
        screen.ids.age.text = str(user.get("age", ""))

        self.root.current = "edit_profile"
        
    def save_profile_changes(self):
        screen = self.root.get_screen("edit_profile")
        user_id = self.users_data["current_user"]
        user = self.users_data["users"].get(user_id)

        if not user:
            return

        user["first_name"] = screen.ids.first_name.text
        user["last_name"] = screen.ids.last_name.text
        user["middle_name"] = screen.ids.middle_name.text
        user["school"] = screen.ids.school.text
        user["grade"] = screen.ids.grade.text
        user["age"] = int(screen.ids.age.text) if screen.ids.age.text.isdigit() else user.get("age", 0)

        self.save_users()  # функция должна сохранять users_data в файл

        self.root.current = "main"
        self.show_profile_tab()

    def generate_report(self):
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                users_data = json.load(f)

            current_user = users_data.get("current_user")
            user_info = users_data.get("users", {}).get(current_user)

            if not user_info:
                self.show_dialog("Ошибка", "Пользователь не найден.")
                return

            # Загружаем прогресс
            progress_data = {}
            progress_path = f"data/progress.json"
            if os.path.exists(progress_path):
                with open(progress_path, "r", encoding="utf-8") as pf:
                    progress_data = json.load(pf)

            report = f"""[ОТЧЁТ ПО ПОЛЬЗОВАТЕЛЮ]

    👤 ФИО: {user_info.get('last_name', '')} {user_info.get('first_name', '')} {user_info.get('middle_name', '')}
    🎂 Возраст: {user_info.get('age', '—')}
    🏫 Школа: {user_info.get('school', '—')}
    📚 Класс: {user_info.get('grade', '—')}
    💰 Кешики: {user_info.get('currency', 0)}

    📈 Прогресс:
    """
            for module, progress in progress_data.items():
                report += f" - {module}: {progress.get('progress', 0)}%\n"

            # ✅ ПЕРЕДАЁМ ОБА ПАРАМЕТРА
            to_email = self.root.get_screen("report").ids.email_field.text.strip()
            self.send_email_with_report(to_email, report)

        except Exception as e:
            print("[Ошибка генерации отчёта]:", e)
            self.show_dialog("Ошибка", "Не удалось создать или отправить отчёт.")


        
    
    
    
        
    def show_dialog(self, title, text):
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(text="Ок", on_release=lambda x: self.dialog.dismiss())
            ],
        )
        self.dialog.open()
        
            
    def load_profile(self, username):
        user_file = f"data/users/{username}.json"
        if os.path.exists(user_file):
            with open(user_file, "r", encoding="utf-8") as f:
                self.profile = json.load(f)
            return True
        if "username" in self.profile:
            self.load_profile(self.profile["username"])
        else:
            return False
        
    def send_email_with_report(self, to_email, report_text):
        try:
            # Настройка письма
            msg = EmailMessage()
            msg["Subject"] = "Ваш отчёт из приложения Финансовый Топ"
            msg["From"] = "funny2006a@gmail.com"  
            msg["To"] = to_email
            msg.set_content(report_text)

            # SMTP-сервер Gmail
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            your_email = "funny2006a@gmail.com"  
            app_password = "hrif fbjy xsmg fojx"  # Пароль приложения, НЕ обычный пароль!

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(your_email, app_password)
                server.send_message(msg)

            self.show_dialog("Успех", f"Отчёт отправлен на {to_email}.")

        except Exception as e:
            print("[SMTP ошибка]:", e)
            self.show_dialog("Ошибка", "Не удалось отправить отчёт на email.")    

    
    def start_game(self, game_id):
        if game_id == "guess_word":
            self.reset_guess_game()
            self.root.current = "guess_word"

    def reset_guess_game(self):
        self.target_word = random.choice(self.words)  # ❗ или выбери случайно из списка
        self.attempts = []
        self.max_attempts = 6
        screen = self.root.get_screen("guess_word")
        screen.ids.guess_input.text = ""
        screen.ids.guess_output.clear_widgets()

    def submit_guess(self):
        screen = self.root.get_screen("guess_word")
        guess = screen.ids.guess_input.text.strip().lower()

        if len(guess) != 5:
            self.show_dialog("Ошибка", "Введите корректное слово из 5 букв.")
            return

        self.attempts.append(guess)
        self.display_guess_result(guess)
        screen.ids.guess_input.text = ""

        if guess == self.target_word:
            self.add_currency(20)
            self.show_confirm_restart("🎉 Победа", "Вы угадали слово! Хотите сыграть ещё?")
        elif len(self.attempts) >= self.max_attempts:
            self.show_confirm_restart("😢 Проигрыш", f"Вы не угадали. Слово было: {self.target_word}. Сыграем ещё?")

    def display_guess_result(self, guess):
        target = self.target_word
        layout = MDBoxLayout(spacing="4dp", size_hint_y=None, height="40dp")

        for i, letter in enumerate(guess):
            color = (0.3, 0.3, 0.3, 1)  # ⬛ по умолчанию

            if letter == target[i]:
                color = (0, 0.7, 0, 1)  # 🟩
            elif letter in target:
                color = (0.9, 0.7, 0, 1)  # 🟨

            box = MDCard(
                size_hint=(None, None),
                size=("40dp", "40dp"),
                md_bg_color=color,
                radius=[6],
            )
            box.add_widget(MDLabel(text=letter.upper(), halign="center", valign="middle"))
            layout.add_widget(box)

        screen = self.root.get_screen("guess_word")
        screen.ids.guess_output.add_widget(layout)
        
        
    def load_words(self):
        try:
            with open("data/words_5.txt", "r", encoding="utf-8") as f:
                self.words = [line.strip().lower() for line in f if len(line.strip()) == 5]
        except Exception as e:
            print("[Ошибка загрузки слов]:", e)
            self.words = ["налог"]  # запасной вариант
            
            
    def show_confirm_restart(self, title, message):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(text="Нет", on_release=lambda x: self.end_game()),
                MDFlatButton(text="Да", on_release=lambda x: self.restart_guess_game()),
            ],
        )
        self.dialog.open()
        
    def restart_guess_game(self):
        if self.dialog:
            self.dialog.dismiss()
        self.reset_guess_game()
        
    def end_game(self):
        if self.dialog:
            self.dialog.dismiss()
        self.root.current = "main"
        
    def add_currency(self, amount):
        self.profile["currency"] = self.profile.get("currency", 0) + amount
        self.save_profile()

    
if __name__ == "__main__":
    FinanceApp().run()
