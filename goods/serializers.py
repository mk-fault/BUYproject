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
        product = instance.product
        data['product_name'] = product.name
        data['product_unit'] = product.unit.name
        data['product_category'] = product.category.name
        data['product_description'] = product.description
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
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'unit', 'category']

    def create(self, validated_data):
        validated_data['ori_price'] = validated_data.pop('price')
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            now_time = datetime.datetime.now()
            # now_time = "2024-06-18"
            price = instance.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).first()
            data['price'] = price.price
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        except:
            # if instance.ori_price is not None:
            #     data['price'] = instance.ori_price
            #     data['status'] = instance.status
            # else:
            #     data['price'] = None
            data['price'] = None
            data['unit'] = instance.unit.name
            data['category'] = instance.category.name
        return data

    
class PriceRequestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceRequestModel
        fields = ['id', 'requested_at']
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['price'] = instance.price.price
        data['cycle_name'] = instance.price.cycle.name
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
        exclude = ['create_at', 'update_at']
        read_only_fields = ['creater_id']
        
    def create(self, validated_data):
        validated_data['creater_id'] = self.context['request'].user.id
        return super().create(validated_data)