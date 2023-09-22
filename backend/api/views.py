from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse


from recipes.models import Tag, Ingredient
from recipes.models import Recipe, Favorite, ShoppingCart
from .serializers import TagSerializer
from .serializers import RecipeSerializer, IngredientSerializer
from .serializers import FavoriteSerializer
from .serializers import ShoppingCartSerializer
from .permissions import IsOwnerOrReadOnly
from .permissions import IsAdminUserOrReadOnly
from .paginations import CustomPagination
from .filters import RecipeFilter


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        queryset = Tag.objects.all()
        return queryset


class IngridientViewSet(ModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [IsOwnerOrReadOnly | IsAdminUserOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteViewSet(ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, recipe_id=None):
        serializer = self.serializer_class(data={'recipe': recipe_id},
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'recipe_id'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, recipe_id=None):
        serializer = self.serializer_class(data={'recipe': recipe_id},
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DownloadShoppingCartViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def download(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        ingredients = {}

        for item in shopping_cart:
            for recipe_ingredient in item.recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
                if ingredient.name in ingredients:
                    ingredients[ingredient.name] += recipe_ingredient.amount
                else:
                    ingredients[ingredient.name] = recipe_ingredient.amount

        content = ''
        for name, amount in ingredients.items():
            content += f'{name} - {amount} г\n'
        content_total = f'Список покупок:\n\n{content}\n\nХорошего дня!'
        response = HttpResponse(content_total, content_type='text/plain')
        response['Content-Disposition'] = ('attachment;'
                                           'filename="shopping_cart.txt"')

        return response
