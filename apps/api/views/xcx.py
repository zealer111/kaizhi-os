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
from apps.api.utils import auth_decorator, generate_token, generate_role_number, now_add_minute
from apps.api.qiniu import Uploader
from apps.api.file_dir import *
import os,zipfile
import re,glob
import json
import hashlib
import datetime
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


# app config
APP_SECRET = '9352b751f6b4'
APP_KEY = '1fe1c5e93b43c0b37bc51481c0540246'
CURTIME = datetime.datetime.utcnow()


def str_encrypt(str):
    """
    使用sha1加密算法，返回str加密后的字符串
    """
    sha = hashlib.sha1(str.encode('utf-8'))
    encrypts = sha.hexdigest()
    return encrypts


class GetAuthCode(BaseHandler):
    """
    获取验证码

    paremeters {
        phone: 'string',   //电话号码
        type: 'string'     //类型：1->注册，2->忘记密码
    }

    return {
        error: '0/1',
        msg：'string',
        data:{
            'auth_code': '',
        }
    }
    """
    @logger_decorator
    def post(self, request):
        msg = json.loads(request.body)
        acs = AuthCode.objects.filter(phone=msg.get('phone'))
        minute = 15
        acs.delete()
        pac = AuthCode()
        pac.phone = msg.get('phone')
        pac.type = msg.get('type')
        pac.auth_code = generate_role_number()
        pac.fail_time = now_add_minute(minute)
        pac.save()
        _str = APP_SECRET + pac.auth_code + str(CURTIME)
        headers = {
            'AppKey': APP_KEY,
            'Nonce': pac.auth_code,
            'CurTime': str(CURTIME),
            'CheckSum': str_encrypt(_str),
            'Content-Type':'application/x-www-form-urlencoded;charset=utf-8'
        }
        data = {
            'mobile':msg.get('phone'),
            'authCode':pac.auth_code
        }
        url = 'https://api.netease.im/sms/sendcode.action'
        resp = requests.post(url, data=data, headers=headers)
        resp = resp.json()
        if resp.get('code') == 200:
            return self.write_json({'errno': 0, 'msg': 'success', 'data': { "auth_code": resp.get('obj')}})
        return self.write_json(resp)


class AuthPhone(BaseHandler):
    """
    根据验证码验证手机号

    parameters {
        phone: 'string',    //手机号
        authcode: 'sting'   //手机收到的验证码
    }

    return {
        error: “0/1”， # 错误码，0 表示成功
        msg：“string”，
        data: {
            exist_status : “y/n”，   // 是否存在状态
            userInfo : {   // 如果已在网站注册过，则返回网站的用户信息
                avatar: 'sting',    //头像
                nickname: 'string', //昵称
                //sex: '0/1',         //性别: 0->女, 1->男
            }
        }
    }
    """
    def post(self, request):
        msg = json.loads(request.body)
        phone = msg.get('phone', '')
        authcode = msg.get('authcode', '')

        if not phone and not authcode:
            return self.write_json({'errno': 1, 'msg': '手机号或验证码为空'})

        try:
            ac = AuthCode.objects.get(phone=phone, auth_code=authcode)
            user = UserProfile.objects.get(phone=phone)
            return self.write_json({'errno': 0, 'msg': '', 'data': {
                    "exist_status": "y",
                    "userInfo":{
                        'avatar': user.head_img,
                        'nickname': user.nickname,
                    }
                }
            })
        except AuthCode.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '验证码错误，请重新获取', 'data': {}})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在', 'data': {'exist_status': 'n'}})


class SetPassword(BaseHandler):
    """
    设置密码
    """
    def post(self, request):
        msg = json.loads(request.body)
        phone = msg.get('phone', '')
        password = msg.get('password', '')
        openid = msg.get('openId', '')
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {'userId': '323534'}})

class CoursesList(BaseHandler):
    """
    课程列表
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': [
            {
                "title": "开智学堂",
                "host": "杨志平",
                "cover": "https://img2.mukewang.com/szimg/59b8a486000107fb05400300.jpg",
                "label": 'bought',  #课程标签状态
                "personNum": 10, #正在学习人数
                "price": 100, #课程价格
                "status": 0, #用户是否购买此课程状态、0已购买/1未购买
                "start_time": "2018-3-20",
                "end_time": "2018-5-10",
                "course_id": "2de4da87065111e88b265254009ecd21", #课程id
            },

            {
                "title": "开智学堂",
                "host": "杨志平",
                "cover": "https://img2.mukewang.com/szimg/59b8a486000107fb05400300.jpg",
                "label": 'new',  #课程标签状态
                "personNum": 23, #正在学习人数
                "price": 100, #课程价格
                "status": 0, #用户是否购买此课程状态、0已购买/1未购买
                "start_time": "2018-3-20",
                "end_time": "2018-5-10",
                "course_id": "2de4da87065111e88b265254009ecd21", #课程id
            },

            {
                "title": "开智学堂",
                "host": "杨志平",
                "cover": "https://img2.mukewang.com/szimg/59b8a486000107fb05400300.jpg",
                "label": 'opened',  #课程标签状态
                "personNum": 10, #正在学习人数
                "price": 1000, #课程价格
                "status": 1, #用户是否购买此课程状态、0已购买/1未购买
                "start_time": "2018-3-20",
                "end_time": "2018-5-10",
                "course_id": "2de4da87065111e88b265254009ecd21", #课程id
            },
        ]
    })

class CourseDetail(BaseHandler):
    """
    课程详情
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {
            "title": "开智智学堂",
            "cover": "http://pic1.win4000.com/wallpaper/d/55efa298766d2.jpg",
            "host": "杨志平", #课程主讲人
            "start_time": "2018-1-20",
            "end_time": "2018-2-10",
            "description": "描述", #内容简介
            "price": 111,
            "personNum": 0, #正在学习人数
            "course_id": "7909e1f1065111e88b265254009ecd21",
        }})

