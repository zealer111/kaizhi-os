#-*-coding:utf8;-*-
from apps.backs.views.base_views import BaseHandler
from apps.api.logger import logger_decorator
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from apps.api.models import *
import requests
from django.core.paginator import Paginator,EmptyPage
from django.db import transaction
from apps.api.utils import auth_decorator,generate_token
from apps.api.qiniu import Uploader
from apps.api.file_dir import *
import os,zipfile
import re,glob
import json
from django.utils import timezone
from pathlib import Path
from django.db.models import Q
from apps import settings
import operator
from libs import log_utils
from libs import git_utils


## logger句柄
import logging
logging.basicConfig(filename=settings.LOG_FILE, level=logging.DEBUG)
log_utils.default_logging_config()
logger = log_utils.getLogger(__name__)


class AuthCode(BaseHandler):
    """
    获取验证码

    paremeters
        phone: ‘string’   //电话号码

    return     {
        error: “0/1”
        msg：“string”
        data:{
            auth_code: “ ”
        }
    }

    """
    def get(self, request):
        logger.info("AuthCode:get %s" % (request.GET.get("phone")))
        return self.write_json({'errno': 0, 'msg': '', 'data': { "auth_code": "000000"}})

    def post(self, request):
        logger.info("AuthCode:post %s" % (request.POST.get("phone")))
        return self.write_json({'errno': 0, 'msg': '', 'data': { "auth_code": "000000"}})

class AuthPhone(BaseHandler):
    """
    根据验证码验证手机号

    parameters
        phone, authcode


    return
    {
        error: “0/1”， # 错误码，0 表示成功
        msg：“string”，
        data: {
            exist_status : “y/n”，   // 是否存在状态
            user_info : {
                    // 如果已在网站注册过，则返回网站的用户信息
            }
        }
    }
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { "exist_status": "y", "user_info":{}}})


class SetPassword(BaseHandler):
    """
    设置密码
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class CoursesList(BaseHandler):
    """
    课程列表
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class CourseDetail(BaseHandler):
    """
    课程详情
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class Messages(BaseHandler):
    """
    消息中心
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class MyCollections(BaseHandler):
    """
    我的收藏
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class CourseList(BaseHandler):
    """
    课程列表目录

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class CardDetail(BaseHandler):
    """
    卡片详情
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class CollectCard(BaseHandler):
    """
    收藏卡片
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class GetOrderNum(BaseHandler):
    """
    获取购买课程订单号

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class GetPayInfo(BaseHandler):
    """
    获取付款信息
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})

class GetPayResult(BaseHandler):
    """
    获取付款结果信息

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': '', 'data': { }})
