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
        return self.write_json({'errno': 0, 'msg': '', 'data': { "auth_code": "000000"}})

class
