from django.db import models
import os
import shutil
from django.conf import settings
# Create your models here.

# 商品种类模型
class CategoryModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="类别名")

    class Meta:
        db_table = 'category'
        verbose_name = '类别'
        verbose_name_plural = verbose_name

# 商品计量单位模型
# class UnitModel(models.Model):
#     name = models.CharField(max_length=10, verbose_name='单位名称')

#     class Meta:
#         db_table = 'unit'
#         verbose_name = '单位'
#         verbose_name_plural = verbose_name

# 商品模型
class GoodsModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='商品名称')
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE, verbose_name='商品类别')
    brand = models.CharField(max_length=100, verbose_name='商品品牌', blank=True, null=True)
    image = models.ImageField(upload_to='goods/', verbose_name='商品图片',blank=True, null=True)
    license = models.ImageField(upload_to='license/', verbose_name='商品资质', blank=True, null=True)
    description = models.CharField(max_length=100, verbose_name='商品规格')
    status = models.BooleanField(verbose_name="商品状态",default=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    update_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'goods'
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        # unique_together = (('name', 'description'),)

    # 重写save方法，将image和license的图片重命名为图片名+时间戳;如果是更新商品，将旧图片复制到detail_img/goods和detail_img/license下
    # def save(self, *args, **kwargs):
    #     # if self.pk:
    #     #     old = GoodsModel.objects.get(pk=self.pk)
    #     #     if old.image != self.image and old.image:
    #     #         # 将旧照片复制到detail_img/goods下
    #     #         old_image_path = os.path.join(settings.MEDIA_ROOT, old.image.name)
    #     #         new_image_path = os.path.join(settings.MEDIA_ROOT, 'detail_img/goods', old.image.name.split('/')[-1])
    #     #         shutil.copyfile(old_image_path, new_image_path)
    #     #     if old.license != self.license and old.license:
    #     #         # 将旧照片复制到detail_img/license下
    #     #         old_license_path = os.path.join(settings.MEDIA_ROOT, old.license.name)
    #     #         new_license_path = os.path.join(settings.MEDIA_ROOT, 'detail_img/license', old.license.name.split('/')[-1])
    #     #         shutil.copyfile(old_license_path, new_license_path)
        
    #     # 获得更新

    #     self.image.name = self.name + str(int(self.update_at.timestamp())) + '.' + self.image.name.split('.')[-1]
    #     self.license.name = self.name + str(int(self.update_at.timestamp())) + '.' + self.license.name.split('.')[-1]
    #     super(GoodsModel, self).save(*args, **kwargs)

    #     # 将图片复制到detail_img/goods和detail_img/license下
    #     if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'detail_img/goods')):
    #         os.makedirs(os.path.join(settings.MEDIA_ROOT, 'detail_img/goods'))
    #     if self.image:
    #         print(os.path.join(settings.MEDIA_ROOT, self.image.name))
    #     shutil.copyfile(os.path.join(settings.MEDIA_ROOT, self.image.name), os.path.join(settings.MEDIA_ROOT, 'detail_img/goods', self.image.name.split('/')[-1]))
    #     if not os.path.exists(os.path.join(settings.MEDIA_ROOT, 'detail_img/license')):
    #         os.makedirs(os.path.join(settings.MEDIA_ROOT, 'detail_img/license'))
    #     shutil.copyfile(os.path.join(settings.MEDIA_ROOT, self.license.name), os.path.join(settings.MEDIA_ROOT, 'detail_img/license', self.license.name.split('/')[-1]))

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
    price_check_1 = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="询价1", blank=True, null=True)
    price_check_2 = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="询价2", blank=True, null=True)
    price_check_avg = models.DecimalField(max_digits=10, decimal_places=2,verbose_name="平均询价", blank=True, null=True)
    cycle = models.ForeignKey(PriceCycleModel, related_name="prices", on_delete=models.CASCADE, verbose_name="关联周期")
    start_date = models.DateField(verbose_name="价格开始时间")
    end_date = models.DateField(verbose_name="价格结束时间")
    status_choice = (("0", "未申报"), ("1", "未审核"), ("2", "已审核"),("-1", "已拒绝"),("-99", "已弃用"))
    status = models.CharField(choices=status_choice, max_length=10, verbose_name="报价状态", default=0, db_index=True)
    creater_id = models.BigIntegerField(verbose_name="报价人ID", blank=True, null=True, default=None)
    create_time = models.DateTimeField(verbose_name="报价申报时间", blank=True, null=True, default=None)
    reviewer_id = models.BigIntegerField(verbose_name="审核人ID", blank=True, null=True, default=None)
    review_time = models.DateTimeField(verbose_name="报价审核时间", blank=True, null=True, default=None)

    class Meta:
        db_table = 'price'
        verbose_name = '价格'
        verbose_name_plural = verbose_name

# # 价格请求模型
# class PriceRequestModel(models.Model):
#     price = models.OneToOneField(PriceModel, on_delete=models.CASCADE)
#     product = models.OneToOneField(GoodsModel, on_delete=models.CASCADE)
#     requested_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'price_request'
#         verbose_name = '价格请求'
#         verbose_name_plural = verbose_name


