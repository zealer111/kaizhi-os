#coding:utf-8
"""（后台管理）
一个urlpatterns 对应一个views文件,
一个views对应一个models(apps.models.xx_models)
"""
from django.conf.urls import url #patterns
from .views import views


urlpatterns = [
    url(r'^get_user$', views.Get_User.as_view()),
    url(r'^upd_user_info$', views.Upd_User_Info.as_view()),
    url(r'^delete_user$', views.Delete_User.as_view()),
    url(r'^delete_package$', views.Delete_Package.as_view()),
    url(r'^get_all_user$', views.Get_All_User.as_view()),
    url(r'^get_assistant_user$', views.Get_Assistant_User.as_view()),
    url(r'^user_package$', views.User_Package.as_view()),
    url(r'^user_assistant$', views.User_Assistant.as_view()),
    url(r'^assistant_user_search$', views.Assistant_User_Search.as_view()),
    url(r'^delete_assistant$', views.Delete_Assistant.as_view()),
    url(r'^get_course$', views.Get_Course.as_view()),
    url(r'^modify_course$', views.Modify_Course.as_view()),
    url(r'^login$', views.Login.as_view()),
    url(r'^get_card$', views.Get_Card.as_view()),
    url(r'^delete_course$', views.Delete_Course.as_view()),
    url(r'^delete_buy_course$', views.Delete_Buy_Course.as_view()),
    url(r'^get_user_buy_record$', views.Get_User_Buy_Record.as_view()),
    url(r'^get_all_course$', views.Get_All_Course.as_view()),
    url(r'^get_assi_package$', views.Get_Assi_Package.as_view()),
    url(r'^get_all_package$', views.Get_All_Package.as_view()),
    url(r'^user_buy_course$', views.User_Buy_Course.as_view()),
    url(r'^upd_buy_course$', views.Upd_Buy_Course.as_view()),
    url(r'^check_user$', views.Check_User.as_view()),
    url(r'^add_package_sign$', views.Add_Package_Sign.as_view()),
    url(r'^get_message$', views.Get_Message.as_view()),
    url(r'^send_message$', views.Send_Message.as_view()),
    url(r'^message_search$', views.Message_Search.as_view()),
    url(r'^delete_message$', views.Delete_Message.as_view()),
    url(r'^delete_assistant$', views.Delete_Assistant.as_view()),
#   url(r'^login_out$', views.ManagerLoginOut.as_view()),
]

urlpatterns +=[

]
