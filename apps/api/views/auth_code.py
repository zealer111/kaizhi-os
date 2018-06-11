from apps.backs.views.base_views import BaseHandler
from apps.api.logger import logger_decorator
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from apps.api.models import *
import requests
import datetime
from django.core.paginator import Paginator,EmptyPage
from django.db import transaction
from apps.api.utils import auth_decorator,generate_token,generate_role_number,now_add_minute
from apps.api.qiniu import *
import os,zipfile
import re,glob
import json
import hashlib
from apps import settings

APP_KEY = '1fe1c5e93b43c0b37bc51481c0540246'
APP_SECRET = '9352b751f6b4'
SERVER_URL = 'https://api.netease.im/sms/sendcode.action'
NONCE = generate_role_number()
TEMPLATEID = '3882545'
MOBILE = '15577334054'
CODELEN = '6'
CURTIME = datetime.datetime.utcnow()


def str_encrypt(str):
    """
    使用sha1加密算法，返回str加密后的字符串
    """
    sha = hashlib.sha1(str.encode('utf-8'))
    encrypts = sha.hexdigest()
    return encrypts


class Get_Auth_Code(BaseHandler):
    @transaction.atomic
    @logger_decorator
    def post(self,request):
        msg = json.loads(request.body)
        ac = AuthCode.objects.filter(phone=msg.get('phone'))
        minute = 15
        for acs in ac:
            acs.delete()
        pac = AuthCode()
        pac.phone = msg.get('phone')
        pac.type = msg.get('type')
        pac.auth_code = generate_role_number()
        pac.fail_time = now_add_minute(minute)
        pac.save()
        _str = APP_SECRET + pac.auth_code + str(CURTIME)
        header ={
        'AppKey':APP_KEY,
        'Nonce':pac.auth_code,
        'CurTime':str(CURTIME),
        'CheckSum':str_encrypt(_str),
        'Content-Type':'application/x-www-form-urlencoded;charset=utf-8'
        }
        data= {
#        'templateid':TEMPLATEID,
        'mobile':msg.get('phone'),
        'authCode':pac.auth_code
        }
        url = 'https://api.netease.im/sms/sendcode.action'
        r = requests.post(url,data=data,headers=header)
        print(r.json())
        return self.write_json({'errno':0,'msg':'success'})

class Msg(BaseHandler):
    @transaction.atomic
    @logger_decorator
    def get(self,request):
        return self.write_json({
    "error": 11,
    "data": [
        {
            "time": 1526895875,
            "msg": [
                {
                    "avatar": "https://upload.jianshu.io/users/upload_avatars/2526386/ec0c1457a0c7.jpg?imageMogr2/auto-orient/strip|imageView2/1/w/96/h/96",
                    "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                    "card": {}
                },
                {
                    "avatar": "https://upload.jianshu.io/users/upload_avatars/2526386/ec0c1457a0c7.jpg?imageMogr2/auto-orient/strip|imageView2/1/w/96/h/96",
                    "text": "",
                    "card": {
                        "type": "markdown",
                        "title": "大脑喜欢情绪——上.md",
                        "link": "www.google.com"
                    }
                }
            ]
        },
        {
            "time": 1526895875,
            "msg": [
                {
                    "avatar": "https://upload.jianshu.io/users/upload_avatars/2526386/ec0c1457a0c7.jpg?imageMogr2/auto-orient/strip|imageView2/1/w/96/h/96",
                    "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                    "card": {}
                }
            ]
        }
    ]
})
