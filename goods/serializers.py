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
        data['cycle_name'] = instance.cycle.name
        # data['status'] = instance.get_status_display()
        product = instance.product
        data['product_name'] = product.name
        data['product_unit'] = product.unit.name
        data['product_category'] = product.category.name
        data['product_description'] = product.description
        return data
    
class PricePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceModel
        fields = ["price",]

class UnitModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitModel
        fields = ['id', 'name']

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)
    status = serializers.BooleanField(default=True,write_only=True)

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'unit', 'category', 'status']

    # 创建一个商品时，为它生成目前以及日期往后已存在的价格周期的价格对象
    def create(self, validated_data):
        price = validated_data.pop('price')
        instance = super().create(validated_data)
        now_time = datetime.datetime.now()
        # now_time = "2024-07-18"
        cycle_queryset = PriceCycleModel.objects.filter(end_date__gt=now_time, status=True)
        if not cycle_queryset:
            instance.ori_price = price
            instance.save()
        else:
            for cycle in cycle_queryset:
                PriceModel.objects.create(product=instance, price=price, cycle=cycle, start_date=cycle.start_date, end_date=cycle.end_date,status=0)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            now_time = datetime.datetime.now()
            # now_time = "2024-07-18"
            price = instance.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).first()
            data['price'] = price.price
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        except:
            data['price'] = None
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        return data

    
# class PriceRequestModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PriceRequestModel
#         fields = ['id', 'requested_at']
    
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         data['price'] = instance.price.price
#         data['cycle_name'] = instance.price.cycle.name
#         data['start_date'] = instance.price.start_date
#         data['end_date'] = instance.price.end_date
#         data['unit'] = instance.product.unit.name
#         data['category'] = instance.product.category.name
#         data['product'] = instance.product.name
#         data['product_id'] = instance.product.id
#         data['description'] = instance.product.description
#         return data
    
class PriceCycleModelSerializer(serializers.ModelSerializer):
    # status = serializers.BooleanField(default=True)
    class Meta:
        model = PriceCycleModel
        exclude = ['create_at', 'update_at', 'status']
        read_only_fields = ['creater_id']
        
    def create(self, validated_data):
        validated_data['creater_id'] = self.context['request'].user.id
        return super().create(validated_data)
