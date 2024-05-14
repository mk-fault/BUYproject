import time

from rest_framework import serializers

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AccountModel

class AccountSerializer(serializers.ModelSerializer):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.default_password = '123456'

    class Meta:
        model = AccountModel
        fields = ('id','username','is_active','last_login','password', 'role')
        read_only_fields = ('id','is_active','last_login')
        extra_kwargs = {
            'password':{
                'write_only':True,
                'required':False,
                'default':None
            },
            'role':{
                'required':False,
            }
        }

    def validate(self, attrs):
        password = attrs.get('password')
        role = attrs.get('role')
        # 判断账户类型是否合法
        if role is not None and role not in [0,1,2,3,4,5]:
            raise serializers.ValidationError('账户类型不合法')

        # 没有密码则为添加教师或重置密码，无需校验
        if not password:
            return attrs
        
        # 判断密码是否符合要求
        if len(password) < 6 or len(password) > 20:
            raise serializers.ValidationError('密码长度应在6-20位之间')
        # if password.isdigit():
        #     raise serializers.ValidationError('密码不能为纯数字')
        return attrs

    def create(self, validated_data):
        if 'role' not in validated_data:
            raise serializers.ValidationError('未传入账户类型')
        validated_data['password'] = self.default_password  # 添加账户，设置为默认密码
        return AccountModel.objects.create_user(**validated_data)
    
    def update(self, instance, validated_data):
        # 修改密码，以PATCH未传入密码时，设置为默认密码
        # PUT方式传入密码时，设置为传入的密码
        instance.set_password(validated_data.get('password',self.default_password)) 
        if 'role' not in validated_data:
            validated_data['role'] = instance.role
        else:
            raise serializers.ValidationError('不允许修改账户类型')
        instance.save()
        return instance
    
class MyUserTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 调用父类的validate方法，获取token，实现登录
        data = super().validate(attrs)

        # 更新最后登录时间
        self.user.last_login = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) 
        self.user.save()

        # 将用户信息添加到返回的数据中
        data['id'] = self.user.id
        data['username'] = self.user.username
        data['role'] = self.user.role

        # 判断是否为简单密码
        if AccountModel.check_password(self.user,'123456'):
            data['is_simple'] = True
        else:
            data['is_simple'] = False

        # 判断是否为管理员
        if self.user.is_superuser:
            data['is_admin'] = True
        else:
            data['is_admin'] = False
            
        return data