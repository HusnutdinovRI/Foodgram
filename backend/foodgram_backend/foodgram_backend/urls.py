from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api.views import UsersView, CustomAuthToken, Logout, SubscriptionsViewSet

router = routers.DefaultRouter()
router.register(r'api/users/subscriptions', SubscriptionsViewSet, basename='user-subscriptions')
router.register(r'api/users', UsersView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/token/login/', CustomAuthToken.as_view()),
    path('api/auth/token/logout/', Logout.as_view()),
    path('api/users/<int:user_id>/subscribe/', SubscriptionsViewSet.as_view({'post': 'create', 'delete': 'destroy'}), name='subscribe'),
    path('', include(router.urls))
]