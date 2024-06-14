from .models import *
from django_filters import rest_framework as filters

class OrdersFilter(filters.FilterSet):
    class Meta:
        model = OrdersModel
        fields = ['status', 'creater_id']
