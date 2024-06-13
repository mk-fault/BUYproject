from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'funds', views.FundsViewset)
router.register(r'cart', views.CartViewset)

urlpatterns = [
    path('', include(router.urls)),
]