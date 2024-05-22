from rest_framework import serializers
import datetime
from .models import GoodsModel, PriceModel, UnitModel, CategoryModel

class PriceModelSerializer(serializers.ModelSerializer):
    status = serializers.BooleanField(default=True)
    class Meta:
        model = PriceModel
        fields = ['price', 'start_time', 'end_time', 'status', 'product', 'unit']

class UnitModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitModel
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryModel
        fields = ['id', 'name']

class GoodsModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True)  # 添加一个价格字段
    unit = serializers.IntegerField(write_only=True)  # 添加一个单位字段

    class Meta:
        model = GoodsModel
        fields = ['id', 'name', 'image', 'description', 'price', 'unit', 'category']
        # extra_kwargs = {
        #     'category':{
        #         'required':True
        #     }
        # }

    def create(self, validated_data):
        # 获取传入的价格数据
        price_data = validated_data.pop('price')
        unit_data = validated_data.pop('unit')
        # 获取当前时间和结束时间
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(days=30)

        # 创建单位对象
        try:
            unit = UnitModel.objects.get(id=unit_data)
        except:
            raise serializers.ValidationError("计量单位对象不存在")

        # 创建商品对象
        product = GoodsModel.objects.create(**validated_data)
        # 创建关联的价格对象
        PriceModel.objects.create(product=product, start_time=start_time, end_time=end_time, price=price_data, unit=unit)

        return product
    
    def to_representation(self, instance):
        # 编辑返回的数据
        data = super().to_representation(instance)
        try:
            data['price'] = instance.prices.filter(status=True).first().price
            data['start_time'] = instance.prices.filter(status=True).first().start_time
            data['end_time'] = instance.prices.filter(status=True).first().end_time
            data['unit'] = instance.prices.filter(status=True).first().unit.name
            data['category'] = instance.category.name
        except:
            raise serializers.ValidationError("获取商品失败")
        return data