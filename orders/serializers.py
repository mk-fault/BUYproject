from rest_framework import serializers
from .models import *
from goods.models import GoodsModel, PriceModel
import datetime

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
        product = instance.product
        data['product_name'] = product.name
        data['product_id'] = data.pop('product')
        data['description'] = product.description
        data['category'] = product.category.name
        data['unit'] = product.unit.name
        data['image'] = self.context['request'].build_absolute_uri(product.image.url) if product.image else None
        try:
            now_time = datetime.datetime.now()
            # now_time = "2024-07-18"
            price = product.prices.filter(status=2, start_date__lt=now_time, end_date__gt=now_time).first()
            data['price'] = price.price  # Convert to integer
        except:
            instance.delete()
            raise serializers.ValidationError(f"Cart item {product.name} dont have a price,frush to apply the delete")
        data['funds'] = instance.funds.name
        data['tolto_price'] = float(data['price']) * float(data['quantity'])  # Convert to floats
        return data
    
class CartPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartModel
        fields = ["quantity"]
            


class OrdersModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersModel
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['status_code'] = data.pop("status")
        data['status'] = instance.get_status_display()
        return data

class OrderDetailModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetailModel
        fields = "__all__"
        
    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
    #     data['product_name'] = GoodsModel.objects.get(id=instance.product_id).name
    #     return data
