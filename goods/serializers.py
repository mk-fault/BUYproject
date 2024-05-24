from rest_framework import serializers
import datetime
from .models import *

class PriceModelSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(default=False)
    class Meta:
        model = PriceModel
        fields = ['price', 'start_time', 'end_time', 'status', 'product']

class UnitModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitModel
        fields = ['id', 'name']

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)  # 添加一个价格字段
    status = serializers.BooleanField(default=True)

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'unit', 'category','status']
        # extra_kwargs = {
        #     'category':{
        #         'required':True
        #     }
        # }

    def create(self, validated_data):
        # 获取传入的价格数据
        price_data = validated_data.pop('price')

        # 获取当前时间和结束时间
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(days=30)

        # 创建商品对象
        product = GoodsModel.objects.create(**validated_data)

        # 创建关联的价格对象
        price = PriceModel.objects.create(product=product, start_time=start_time, end_time=end_time, price=price_data)

        # 创建关联的价格请求对象
        PriceRequestModel.objects.create(product=product, price=price)

        return product
    
    def to_representation(self, instance):
        # 编辑返回的数据
        data = super().to_representation(instance)
        try:
            data['price'] = instance.prices.filter(status=True).first().price
            data['start_time'] = instance.prices.filter(status=True).first().start_time
            data['end_time'] = instance.prices.filter(status=True).first().end_time
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        except:
            # raise serializers.ValidationError("获取商品失败")
            data['price'] = None
            data['start_time'] = None
            data['end_time'] = None
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        return data
    
class PriceRequestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRequestModel
        fields = ['id', 'requested_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['price_id'] = data['price']
        data['price'] = instance.price.price
        data['start_time'] = instance.price.start_time
        data['end_time'] = instance.price.end_time
        data['unit'] = instance.product.unit.name
        data['category'] = instance.product.category.name
        data['product'] = instance.product.name
        data['product_id'] = instance.product.id
        return data