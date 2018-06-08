#coding:utf-8
from django.conf.urls import url

from apps.api.views import views,basic,auth_code

from apps.api.youzan import youzan
from apps.xcx.views import login

#base
urlpatterns = [

    url('^login', login.Login.as_view()),
]

urlpatterns +=[
    url('^youzan/callback', youzan.Get_Order.as_view()),
    url('^my_buy_course_info', youzan.My_Buy_Course_Info.as_view()),
    url('^user_apply_course', youzan.User_Apply_Course.as_view()),
    url('^buy_course_info', youzan.Buy_Course_Info.as_view()),
    url('^msg', auth_code.Msg.as_view()),
]
