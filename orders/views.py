from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import *
from .serializers import *
from .filters import *
from goods.pagination import GoodsPagination
from account import permissions as mypermissions
from utils import response as myresponse
import datetime
# Create your views here.

class FundsViewset(viewsets.GenericViewSet,
                   myresponse.CustomCreateModelMixin,
                   myresponse.CustomDestroyModelMixin,
                   myresponse.CustomListModelMixin):
    queryset = FundsModel.objects.all()
    serializer_class = FundsModelSerializer

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            return [mypermissions.IsRole1()]
        else:
            return [permissions.IsAuthenticated()]


class CartViewset(myresponse.CustomModelViewSet):
    queryset = CartModel.objects.all()
    permission_classes = [mypermissions.IsRole2]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return CartPatchSerializer
        else:
            return CartModelSerializer
        
    @action(methods=['post'], detail=False)
    def purchase(self, request):
        item_list = request.data.get('cart_ids')
        user_id = request.user.id
        if not item_list:
            return Response({"msg": "未选择购物车商品",
                                "data": None,
                                "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        fail_list = []
        order = OrdersModel.objects.create(status=0, creater_id=user_id)
        for item in item_list:
            cart = CartModel.objects.get(id=item, creater_id=user_id)
            product = cart.product
            now_time = datetime.datetime.now()
            # now_time = "2024-07-18"
            price = product.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).first()
            if not price:
                fail_list.append(product.name)
                cart.delete()
                continue
            OrderDetailModel.objects.create(order=order, product_id=product.id, product_name=product.name,
                                            description=product.description, unit=product.unit.name, category=product.category.name,
                                            price=price.price, funds=cart.funds.name, order_quantity=cart.quantity)
            cart.delete()
        if len(fail_list) == len(item_list):
            order.delete()
            return Response({"msg": "所有商品不存在可用价格，下单失败",
                                "data": None,
                                "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        if fail_list:
            return Response({"msg": "部分商品不存在可用价格，部分下单失败",
                                "data": fail_list,
                                "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        
        order.product_num = order.details.count()
        order.save()
        return Response({"msg": "商品下单成功",
                    "data": None,
                    "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
class OrdersViewset(viewsets.GenericViewSet,
                   myresponse.CustomListModelMixin):
    queryset = OrdersModel.objects.all()
    serializer_class = OrdersModelSerializer
    filterset_class = OrdersFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == "1" or self.request.user.role == "0":
            return queryset.order_by('id')
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    
    def get_permissions(self):       
        if self.action in ["accept", "ship", "delivered"]:
            return [mypermissions.IsRole0()]
        else:
            return [permissions.IsAuthenticated()]
    
    @action(methods=['get'], detail=True)
    def details(self, request, pk=None):
        order = self.get_object()
        order_details = order.details.all()
        page_details = self.paginate_queryset(order_details)
        serializer = OrderDetailModelSerializer(page_details, many=True)
        return self.get_paginated_response(serializer.data)
        # if page_details is not None:
        #     serializer = OrderDetailModelSerializer(page_details, many=True)
        #     return self.get_paginated_response(serializer.data)
        # serializer = OrderDetailModelSerializer(order_details, many=True)
        # return Response({
        #     "msg": "ok",
        #     "data": serializer.data,
        #     "code": status.HTTP_200_OK
        # }, status=status.HTTP_200_OK)
    
    @action(methods=['post'],detail=True)
    def accept(self, request, pk=None):
        order = self.get_object()
        if order.status != "0":
            return Response({
                "msg": "接单失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        user_id = request.user.id
        order.accepter_id = user_id
        order.accept_time = datetime.datetime.now()
        order.status = 1
        order.save()
        return Response({
            "msg": "接单成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'],detail=True)
    def ship(self, request, pk=None):
        order = self.get_object()
        if order.status != "1":
            return Response({
                "msg": "发货失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        order.status = 2
        order.save()
        return Response({
            "msg": "发货成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'],detail=True)
    def delivered(self, request, pk=None):
        order = self.get_object()
        if order.status != "2":
            return Response({
                "msg": "送达失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        order.status = 3
        order.save()
        return Response({
            "msg": "订单送达成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

class OrderDetailsViewset(viewsets.GenericViewSet):
    queryset = OrderDetailModel.objects.all()
    permission_classes = [mypermissions.IsRole2]
    serializer_class = OrderDetailModelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(order__creater_id=self.request.user.id)
        return queryset
    
    @action(methods=['post'], detail=True)
    def confirm(self, request, pk=None):
        received_quantity = request.data.get("received_quantity")
        item = self.get_object()
        item.received_quantity = received_quantity
        item.cost = float(received_quantity) * float(item.price)
        item.recipient_id = request.user.id
        item.recipient_time = datetime.datetime.now()
        item.save()
        order = item.order
        order.finish_num += 1
        if order.finish_num == order.product_num:
            order.finish_time = datetime.datetime.now()
            order.status = 4
        order.save()
        return Response({
            "msg": "商品收货成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)