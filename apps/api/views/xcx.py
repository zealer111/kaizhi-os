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
            exist_status : 0/1,   // 是否存在状态
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
            return self.write_json({'errno': 0, 'msg': 'success', 'data': {
                    "exist_status": 0,
                    "userInfo":{
                        'avatar': user.head_img,
                        'nickname': user.nickname,
                        'phone': user.phone,
                    }
                }
            })
        except AuthCode.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '验证码错误，请重新获取', 'data': {}})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 0, 'msg': '用户不存在', 'data': {'exist_status': 1}})


class SetPassword(BaseHandler):
    """
    设置密码

    parameters {
        phone: 'string',    #手机号
        password: 'string', #密码
        openId: 'string',   #
        type: 1/2, #1->网站用户, 2->小程序用户
    }

    return {
        errno: 0/1,
        msg: "string",
        data {
            userId: 'string'
        }
    }
    """
    def post(self, request):
        msg = json.loads(request.body)
        phone = msg.get('phone', '')
        password = msg.get('password', '')
        open_id = msg.get('openId', '')
        _type = msg.get('type', '')

        print('>>>>>>>>>>', msg)
        if not phone and not password and not open_id and not _type:
            print('%%%%%%%%%')
            return self.write_json({'errno': 1, 'msg': '信息不全', 'data': {'userId': ''}})

        user = User(username=phone, password=password)
        user.save()
        up = UserProfile()
        up.user = user
        up.phone = phone
        up.openid = open_id
        up.type = _type
        up.save()
        return self.write_json({'errno': 0, 'msg': 'success', 'data': {'userId': user.id}})

class CoursesList(BaseHandler):
    """
    课程列表

    url: api/xcx/courses-list
    method: POST
    parameters {
        token: 'string',
        page: int, #页码
        userId: string,
        limit: int, #每页显示多少个课程
    }

    return {
        errnor: 0/1,
        msg: 'string',
        data: [
            "title": "string", #标题
            "host": "string", #讲师
            "cover": "http://i10.topitme.com/o054/1005435275a84a3f41.jpg", #封面
            "label": 'string',  #课程标签状态: bought/new/opened
            "personNum": int, #正在学习人数
            "price": int, #课程价格
            "status": int, #用户是否购买此课程状态、0已购买/1未购买
            "start_time": "2018-3-20",
            "end_time": "2018-5-10"
            "course_id": "2de4da87065111e88b265254009ecd21", #课程id
        ]
    }
    """
    def post(self, request):
        courses = Course.objects.all()
        msg = json.loads(request.body)
        token = msg.get('token', '')
        page = msg.get('page', 1)
        user_id = msg.get('userId', '')
        limit = msg.get('limit', 5)

        bought = User_Buy_Record.objects.filter(user__id=user_id, status=1)

        data = []
        for c in courses:
            status = 0 if c in bought else 1
            if not status:
                label = 'bought'
            elif datetime.datetime.strptime(c.start_time[:10], '%Y-%m-%d') < datetime.datetime.now() and status:
                label = 'opened'
            else:
                label = 'new'
            data.append({
                'course_id': c.id,
                'title': c.title,
                'host': c.host,
                'is_fee': c.is_fee,
                'cover': c.cover,
                'label': label,
                'personNum': '', #TODO 
                'price': c.price,
                'status': status,
                'start_time': c.start_time,
                'end_time': c.end_time,
            })

        p = Paginator(data, limit)
        data = p.page(page).object_list
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})

class CourseDetail(BaseHandler):
    """
    课程详情

    url: api/xcx/course-detail
    method: POST
    parameters {
        course_id: int, #课程ID
    }

    return {
        "title": "string",
        "cover": "string", #封面
        "host": "string", #课程主讲人
        "start_time": "2018-1-20",
        "end_time": "string",
        "description": "string", #内容简介
        "price": int,
        "personNum": int, #正在学习人数
        "course_id": "string",
    }
    """
    def post(self, request):
        msg = json.loads(request.body)
        course_id = msg.get('course_id', '')

        try:
            c = Course.objects.get(id=course_id)
            return self.write_json({'errno': 0, 'msg': 'success', 'data': {
                "title": c.title,
                "cover": c.cover,
                "host": c.host, #课程主讲人
                "start_time": c.start_time[:10],
                "end_time": c.end_time[:10],
                "description": c.description, #内容简介
                "price": c.price,
                "personNum": 0, #TODO 正在学习人数
                "course_id": c.id,
            }})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '课程不存在', 'data': {}})

class Messages(BaseHandler):
    """
    消息中心

    url: api/xcx/messages
    method: POST
    parameters {
        token: string,
        page: int,
        userId: string
    }

    return {
        errno: 0/1,
        msg: string,
        data: [
            {
                time: int,
                msg: [
                    {
                        avatar: string,
                        text: string,
                        card: {
                            type: string, # markdown
                            title: string,
                            link: string,
                        }
                    }
                ]
            }
        ]
    }
    """
    def post(self, request):
        msg = json.loads(request.body)
        token = msg.get('token', '')
        page = msg.get('page', '')
        user_id = msg.get('userId', '')

        try:
            user = UserProfile.objects.get(id=user_id)
            messages = System_Message.objects.filter(to_user=user)
            if not messages:
                return self.write_json({'errno': 1, 'msg': '无消息', 'data': []})

            date_set = set([m.create_time.strftime('%Y-%m-%d') for m in messages])
            for d in date_set:
                one_more_day = datetime.datetime.strptime(d, '%Y-%m-%d') + datetime.timedelta(days=1)
                msgs = messages.filter(
                            create_time__gte=datetime.datetime.strptime(d, '%Y-%m-%d'),
                            create_time__lt=one_more_day
                )

                temp = {}
                temp['time'] = msgs[0].create_time
                temp['msg'] = []
                for m in msgs:
                    temp_msg = {}
                    temp_msg['avatar'] = m.user.avatar
                    temp_msg['text'] = m.message #TODO
                    temp_msg['card'] = {
                        'type': m.card_tags,
                        'title': m.content, #TODO
                        'link': m.card_url,
                        'card_id': m.card_id
                    }
                    temp['msg'].append(temp_msg)
            data = []
            data.append(temp)
            return self.write_json({'errno': 0, 'msg': 'success', 'data': {'errno': 0, 'msg': 'success', 'data': data}})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在', 'data': []})

class MyCollections(BaseHandler):
    """
    我的收藏/卡片收藏

    url: api/xcx/my-collections
    method: POST
    parameters {
        userId: string,
        token: string,
        collect_type: string, # all/deep/writing
        page: int,
    }

    return {
        errno: int, #0/1
        msg: string,
        data: list, # [
            {
                card_type: string, #markdown/exam/video
                title: string,
                card_id: string,
            }
        ]
    }
    """
    def post(self, request):
        msg = json.loads(request.body)
        user_id = msg.get('userId', '')
        token = msg.get('token', '')
        collect_type = msg.get('collect_type', '')
        page = msg.get('page', 1)

        user = UserProfile.objects.get(id=user_id)
        colt = Card_Collect.objects.filter(user=user, status=1)

        data = []
        for c in colt:
            data.append({
                'card_type': c.card.c_type,
                'title': c.card.file_name,
                'card_id': c.card.id
            })
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})

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
                        "status": 1, #1已学
                        "childern": []
                    },
                    {
                        "title": "美美美",
                        "key": "af13895a0b0f11e88b265254009ecd21",
                        "type": "file",
                        "status": 0, #0未学
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
