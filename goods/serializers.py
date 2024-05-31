from rest_framework import serializers
import datetime
from .models import *

class PriceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceModel
        fields = "__all__"
        read_only_fields = ['product', 'cycle', 'start_date', 'end_date', 'status', 'creater_id',
                            'create_time', 'reviewer_id', 'review_time']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['product_id'] = data.pop('product')
        data['cycle_id'] = data.pop('cycle')
        return data

class UnitModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitModel
        fields = ['id', 'name']

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    # price = serializers.DecimalField(max_digits=10, decimal_places=2)  # 添加一个价格字段
    # status = serializers.BooleanField(default=True)

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'ori_price', 'unit', 'category','status']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['ori_price'] is not None:
            data['price'] = data.pop('ori_price')
            return data
        else:
            try:
                data['price'] = instance.prices.filter(status=2).first().price
                data['start_date'] = instance.prices.filter(status=2).first().start_date
                data['end_date'] = instance.prices.filter(status=2).first().end_date
                data['unit'] = instance.unit.name
                data['category'] = instance.category.name
            except:
                data['price'] = None
                data['start_date'] = None
                data['end_date'] = None
                data['unit'] = instance.unit.name
                data['category'] = instance.category.name
            return data
                


    # def create(self, validated_data):
    #     # 获取传入的价格数据
    #     price_data = validated_data.pop('price')

    #     # 获取当前时间和结束时间
    #     start_time = datetime.datetime.now()
    #     end_time = start_time + datetime.timedelta(days=30)

    #     # 创建商品对象
    #     product = GoodsModel.objects.create(**validated_data)

    #     # 创建关联的价格对象
    #     price = PriceModel.objects.create(product=product, start_time=start_time, end_time=end_time, price=price_data)

    #     # 创建关联的价格请求对象
    #     PriceRequestModel.objects.create(product=product, price=price)

    #     return product
    
    # def to_representation(self, instance):
    #     # 编辑返回的数据
    #     data = super().to_representation(instance)
    #     try:
    #         data['price'] = instance.prices.filter(status=True).first().price
    #         data['start_time'] = instance.prices.filter(status=True).first().start_time
    #         data['end_time'] = instance.prices.filter(status=True).first().end_time
    #         data['unit'] = instance.unit.name
    #         data['category'] = instance.category.name
    #     except:
    #         # raise serializers.ValidationError("获取商品失败")
    #         data['price'] = None
    #         data['start_time'] = None
    #         data['end_time'] = None
    #         data['unit'] = instance.unit.name
    #         data['category'] = instance.category.name
    #     return data
    
class PriceRequestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRequestModel
        fields = ['id', 'requested_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['price_id'] = data['price']
        data['price'] = instance.price.price
        data['start_date'] = instance.price.start_date
        data['end_date'] = instance.price.end_date
        data['unit'] = instance.product.unit.name
        data['category'] = instance.product.category.name
        data['product'] = instance.product.name
        data['product_id'] = instance.product.id
        data['description'] = instance.product.description
        return data
    
class PriceCycleModelSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(default=True)
    class Meta:
        model = PriceCycleModel
        fields = '__all__'
        read_only_fields = ['creater_id']
        
    def create(self, validated_data):
        validated_data['creater_id'] = self.context['request'].user.id
        return super().create(validated_data)