from django.db import models

# Create your models here.

# 商品种类模型
class CategoryModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="类别名")

    class Meta:
        db_table = 'category'
        verbose_name = '类别'
        verbose_name_plural = verbose_name

# 商品计量单位模型
class UnitModel(models.Model):
    name = models.CharField(max_length=10, verbose_name='单位名称')

    class Meta:
        db_table = 'unit'
        verbose_name = '单位'
        verbose_name_plural = verbose_name

# 商品模型
class GoodsModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='商品名称')
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE, verbose_name='商品类别')
    unit = models.ForeignKey(UnitModel, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='goods/', verbose_name='商品图片',blank=True, null=True)
    # ori_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品初始价格",blank=True,null=True)
    description = models.TextField(verbose_name='商品描述')
    status = models.BooleanField(verbose_name="商品状态",default=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'goods'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

# 价格周期模型
class PriceCycleModel(models.Model):
    name = models.CharField(max_length=200, verbose_name="周期名字")
    start_date = models.DateField(verbose_name="周期开始时间")
    end_date = models.DateField(verbose_name="周期结束时间")
    status = models.BooleanField(verbose_name="周期状态", default=True)
    creater_id = models.BigIntegerField(verbose_name="创建人ID")
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'price_cycle'
        verbose_name = '价格周期'
        verbose_name_plural = verbose_name

# 价格模型
class PriceModel(models.Model):
    product = models.ForeignKey(GoodsModel, related_name='prices', on_delete=models.CASCADE, verbose_name="关联商品")
    price = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="当前报价")
    cycle = models.ForeignKey(PriceCycleModel, related_name="prices", on_delete=models.CASCADE, verbose_name="关联周期")
    start_date = models.DateField(verbose_name="价格开始时间")
    end_date = models.DateField(verbose_name="价格结束时间")
    status_choice = ((0, "未申报"), (1, "未审核"), (2, "已审核"),(-1, "已拒绝"),(4, "过期"))
    status = models.CharField(choices=status_choice, max_length=10, verbose_name="报价状态", default=0)
    creater_id = models.BigIntegerField(verbose_name="报价人ID", blank=True, null=True, default=None)
    create_time = models.DateTimeField(verbose_name="报价申报时间", blank=True, null=True, default=None)
    reviewer_id = models.BigIntegerField(verbose_name="审核人ID", blank=True, null=True, default=None)
    review_time = models.DateTimeField(verbose_name="报价审核时间", blank=True, null=True, default=None)

    class Meta:
        db_table = 'price'
        verbose_name = '价格'
        verbose_name_plural = verbose_name

# 价格请求模型
class PriceRequestModel(models.Model):
    price = models.OneToOneField(PriceModel, on_delete=models.CASCADE)
    product = models.OneToOneField(GoodsModel, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_request'
        verbose_name = '价格请求'
        verbose_name_plural = verbose_name


