from django.contrib import admin
import xadmin
from xadmin import views
from apps.api.models import *

admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Card)
admin.site.register(Card_Comment)
admin.site.register(Card_Action)
admin.site.register(Master_Package)
admin.site.register(Branch_Package)
admin.site.register(Package_Auth_Info)
admin.site.register(User_Branch)
admin.site.register(User_Study_Record)
admin.site.register(User_Hw_Record)
admin.site.register(User_Buy_Record)
admin.site.register(User_Course_Record)
admin.site.register(User_Package_Record)
admin.site.register(AuthCode)
admin.site.register(System_Message)
admin.site.register(Short_Url)
admin.site.register(Banner)



