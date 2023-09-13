from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Subscriptions(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
        related_name='user'
    )
    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='subscriber'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['id']


class Ingredient(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название'
        )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='Единицы измерения'
        )

    def __str__(self):
        return self.name[:15]

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'


class Tag(models.Model):
    name = models.CharField(
        max_length=256,
        unique=True,
        verbose_name='Название'
        )
    color = models.CharField(
        max_length=16,
        verbose_name='Цвет'
        )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Slug')

    def __str__(self):
        return self.name[:15]

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['name']


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
        )
    image = models.ImageField(
        upload_to='media/',
        null=True,
        blank=True,
        verbose_name='Изображение'
        )
    text = models.TextField(
        verbose_name='Текст'
        )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингридиенты'
        )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',
        verbose_name='Тэг'
        )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления'
        )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )

    def __str__(self) -> str:
        return self.name[:15]

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
        )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингридиент'
        )
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
        )

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name} - {self.amount}'

    class Meta:
        verbose_name = 'Рецепт-Ингридиент'
        verbose_name_plural = 'Рецепты-Ингридиенты'


class RecipeTag(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тэг'
        )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
        )

    def __str__(self):
        return f'{self.recipe.name} {self.tag} '

    class Meta:
        verbose_name = 'Рецепт-Тэг'
        verbose_name_plural = 'Рецепты-Тэги'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='users_who_favorited'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='shipping_cart_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart_users'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзина'
