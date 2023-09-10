import pandas as pd

from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        data = pd.read_csv('../../data/ingredients.csv', 
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
