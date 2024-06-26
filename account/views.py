from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser,AllowAny

from rest_framework_simplejwt.views import TokenViewBase

from .serializers import AccountSerializer,MyUserTokenSerializer
from .permissions import IsAdminOrOwnerPutOnly
from .models import AccountModel
from .filters import AccountFilter
from utils.response import CustomModelViewSet

# Create your views here.

# 账户信息获取视图
# GET：获取全部账户信息(仅管理员)
# POST：添加账户(仅管理员)
# PATCH：重置密码(仅管理员)(默认密码123456)
# PUT: 重置密码(需要传入username)(仅允许修改自己的密码)
class AccountViewset(CustomModelViewSet):
    queryset = AccountModel.objects.exclude(is_superuser=True).order_by('id')
    serializer_class = AccountSerializer
    permission_classes = [IsAdminOrOwnerPutOnly]
    filterset_class = AccountFilter





# 账户失活视图
# PATCH：失活账户(仅管理员)
class DeactiveAccountView(APIView):
    permission_classes = [IsAdminUser]

    def post(self,request):
        id = request.data.get('id')
        if not id:
            return Response({'msg':'请传入账号ID', 'data':None, 'code':status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        try:
            user = AccountModel.objects.get(id=id)
        except AccountModel.DoesNotExist:
            return Response({'msg':'账号不存在，请刷新后重试', 'data':None, 'code':status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        user.is_active = False
        user.save()
        return Response({'msg':'账号失活成功', 'data':None, 'code':status.HTTP_200_OK},status=status.HTTP_200_OK)

# 账户激活视图
# PATCH：激活账户(仅管理员)
class ReactiveAccountView(APIView):
    permission_classes = [IsAdminUser]

    def post(self,request):
        id = request.data.get('id')
        if not id:
            return Response({'msg':'请传入账号ID', 'data':None, 'code':status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        try:
            user = AccountModel.objects.get(id=id)
        except AccountModel.DoesNotExist:
            return Response({'msg':'账号不存在，请刷新后重试', 'data':None, 'code':status.HTTP_404_NOT_FOUND},status=status.HTTP_404_NOT_FOUND)
        user.is_active = True
        user.save()
        return Response({'msg':'账号激活成功', 'data':None, 'code':status.HTTP_200_OK},status=status.HTTP_200_OK)
    
# 登录视图
class LoginView(TokenViewBase):
    serializer_class = MyUserTokenSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # print(serializer)
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({'msg':'用户名或密码错误', 'data':None, 'code':status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        
        return Response(data={
            "msg":"Login successfully",
            "data": serializer.validated_data,
            "code":status.HTTP_200_OK
        }, status=status.HTTP_200_OK)