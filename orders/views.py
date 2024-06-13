from django.shortcuts import render

from rest_framework import viewsets
from rest_framework import permissions

from .models import *
from .serializers import *
from account import permissions as mypermissions
from utils import response as myresponse
# Create your views here.

class FundsViewset(viewsets.GenericViewSet,
                   myresponse.CustomCreateModelMixin,
                   myresponse.CustomDestroyModelMixin,
                   myresponse.CustomListModelMixin):
    queryset = FundsModel.objects.all()
    serializer_class = FundsModelSerializer

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            return [mypermissions.IsRole1()]
        else:
            return [permissions.IsAuthenticated()]


class CartViewset(myresponse.CustomModelViewSet):
    queryset = CartModel.objects.all()
    permission_classes = [mypermissions.IsRole2]

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.user.id
        queryset = queryset.filter(creater_id=user_id).order_by('id')
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'partial_update':
            return CartPatchSerializer
        else:
            return CartModelSerializer
    