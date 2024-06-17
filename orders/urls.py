from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'funds', views.FundsViewset)
router.register(r'cart', views.CartViewset)
router.register(r'orders', views.OrdersViewset)
router.register(r'orderdetails', views.OrderDetailsViewset)

urlpatterns = [
    path('', include(router.urls)),
]