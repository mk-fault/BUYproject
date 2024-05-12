from rest_framework import serializers
import datetime
from .models import GoodsModel, PriceModel, UnitModel

class PriceModelSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(default=True)
    class Meta:
        model = PriceModel
        fields = ['price', 'start_time', 'end_time', 'status', 'product', 'unit']

class UnitModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)  # 添加一个价格字段
    unit = serializers.IntegerField(write_only=True)  # 添加一个单位字段

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'unit']

    def create(self, validated_data):
        # 获取传入的价格数据
        price_data = validated_data.pop('price')
        unit_data = validated_data.pop('unit')
        # 获取当前时间和结束时间
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(days=30)

        # 创建商品对象
        product = GoodsModel.objects.create(**validated_data)

        # 创建单位对象
        unit = UnitModel.objects.get(id=unit_data)

        # 创建关联的价格对象
        PriceModel.objects.create(product=product, start_time=start_time, end_time=end_time, price=price_data, unit=unit)

        return product
    
    def to_representation(self, instance):
        # 编辑返回的数据
        data = super().to_representation(instance)
        data['price'] = instance.prices.filter(status=True).first().price
        data['start_time'] = instance.prices.filter(status=True).first().start_time
        data['end_time'] = instance.prices.filter(status=True).first().end_time
        data['unit'] = instance.prices.filter(status=True).first().unit.name
        return data