from apps.backs.views.base_views import BaseHandler
from apps.api.logger import logger_decorator
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from apps.api.models import UserProfile
import requests
from django.core.paginator import Paginator,EmptyPage
from django.db import transaction
from apps.api.utils import auth_decorator,generate_token
from apps.api.qiniu import Uploader
import os,zipfile
import re
import json
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from apps import settings
from django.db.models import Q



class Login(BaseHandler):
    @logger_decorator
    def post(self, request):
        user = json.loads(request.body)
        phone = user.get('phone')
        password = user.get('password')
        user = authenticate(request, username=phone, password=password)
        u = UserProfile.objects.filter(phone=phone)
        if not u:
            return self.write_json({'errno':1,'msg':'手机号尚未注册！！!'})
        if user:
            login(request, user)
            try:
                up = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return self.write_json({'errno':1,'msg':'用户不存在!'})
        else:
            return self.write_json({'errno':'1','msg':'密码错误，请重新输入！！！'})
        data = {
            'token':generate_token(up.id),
            'userid':up.id,
            'username':up.username,
            'head_img':up.head_img,
            'phone':up.phone,
            'role':up.role
         }
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})


class Logout(BaseHandler):
    @logger_decorator
    def get(self, request):
        logout(request)
        data = {
           'message':'退出登录'
           }
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})


class Register(BaseHandler):
    @logger_decorator
    def post(self, request):
        user_info = json.loads(request.body)
        print(user_info)
        username = user_info.get('username')
        password = user_info.get('password')
        phone = user_info.get('phone')
        auth_code = user_info.get('auth_code')
  #      ac = AuthCode.objects.filter(phone=phone,auth_code=auth_code).first()
  #      if not ac:
  #          return self.write_json({'errno':1,'msg':'手机验证码不存在!'})
        ups = UserProfile.objects.filter(username=username)
        if ups:
            return self.write_json({'errno':1,'msg':'昵称已存在，请换一个昵称！！！'})
        try:
            User.objects.get(username=phone)
            return self.write_json({'errno':1,'msg':'该手机号的用户已存在！！！'})
        except User.DoesNotExist:
#            user = User.objects.create_user(username=phone,password=password)
            user = User(username=phone)
            user.password = make_password(password=password, salt=None)
            user.save()
            up = UserProfile()
            up.user = user
            up.head_img = 'http://static.openmindclub.com/image/default-avatar/avatar2.png'
            up.username = username
            up.phone = phone
            up.token = generate_token(up.id)
            up.save()
        data = {
            'user':user.username,
            'username':up.username,
            'id':str(up.id),
            'token':up.token,
             'head_img':up.head_img
        }
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})

#修改密码
class User_Upd_Password(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        print(request.body)
        user_info = json.loads(request.body)
        password = user_info.get('password')
        new_password = user_info.get('new_password')
        up = UserProfile.objects.filter(username=request.user)
        user = request.user
        phone = user.phone
        user = authenticate(request,username=phone,password=password)
        if not user:
           return self.write_json({'errno':1,'msg':'旧密码错误!'})
        user.set_password(new_password)
        user.save()
        if user:
            login(request,user)
            try:
                ups = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return self.write_json({'errno':1,'msg':'不存在用户信息!'})
        try:
            ups = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            up = UserProfile()
            up.user = user
            up.username = user.username
            up.phone = user.username
            up.token = generate_token(up.id)
            up.save()
        return self.write_json({'errno': 0, 'msg': 'success'})

#忘记密码
class User_Set_New_Password(BaseHandler):
    @logger_decorator
    def post(self, request):
        user_info = json.loads(request.body)
        new_password = user_info.get('new_password')
        phone = user_info.get('phone')
        print(phone)
        try:
            user = User.objects.get(username=phone)
            user.set_password(new_password)
            user.save()
            try:
               up = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                up = UserProfile()
                up.phone = user.username
                up.token = generate_token(up.id)
                up.save()
            up.user = user
            up.save()
            return self.write_json({'errno': 0, 'msg': 'success'})
        except User.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户'})


class Upd_User_Info(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        print(request.body)
        user_info = json.loads(request.body)
        try:
            user = UserProfile.objects.get(id=user_info.get('userid'))
            name = UserProfile.objects.filter(~Q(username=request.user),username=user_info.get('username'))
            if name :
                return self.write_json({'errno': 1, 'msg': '昵称已存在，请换一个昵称！！！'})
            user.username = user_info.get('username')
            user.nickname = user_info.get('nickname')
            user.phone = user_info.get('phone')
            user.save()
            up = User.objects.get(username=user.user)
            up.username = user_info.get('phone')
            up.save()
            data = {
            'userid':user.id,
            'token':user.token,
            'username':user.username,
            'nickname':user.nickname,
            'phone':user.phone,
            'head_img':user.head_img
            }
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except User.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户'})
        except BaseException:
            return self.write_json({'errno': 1, 'msg': '手机号已存在！！！'})


class Upd_Head_Img(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        user_info = json.loads(request.body)
        try:
            user = UserProfile.objects.get(id=user_info.get('userid'))
            user.head_img = user_info.get('head_img')
            user.save()
            data = {
            'userid':user.id,
            'token':user.token,
            'username':user.username,
            'nickname':user.nickname,
            'phone':user.phone,
            'head_img':user.head_img
            }
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户'})


