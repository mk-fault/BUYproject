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
from .filters import *
from utils import response as myresponse

import datetime

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
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')

        # 当粮油公司查看商品时，列出所有商品，包括未上架、为审核的商品
        if self.request.user.role == "0":
            return queryset
        
        # 当其他用户查看商品时，列出可用商品（已上架、当前价格周期内有已审核价格的商品）
        now_time = datetime.datetime.now()
        # now_time = "2024-07-18"
        # queryset = [product for product in queryset if product.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).exists()]
        queryset = queryset.filter(status=True, prices__status=2, prices__start_date__lt=now_time, prices__end_date__gt=now_time).order_by('id').distinct()

        return queryset


# 价格周期视图集
class PriceCycleViewSet(myresponse.CustomModelViewSet):
    queryset = PriceCycleModel.objects.all()
    serializer_class = PriceCycleModelSerializer
    # permission_classes = [IsRole1]


    # 粮油公司用户仅允许查看周期
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [IsRole0OrRole1()]
        elif self.action == 'destroy' or self.action == 'update' or self.action == 'partial_update':
            return [IsRole1()]
        
        return super().get_permissions()
    
    # 当粮油公司查看时只能查看到价格周期状态为True的
    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')

        # # 教体局可以查看所有的周期
        # if self.request.user.role == "1":
        #     return queryset
        
        # # 粮油公司查看时只能看到可用的周期
        # queryset = queryset.filter(status=True).order_by('id')

        # 只能查看到status=True的周期
        queryset = queryset.filter(status=True).order_by('id')
        return queryset

    # 创建价格周期时，分情况创建price对象
    def perform_create(self, serializer):
        instance = serializer.save()
        # 获得所有的商品
        product_queryset = GoodsModel.objects.all()
        for product in product_queryset:

            # # 当由ori_price时表示刚上架的商品，使用ori_price
            # if product.ori_price is not None:
            #     PriceModel.objects.create(
            #         product=product,
            #         price=product.ori_price,
            #         cycle=instance,
            #         start_date=instance.start_date,
            #         end_date=instance.end_date,
            #         status=0
            #     )
            #     product.ori_price = None
            #     product.status = True
            #     product.save()
            # # 否则是已存在的商品，使用上一个价格
            # else:
            # 使用上一个价格
            old_price = PriceModel.objects.filter(product=product).order_by('-id').first().price
            PriceModel.objects.create(
                product=product,
                price=old_price,
                cycle=instance,
                start_date=instance.start_date,
                end_date=instance.end_date,
                status=0
            )
    
    # 弃用一个周期，并将该周期的价格对象的状态都设置为-99（已弃用）
    @action(detail=True, methods=['post'])
    def deprecate(self, request, pk=None):
        price_cycle = self.get_object()
        price_cycle.status = False
        price_cycle.creater_id = request.user.id
        price_queryset = price_cycle.prices.all()
        for price in price_queryset:
            price.status = -99
            price.save()
        price_cycle.save()
        return Response({"msg": "Price Cycle deprecate",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
        

        

# 价格视图集
class PriceViewSet(viewsets.GenericViewSet,
                   myresponse.CustomUpdateModelMixin,
                   myresponse.CustomListModelMixin): 
    queryset = PriceModel.objects.all()
    serializer_class = PriceModelSerializer
    filterset_class = PriceFilter
    permission_classes = [IsRole0]

    # queryset去除掉status=-99即已弃用的价格
    def get_queryset(self):
        queryset = super().get_queryset()

        # 粮油公司查看时只能看到可用的周期
        queryset = queryset.exclude(status=-99).order_by('id')

        return queryset

    # 修改时创建价格请求
    def perform_update(self, serializer):
        #  price对象实例
        instance = serializer.save()

        # 提取到对应商品实例
        product = instance.product
        # 检查是否已经存在该商品的价格请求
        existing_request = PriceRequestModel.objects.filter(product=product).first()
        if existing_request:
            existing_request.delete()
        
        # 创建一个新的 PriceRequestModel 实例关联到这个 PriceModel 实例
        PriceRequestModel.objects.create(price=instance,product=product)
        
        # 将price的状态修改为1（未审核）
        instance.status = 1
        instance.creater_id = self.request.user.id       # 申请人设置为提交请求的账号的id
        instance.create_time = datetime.datetime.now()   # 申请时间为当前时间
        instance.reviewer_id = None                      # 审核人清空
        instance.review_time = None                      # 审核时间清空
        instance.save()

    # 按商品ID查询商品过往所有价格
    # @action(detail=False, methods=['post'], url_path='history')
    # def get_prices_by_product(self, request):
    #     product_id = request.data.get('product')
    #     if not product_id:
    #         return Response({"msg": "Product ID is required.",
    #                          "data": None,
    #                          "code":status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         product = GoodsModel.objects.get(id=product_id)
    #     except GoodsModel.DoesNotExist:
    #         return Response({"msg": "Product not found.",
    #                          "data": None,
    #                          "code": status.HTTP_404_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

    #     prices = PriceModel.objects.filter(product=product)
    #             # 使用分页器
    #     paginator = GoodsPagination()
    #     page = paginator.paginate_queryset(prices, request)
    #     if page is not None:
    #         serializer = self.get_serializer(page, many=True)
    #         return paginator.get_paginated_response(serializer.data)
        
    
class PriceRequestViewSet(viewsets.GenericViewSet,
                               myresponse.CustomListModelMixin):
    queryset = PriceRequestModel.objects.all()
    serializer_class = PriceRequestModelSerializer
    permission_classes = [IsRole1]

    # 通过某价格请求
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        price_request = self.get_object()
        price = price_request.price
        # 将刚审核的价格状态设置为2(已审核)，更新审核人id和审核时间
        price.status = 2
        price.reviewer_id = request.user.id
        price.review_time = datetime.datetime.now()
        price.save()
        # 将已审核的价格请求删除
        price_request.delete()
        return Response({"msg": "Price Request Accept",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
    # 拒绝某价格请求
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        price_request = self.get_object()
        price = price_request.price
        # 将刚审核的价格状态设置为-1(已拒绝)，更新审核人id和审核时间
        price.status = -1
        price.reviewer_id = request.user.id
        price.review_time = datetime.datetime.now()
        price.save()
        # 将已审核的价格请求删除
        price_request.delete()
        return Response({"msg": "Price Request Reject",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    # @action(detail=True, methods=['post'])
    # def review(self, request, pk=None):
    #     price_request = self.get_object()
    #     price = price_request.price
    #     # 将商品以往的价格状态设置为false
    #     product = price.product
    #     PriceModel.objects.filter(product=product).update(status=False)
    #     # 将刚审核的价格状态设置为true
    #     price.status = True
    #     price.save()
    #     # 将已审核的价格请求删除
    #     price_request.delete()
    #     return Response({"msg": "Price Review successfully.",
    #                         "data": None,
    #                         "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)


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



