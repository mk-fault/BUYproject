from .models import *
from django_filters import rest_framework as filters

class PriceFilter(filters.FilterSet):
    product_id = filters.NumberFilter(field_name='product__id')
    cycle_id = filters.NumberFilter(field_name='cycle__id')

    class Meta:
        model = PriceModel
        fields = ['status', 'creater_id', 'reviewer_id', 'product_id', 'cycle_id']