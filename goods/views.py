from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import *
from .serializers import *
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
    permission_classes = [IsRole0]

    # # 添加时修改价格状态
    # def perform_create(self, serializer):
    #     # 将商品以往价格status设置为False
    #     product = self.request.data.get('product')
    #     PriceModel.objects.filter(product=product).update(status=False)
    #     return super().perform_create(serializer)

    def perform_create(self, serializer):
        # 保存新的 PriceModel 实例
        instance = serializer.save()

        # 提取到对应商品实例
        product = instance.product

        # 检查是否已经存在该商品的价格请求
        existing_request = PriceRequestModel.objects.filter(product=product).first()
        if existing_request:
            existing_request.delete()
        
        # 创建一个新的 PriceRequestModel 实例关联到这个 PriceModel 实例
        PriceRequestModel.objects.create(price=instance,product=product)

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
        
    
class PriceRequestViewSet(viewsets.GenericViewSet,
                               myresponse.CustomListModelMixin):
    queryset = PriceRequestModel.objects.all()
    serializer_class = PriceRequestModelSerializer
    permission_classes = [IsRole1]

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        price_request = self.get_object()
        price = price_request.price
        # 将商品以往的价格状态设置为false
        product = price.product
        PriceModel.objects.filter(product=product).update(status=False)
        # 将刚审核的价格状态设置为true
        price.status = True
        price.save()
        # 将已审核的价格请求删除
        price_request.delete()
        return Response({"msg": "Price Review successfully.",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)


# 计量单位视图集
class UnitViewSet(myresponse.CustomModelViewSet):
    queryset = UnitModel.objects.all()
    serializer_class = UnitModelSerializer
    permission_classes = [IsRole0]

# 商品种类视图集
class CategoryViewSet(myresponse.CustomModelViewSet):
    queryset = CategoryModel.objects.all()
    serializer_class = CategoryModelSerializer
    permission_classes = [IsRole0]



