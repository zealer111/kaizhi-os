from apps.api.youzan import auth
from apps.api.youzan.yzclient import *
from apps.backs.views.base_views import BaseHandler
from django.http import HttpResponse
from apps.api.models import * 
import requests
import json
from django.db import transaction
from apps.api.utils import auth_decorator,generate_token
from django.contrib.auth.models import User


class Get_Order(BaseHandler):
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        if 'TRADE' in msg.get('type'):
            print(msg.get('id'))
            sign = auth.Sign(app_id='${app_id}', app_secret='${app_secret}')
            yzclient = YZClient(sign)
            params = {}
            params['tid']=msg.get('id')
            files = {}
            result = yzclient.invoke('youzan.trade.get','4.0.0','GET',params=params,files=files)
            r = json.loads(result.decode('utf-8'))
            s = (((r.get('response')).get('full_order_info')).get('order_info')).get('status_str')
            phone = (((r.get('response')).get('full_order_info')).get('address_info')).get('receiver_tel')
            good =  (((r.get('response')).get('full_order_info')).get('orders'))
            price =  (((r.get('response')).get('full_order_info')).get('pay_info')).get('total_fee')
            print(r)
            print(s)
            print(phone)
            print(price)
            try:
                for goods in good:
                    course = Course.objects.get(title=goods.get('title'))
                    if '已完成' == s:
                        ups = UserProfile.objects.filter(phone=phone)
                        if not ups:
                            user = User.objects.create_user(username=phone,password='123456')
                            up = UserProfile()
                            up.user = user
                            up.head_img = 'http://static.openmindclub.com/image/default-avatar/avatar2.png'
                            up.phone = phone
                            up.username = phone
                            up.token = generate_token(up.id)
                            up.save()
                            user_buy = User_Buy_Record()
                            user_buy.user = up
                            user_buy.price = price
                            user_buy.course = course
                            user_buy.status = 1
                            user_buy.save()
                        if ups:
                            for us in ups:
                                user_buy = User_Buy_Record()
                                user_buy.user = us
                                user_buy.course = course
                                user_buy.status = 1
                                user_buy.save()
                return self.write_json({'code':0,'msg':'success'})
            except Course.DoesNotExist:
                return self.write_json({'code':0,'msg':'success'})
        return self.write_json({'code':0,'msg':'success'})


class My_Buy_Course_Info(BaseHandler):
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            info = User_Buy_Record.objects.filter(user=up)
            for infos in info:
                course = Course.objects.filter(title=infos.course)
                for courses in course:
                    data.append({
                        'title':courses.title,
                        'status':1,
                        'course_id':courses.id,
                        'description':courses.description,
                        'host':courses.host,
                        'subtitle':courses.subtitle,
                        'classify':courses.classify,
                        'price':courses.price,
                        'subtitle':courses.subtitle,
                        'is_discuss':courses.is_discuss,
                        'cover':courses.cover,
                        'price_url':courses.price_url,
                        'start_time':courses.start_time,
                        'end_time':courses.end_time,
                    })
            return self.write_json({'errno':0,'msg':'success','data':data})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在用户！！！'})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在购买记录！！！'})


class User_Apply_Course(BaseHandler):
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            course = Course.objects.get(id=msg.get('course_id'))
            ubr = User_Buy_Record.objects.filter(course=course,user=up)
            if not ubr:
                user_buy = User_Buy_Record()
                user_buy.user = up
                user_buy.course = course
                user_buy.status = 1
                user_buy.save()
            return self.write_json({'errno':0,'msg':'success'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在用户！！！'})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在购买记录！！！'})
        except Course.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在课程！！！'})


class Buy_Course_Info(BaseHandler):
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        try:
            data = {}
            up = UserProfile.objects.get(username=request.user)
            if '0' == msg.get('type'):
                course = Course.objects.get(id=msg.get('course_id'))
            if '1' == msg.get('type'):
                course = Course.objects.get(short_url=msg.get('short_url'))
            ubr = User_Buy_Record.objects.filter(course=course,user=up)
            if not ubr:
                data = {
                'status':0,
                }
            for ubrs in ubr:
                data = {
                    'status':ubrs.status
                    }
            return self.write_json({'errno':0,'msg':'success','data':data})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在用户！！！'})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在购买记录！！！'})
        except Course.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在课程！！！'})


