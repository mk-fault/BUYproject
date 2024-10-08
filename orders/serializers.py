from rest_framework import serializers
from .models import *
from goods.models import GoodsModel, PriceModel
import datetime
import os

class FundsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundsModel
        fields = "__all__"
        
class CartModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartModel
        exclude = ["creater_id"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            product = instance.product
        except:
            instance.delete()
            raise serializers.ValidationError(f"商品不存在，刷新以删除购物车商品")
        data['product_name'] = product.name
        data['product_id'] = data.pop('product')
        data['description'] = product.description
        data['category'] = product.category.name
        data['brand'] = product.brand
        data['image'] = self.context['request'].build_absolute_uri(product.image.url) if product.image else None
        try:
            now_time = datetime.datetime.now()
            # now_time = "2024-07-18"
            price = product.prices.filter(status=2, start_date__lte=now_time, end_date__gte=now_time).order_by('-id').first()
            data['price'] = price.price  # Convert to integer
        except:
            # instance.delete()
            # raise serializers.ValidationError(f"{product.name}不存在可用价格，刷新以删除购物车商品")
            data['price'] = 0
        data['funds'] = instance.funds.name
        data['tolto_price'] = round(float(data['price']) * float(data['quantity']), 2)  # Convert to floats and round to 2 decimal places
        return data
    
class CartPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartModel
        fields = ["quantity", "funds", "note"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['funds'] = instance.funds.name
        return data
            


class OrdersModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersModel
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status_code'] = data.pop("status")
        data['status'] = instance.get_status_display()
        return data
    
class OrderPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersModel
        fields = ["deliver_date", "note"]
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # data['status_code'] = data.pop("status")
        # data['status'] = instance.get_status_display()
        return data

class OrderDetailModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetailModel
        fields = "__all__"
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        server_url = self.context['request'].build_absolute_uri('/')
        data['image'] = os.path.join(server_url, 'media', instance.image) if instance.image else None
        data['license'] = os.path.join(server_url, 'media', instance.license) if instance.license else None
        return data
