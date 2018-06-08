import json

from django.http import HttpResponse
from functools import wraps
import datetime
from apps.api.models import UserProfile


# 授权装饰器
def wx_app_login_required(func):
    @wraps(func)
    def verify_login(request, *args, **kwargs):
        if request.jwt_user:
            return func(request, *args, **kwargs)
        else:

            unauthorized = {"errno": 1, "msg": "未授权！"}

            return HttpResponse(json.dumps(unauthorized), content_type="application/json", status=401)

    return verify_login


def user_to_payload(user):
    exp = datetime.datetime.now() + datetime.timedelta(seconds=3600)
    return {
        'user_id': str(user.id),
        'exp': exp
    }


def payload_to_user(payload):
    if not payload:
        return None
    user_id = payload.get('user_id')
    user = UserProfile.objects.filter(pk=user_id).first()
    return user

