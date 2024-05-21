from django.db import models

# Create your models here.

class CategoryModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="类别名")

    class Meta:
        db_table = 'category'
        verbose_name = '类别'
        verbose_name_plural = verbose_name

class GoodsModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='商品名称')
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE, verbose_name='商品类别')
    image = models.ImageField(upload_to='goods/', verbose_name='商品图片')
    description = models.TextField(verbose_name='商品描述')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'goods'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

class UnitModel(models.Model):
    name = models.CharField(max_length=10, verbose_name='单位名称')

    class Meta:
        db_table = 'unit'
        verbose_name = '单位'
        verbose_name_plural = verbose_name

class PriceModel(models.Model):
    product = models.ForeignKey(GoodsModel, related_name='prices', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.ForeignKey(UnitModel, on_delete=models.CASCADE, default=1)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.BooleanField(default=True)

    class Meta:
        db_table = 'price'
        verbose_name = '价格'
        verbose_name_plural = verbose_name

