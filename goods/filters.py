from .models import *
from django_filters import rest_framework as filters

class PriceFilter(filters.FilterSet):
    product_id = filters.NumberFilter(field_name='product__id')
    product_name = filters.CharFilter(field_name="product__name")
    cycle_id = filters.NumberFilter(field_name='cycle__id')
    category_id = filters.NumberFilter(field_name='product__category__id')


    class Meta:
        model = PriceModel
        fields = ['status', 'product_id', 'cycle_id', 'category_id', 'product_name']