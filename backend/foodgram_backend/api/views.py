from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from djoser.views import UserViewSet

from django.shortcuts import get_object_or_404

from recipes.models import User, Subscriptions
from .serializers import CreateUserSerializer, UserDisplaySerializer, CustomAuthTokenSerializer, SubscriptionsSerializer, UserSubscripeSerializer
from .permissions import IsAuthenticatedOrAdminOnly, IsAdminOrSelf
from .paginations import SubscriptionsPagination


class UsersView(UserViewSet):
    serializer_class = UserDisplaySerializer
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        elif self.action == 'me':
            return UserDisplaySerializer
        else:
            return super().get_serializer_class()
        
    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAuthenticatedOrAdminOnly]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsAdminOrSelf]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
    pagination_class = SubscriptionsPagination

    def get_queryset(self):
        return Subscriptions.objects.all()
    
    def create(self, request, user_id=None):
        subscriber_id = user_id
        subscriber = get_object_or_404(User, id=subscriber_id)
        serializer = self.serializer_class(data={
            'subscriber': subscriber_id
        }, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)  
        users = [subscriber]
        user_serializer = UserSubscripeSerializer(users, many=True, context={'request': request})
        return Response(user_serializer.data, status=status.HTTP_201_CREATED)
    
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        users = [subscription.subscriber for subscription in page]
        serializer = UserSubscripeSerializer(users, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    def destroy(self, request, user_id=None):
        subscriber_id = user_id
        subscriber = get_object_or_404(User, id=subscriber_id)
        subscription = get_object_or_404(Subscriptions, user=request.user, subscriber=subscriber)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    

