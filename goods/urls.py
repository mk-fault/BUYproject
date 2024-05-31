from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'goods', views.GoodsViewSet)
router.register(r'price', views.PriceViewSet)
router.register(r'priceReq', views.PriceRequestViewSet)
router.register(r'unit', views.UnitViewSet)
router.register(r'category', views.CategoryViewSet)
router.register(r'priceCycle', views.PriceCycleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]