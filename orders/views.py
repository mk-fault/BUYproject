from io import BytesIO
import datetime
import pandas as pd
from urllib.parse import quote
import datetime
import xlsxwriter
import os

from django.shortcuts import render
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path
from django.conf import settings

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

# Create your views here.

class FundsViewset(viewsets.GenericViewSet,
                   myresponse.CustomCreateModelMixin,
                   myresponse.CustomDestroyModelMixin,
                   myresponse.CustomListModelMixin):
    queryset = FundsModel.objects.all()
    serializer_class = FundsModelSerializer

    # 只有教体局组能进行经费来源的添加删除
    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            return [mypermissions.IsRole1()]
        else:
            return [permissions.IsAuthenticated()]


class CartViewset(myresponse.CustomModelViewSet):
    queryset = CartModel.objects.all()
    permission_classes = [mypermissions.IsRole2]

    # 仅能看到由自己账户创建的购物车项
    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    
    # PATCH方法时使用专用的序列化器
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return CartPatchSerializer
        else:
            return CartModelSerializer
        
    @action(methods=['post'], detail=False)
    def purchase(self, request):
        """
        购物车商品下单
        """
        # 获取购物车项ID列表
        item_list = request.data.get('cart_ids')
        deliver_date = request.data.get('deliver_date')
        user_id = request.user.id

        # 判断列表是否为空
        if not item_list:
            return Response({"msg": "未选择购物车商品",
                                "data": None,
                                "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
        # 判断送达时间是否为空
        if not deliver_date:
            return Response({"msg": "未选择送达日期",
                                "data": None,
                                "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
        # 失败列表，存储下单失败的商品的名字
        fail_list = []

        # 创建成功数，大于0则在失败时不删除订单
        success = 0

        # 创建订单实例
        order, _ = OrdersModel.objects.get_or_create(status=0, creater_id=user_id, deliver_date=deliver_date)

        cart_del_list = []
        # 对每一个购物车项，创建一个订单详情实例，并关联在订单实例上
        for item in item_list:
            # 获取购物车项实例和对应商品实例
            try:
                cart = CartModel.objects.get(id=item, creater_id=user_id)
            except:
                if success == 0:
                    order.delete()
                return Response({"msg": "购物车商品不存在，请刷新后重试",
                                    "data": None,
                                    "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
            product = cart.product

            # 获取商品当前的价格
            now_time = datetime.datetime.now()
            # now_time = "2024-07-18"
            price = product.prices.filter(status=2, start_date__lte=now_time, end_date__gte=now_time).order_by('-id').first()

            # 商品没有可用价格则下单失败，将商品名添加到失败列表中
            if not price:
                fail_list.append(product.name)
                continue

            # 创建订单详情实例
            try:
                OrderDetailModel.objects.create(order=order, product_id=product.id, product_name=product.name, brand=product.brand,
                                            description=product.description, category=product.category.name,
                                            price=price.price, funds=cart.funds.name, order_quantity=cart.quantity)
            # OrderDetailModel.objects.create(order=order, product_id=product.id, product_name=product.name,
            #                                 description=product.description, unit=product.unit.name, category=product.category.name,
            #                                 price=price.price, funds=cart.funds.name, order_quantity=cart.quantity)
                success += 1
                cart_del_list.append(cart)
            except:
                fail_list.append(product.name)
            # 下单后删除购物车项
        

        # 如果全失败，则删除创建的订单实例
        if not order.details:
            order.delete()
            return Response({
                        "msg": "所有商品下单失败",
                        "data": None,
                        "code": status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)
        
        # 部分失败则返回失败的商品名
        if fail_list:
            return Response({
                    "msg": "部分商品下单失败",
                    "data": fail_list,
                    "code": status.HTTP_200_OK}, status=status.HTTP_200_OK)
        
        # 添加订单的下单总数
        order.product_num = order.details.count()
        order.save()
        for cart in cart_del_list:
            cart.delete()

        # 返回响应
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

        # 教体局组和粮油公司组获得所有的订单查看权
        if self.request.user.role == "1" or self.request.user.role == "0":
            return queryset.order_by('id')
        
        # 学校用户只查询该用户创建的订单
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    
    def get_permissions(self):       
        # 仅粮油公司组能进行接单、发货、送达操作
        if self.action in ["accept", "ship", "delivered", "argue", "agree", "gendeliver"]:
            return [mypermissions.IsRole0()]
        elif self.action in ["gendoc"]:
            return [mypermissions.IsRole1()]
        else:
            return [permissions.IsAuthenticated()]
    
    @action(methods=['get'], detail=True)
    def details(self, request, pk=None):
        """
        获取订单对应的订单详情
        """
        # 获取当前订单实例
        order = self.get_object()

        # 获取订单关联的所有订单详情
        order_details = order.details.all()

        # 制作分页响应
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
        """
        修改订单状态为1，表示订单已接单，并添加接单人和接单时间
        """
        order = self.get_object()
                
        # 检查订单当前状态
        if order.status != "0":
            return Response({
                "msg": "接单失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改订单数据和状态
        user_id = request.user.id
        order.accepter_id = user_id
        order.accept_time = datetime.datetime.now()
        order.status = 1
        order.save()

        # 返回响应
        return Response({
            "msg": "接单成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'],detail=True)
    def ship(self, request, pk=None):
        """
        修改订单状态为2，表示订单已发货
        """
        order = self.get_object()

        # 检查订单当前状态
        if order.status != "1":
            return Response({
                "msg": "发货失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
                
        # 修改订单状态
        order.status = 2
        order.save()

        # 返回响应
        return Response({
            "msg": "发货成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'],detail=True)
    def delivered(self, request, pk=None):
        """
        修改订单状态为3，表示订单已送达
        """
        order = self.get_object()

        # 检查订单当前状态
        if order.status != "2":
            return Response({
                "msg": "送达失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改订单状态
        order.status = 3
        order.save()

        # 反回响应
        return Response({
            "msg": "订单送达成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=True)
    def argue(self, request, pk=None):
        """
        对收货情况有异议
        """
        order = self.get_object()

        # 检查订单当前状态
        if order.status != "4":
            return Response({
                "msg": "复核失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改订单状态
        order.status = 5
        order.save()

        # 放回响应
        return Response({
            "msg": "订单复核结果：订单有疑问",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=True)
    def agree(self, request, pk=None):
        """
        对收货情况没有异议，订单结束
        """
        order = self.get_object()

        # 检查订单当前状态
        if order.status != "4" and order.status != "5":
            return Response({
                "msg": "复核失败，请检查订单状态",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 修改订单状态
        order.status = 6
        order.finish_time = datetime.datetime.now()
        order.save()

        # 放回响应
        return Response({
            "msg": "订单复核结果：订单完成",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=True)
    def confirm(self, request, pk=None):
        """
        对订单确认收货
        """
        order = self.get_object()
        if order.status not in ["3", "4", "5"]:
            return Response({
                "msg": f"当前订单状态为：{order.get_status_display()},无法进行收货操作",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # err_list存储收货失败的订单详情号
        err_list = []

        # 接收确认收货的订单详情id和收货数量对象
        recv = request.data.get("recv")

        # 遍历json进行收货
        for detail_id, recv_num in recv.items():
            try:
                item = OrderDetailModel.objects.get(id=detail_id)
                # 如果该订单详情不属于该订单，则加入错误列表
                if item.order != order:
                    raise ValueError
                # 当该项之前未有过收货行为时，增加已收货条目数
                if item.received_quantity is None:
                    order.finish_num += 1
                # 更新收货数量和总计价格、时间
                item.received_quantity = recv_num
                item.cost = float(recv_num) * float(item.price)
                item.recipient_id = request.user.id
                item.recipient_time = datetime.datetime.now()
                item.save()
            except:
                err_list.append(detail_id)

        # 当已收货条目和待收获条目相等时，视为订单全部收货，修改订单状态为待复核
        if order.finish_num == order.product_num:
            order.status = 4
        order.save()

        if len(err_list) != 0:
            return Response({
                "msg": "部分商品收货失败，请检查订单详情号是否正确",
                "data": err_list,
                "code": status.HTTP_200_OK
            }, status=status.HTTP_200_OK)
        
        return Response({
            "msg": "收货成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    
    @action(methods=['post'], detail=False)
    def report(self, request, pk=None):
        """
        根据起止时间和学校ID生成学校在某时间段内的订单报表
        """

        # 获取data中的参数
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
            # queryset = queryset.filter(finish_time__range=[start_date, end_date])
            # 获取当天的最后时间
            _end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)

            # 过滤在起止日期内的订单详情
            queryset = queryset.filter(finish_time__gte=start_date, finish_time__lte=_end_date)

            # first_name为当期用户
            first_name = request.user.first_name
        
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
            # queryset = queryset.filter(finish_time__range=[start_date, end_date], creater_id=school_id)
            _end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)
            queryset = queryset.filter(finish_time__gte=start_date, finish_time__lte=_end_date, creater_id=school_id)

            # first_name为对应school_id的用户名
            first_name = AccountModel.objects.filter(id=school_id).first().first_name

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
                    "商品规格": detail.description,
                    "商品品牌": detail.brand,
                    "商品种类": detail.category,
                    "商品单价": detail.price,
                    "经费来源": detail.funds,
                    "订购数量": detail.order_quantity,
                    "实收数量": detail.received_quantity,
                    "总价": detail.cost,
                    "收货时间": str(detail.recipient_time),
                    "学校": first_name
                }
                data.append(detail_data)

        # 返回文件响应
        df = pd.DataFrame(data)
        file_name = f"{first_name}_{start_date}~{end_date}_订单报表.xlsx"

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{quote(file_name)}"'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')

        return response

    @action(methods=['post'], detail=False)
    def gendeliver(self, request, pk=None):
        """
        生成对应日期的送货表
        """
        deliver_date = request.data.get("deliver_date")
        school_id = request.data.get("school_id")

        if not deliver_date:
            return Response({
                "msg": "未选择送货时间",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not school_id:
            return Response({
                "msg": "未选择收货单位",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取指定送货时间和收货单位的查询集
        queryset = self.get_queryset()
        queryset = queryset.filter(deliver_date=deliver_date, creater_id=school_id)
        if not queryset:
            return Response({
                "msg": "未找到对应订单",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 制作表单数据
        data = []
        no = 1
        total = 0
        for order in queryset:
            if order.status == '6':
                continue
            details = order.details.all()
            for detail in details:
                detail_data = []
                detail_data.append(no)
                no += 1
                detail_data.append(detail.product_name)
                detail_data.append(detail.brand)
                detail_data.append(detail.description)
                detail_data.append('')
                detail_data.append(detail.order_quantity)
                detail_data.append(detail.price)
                cost = round(float(detail.price) * float(detail.order_quantity), 2)
                total += cost
                detail_data.append(cost)
                detail_data.append('')
                data.append(detail_data)
        
        # 填充表格数据
        # data1 = [
        #     [1, '产品A', '品牌X', '规格1', '个', 100, 10, 1000, ''],
        #     [2, '产品B', '品牌Y', '规格2', '盒', 50, 20, 1000, ''],
        #     # 添加更多数据...
        # ]

        # 获取收货单位
        first_name = AccountModel.objects.get(id=school_id).first_name
        
        """
        以下为生成表格样式
        """
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {"in_memory":True})
        worksheet = workbook.add_worksheet()


        # 设置列宽度
        worksheet.set_column('A:I', 9)   # 单位列

        # 合并单元格并添加标题
        worksheet.set_row(0, 33)
        worksheet.merge_range('A1:I1', '泸定县粮油购销有限责任公司配送清单', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 18, 
            'bold': True
        }))

        worksheet.set_row(1, 25)
        worksheet.write('A2', '收货单位', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.merge_range('B2:D2', first_name, workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.write('E2', '配送日期', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.merge_range('F2:I2', deliver_date, workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))

        # 添加表头
        worksheet.set_row(2, 25)
        headers = ['行号', '品名', '品牌', '规格', '单位', '数量', '单价', '金额', '备注']
        worksheet.write_row('A3', headers, workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
            'border': 1
        }))

        # 写入数据
        row_start = 3
        row_for_total = 0
        for row, record in enumerate(data, start=row_start):
            worksheet.set_row(row, 25)
            worksheet.write_row(row, 0, record, workbook.add_format({
                'border': 1,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter'
                }))
            row_for_total = row

        # 添加合计
        row_for_total += 1
        worksheet.set_row(row_for_total, 25)
        worksheet.write(f'A{row_for_total+1}',"合计", workbook.add_format({
                'border': 1,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter'
                }))

        worksheet.merge_range(f'B{row_for_total+1}:F{row_for_total+1}', '   万    仟    佰    拾    元    角    分', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter',
            'bold': True,
            'border': 1
        }))
        worksheet.write(f'G{row_for_total+1}','小计', workbook.add_format({
                'border': 1,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter'
                }))
        worksheet.write(f'H{row_for_total+1}', total, workbook.add_format({
                'border': 1,
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter'
                }))
        worksheet.write(f'I{row_for_total+1}','', workbook.add_format({
                'border': 1,
                }))
        
        # 添加额外信息
        row_for_total += 1
        worksheet.set_row(row_for_total, 25)
        worksheet.write(f'A{row_for_total+1}', '送货人', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.merge_range(f'B{row_for_total+1}:C{row_for_total+1}', '')

        worksheet.write(f'D{row_for_total+1}', '验收人', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.merge_range(f'E{row_for_total+1}:F{row_for_total+1}', '')

        worksheet.write(f'G{row_for_total+1}', '负责人', workbook.add_format({
            'align': 'center', 
            'valign': 'vcenter', 
            'font_size': 11, 
        }))
        worksheet.merge_range(f'H{row_for_total+1}:I{row_for_total+1}', '')

        # 关闭Excel文件
        workbook.close()

        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        file_name = f"{first_name}_{deliver_date}_送货单.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{quote(file_name)}"'

        return response

    @action(methods=['post'], detail=False)
    def gendoc(self, request, pk=None):
        from docx import Document
        from docx.shared import Pt  # 用于设置字体大小
        from docx.oxml.ns import qn  # 用于设置字体

        # 定位模板文件
        output = BytesIO()
        template_path = os.path.join(settings.MEDIA_ROOT, 'template.docx')
        doc = Document(template_path)

        # 接收参数
        school_id = request.data.get("school_id")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        if not school_id:
            return Response({
                "msg": "请传入学校ID",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        if not start_date or not end_date:
            return Response({
                "msg": "请传入起止时间",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 生成填充数据
        try:
            school = AccountModel.objects.get(id=school_id)
        except:
            return Response({
                "msg": "ID对应的学校不存在",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if school.role != "2":
            return Response({
                "msg": "ID对应的学校不存在",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取学校名称
        school_name = school.first_name
        
        # 结束日期加一天，避免漏掉最后一天的数据
        _end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d") + datetime.timedelta(days=1)

        # 获取查询集
        queryset = self.get_queryset()
        queryset = queryset.filter(finish_time__gte=start_date, finish_time__lte=_end_date, creater_id=school_id)

        if not queryset:
            return Response({
                "msg": "未查询到时间段内订单",
                "data": None,
                "code": status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)

        # 生成日期表示
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        start_date = start_date.strftime("%Y 年 %m 月 %d 日")
        end_date = end_date.strftime("%Y 年 %m 月 %d 日")
        date = f"{start_date}  ------------ {end_date}"

        # 获取经费情况
        funds_dic = {}
        for order in queryset:
            order_details = order.details.all()
            for detail in order_details:
                now_fund = detail.funds
                funds_dic[now_fund] = funds_dic.get(now_fund, 0) + detail.cost
        
        total = 0
        for k,v in funds_dic.items():
            total += v

        """
        以下为生成docx
        """
        # 遍历文档中的所有表格
        for table in doc.tables:
            for row in table.rows:
                if row.cells[0].text == "学校名称":
                    row.cells[1].text = ''
                    run = row.cells[1].paragraphs[0].add_run(school_name)
                    run.font.name = '宋体'  # 设置字体
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')  # 强制设置中文字体为宋体
                    run.font.size = Pt(11)  # 设置字体大小为11号
                if row.cells[0].text == "结算时间":
                    row.cells[1].text = ''
                    run = row.cells[1].paragraphs[0].add_run(date)
                    run.font.name = '宋体'  # 设置字体
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')  # 强制设置中文字体为宋体
                    run.font.size = Pt(11)  # 设置字体大小为11号
                if row.cells[0].text == "结算资金（元）":
                    if row.cells[1].text == "以上三项合计金额：":
                        res = row.cells[1].text + str(total)
                        row.cells[1].text = ''
                        run = row.cells[1].paragraphs[0].add_run(res)
                        run.font.name = '宋体'  # 设置字体
                        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')  # 强制设置中文字体为宋体
                        run.font.size = Pt(11)  # 设置字体大小为11号
                    else:
                        for k, v in funds_dic.items():
                            if k in row.cells[1].text:
                                res = row.cells[1].text + str(v)
                                row.cells[1].text = ''
                                run = row.cells[1].paragraphs[0].add_run(res)
                                run.font.name = '宋体'  # 设置字体
                                run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')  # 强制设置中文字体为宋体
                                run.font.size = Pt(11)  # 设置字体大小为11号
        
        doc.save(output)
        output.seek(0)
        response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        file_name = f"{start_date}~{end_date}_{school_name}经费情况.docx"
        response['Content-Disposition'] = f'attachment; filename={quote(file_name)}'


        return response
    
class OrderDetailsViewset(viewsets.GenericViewSet):
    """
    仅用于确认收货，无CRUD方法
    """
    queryset = OrderDetailModel.objects.all()
    permission_classes = [mypermissions.IsRole2]
    serializer_class = OrderDetailModelSerializer

    # 仅获取当期用户创建的订单详情
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(order__creater_id=self.request.user.id)
        return queryset
    
    @action(methods=['post'], detail=True)
    def confirm(self, request, pk=None):
        """
        确认收货，并修改订单的完成项和完成时间
        """
        # 获取data中的数据，实际收货数量
        received_quantity = request.data.get("received_quantity")

        # 获取到当期订单详情实例，用于修改
        item = self.get_object()

        # 修改订单详情数据
        item.received_quantity = received_quantity
        item.cost = float(received_quantity) * float(item.price)
        item.recipient_id = request.user.id
        item.recipient_time = datetime.datetime.now()
        item.save()

        # 修改订单详情关联的订单的数据，修改完成项
        order = item.order
        order.finish_num += 1

        # 如果完成项等于下单数量，则添加完成时间，表示订单已全部完成
        if order.finish_num == order.product_num:
            order.status = 4
        order.save()

        # 返回响应
        return Response({
            "msg": "商品收货成功",
            "data": None,
            "code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)
    


    
