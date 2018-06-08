#coding: utf-8
from django.core.cache import cache
from apps.settings import BACKS_LOGIN_URL
from django.shortcuts import redirect
import urllib
from django.http import HttpResponse
from apps.api.utils import backs_token
from apps.api.models import UserProfile
from functools import wraps
import json
def login():
    #后台登录验证
    def wrap(view_func):
        def is_login(self, *args, **kwargs):
            token = self.request.session.get('backs_token', None)
            self.user = self.request.user
            self.username = self.request.session.get('backs_username', None)
            self.user_id = self.request.session.get('backs_user_id', None)
            if not self.user_id or token != backs_token(self.user_id) or not self.user:
                url = BACKS_LOGIN_URL
                if self.request.path.count("next") > 3:
                    return redirect(url)
                if "?" not in url:
                    url += "?" + urllib.urlencode(dict(next=self.request.path))
                return redirect(url)
            return view_func(self, *args, **kwargs)
        return is_login
    return wrap

def write_json(obj):
      return HttpResponse(json.dumps(obj), content_type='application/json')
      #return HttpResponse(json.dumps(obj))


def auth_decorator(method):
    @wraps(method)
    def wrapper(self,request, *args, **kwargs):
        msg = json.loads(request.body)
        user_id = msg.get('userid')
        user = UserProfile.objects.get(id=user_id)
        username = request.session.get('username')
        print(user)
        print([username])
        if not user or not username:
            return write_json({"errno": 2, "msg": "登陆已过期，请重新登录！！！"})
        else:
            return write_json({"errno": 0, "msg": "success"})
    return wrapper

