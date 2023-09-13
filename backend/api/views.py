from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

from recipes.models import User, Subscriptions, Tag, Ingredient
from recipes.models import Recipe, Favorite, ShoppingCart
from .serializers import CreateUserSerializer, UserDisplaySerializer
from .serializers import CustomAuthTokenSerializer, SubscriptionsSerializer
from .serializers import UserSubscripeSerializer, TagSerializer
from .serializers import RecipeSerializer, IngredientSerializer
from .serializers import FavoriteSerializer, LimitedRecipeSerializer
from .serializers import ShoppingCartSerializer
from .permissions import IsPostOrReadOnly, IsOwnerOrReadOnly
from .permissions import IsAdminUserOrReadOnly
from .paginations import CustomPagination
from .filters import RecipeFilter


class UsersView(UserViewSet):
    serializer_class = UserDisplaySerializer
    lookup_field = 'id'
    pagination_class = CustomPagination
    permission_classes = [AllowAny, IsPostOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'me':
            return UserDisplaySerializer
        else:
            return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False)
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {'detail': 'Учетные данные не были предоставлены.'},
                status=401)

        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class CustomAuthToken(ObtainAuthToken):
    permission_classes = [AllowAny]
    serializer_class = CustomAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'auth_token': token.key
        })


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=204)


class SubscriptionsViewSet(ModelViewSet):
    serializer_class = SubscriptionsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Subscriptions.objects.filter(user=user)

    def create(self, request, user_id=None):
        subscriber_id = user_id
        subscriber = get_object_or_404(User, id=subscriber_id)
        serializer = self.serializer_class(data={
            'subscriber': subscriber_id
            }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        users = [subscriber]
        user_serializer = UserSubscripeSerializer(users, many=True,
                                                  context={'request': request})
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            users = [subscription.subscriber for subscription in page]
            serializer = UserSubscripeSerializer(users, many=True,
                                                 context={'request': request})
            return self.get_paginated_response(serializer.data)
        users = [subscription.subscriber for subscription in queryset]
        serializer = UserSubscripeSerializer(users, many=True,
                                             context={'request': request})
        return Response(serializer.data)

    def destroy(self, request, user_id=None):
        subscriber_id = user_id
        subscriber = get_object_or_404(User, id=subscriber_id)
        subscription = get_object_or_404(Subscriptions, user=request.user,
                                         subscriber=subscriber)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise PermissionDenied('Только аутентифициованные пользователи'
                                   'могут создавать рецепты')
        serializer.save(author=self.request.user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsPostOrReadOnly]
        else:
            permission_classes = [IsAdminUser | IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]


class FavoriteViewSet(ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'recipe_id'

    def create(self, request, recipe_id=None):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = self.serializer_class(data={
            'recipe': recipe_id
        }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        user_serializer = LimitedRecipeSerializer(recipe, many=False,
                                                  context={'request': request})
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


class ShoppingCartViewSet(ModelViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'recipe_id'

    def create(self, request, recipe_id=None):
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = self.serializer_class(data={
            'recipe': recipe_id
            }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        user_serializer = LimitedRecipeSerializer(recipe, many=False,
                                                  context={'request': request})
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)


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
