from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count

from .models import Subscriptions, Tag, Ingredient, Recipe, Favorite
from .models import RecipeIngredient, RecipeTag, ShoppingCart

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DefaultUserAdmin):
    list_display = ('email', 'username')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author',)
    list_filter = ('author', 'name', 'tags')
    search_fields = ('name',)
    readonly_fields = ('favorite_count',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(favorite_count=Count('users_who_favorited'))

    def favorite_count(self, obj):
        return obj.favorite_count
    favorite_count.short_description = 'Число добавлений в избранное'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)


admin.site.register(Subscriptions)
admin.site.register(Tag)
admin.site.register(Favorite)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeTag)
admin.site.register(ShoppingCart)
