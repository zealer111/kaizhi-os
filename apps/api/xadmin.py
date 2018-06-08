from django.contrib import admin
from apps.api.models import UserProfile,Course,Package,Card,Card_Comment,Card_Action,User_Branch,User_Study_Record
from apps.api.models import User_Hw_Record,User_Buy_Record,AuthCode,Short_Url,Banner
import xadmin
form xadmin import views


class GlobalSetting(object):
    site_title = "开智后台管理系统"
    menu_style = "accordion"
    site_footer = "上海开智信息技术有限公司"


class BaseSetting(object):
    enable_themes = True


class UserProfileAdmin(object):
    list_display = ("id", 'user', 'username', 'phone', 'head_img', 'role', 'token', 'create_time', "update_time")
    search_fields =("id", 'user', 'username', 'phone', 'head_img', 'role', 'token', 'create_time', "update_time")
    list_filter = ("id", 'user', 'username', 'phone', 'head_img', 'role', 'token', 'create_time', "update_time")
    readonly_fields = []

xadmin.site.register(views.CommAdminView, GlobalSetting)
xadmin.site.register(views.BaseAdminView, BaseSetting)

xadmin.site.register(UserProfile, UserProfileAdmin)
