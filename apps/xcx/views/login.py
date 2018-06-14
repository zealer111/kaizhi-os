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
import re
import json
from django.core.cache import cache
from apps.xcx.WXBizDataCrypt import WXBizDataCrypt
from apps.xcx.django_jwt_session_auth import jwt_login
from django.contrib.auth.hashers import make_password
from django.shortcuts import render
from apps import settings
from django.db.models import Q


class Login(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self, request):
        msg = json.loads(request.body)
        app_id = msg.get('appId')
        secret = msg.get('secret')
        js_code = msg.get('js_code')
        iv = msg.get('iv')
        encrypted_data = msg.get('encryptedData')

        response = get_session_info(app_id, secret, js_code)
        session_key = response.get('session_key')
        print(response)
        print(session_key)
        pc = WXBizDataCrypt(app_id, session_key)
        user_info = pc.decrypt(encrypted_data, iv)
        print('>>>>>', user_info)
        # 获得openid
        open_id = user_info['openId']
#        cache.set("open_id", open_id, 3600)
#        cache.set("app_id", app_id, 3600)
#        cache.set("secret", secret, 3600)

        if "openId" in user_info:
            try:
                user = UserProfile.objects.get(openid=open_id)
                # 存在状态
            except UserProfile.DoesNotExist:
                #user = register(user_info)
                return self.write_json({'errno': 1, 'msg': '用户不存在', 'openId': open_id})

            #token = jwt_login(user, request)

            data = {
                'errno': 0,
                'msg': 'success',
                #'token_jwt': token.decode("utf-8"),
                'user_info': user_info,
                'openId': open_id,
            }
            return self.write_json(data)
        else:
            data = {'errno': 1, 'msg': 'an unknown error occurred'}
            return self.write_json(data)


# 获取session_info
def get_session_info(appid, secret, js_code):
    base_url = 'https://api.weixin.qq.com/sns/jscode2session?'

    url = base_url + 'appid=%s&secret'\
                    '=%s&grant_type=authorization_code&js_code=%s' % (
              appid, secret, js_code)

    response = requests.get(url).json()
    return response


# 储存用户到数据库中
def register(user_info):
    up = UserProfile(username=user_info['nickName'], head_img=user_info['avatarUrl'],
                       openid=user_info['openId'])
    up.save()
    return up

