from django_filters import rest_framework as filters
from django.contrib.auth.models import AnonymousUser
from recipes.models import Recipe

class RecipeFilter(filters.FilterSet):
    tags = filters.CharFilter(field_name='tags__slug', method='filter_tags')
    is_favorited = filters.BooleanFilter(field_name='users_who_favorited__user', method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(field_name='shopping_cart_users__user', method='filter_in_shopping_cart')
    author = filters.NumberFilter(field_name='author__id')

    def filter_tags(self, queryset, name, value):
        tags = self.request.GET.getlist('tags')
        return queryset.filter(tags__slug__in=tags)

    def filter_favorited(self, queryset, name, value):
        if not isinstance(self.request.user, AnonymousUser):
            if value:
                return queryset.filter(users_who_favorited__user=self.request.user)
            else:
                return queryset.exclude(users_who_favorited__user=self.request.user)
        else:
            return queryset

    def filter_in_shopping_cart(self, queryset, name, value):
        if not isinstance(self.request.user, AnonymousUser):
            if value:
                return queryset.filter(shopping_cart_users__user=self.request.user)
            else:
                return queryset.exclude(shopping_cart_users__user=self.request.user)
        else:
            return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'is_favorited', 'is_in_shopping_cart', 'author']