class Messages(BaseHandler):
    """
    消息中心
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': [
            {
                "time": 1526895875,
                "msg": [
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {
                            "type": "markdown",
                            "title": "大脑喜欢情绪--上.md",
                            "link": "www.google.com"
                        }
                    },
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {
                            "type": "markdown",
                            "title": "大脑喜欢情绪--上.md",
                            "link": "www.google.com"
                        }
                    },
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {
                            "type": "markdown",
                            "title": "大脑喜欢情绪--上.md",
                            "card_id": '0', #卡片id
                        }
                    }
                ]
            },
            {
                "time": 1526895875,
                "msg": [
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {
                            "type": "markdown",
                            "title": "大脑喜欢情绪--上.md",
                            "card_id": '0', #卡片id
                        }
                    },
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {}
                    },
                    {
                        "avatar": "",
                        "text": "欢迎加入认知写作学5期，接下来的三个月一起加油吧~",
                        "card": {}
                    }
                ]
            }

        ]})

class MyCollections(BaseHandler):
    """
    我的收藏
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': [{
            'card_type': 'markdown', #卡片类型
            'title': '卡片标题',
            'card_id': '352' #卡片ID
        }]
    })

class CourseList(BaseHandler):
    """
    课程列表目录

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': [
            {
                "title": "第一讲",
                "type": "directory", #目录
                "key": "cf7734660b1011e88b265254009ecd21",
                "children": [
                    {
                        "title": "1-1",
                        "key": "cf7734660b1011e88b265254009ecd21",
                        "type": "directory",
                        "status": 0, #0未学
                        "childern": []
                    },
                    {
                        "title": "美美美",
                        "key": "af13895a0b0f11e88b265254009ecd21",
                        "type": "file",
                        "status": 1, #1已学
                        "childern": []
                    }
                ]
            }
        ]})

class CardDetail(BaseHandler):
    """
    卡片详情
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': [
            {
                "card_id": "783262e0-3b1f-47b5-85d0-849623e489bc",
                "type": 1,   #0是文本，1是视频，2是测试题
                "title": "008.阳老师分享 GitHub 使用技巧 | 三期典礼",
                "front": {
                    "url": "http://1251595766.vod2.myqcloud.com/4ae9bcd6vodtransgzp1251595766/2f6bf28e9031868223375388283/v.f30.mp4\n"
                },
                "back": "\n如果你有不错的实践经验或技巧，欢迎到 GitHub 上和大伙儿分享~\n\n\n"
            },
            {
                "card_id": "07f95927-35a2-49da-b483-9ae02d040a1e",
                "type": 2,
                "title": "丹尼特的四层心智是？",
                "front": {
                    "exam": [
                        {
                            "is_single": "false",
                            "mq": [
                                " 以下属于丹尼特四层心智的是？（多选）"
                            ],
                            "asw": [
                                " 达尔文心智",
                                " 斯金纳心智",
                                " 霍金心智",
                                " 波普尔心智",
                                " 格列高利心智"
                            ],
                            "aswt": [
                                " 达尔文心智",
                                " 斯金纳心智",
                                " 波普尔心智",
                                " 格列高利心智"
                            ]
                        }
                    ]
                },
                "back": "\n做得对不对？看图吧\n\n![](http://openmindclub.qiniudn.com/cnfeat/image/4-kinds-of-minds-2.jpg)\n\n\n\n\n"
            }
        ]})

class CollectCard(BaseHandler):
    """
    收藏卡片
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {
            'type': 1, #0->收藏，1->未收藏
        }})

class GetOrderNum(BaseHandler):
    """
    获取购买课程订单号

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {
            'orderNum': '201806122008a234', #订单号
        }})

class GetPayInfo(BaseHandler):
    """
    获取付款信息
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {
            'timeStamp': datetime.datetime.now().strftime('%Y-%m-%d'),
            'nonceStr': 'asda',
            'package': 'kajske',
            'paySign': 'al3j42h1jo43majewkwksken397s',
        }})

class GetPayResult(BaseHandler):
    """
    获取付款结果信息

    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success'})

class AuthLogin(BaseHandler):
    """
    授权登陆
    """
    def post(self, request):
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {'openId': 'ajskhj252176a6ssfjkb'}})
