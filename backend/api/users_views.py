from djoser.views import UserViewSet

from django.shortcuts import get_object_or_404

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .serializers import CreateUserSerializer, UserDisplaySerializer
from .serializers import CustomAuthTokenSerializer, UserSubscripeSerializer
from .serializers import SubscriptionsSerializer
from .paginations import CustomPagination
from .permissions import IsPostOrReadOnly

from recipes.models import User
from users.models import Subscriptions


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


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=204)


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
        serializer = self.serializer_class(
            data={'subscriber': subscriber_id},
            context={'request': request})
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
