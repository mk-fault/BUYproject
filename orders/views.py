from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import *
from .serializers import *
from .filters import *
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
            return Response({"msg": "No item selected",
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
                continue
            OrderDetailModel.objects.create(order=order, product_id=product.id, product_name=product.name,
                                            description=product.description, unit=product.unit.name, category=product.category.name,
                                            price=price.price, funds=cart.funds.name, order_quantity=cart.quantity)
            cart.delete()
        if len(fail_list) == len(item_list):
            order.delete()
            return Response({"msg": "All item selected are not available",
                                "data": None,
                                "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        if fail_list:
            return Response({"msg": "Some item selected are not available",
                                "data": fail_list,
                                "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        return Response({"msg": "Purchase successfullly",
                            "data": None,
                            "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
    
class OrdersViewset(viewsets.GenericViewSet,
                   myresponse.CustomListModelMixin):
    queryset = OrdersModel.objects.all()
    serializer_class = OrdersModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = OrdersFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 1 or self.request.user.role == 0:
            return queryset.order_by('id')
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    