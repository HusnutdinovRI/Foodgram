from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from recipes.models import User, Subscriptions


from django.contrib.auth import authenticate

class CreateUserSerializer(UserCreateSerializer):
    email = serializers.EmailField(max_length=254)
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=150)
    

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', 'username', 'password', 'first_name', 'last_name',)

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
            raise serializers.ValidationError('Такой пользователь уже существует')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return attrs
    

class UserDisplaySerializer(CreateUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = ('email','id' ,'username', 'password', 'first_name', 'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            subscriber = request.user
            subscribed_user = obj
            is_subscribed = Subscriptions.objects.filter(user=subscriber, subscriber=subscribed_user).exists()
            return is_subscribed
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)
        return representation


class UserSubscripeSerializer(UserDisplaySerializer):
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'is_subscribed', 'recipes')

    def get_recipes(self, user):
        # Ваша заглушка для поля recipes
        return []


class CustomAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        User = get_user_model()
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('User with given email does not exist.')
        user = authenticate(username=user.username, password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Incorrect email or password.')
        return {'user': user}
    

class SubscriptionsSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    subscriber = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = Subscriptions
        fields = ('user', 'subscriber', 'recipes')

    def validate(self, validated_data):
        user = self.context['request'].user
        subscriber = validated_data['subscriber']
        subscriber_obj = Subscriptions.objects.filter(user=user, subscriber=subscriber)
        if user.id == subscriber.id:
            raise serializers.ValidationError('Ошибка! Нельзя подписаться на себя')

        if len(subscriber_obj) > 0:
            raise serializers.ValidationError('Ошибка! Нельзя подписаться на автора два раза')

        return validated_data
    
    def get_recipes(self, subscription):
        """recipes_limit = self.context['request'].query_params.get('recipes_limit', None)
        if recipes_limit is not None:
            user = subscription.subscriber
            recipes = user.recipes.all()[:int(recipes_limit)]
            # Сериализовать рецепты
            recipe_serializer = RecipeSerializer(recipes, many=True)
            serialized_recipes = recipe_serializer.data
            return serialized_recipes"""
        return None
