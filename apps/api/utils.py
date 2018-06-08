#coding: utf-8
from functools import wraps
from django.utils.decorators import available_attrs
import datetime
import json
import random
from django.utils import timezone
from django.http import HttpResponse
import time
from hashlib import md5
import re,os
import uuid
from django.forms import forms
# import model
from apps.api.models import UserProfile


class FileUploadForm(forms.Form):
    my_file = forms.FileField()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def write_json(obj):
    """return json obj"""
    return HttpResponse(json.dumps(obj), content_type='application/json')
    #return HttpResponse(json.dumps(obj))

def backs_token(user_id):
    """generate manager user token"""
    _sign = str(user_id) + "this_is_shennan_application_backs_token"
    return md5(_sign).hexdigest()

def generate_token(user_id):
    """generate user token"""
    print(user_id)
    _sign = str(user_id) + "this_is_kaizhi_application_user_token"
    return md5(_sign.encode('utf-8')).hexdigest()


def timestampTodate(timestamp):
    return datetime.fromtimestamp(timestamp)


def auth_decorator(method):
    """api 登录验证"""
    @wraps(method)
    def wrapper(self,request, *args, **kwargs):
        msg = json.loads(request.body)
        token = msg.get('token')
        user_id = msg.get('userid')
        # 验证token
        try:
            if len(token) != 32 or token != generate_token(user_id):
                return write_json({"errno": 3, "msg": "user_id or token invalid"})
        except BaseException:
            return write_json({"errno": 3})

        self.user_id = user_id
        user = UserProfile.objects.filter(id=user_id,token=token)
        if not user.count():
            return write_json({"errno": 3, "msg": "登陆已过期，请重新登录！！！"})
        self.request.user = user[0]
        return method(self,request, *args, **kwargs)
    return wrapper


def create_noncestr(length=32):
    """产生随机字符串，不长于32位"""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789"
    strs = []
    for x in range(length):
        strs.append(chars[random.randrange(0, len(chars))])
    return "".join(strs)

def separate(num):
    """千位分隔, 用于金额分隔"""
    try:
        num = float('%0.2f'% float(num))
        return '{:,}'.format(num)
    except Exception as e:
        return num

    #return num

def generate_password(password):
    """generate password"""
    pwd = "%s%s" % (password, "this_is_shennan_application")
    return md5(pwd).hexdigest()

def validate_phone(phone):
    return re.match(r'1(3|4|5|7|8)\d{9}', str(phone))

def now_add_minute(minute=None):
    """在现有的时间加上传入的分中数，默认60分钟"""
    if not isinstance(minute, int) or minute is None:
        minute = 60
    return timezone.now() + timezone.timedelta(minutes=minute)

def generate_role_number():
    """随机产生6位数权限码"""
    return str(random.randint(100000, 999999))

def get_random_code(length=6):
    """随机数"""
    return "".join(random.sample('0123456789', length))
