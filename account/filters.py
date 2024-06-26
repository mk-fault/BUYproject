from .models import *
from django_filters import rest_framework as filters

class AccountFilter(filters.FilterSet):
    class Meta:
        model = AccountModel
        fields = ['role']
