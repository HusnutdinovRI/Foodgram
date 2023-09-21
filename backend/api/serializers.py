import base64
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from recipes.models import User, Tag, Ingredient
from recipes.models import Recipe, RecipeIngredient, Favorite, ShoppingCart
from users.models import Subscriptions


class CreateUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=150)

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', 'username', 'password', 'first_name',
                  'last_name',)

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError('Такой пользователь '
                                              'уже существует')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Пользователь c таким email '
                                              'уже существует')
        return attrs


class LimitedRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserDisplaySerializer(CreateUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', 'username', 'password', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.id:
            user = request.user
            subscribed_user = obj
            is_subscribed = Subscriptions.objects.filter(
                user=user, subscriber=subscribed_user).exists()
            return is_subscribed
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)
        return representation


class UserSubscripeSerializer(UserDisplaySerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        subscribed_user = obj
        recipe_count = Recipe.objects.filter(author=subscribed_user).count()
        return recipe_count

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request').query_params.get('recipes_limit')
        if recipes_limit:
            return LimitedRecipeSerializer(
                obj.recipes.all()[:int(recipes_limit)], many=True).data
        return LimitedRecipeSerializer(obj.recipes.all(), many=True).data


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        User = get_user_model()
        try:
            user = get_object_or_404(User, email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'User with given email does not exist.')
        user = authenticate(username=user.username, password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Incorrect email or password.')
        return {'user': user}


class SubscriptionsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    subscriber = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all())
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscriptions
        fields = ('user', 'subscriber', 'recipes')

    def validate(self, validated_data):
        user = self.context['request'].user
        subscriber = validated_data['subscriber']
        if user.id == subscriber.id:
            raise serializers.ValidationError(
                'Ошибка! Нельзя подписаться на себя')

        if Subscriptions.objects.filter(
           user=user, subscriber=subscriber).exists():
            raise serializers.ValidationError(
                'Ошибка! Нельзя подписаться на автора два раза')

        return validated_data

    def get_recipes(self):
        user = self.context['request'].user
        recipes = Recipe.objects.filter(user=user)
        return RecipeSerializer(recipes, many=True).data


class TagSerializer(serializers.ModelSerializer):
    color = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'amount', 'measurement_unit']


class RecipeSerializer(serializers.ModelSerializer):
    author = UserDisplaySerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    name = serializers.CharField(max_length=254)
    text = serializers.CharField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['id', 'author', 'image', 'ingredients', 'tags', 'name',
                  'text', 'cooking_time', 'is_favorited',
                  'is_in_shopping_cart']

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return RecipeIngredientSerializer(recipe_ingredients, many=True).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.id:
            user = request.user
            recipe = obj
            is_favorited = Favorite.objects.filter(
                user=user, recipe=recipe).exists()
            return is_favorited
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.id:
            user = request.user
            recipe = obj
            is_in_cart = ShoppingCart.objects.filter(
                user=user, recipe=recipe).exists()
            return is_in_cart
        return False

    def validate_request_data(self, request):
        required_fields = ['ingredients', 'tags', 'image', 'name',
                           'text', 'cooking_time']
        for field in required_fields:
            if not request.data.get(field):
                if Recipe._meta.get_field(field).verbose_name:
                    verbose_name = Recipe._meta.get_field(field).verbose_name
                else:
                    verbose_name = field
                raise serializers.ValidationError(f'Поле {verbose_name}'
                                                  'обязательно для заполения')

    @transaction.atomic
    def create(self, validated_data):
        self.validate_request_data(self.context['request'])

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(self.context['request'].data.get('tags'))
        ingredients = self.context['request'].data.get('ingredients')

        self.create_recipe_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        instance.tags.set(self.context['request'].data.get('tags'))
        ingredients = self.context['request'].data.get('ingredients')

        RecipeIngredient.objects.filter(recipe=instance).delete()

        self.create_recipe_ingredients(instance, ingredients)

        instance.save()
        return instance

    def create_recipe_ingredients(self, recipe, ingredients):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=get_object_or_404(Ingredient,
                                             id=ingredient_data['id']),
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже в избранном!')
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже в корзине!')
        return data
