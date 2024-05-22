from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import GoodsModel, PriceModel, UnitModel, CategoryModel
from .serializers import GoodsModelSerializer, PriceModelSerializer, UnitModelSerializer, CategorySerializer
from .pagination import GoodsPagination
from .permissions import *
from utils import response as myresponse


# 商品视图集
class GoodsViewSet(myresponse.CustomModelViewSet):
    queryset = GoodsModel.objects.all()
    serializer_class = GoodsModelSerializer
    pagination_class = GoodsPagination

    # 非粮油公司用户仅允许查看商品
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        elif self.action == 'destroy' or self.action == 'update' or self.action == 'partial_update':
            return [IsRole0()]
        
        return super().get_permissions()

# 价格视图集
class PriceViewSet(viewsets.GenericViewSet,
                   myresponse.CustomCreateModelMixin): 
    queryset = PriceModel.objects.all()
    serializer_class = PriceModelSerializer
    permission_classes = [IsRole0 | IsRole1]

    # 添加时修改价格状态
    def perform_create(self, serializer):
        # 将商品以往价格status设置为False
        product = self.request.data.get('product')
        PriceModel.objects.filter(product=product).update(status=False)

        return super().perform_create(serializer)

    # 按商品ID查询商品过往所有价格
    @action(detail=False, methods=['post'], url_path='history')
    def get_prices_by_product(self, request):
        product_id = request.data.get('product')
        if not product_id:
            return Response({"msg": "Product ID is required.",
                             "data": None,
                             "code":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = GoodsModel.objects.get(id=product_id)
        except GoodsModel.DoesNotExist:
            return Response({"msg": "Product not found.",
                             "data": None,
                             "code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

        prices = PriceModel.objects.filter(product=product)
                # 使用分页器
        paginator = GoodsPagination()
        page = paginator.paginate_queryset(prices, request)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        # serializer = self.get_serializer(prices, many=True)
        # return Response({"msg": "ok",
        #                 "data": serializer.data,
        #                 "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
# 计量单位视图集
class UnitViewSet(myresponse.CustomModelViewSet):
    queryset = UnitModel.objects.all()
    serializer_class = UnitModelSerializer
    permission_classes = [IsRole0]

# 商品种类视图集
class CategoryViewSet(myresponse.CustomModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsRole0]



