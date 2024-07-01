from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import *
from .serializers import *
from .pagination import GoodsPagination
from account.permissions import *
from .filters import *
from orders.models import FundsModel, CartModel
from orders.serializers import CartModelSerializer
from utils import response as myresponse

import datetime

# 商品视图集
class GoodsViewSet(myresponse.CustomModelViewSet):
    queryset = GoodsModel.objects.all()
    serializer_class = GoodsModelSerializer
    pagination_class = GoodsPagination
    filterset_class = GoodsFilter

    # 非粮油公司用户仅允许查看商品
    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        elif self.action == 'order':
            return [IsRole2()]
        else:
            return [IsRole0()]
        
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')

        # 当粮油公司查看商品时，列出所有商品，包括未上架、为审核的商品
        if self.request.user.role == "0":
            return queryset
        
        # 当其他用户查看商品时，列出可用商品（已上架、当前价格周期内有已审核价格的商品）
        now_time = datetime.datetime.now()
        # now_time = "2024-07-18"
        # queryset = [product for product in queryset if product.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).exists()]
        queryset = queryset.filter(status=True, prices__status=2, prices__start_date__lte=now_time, prices__end_date__gte=now_time).order_by('id').distinct()

        return queryset
    
    @action(detail=True, methods=["post"])
    def order(self, request, pk=None):
        product = self.get_object()
        product_id = pk

        # 获取经费来源与订加购数量
        funds = request.data.get('funds')
        quantity = request.data.get('quantity')

        # 创建人ID为当前用户ID
        creater_id = request.user.id

        # ser = CartModelSerializer(data={
        #     'product': product_id,
        #     'funds': funds,
        #     'quantity': quantity,
        #     'creater_id': creater_id
        # })

        # if ser.is_valid():
        #     ser.save()
        #     return Response({
        #         "msg": "Product added to cart successfully",
        #         "data": None,
        #         "code": status.HTTP_201_CREATED
        #     }, status=status.HTTP_201_CREATED)
        # else:
        #     return Response({
        #         "msg": "Invalid data",
        #         "data": ser.errors,
        #         "code": status.HTTP_400_BAD_REQUEST
        #     }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取经费来源实例
        funds_obj = FundsModel.objects.filter(id=funds).first()

        # 查看是否存在此经济来源ID
        if not funds_obj:
            return Response({"msg": "经费来源ID错误",
                             "data": None,
                             "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查购物车中是否有相同人创建的相同的商品和经费来源的项，如果有，进行累加
        existing_cart = CartModel.objects.filter(product=product, funds=funds, creater_id=creater_id).first()
        if existing_cart:
            existing_cart.quantity += int(quantity)
            existing_cart.save()
            return Response({"msg": "成功添加至购物车",
                     "data": None,
                     "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        
        # 没有则创建新的购物车实例
        CartModel.objects.create(product=product, funds=funds_obj, quantity=quantity, creater_id=creater_id)
        return Response({"msg": "成功添加至购物车",
                 "data": None,
                 "code": status.HTTP_201_CREATED}, status=status.HTTP_201_CREATED)


# 价格周期视图集
class PriceCycleViewSet(viewsets.GenericViewSet,
                        myresponse.CustomListModelMixin,
                        myresponse.CustomCreateModelMixin):
    queryset = PriceCycleModel.objects.all()
    serializer_class = PriceCycleModelSerializer
    # permission_classes = [IsRole1]


    # 粮油公司用户仅允许查看周期
    def get_permissions(self):
        if self.action == 'list':
            return [IsRole0OrRole1()]
        else:
            return [IsRole1()]
        
    
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
            # 当由ori_price时表示创建时没有可用价格周期的商品，使用ori_price
            if product.ori_price is not None:
                PriceModel.objects.create(
                    product=product,
                    price=product.ori_price,
                    price_check_1 = product.ori_price_check_1,
                    price_check_2 = product.ori_price_check_2,
                    price_check_avg = product.ori_price_check_avg,
                    cycle=instance,
                    start_date=instance.start_date,
                    end_date=instance.end_date,
                    status=0
                )
                product.ori_price = None
                product.save()
            # 否则是已存在价格对象的商品，使用上一个价格
            else:
            # 使用上一个价格
                try:
                    old_price_obj = PriceModel.objects.filter(product=product).order_by('-id').first()
                    old_price = old_price_obj.price
                    old_price_check_1 = old_price_obj.price_check_1
                    old_price_check_2 = old_price_obj.price_check_2
                    old_price_check_avg = old_price_obj.price_check_avg
                except:
                    old_price = 0
                    old_price_check_1 = 0
                    old_price_check_2 = 0
                    old_price_check_avg = 0
                PriceModel.objects.create(
                    product=product,
                    price=old_price,
                    price_check_1 = old_price_check_1,
                    price_check_2 = old_price_check_2,
                    price_check_avg = old_price_check_avg,
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
        return Response({"msg": "价格周期弃用成功",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
        

        

# 价格视图集
class PriceViewSet(viewsets.GenericViewSet,
                   myresponse.CustomUpdateModelMixin,
                   myresponse.CustomListModelMixin): 
    queryset = PriceModel.objects.all()
    # serializer_class = PriceModelSerializer
    filterset_class = PriceFilter
    permission_classes = [IsRole0OrRole1]

    def get_permissions(self):
        # accept和reject价格审查行为仅允许教体局组使用
        if self.action in ['accept', 'reject']:
            return [IsRole1()]
        elif self.action == 'partial_update':
            return [IsRole0()]
        else:
            return [IsRole0OrRole1()]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 粮油公司的queryset去除掉status=-99即已弃用的价格
        if self.request.user.role == '0':
            # queryset = queryset.exclude(status=-99)
            now_time = datetime.datetime.now()
            queryset = queryset.exclude(status=-99).filter(start_date__lte=now_time, end_date__gte=now_time).order_by('id')
        # 教体局的queryset只查询未审核的价格
        else:
            queryset = queryset.filter(status=1).order_by('id')
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PricePatchSerializer
        else:
            return PriceModelSerializer

    # 修改时创建价格请求
    def perform_update(self, serializer):
        #  price对象实例
        instance = serializer.save()

        # # 提取到对应商品实例
        # product = instance.product
        # # 检查是否已经存在该商品的价格请求
        # existing_request = PriceRequestModel.objects.filter(product=product).first()
        # if existing_request:
        #     existing_request.delete()
        
        # # 创建一个新的 PriceRequestModel 实例关联到这个 PriceModel 实例
        # PriceRequestModel.objects.create(price=instance,product=product)
        
        # 将price的状态修改为1（未审核）
        instance.status = 1
        instance.creater_id = self.request.user.id       # 申请人设置为提交请求的账号的id
        instance.create_time = datetime.datetime.now()   # 申请时间为当前时间
        instance.reviewer_id = None                      # 审核人清空
        instance.review_time = None                      # 审核时间清空
        instance.save()     

    # 通过某价格请求
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        price = self.get_object()
        # 将刚审核的价格状态设置为2(已审核)，更新审核人id和审核时间
        price.status = 2
        price.reviewer_id = request.user.id
        price.review_time = datetime.datetime.now()
        price.save()
        return Response({"msg": "已批准该价格",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
    # 拒绝某价格请求
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        price = self.get_object()
        # 将刚审核的价格状态设置为-1(已拒绝)，更新审核人id和审核时间
        price.status = -1
        price.reviewer_id = request.user.id
        price.review_time = datetime.datetime.now()
        price.save()
        return Response({"msg": "已拒绝该价格",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
# class PriceRequestViewSet(viewsets.GenericViewSet,
#                                myresponse.CustomListModelMixin):
#     queryset = PriceRequestModel.objects.all()
#     serializer_class = PriceRequestModelSerializer
#     permission_classes = [IsRole1]

#     # 通过某价格请求
#     @action(detail=True, methods=['post'])
#     def accept(self, request, pk=None):
#         price_request = self.get_object()
#         price = price_request.price
#         # 将刚审核的价格状态设置为2(已审核)，更新审核人id和审核时间
#         price.status = 2
#         price.reviewer_id = request.user.id
#         price.review_time = datetime.datetime.now()
#         price.save()
#         # 将已审核的价格请求删除
#         price_request.delete()
#         return Response({"msg": "Price Request Accept",
#                             "data": None,
#                             "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
#     # 拒绝某价格请求
#     @action(detail=True, methods=['post'])
#     def reject(self, request, pk=None):
#         price_request = self.get_object()
#         price = price_request.price
#         # 将刚审核的价格状态设置为-1(已拒绝)，更新审核人id和审核时间
#         price.status = -1
#         price.reviewer_id = request.user.id
#         price.review_time = datetime.datetime.now()
#         price.save()
#         # 将已审核的价格请求删除
#         price_request.delete()
#         return Response({"msg": "Price Request Reject",
#                             "data": None,
#                             "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)


# 计量单位视图集
# class UnitViewSet(viewsets.GenericViewSet,
#                   myresponse.CustomCreateModelMixin,
#                   myresponse.CustomDestroyModelMixin,
#                   myresponse.CustomListModelMixin):
#     queryset = UnitModel.objects.all()
#     serializer_class = UnitModelSerializer
#     # permission_classes = [IsRole0]

#     # 非粮油公司组仅能查询
#     def get_permissions(self):
#         if self.action == 'list':
#             return [permissions.IsAuthenticated()]
#         else:
#             return [IsRole0()]
        

# 商品种类视图集
class CategoryViewSet(viewsets.GenericViewSet,
                      myresponse.CustomCreateModelMixin,
                      myresponse.CustomDestroyModelMixin,
                      myresponse.CustomListModelMixin):
    queryset = CategoryModel.objects.all()
    serializer_class = CategoryModelSerializer
    # permission_classes = [IsRole0]

    # 非粮油公司组仅能查询
    def get_permissions(self):
        if self.action == 'list':
            return [permissions.IsAuthenticated()]
        else:
            return [IsRole0()]
        



