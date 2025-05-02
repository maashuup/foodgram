import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ingredients из CSV и JSON в базу данных'

    def handle(self, *args, **kwargs):
        self.load_csv()
        self.load_json()
        self.stdout.write(self.style.SUCCESS('Импорт данных завершен.'))

    def load_csv(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.csv'
        )
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'CSV-файл не найден: {file_path}')
            )
            return

        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)

            for row in reader:
                if len(row) != 2:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Пропущена некорректная строка: {row}'
                        )
                    )
                    continue

                name, measurement_unit = row
                name = name.strip()
                measurement_unit = measurement_unit.strip()
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=measurement_unit.strip()
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Добавленный ингредиент: {name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Ингридиент уже есть: {name}')
                    )

    def load_json(self):
        file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.json'
        )
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'JSON-файл не найден: {file_path}')
            )
            return

        with open(file_path, encoding='utf-8') as file:
            ingredients = json.load(file)

        for item in ingredients:
            name = item.get('name')
            measurement_unit = item.get('measurement_unit')

            if not name or not measurement_unit:
                self.stdout.write(
                    self.style.WARNING(
                        f'Пропущен некорректный элемент: {item}'
                    )
                )
                continue

            ingredient, created = Ingredient.objects.get_or_create(
                name=name.strip(),
                measurement_unit=measurement_unit.strip()
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Добавлен: {name}'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'Уже существует: {name}')
                )
