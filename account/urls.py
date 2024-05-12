from django.urls import path,include

from . import views

from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('accounts',views.AccountViewset)

urlpatterns = [
    path('',include(router.urls)),
    path('login/',views.LoginView.as_view()),
    path('reactive/',views.ReactiveAccountView.as_view()),
    path('deactive/',views.DeactiveAccountView.as_view())
]