from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from api.views import TagViewSet
from api.views import IngridientViewSet, RecipeViewSet
from api.views import FavoriteViewSet, ShoppingCartViewSet
from api.views import DownloadShoppingCartViewSet
from api.users_views import UsersView, Logout, CustomAuthToken
from api.users_views import SubscriptionsViewSet


router = routers.DefaultRouter()
router.register(r'users/subscriptions', SubscriptionsViewSet,
                basename='user-subscriptions')
router.register(r'users', UsersView)
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngridientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/me/', UsersView.as_view, name='me'),
    path('api/auth/token/login/', CustomAuthToken.as_view()),
    path('api/auth/token/logout/', Logout.as_view()),
    path('api/users/<int:user_id>/subscribe/',
         SubscriptionsViewSet.as_view(
             {'post': 'create', 'delete': 'destroy'}), name='subscribe'),
    path('api/recipes/<int:recipe_id>/favorite/',
         FavoriteViewSet.as_view(
             {'post': 'create', 'delete': 'destroy'}), name='add_to_favorite'),
    path('api/recipes/<int:recipe_id>/shopping_cart/',
         ShoppingCartViewSet.as_view(
             {'post': 'create', 'delete': 'destroy'}), name='shopping_list'),
    path('api/recipes/download_shopping_cart/',
         DownloadShoppingCartViewSet.as_view(
             {'get': 'download'}), name='download_shopping_cart'),
    path('api/', include(router.urls))
]
