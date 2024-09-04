from rest_framework import serializers
import datetime
from .models import *
import os
import shutil
from django.conf import settings

class PriceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceModel
        fields = "__all__"
        read_only_fields = ['product', 'cycle', 'start_date', 'end_date', 'status', 'creater_id',
                            'create_time', 'reviewer_id', 'review_time']
        # read_only_fields = "__all__"
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['product_id'] = data.pop('product')
        data['cycle_id'] = data.pop('cycle')
        data['cycle_name'] = instance.cycle.name
        data['status_code'] = data.pop('status')
        data['status'] = instance.get_status_display()
        try:
            product = instance.product
        except:
            instance.delete()
            raise serializers.ValidationError("商品不存在, 价格对象已删除")
        data['product_name'] = product.name
        data['product_brand'] = product.brand
        data['product_category'] = product.category.name
        data['product_description'] = product.description
        return data
    
class PricePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceModel
        fields = ["price", "price_check_1", "price_check_2", "price_check_avg"]

# class UnitModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UnitModel
#         fields = ['id', 'name']

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    price_check_1 = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, allow_null=True)
    price_check_2 = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, allow_null=True)
    price_check_avg = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    status = serializers.BooleanField(default=True)

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'price_check_1', 'price_check_2', 'price_check_avg', 'category', 'status', 'brand', 'license', 'status']

    # 创建一个商品时，为它生成目前以及日期往后已存在的价格周期的价格对象
    def create(self, validated_data):
        if GoodsModel.objects.filter(name=validated_data['name'], description=validated_data['description'], brand=validated_data['brand']).exists():
            if 'upload' in self.context:
                product_obj = GoodsModel.objects.get(name=validated_data['name'], description=validated_data['description'], brand=validated_data['brand'])
                cycle_id = self.context.get("cycle_id")
                try:
                    price_obj = PriceModel.objects.get(product=product_obj, cycle__id=cycle_id)
                    price_obj.price = validated_data['price']
                    price_obj.price_check_1 = validated_data['price_check_1']
                    price_obj.price_check_2 = validated_data['price_check_2']
                    price_obj.price_check_avg = validated_data['price_check_avg']
                    price_obj.status = 2
                    price_obj.reviewer_id = self.context['user_id']
                    price_obj.review_time = datetime.datetime.now()
                    price_obj.save()
                except:
                    price_obj = PriceModel.objects.create(product=product_obj, price=validated_data['price'], price_check_1=validated_data['price_check_1'], 
                                                            price_check_2=validated_data['price_check_2'], price_check_avg=validated_data['price_check_avg'], 
                                                            cycle=PriceCycleModel.objects.get(id=cycle_id), start_date=PriceCycleModel.objects.get(id=cycle_id).start_date, 
                                                            end_date=PriceCycleModel.objects.get(id=cycle_id).end_date, status=2, creater_id=self.context['user_id'], 
                                                            create_time=datetime.datetime.now(), reviewer_id=self.context['user_id'], review_time=datetime.datetime.now())
                return product_obj
            else:   
                raise serializers.ValidationError("已存在该规格商品")
        price = validated_data.pop('price')
        price_check_1 = validated_data.pop('price_check_1')
        price_check_2 = validated_data.pop('price_check_2')
        price_check_avg = validated_data.pop('price_check_avg')


        # 获取开始时间在当前时间之后的价格周期
        now_time = datetime.datetime.now()
        # now_time = "2024-07-18"
        cycle_queryset = PriceCycleModel.objects.filter(end_date__gte=now_time, status=True)

        # 不存在价格周期则为商品添加上ori_price,下次添加价格周期时,会使用此价格

        if not cycle_queryset:
            raise serializers.ValidationError("没有可用的价格周期，无法添加商品")
        else:
            instance = super().create(validated_data)
            try:
                # Convert now_time to a date object
                now_date = datetime.datetime.now().date()

                # 对于每一个周期,都为商品添加一个价格对象
                for cycle in cycle_queryset:

                    # 如果是上传文件的方式添加的商品，则为所传入周期的价格提交价格请求，即设置价格状态为2（已审核），其他周期的价格状态设为0
                    if self.context.get("cycle_id"):
                        if cycle.id == int(self.context.get("cycle_id")):
                            PriceModel.objects.create(product=instance, price=price, price_check_1=price_check_1, price_check_2=price_check_2,
                                                price_check_avg=price_check_avg, cycle=cycle, start_date=cycle.start_date, end_date=cycle.end_date,
                                                status=2, creater_id=self.context['user_id'], create_time=now_time, reviewer_id=self.context['user_id'], review_time=now_time)
                        else:
                            PriceModel.objects.create(product=instance, price=price, price_check_1=price_check_1, price_check_2=price_check_2,
                                                price_check_avg=price_check_avg, cycle=cycle, start_date=cycle.start_date, end_date=cycle.end_date,
                                                status=0) 
                        
                    # 如果是手动添加的商品，则为现在处于的周期的价格提交价格请求，即设置价格状态为1（已提交），未包括当前时间的周期的价格状态设为0
                    else:
                        if now_date > cycle.start_date and now_date < cycle.end_date:
                            PriceModel.objects.create(product=instance, price=price, price_check_1=price_check_1, price_check_2=price_check_2,
                                                price_check_avg=price_check_avg, cycle=cycle, start_date=cycle.start_date, end_date=cycle.end_date,
                                                status=1, creater_id=self.context['user_id'], create_time=now_time)
                        else:
                            PriceModel.objects.create(product=instance, price=price, price_check_1=price_check_1, price_check_2=price_check_2,
                                                price_check_avg=price_check_avg, cycle=cycle, start_date=cycle.start_date, end_date=cycle.end_date,
                                                status=0, creater_id=self.context['user_id'], create_time=now_time)
            except:
                instance.delete()
                raise serializers.ValidationError("为商品添加价格失败")
        return instance

    def update(self, instance, validated_data): 
        # 修改商品图片名字为商品名字+时间戳
        if 'image' in validated_data and validated_data['image']:
            validated_data['image'].name = instance.name + str(int(datetime.datetime.now().timestamp())) + os.path.splitext(validated_data['image'].name)[1]
        
        # 修改商品资质名字为商品名字+时间戳
        if 'license' in validated_data and validated_data['license']:
            validated_data['license'].name = instance.name + str(int(datetime.datetime.now().timestamp())) + os.path.splitext(validated_data['license'].name)[1]
        data = super().update(instance, validated_data)

        # 如果是更新商品，则将旧图片复制到detail_img/goods和detail_img/license下
        if 'image' in validated_data and validated_data['image']:
            image = instance.image.path
            detail_image_path = os.path.join(settings.MEDIA_ROOT, 'detail_image', 'goods')
            if not os.path.exists(detail_image_path):
                os.makedirs(detail_image_path)
            shutil.copyfile(image, os.path.join(detail_image_path, os.path.basename(image)))
        if 'license' in validated_data and validated_data['license']:
            license = instance.license.path
            detail_image_path = os.path.join(settings.MEDIA_ROOT, 'detail_image', 'license')
            if not os.path.exists(detail_image_path):
                os.makedirs(detail_image_path)
            shutil.copyfile(license, os.path.join(detail_image_path, os.path.basename(license)))
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        now_time = datetime.datetime.now()
        # now_time = "2024-07-18"
        price = instance.prices.filter(status=2, start_date__lte=now_time, end_date__gte=now_time).order_by('-id').first()
        if not price:
            data['price'] = None
        else:
            data['price'] = price.price
        # data['unit'] = instance.unit.name
        data['category'] = instance.category.name  
        return data
    
class PriceCycleModelSerializer(serializers.ModelSerializer):

    # status = serializers.BooleanField(default=True)
    class Meta:
        model = PriceCycleModel
        exclude = ['create_at', 'update_at', 'status']
        read_only_fields = ['creater_id']
        
    def create(self, validated_data):
        validated_data['creater_id'] = self.context['request'].user.id
        return super().create(validated_data)

