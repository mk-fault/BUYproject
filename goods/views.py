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
import pandas as pd

# 商品视图集
class GoodsViewSet(myresponse.CustomModelViewSet):
    queryset = GoodsModel.objects.all()
    serializer_class = GoodsModelSerializer
    pagination_class = GoodsPagination
    filterset_class = GoodsFilter

    # 添加上下文
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context

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

    # 商品报价表格上传
    @action(methods=['post'], detail=False)
    def upload(self, request, pk=None):
        f = request.data.get('file')
        cycle_id = request.data.get('cycle')
        try:
            df = pd.read_excel(f, sheet_name=None, skiprows=2)
        except:
            return Response({
                "msg": "文件格式错误，请传入xlsx文件",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if cycle_id is None:
            return Response({
                "msg": "请传入价格周期ID",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        if not PriceCycleModel.objects.filter(id=cycle_id).exists():

            return Response({
                "msg": "所选周期不存在",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 错误信息，保存修改或添加失败的商品信息
        errs = {
            "edit":[],
            "add":[]
        }

        # 遍历每一张工作簿，添加商品或修改商品价格
        for sheet_name, sheet_data in df.items():
            # 如果工作簿名不含“类”，则不是商品列表，跳过
            if '类' not in sheet_name:
                continue

            # 获取类别名，如果当前类别不存在，则创建类别
            category_name = sheet_name.strip()
            category_obj, _ = CategoryModel.objects.get_or_create(name=category_name)
            category_id = category_obj.id

            # 处理df，价格保留两位小数
            sheet_data = sheet_data.drop('序号', axis=1)
            # sheet_data = sheet_data.dropna()
            col_name = ['brand', 'name', 'description', 'price_check_1', 'price_check_2', 'price_check_avg', 'price_down5', 'price']
            sheet_data.columns = col_name
            sheet_data = sheet_data.drop('price_down5', axis=1)
            sheet_data['price_check_1'] = sheet_data['price_check_1'].round(2)
            sheet_data['price_check_2'] = sheet_data['price_check_2'].round(2)
            sheet_data['price_check_avg'] = sheet_data['price_check_avg'].round(2)
            sheet_data['price'] = sheet_data['price'].round(2)

            # 遍历每一行数据，进行商品的添加或报价的修改提交
            for _, row in sheet_data.iterrows():
                if row.isnull().all():
                    break
                row_dict = row.to_dict()
                row_dict['category'] = category_id
                row_dict['brand'] = None if pd.isnull(row_dict['brand']) else row_dict['brand']
                # 如果商品及其规格存在的话，则修改并提交报价
                if GoodsModel.objects.filter(name=row['name'], brand=row['brand'], description=row['description']).exists():
                    product_obj = GoodsModel.objects.filter(name=row['name'], brand=row['brand'], description=row['description']).first()
                    
                    # 没有status=0的价格，表示已经提出报价或报价已经被处理，需要手动调整
                    if not PriceModel.objects.filter(product=product_obj, status=0, cycle__id=cycle_id).exists():
                        errs['edit'].append(row_dict)

                    # 有status=0的价格，则修改报价，并提交申请
                    else:
                        price_obj = PriceModel.objects.get(product=product_obj, status=0, cycle__id=cycle_id)
                        price_obj.price = row_dict['price']
                        price_obj.price_check_1 = row_dict['price_check_1']
                        price_obj.price_check_2 = row_dict['price_check_2']
                        price_obj.price_check_avg = row_dict['price_check_avg']
                        price_obj.status = 1
                        price_obj.creater_id = request.user.id
                        price_obj.create_time = datetime.datetime.now()
                        price_obj.reviewer_id = None
                        price_obj.review_time = None
                        price_obj.save()


                # 如果不存在，则添加作为新的商品
                else:
                    ser = GoodsModelSerializer(data=row_dict, context={'user_id': request.user.id, 'cycle_id':cycle_id})
                    if ser.is_valid():
                        ser.save()
                    else:
                        print(ser.errors)
                        errs['add'].append(row_dict)

        # 如果添加过程存在错误，则返回错误信息
        if errs['add'] or errs['edit']:
            return Response({
                "msg": "部分商品添加失败或报价修改失败，已提出报价请求或已审核的价格需手动调整",
                "data": {
                    "报价修改失败": errs['edit'],
                    "商品添加失败": errs['add']
                },
                "code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "msg": "商品添加成功/报价修改成功",
                "data": None,
                "code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)


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
            # # 当由ori_price时表示创建时没有可用价格周期的商品，使用ori_price,并直接提交价格请求
            # if product.ori_price is not None:
            #     PriceModel.objects.create(
            #         product=product,
            #         price=product.ori_price,
            #         price_check_1 = product.ori_price_check_1,
            #         price_check_2 = product.ori_price_check_2,
            #         price_check_avg = product.ori_price_check_avg,
            #         cycle=instance,
            #         start_date=instance.start_date,
            #         end_date=instance.end_date,
            #         status=1
            #     )
            #     product.ori_price = None
            #     product.ori_price_check_1 = None
            #     product.ori_price_check_2 = None
            #     product.ori_price_check_avg = None
            #     product.save()
            # # 否则是已存在价格对象的商品，使用上一个价格
            # else:

            # 使用上一个价格
                try:
                    old_price_obj = PriceModel.objects.filter(product=product).order_by('-id').first()
                    old_price = old_price_obj.price
                    old_price_check_1 = old_price_obj.price_check_1
                    old_price_check_2 = old_price_obj.price_check_2
                    old_price_check_avg = old_price_obj.price_check_avg
                except:
                    instance.delete()
                    return Response({
                        "msg": "价格周期创建错误",
                        "data": None,
                        "code": status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)
                
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
        # 粮油公司的queryset去除掉status=-99即已弃用的价格,和已过期的价格（结束时间在当前时间之前的）
        if self.request.user.role == '0' or self.request.user.role == '1':
            # queryset = queryset.exclude(status=-99)
            now_time = datetime.datetime.now()
            queryset = queryset.exclude(status=-99).filter(end_date__gte=now_time).order_by('id')
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

    # 批量通过某些价格请求,传入价格对象id的列表
    @action(methods=['post'], detail=False)
    def multiaccept(self, request, pk=None):
        price_list = request.data.get('price_ids')
        if not price_list:
            return Response({
                "msg": "未传入价格对象id",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        err_list = []
        for price_id in price_list:
            try:
                price = PriceModel.objects.get(id=price_id)
                price.status = 2
                price.reviewer_id = request.user.id
                price.review_time = datetime.datetime.now()
                price.save()
            except:
                err_list.append(price_id)
                continue
        if err_list:
            return Response({
                "msg": "部分价格请求批准失败",
                "data": err_list,
                "code": status.HTTP_200_OK
            },status=status.HTTP_200_OK)
        else:
            return Response({
                "msg": "价格请求批准成功",
                "data": None,
                "code": status.HTTP_200_OK
            },status=status.HTTP_200_OK)

    
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
    

    # 批量拒绝某些价格请求,传入价格对象id的列表
    @action(methods=['post'], detail=False)
    def multireject(self, request, pk=None):
        price_list = request.data.get('price_ids')
        if not price_list:
            return Response({
                "msg": "未传入价格对象id",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        err_list = []
        for price_id in price_list:
            try:
                price = PriceModel.objects.get(id=price_id)
                price.status = -1
                price.reviewer_id = request.user.id
                price.review_time = datetime.datetime.now()
                price.save()
            except:
                err_list.append(price_id)
                continue
        if err_list:
            return Response({
                "msg": "部分价格请求拒绝失败",
                "data": err_list,
                "code": status.HTTP_200_OK
            },status=status.HTTP_200_OK)
        else:
            return Response({
                "msg": "价格请求拒绝成功",
                "data": None,
                "code": status.HTTP_200_OK
            },status=status.HTTP_200_OK)
    
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
        


