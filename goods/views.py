from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response

from .models import GoodsModel, PriceModel, UnitModel, CategoryModel
from .serializers import GoodsModelSerializer, PriceModelSerializer, UnitModelSerializer, CategorySerializer
from .pagination import GoodsPagination
from .permissions import *
from utils.response import CustomModelViewSet


# 商品视图集
class GoodsViewSet(viewsets.ModelViewSet):
    queryset = GoodsModel.objects.all()
    serializer_class = GoodsModelSerializer
    pagination_class = GoodsPagination

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        elif self.action == 'destroy' or self.action == 'update' or self.action == 'partial_update':
            return [IsRole0()]
        
        return super().get_permissions()

class PriceViewSet(viewsets.ModelViewSet): 
    queryset = PriceModel.objects.all()
    serializer_class = PriceModelSerializer
    permission_classes = [IsRole0 | IsRole1]

    def perform_create(self, serializer):
        # 将商品以往价格status设置为False
        product = self.request.data.get('product')
        PriceModel.objects.filter(product=product).update(status=False)

        return super().perform_create(serializer)
    
class UnitViewSet(viewsets.ModelViewSet):
    queryset = UnitModel.objects.all()
    serializer_class = UnitModelSerializer
    permission_classes = [IsRole0]

class CategoryViewSet(CustomModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsRole0]

