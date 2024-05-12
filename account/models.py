from django.contrib.auth.models import AbstractUser
from django.db import models

class AccountModel(AbstractUser):
    role_choice = ((0,'粮油公司'),(1,'教体局'),(2, "学校"),(3, "其他1"),(4, "其他2"),(5, "其他3"))
    role = models.CharField(choices=role_choice, max_length=20, verbose_name="账户类型")  # 例如，角色可以是 'admin'、'user' 等

    class Meta:
        db_table = 'account'
        verbose_name = '账户'
        verbose_name_plural = verbose_name

