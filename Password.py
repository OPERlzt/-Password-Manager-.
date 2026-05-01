import json
import os
import random
import string
from datetime import datetime
from abc import ABC, abstractmethod


# --- MODELS (Модели данных и логика хранения) ---

class PasswordRecord:
    def __init__(self, service: str, username: str, password: str):
        self.service = service
        self.username = username
        self.password = password
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "service": self.service,
            "username": self.username,
            "password": self.password,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict):
        record = cls(data['service'], data['username'], data['password'])
        record.created_at = data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return record


class StorageBackend(ABC):
    @abstractmethod
    def save(self, records: list[PasswordRecord]):
        pass

    @abstractmethod
    def load(self) -> list[PasswordRecord]:
        pass


class JsonStorageBackend(StorageBackend):
    def __init__(self, filename: str = 'passwords.json'):
        self._filename = filename

    def save(self, records: list[PasswordRecord]):
        with open(self._filename, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in records], f, indent=4, ensure_ascii=False)

    def load(self) -> list[PasswordRecord]:
        if not os.path.exists(self._filename):
            return []
        try:
            with open(self._filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [PasswordRecord.from_dict(d) for d in data]
        except (json.JSONDecodeError, KeyError):
            return []


# --- VIEWS (Представление - интерфейс) ---

class ConsoleView:
    @staticmethod
    def show_menu():
        print("\n=== Password Manager ===")
        print("1. Добавить пароль")
        print("2. Просмотреть пароли")
        print("3. Удалить пароль")
        print("4. Сгенерировать случайный пароль")
        print("5. Выход")
        return input("Выберите действие: ")

    @staticmethod
    def get_input(prompt: str) -> str:
        return input(prompt)

    @staticmethod
    def show_message(msg: str, is_error: bool = False):
        prefix = "[ОШИБКА]" if is_error else "[ИНФО]"
        print(f"{prefix} {msg}")

    @staticmethod
    def display_records(records):
        if not records:
            print("\nСписок паролей пуст.")
            return

        print("\n--- Сохраненные пароли ---")
        for idx, r in enumerate(records, 1):
            print(f"{idx}. Сервис: {r.service} | Логин: {r.username} | Пароль: {r.password} | Создан: {r.created_at}")
        print("--------------------------")


# --- CONTROLLERS (Контроллер - связующая логика) ---

class PasswordManagerController:
    def __init__(self, storage: StorageBackend, view: ConsoleView):
        self._storage = storage
        self._view = view
        self._records = self._storage.load()

    def run(self):
        while True:
            choice = self._view.show_menu()
            if choice == '1':
                self.add_record()
            elif choice == '2':
                self._view.display_records(self._records)
            elif choice == '3':
                self.delete_record()
            elif choice == '4':
                self.generate_password()
            elif choice == '5':
                self._view.show_message("Выход из программы. Данные сохранены.")
                break
            else:
                self._view.show_message("Неверный выбор. Попробуйте снова.", is_error=True)

    def add_record(self):
        service = self._view.get_input("Введите название сервиса: ").strip()
        username = self._view.get_input("Введите логин: ").strip()
        password = self._view.get_input("Введите пароль: ").strip()

        if not service or not username or not password:
            self._view.show_message("Все поля должны быть заполнены!", is_error=True)
            return

        record = PasswordRecord(service, username, password)
        self._records.append(record)
        self._storage.save(self._records)
        self._view.show_message("Запись успешно добавлена!")

    def delete_record(self):
        self._view.display_records(self._records)
        if not self._records:
            return

        try:
            idx = int(self._view.get_input("Введите номер записи для удаления: ")) - 1
            if 0 <= idx < len(self._records):
                deleted = self._records.pop(idx)
                self._storage.save(self._records)
                self._view.show_message(f"Запись для сервиса '{deleted.service}' удалена.")
            else:
                self._view.show_message("Неверный номер записи.", is_error=True)
        except ValueError:
            self._view.show_message("Пожалуйста, введите число.", is_error=True)

    def generate_password(self):
        try:
            length_str = self._view.get_input("Введите длину пароля (по умолчанию 12): ")
            length = int(length_str) if length_str.strip() else 12

            if length <= 0:
                raise ValueError("Длина должна быть положительной.")

            use_special = self._view.get_input("Использовать спецсимволы? (y/n, по умолчанию y): ").lower() != 'n'

            chars = string.ascii_letters + string.digits
            if use_special:
                chars += string.punctuation

            password = ''.join(random.choice(chars) for _ in range(length))
            self._view.show_message(f"Сгенерированный пароль: {password}")

        except ValueError as e:
            self._view.show_message(f"Ошибка ввода: {e}", is_error=True)


# --- ТОЧКА ВХОДА ---

if __name__ == "__main__":
    # Инициализация хранилища, интерфейса и контроллера
    storage = JsonStorageBackend('passwords.json')
    view = ConsoleView()
    app = PasswordManagerController(storage, view)

    # Запуск приложения
    app.run()