from django.db import models
from goods.models import GoodsModel
from goods.models import PriceCycleModel

# Create your models here.
class FundsModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="经费来源名字")

    class Meta:
        db_table = 'funds'
        verbose_name = '经费来源'
        verbose_name_plural = verbose_name

class CartModel(models.Model):
    product = models.ForeignKey(GoodsModel, on_delete=models.CASCADE, verbose_name="商品实例")
    funds = models.ForeignKey(FundsModel, on_delete=models.CASCADE, verbose_name="经费实例", null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="购买数量")
    creater_id = models.IntegerField(verbose_name="加购人ID", db_index=True)

    class Meta:
        db_table = 'cart'
        verbose_name = '购物车'
        verbose_name_plural = verbose_name

class OrdersModel(models.Model):
    status_choice = (("0", "待接单"), ("1", "待发货"), ("2", "配送中"), ("3", "配送完成"), ("4", "已收货待复核"), ("5", "订单有疑问"), ("6", "订单完成"), ("-1", "撤销"))
    status = models.CharField(max_length=10, choices=status_choice, verbose_name="订单状态", db_index=True)
    creater_id = models.IntegerField(verbose_name="订单创建人ID", db_index=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="订单创建时间")
    accepter_id = models.IntegerField(verbose_name="订单接受人ID", blank=True, null=True)
    accept_time = models.DateTimeField(verbose_name="订单接受时间", blank=True, null=True)
    deliver_date = models.DateField(verbose_name="订单预定送达日期", blank=True, null=True)
    product_num = models.IntegerField(verbose_name="订单项个数", default=0)
    finish_num = models.IntegerField(verbose_name="完成项个数", default=0)
    finish_time = models.DateTimeField(verbose_name="订单完成时间", blank=True, null=True)
    cycle = models.ForeignKey(PriceCycleModel, on_delete=models.SET_NULL, verbose_name="价格周期", blank=True, null=True)
    note = models.TextField(verbose_name="备注", blank=True, null=True)
    # finish_status_choice = (("0", "未完成"), ("-1", "完成但数量有误"), ("1", "全部完成"))
    # finish_status = models.CharField(max_length=10, choices=finish_status_choice, verbose_name="订单完成情况")

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name

class OrderDetailModel(models.Model):
    order = models.ForeignKey(OrdersModel, related_name='details',on_delete=models.CASCADE, verbose_name="订单实例")
    product_id = models.IntegerField(verbose_name="商品ID")
    product_name = models.CharField(max_length=100, verbose_name="商品名称")
    brand = models.CharField(max_length=100, verbose_name="商品品牌", blank=True, null=True)
    description = models.TextField(verbose_name="商品规格")
    category = models.CharField(max_length=100, verbose_name="商品类别")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品价格")
    funds = models.CharField(max_length=100, verbose_name="经费来源")
    order_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="购入数量")
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="实收数量", blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="商品总价", blank=True, null=True)
    recipient_id = models.IntegerField(verbose_name="收货人ID", blank=True, null=True)
    recipient_time = models.DateTimeField(verbose_name="收货时间", blank=True, null=True)
    image = models.CharField(max_length=200, verbose_name="商品图片", blank=True, null=True)
    license = models.CharField(max_length=200, verbose_name="商品资质", blank=True, null=True)

    class Meta:
        db_table = 'order_detail'
        verbose_name = '订单详情'
        verbose_name_plural = verbose_name