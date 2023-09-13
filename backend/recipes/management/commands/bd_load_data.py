import pandas as pd
import os

from django.core.management import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        csv_file = os.path.join(settings.BASE_DIR, 'data', 'ingredients.csv')
        data = pd.read_csv(csv_file,
                           header=None,
                           names=['name', 'measurement_unit'])
        row_iter = data.iterrows()
        ingredients = [
            Ingredient(
                id=index + 1,
                name=row["name"],
                measurement_unit=row["measurement_unit"],
            )
            for index, row in row_iter
        ]
        Ingredient.objects.bulk_create(ingredients,)
