import os
from django.shortcuts import render
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path
from django.conf.global_settings import MEDIA_ROOT

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
from account.models import AccountModel
from utils import response as myresponse
import datetime
import pandas as pd
from urllib.parse import quote
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
    
    @action(methods=['post'], detail=False)
    def report(self, request, pk=None):
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        school_id = request.data.get("school_id", None)
        queryset = self.get_queryset()
        
        # 没传入shool_id时表示是学校账户访问自己的报表
        if school_id is None:
            # 判断如果当期账户是非学校账户，则要求传入学校ID
            if request.user.role in ["0", "1"]:
                return Response({
                    "msg": "请传入学校ID",
                    "data": None,
                    "code": status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            # 过滤在起止日期内的订单详情
            queryset = queryset.filter(finish_time__range=[start_date, end_date])
            # username为当期用户
            username = request.user.username
        
        # 如果传入的school_id不是学校账户则返回错误
        elif AccountModel.objects.filter(id=school_id).first().role != '2':
            return Response({
                "msg": "访问对象非学校",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 传入了school_id，表示教体局或粮油公司访问报表
        else:
            # 判断当期是否是教体局或粮油公司组用户
            if request.user.role not in ["0", "1"]:
                return Response({
                    "msg": "没有访问权限",
                    "data": None,
                    "code": status.HTTP_401_UNAUTHORIZED
                }, status=status.HTTP_401_UNAUTHORIZED)
            # 过滤某一学校在起止日期内的订单详情
            queryset = queryset.filter(finish_time__range=[start_date, end_date], creater_id=school_id)
            # username为对应school_id的用户名
            username = AccountModel.objects.filter(id=school_id).first().username

        # 如果查询结果为空，表示时间段内没有订单
        if not queryset.exists():
            return Response({
                "msg": "所选时间段没有订单",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 制作表格数据
        data = []
        for order in queryset:
            order_details = order.details.all()
            for detail in order_details:
                detail_data = {
                    "商品编号": detail.product_id,
                    "商品名称": detail.product_name,
                    "商品描述": detail.description,
                    "计量单位": detail.unit,
                    "商品种类": detail.category,
                    "商品单价": detail.price,
                    "经费来源": detail.funds,
                    "订购数量": detail.order_quantity,
                    "实收数量": detail.received_quantity,
                    "总价": detail.cost,
                    "收货时间": detail.recipient_time,
                    "学校": username
                }
                data.append(detail_data)

        # 返回文件响应
        df = pd.DataFrame(data)
        file_name = f"{username}_{start_date}~{end_date}_订单报表"

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{quote(file_name)}.xlsx"'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')

        return response
        


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
    


    
