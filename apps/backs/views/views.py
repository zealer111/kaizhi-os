#-*-coding:utf8;-*-
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from .base_views import BaseHandler
from django.contrib.auth import authenticate,login
from django.http import HttpResponse
from datetime import datetime
import requests
from apps.api.utils import backs_token
import json
from django.db.models import Q
from apps.api.utils import get_client_ip,auth_decorator,auth_decorator,generate_token
from apps.api.models import *
from apps.api.logger import logger_decorator
from django.core.paginator import Paginator,EmptyPage
from django.contrib.auth.models import User
from django.db import transaction
from apps import settings
from apps.backs.utils import auth_decorator


def file_path(self,key, return_json=True):

    package = Master_Package.objects.get(id=key)
    data = []
    data.append({
        'file':package.package_name,
        'type':0,
        'id':package.id,
        'pid':0,
        'index':-1,
        'is_assistant':0,
        'tags':0,
        'content':0,
        'card_location':0
        })
    card = Card.objects.filter(~Q(tags=4),package_id=package.id)
    for cards in card:
        da = {
        'file':cards.file_name,
        'id':cards.id,
        'type':cards.c_type,
        'index':cards.index,
        'is_assistant':0,
        'content':cards.content,
        'pid':cards.pid,
        'tags':cards.tags,
        'card_location':cards.card_location
        }
        data.append(da)


    def getChildren(id=0):
        sz=[]
        for obj in data:
            if  obj['pid'] ==id:
                sz.append({
                    'key':obj["id"],
                    'pid':obj['pid'],
                    'index':obj['index'],
                    'is_assistant':obj['is_assistant'],
                    'title':obj['file'],
                    'type':obj['type'],
                    'content':obj['content'],
                    'tags':obj['tags'],
                    'card_location':obj['card_location'],
                    'children':getChildren(obj['id'])})
        return sz
    if return_json:
        return self.write_json({'errno':0, 'msg': 'success','data':getChildren()})
    else:
        return {'errno':0, 'msg': 'success','data':getChildren()}

class Login(BaseHandler):
    @logger_decorator
    def post(self, request):
        user = json.loads(request.body)
        phone = user.get('phone')
        password = user.get('password')
        try:
            admin = UserProfile.objects.get(phone=phone)
        except:
            return self.write_json({'errno':1,'msg':'用户不存在!'})
        if 1 != admin.role:
            return self.write_json({'errno':'1','msg':'该用户不是管理员！！！'})
        user = authenticate(request, username=phone, password=password)
        if user:
            login(request, user)
            try:
                up = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return self.write_json({'errno':1,'msg':'用户不存在!'})
        else:
            return self.write_json({'errno':'1','msg':'密码错误，请重新输入！！！'})

        request.session['username'] = up.username
        request.session.set_expiry(300)
        data = {
            'token':generate_token(up.id),
            'userid':up.id,
            'username':up.username,
            'head_img':up.head_img,
            'phone':up.phone,
            'role':up.role
           }
        return self.write_json({'errno': 0, 'msg': 'success', 'data': data})


class Get_User(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        user = UserProfile.objects.all()
        phone = request.POST.get('phone')
        data = []
        if phone:
            search_user = UserProfile.objects.filter(phone__contains=phone)
            for us in search_user:
                data.append({
                'id':us.id,
                'username':us.username,
                'phone':us.phone,
                'role':us.role,
                'head_img':us.head_img,
                'create_time':str(us.create_time)[:19]
                })
        else:
            for us in user:
                data.append({
                'id':us.id,
                'username':us.username,
                'phone':us.phone,
                'role':us.role,
                'head_img':us.head_img,
                'create_time':str(us.create_time)[:19]
                })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':user.count(),'data':p.page(page).object_list})


class Check_User(BaseHandler):
    @auth_decorator
    @logger_decorator
    def post(self,request):
        return self.write_json({'errno':0,'msg':''})


class Get_All_User(BaseHandler):
    @logger_decorator
    def post(self,request):
        user = UserProfile.objects.all()
        data = []
        for us in user:
            data.append({
            'id':us.id,
            'username':us.username,
            'phone':us.phone,
            })
        return self.write_json({'errno':0,'msg':'success','data':data})


class Get_All_Course(BaseHandler):
    @logger_decorator
    def post(self,request):
        c = Course.objects.all()
        data = []
        for cs in c:
            data.append({
            'id':cs.id,
            'title':cs.title,
            })
        return self.write_json({'errno':0,'msg':'success','data':data})


class Get_All_Package(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        package = Master_Package.objects.all()
        data = []
        title = ''
        name = request.POST.get('name')
        if name:
            package = Master_Package.objects.filter(package_name__contains=name)
            for ps in package:
                if ps.course:
                    title = ps.course.title
                data.append({
                'id':ps.id,
                'name':ps.package_name,
                'course':title,
                'create_user':ps.create_user.username,
                'sign':ps.sign,
                'create_time':str(ps.create_time)[:19]
                })
        else:
            for ps in package:
                if ps.course:
                    title = ps.course.title
                else:
                    title = ''
                data.append({
                'id':ps.id,
                'name':ps.package_name,
                'course':title,
                'create_user':ps.create_user.username,
                'branch_name':ps.branch,
                'role':ps.role,
                'sign':ps.sign,
                'create_time':str(ps.create_time)[:19]
                })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':package.count(),'data':p.page(page).object_list})


class Get_Assi_Package(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        package = Branch_Package.objects.all()
        data = []
        title = ''
        name = request.POST.get('name')
        if name:
            package = Branch_Package.objects.filter(package_name__contains=name)
            for ps in package:
                if ps.course:
                    title = ps.course.title
                data.append({
                'id':ps.id,
                'name':ps.package_name,
                'course':title,
                'create_user':ps.create_user.username,
                'sign':ps.sign,
                'create_time':str(ps.create_time)[:19]
                })
        else:
            for ps in package:
                if ps.course:
                    title = ps.course.title
                else :
                    title = ''
                data.append({
                'id':ps.id,
                'name':ps.package_name,
                'course':title,
                'create_user':ps.create_user.username,
                'branch_name':ps.branch,
                'role':ps.role,
                'sign':ps.sign,
                'create_time':str(ps.create_time)[:19]
                })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':package.count(),'data':p.page(page).object_list})


class Get_Message(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        message = System_Message.objects.all()
        data = []
        title = ''
        for ms in message:
            data.append({
            'id':ms.id,
            'user':ms.user.username,
            'to_user':ms.to_user.username,
            'phone':ms.user.phone,
            'message':ms.message,
            'key':ms.key,
            'card_url':ms.card_url,
            'create_time':str(ms.create_time)[:19]
            })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':message.count(),'data':p.page(page).object_list})


class Send_Message(BaseHandler):
    @logger_decorator
    def post(self,request):
        msg = json.loads(request.body)
        users = msg.get('user').split(',')
        try:
            for m in users:
                if '所有用户' in msg.get('user'):
                    up = UserProfile.objects.all()
                    for ups in up:
                        admin = UserProfile.objects.get(role=1)
                        message = System_Message()
                        message.user = admin
                        message.to_user = ups
                        message.card_url = msg.get('card_url')
                        message.message = msg.get('message')
                        message.save()
                else:
                    up = UserProfile.objects.get(phone=m.strip())
                    admin = UserProfile.objects.get(role=1)
                    message = System_Message()
                    message.user = admin
                    message.to_user = up
                    message.card_url = msg.get('card_url')
                    message.message = msg.get('message')
                    message.save()
            return self.write_json({'errno':0,'msg':'success'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'输入格式有误！！！'})


class Message_Search(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        phone = request.POST.get('phone')
        user = UserProfile.objects.filter(phone__contains=phone)
        data = []
        for u in user:
            msg = System_Message.objects.filter(user=u)
            for ms in msg:
                data.append({
                    'id':ms.id,
                    'user':ms.user.username,
                    'to_user':ms.to_user.username,
                    'phone':ms.user.phone,
                    'message':ms.message,
                    'create_time':str(ms.create_time)[:19]
                    })
                p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':user.count(),'data':p.page(page).object_list})


class Delete_Message(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self,request):
        s = json.loads(request.body)
        for ss in s:
            msg = System_Message.objects.get(id=ss.get('id'))
            msg.delete()
        return self.write_json({'errno':0,'msg':'success'})


class Add_Package_Sign(BaseHandler):
    @logger_decorator
    def post(self,request):
        try:
            msg = json.loads(request.body)
            package = Master_Package.objects.get(id=msg.get('package_id'))
            package.sign = msg.get('card_id')
            package.save()
            return self.write_json({'errno':0,'msg':'success'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！！'})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡片不存在！！！'})


class Get_User_Buy_Record(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        user = User_Buy_Record.objects.all()
        data = []
        phone = request.POST.get('phone')
        if phone:
            user = UserProfile.objects.filter(phone__contains=phone)
            for u in user:
                buy = User_Buy_Record.objects.filter(user=u)
                for buys in buy:
                    data.append({
                        'id':buys.id,
                        'userid':buys.user.id,
                        'courseid':buys.course.id,
                        'username':buys.user.username,
                        'phone':buys.user.phone,
                        'course':buys.course.title,
                        'price':buys.price,
                        'status':buys.status,
                        'create_time':str(buys.create_time)[:19]
                        })
        else:
            for us in user:
                data.append({
                'id':us.id,
                'userid':us.user.id,
                'courseid':us.course.id,
                'username':us.user.username,
                'phone':us.user.phone,
                'course':us.course.title,
                'price':us.price,
                'status':us.status,
                'create_time':str(us.create_time)[:19]
                })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':user.count(),'data':p.page(page).object_list})


class User_Buy_Course(BaseHandler):
    @logger_decorator
    def post(self,request):
        msg = json.loads(request.body)
        user = UserProfile.objects.get(id=msg.get('userid'))
        course = Course.objects.get(id=msg.get('course_id'))
        r = User_Buy_Record.objects.filter(user=user,course=course)
        if not r:
            buy = User_Buy_Record()
            buy.user = user
            buy.course = course
            buy.price = msg.get('price')
            buy.status = msg.get('status')
            buy.save()
        return self.write_json({'errno':0,'msg':'success'})


class Upd_Buy_Course(BaseHandler):
    @logger_decorator
    def post(self,request):
        msg = json.loads(request.body)
        user = UserProfile.objects.get(id=msg.get('userid'))
        course = Course.objects.get(id=msg.get('course_id'))
        buy = User_Buy_Record.objects.get(id=msg.get('buy_id'))
        buy.user = user
        buy.course = course
        buy.price = msg.get('price')
        buy.status = msg.get('status')
        buy.save()
        return self.write_json({'errno':0,'msg':'success'})


class Get_Card(BaseHandler):
    @logger_decorator
    def post(self,request):
        pid = request.POST.get('id')
        try:
            p = Master_Package.objects.get(id=pid)
            c = Card.objects.filter(~Q(tags=4),package_id=p.id,c_type=1)
            data = []
            data.append({
                'id':'',
                'file':'无',
                })
            for cs in c:
                data.append({
                'id':cs.id,
                'file':cs.file_name,
                })
            return self.write_json({'errno':0,'msg':'success','data':data})
        except Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！！'})


class Get_Course(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        course = Course.objects.all()
        cp = ''
        hp = ''
        cpid = ''
        hpid = ''
        data = []
        title = request.POST.get('title')
        if title:
            search_course = Course.objects.filter(title__contains=title)
            for courses in search_course:
                course_package = Course.objects.get(id=courses.id).master_course.filter(p_type=0)
                homework_package = Course.objects.get(id=courses.id).master__course.filter(p_type=1)
                for cps in course_package:
                    cp = cps.package_name
                    cpid = cps.id
                for hps in homework_package:
                    hp = hps.package_name
                    hpid = hps.id
                num = User_Buy_Record.objects.filter(course=courses).count()
                data.append({
                    'num':num,
                    'title':courses.title,
                    'course_id':courses.id,
                    'description':courses.description,
                    'create_user':courses.create_user.username,
                    'userid':courses.create_user.id,
                    'host':courses.host,
                    'subtitle':courses.subtitle,
                    'classify':courses.classify,
                    'price':courses.price,
                    'sign':courses.sign,
                    'subtitle':courses.subtitle,
                    'is_discuss':courses.is_discuss,
                    'is_discuss':courses.is_graduate,
                    'is_fee':courses.is_fee,
                    'cover':courses.cover,
                    'coursepackage':cp,
                    'cpid':cpid,
                    'hpid':hpid,
                    'homeworkpackage':hp,
                    'price_url':courses.price_url,
                    'start_time':courses.start_time,
                    'end_time':courses.end_time,
                })
        else:
            for courses in course:
                num = User_Buy_Record.objects.filter(course=courses).count()
                course_package = Master_Package.objects.filter(course=courses,p_type=0)
                homework_package = Master_Package.objects.filter(course=courses,p_type=1)
                if course_package:
                    cpid = course_package[0].id
                    cp = course_package[0].package_name
                if homework_package:
                    hpid = homework_package[0].id
                    hp = homework_package[0].package_name
                if not course_package:
                    cp = ''
                    cpid = ''
                if not homework_package:
                    hp = ''
                    hpid =''
                data.append({
                    'num':num,
                    'title':courses.title,
                    'course_id':courses.id,
                    'description':courses.description,
                    'create_user':courses.create_user.username,
                    'userid':courses.create_user.id,
                    'host':courses.host,
                    'subtitle':courses.subtitle,
                    'classify':courses.classify,
                    'price':courses.price,
                    'sign':courses.sign,
                    'subtitle':courses.subtitle,
                    'is_discuss':courses.is_discuss,
                    'is_discuss':courses.is_graduate,
                    'is_fee':courses.is_fee,
                    'cover':courses.cover,
                    'cpid':cpid,
                    'hpid':hpid,
                    'coursepackage':cp,
                    'homeworkpackage':hp,
                    'price_url':courses.price_url,
                    'start_time':courses.start_time,
                    'end_time':courses.end_time,
                })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code': 0,'msg': 'success','count':course.count(),'data': p.page(page).object_list})


class Delete_Course(BaseHandler):
    @logger_decorator
    def post(self,request):
        s = json.loads(request.body)
        try:
            for ss in s:
                course = Course.objects.get(id=ss.get('course_id'))
                p = Master_Package.objects.filter(course=course,p_type=2)
                if p:
                    for ps in p:
                        da = {
                            'branch':'master',
                            'repo':ps.package_location
                        }
                        url = settings.GIT_DELETE_REPO
                        r = requests.post(url,data=da)
                        result = r.json()
                        ps.delete()
                course.delete()
            return self.write_json({'errno':0,'msg':'success'})
        except Course.DoesNotExist:
            return self.write_json({'errno':1,'msg':'课程不存在！！！'})


class Delete_Package(BaseHandler):
    @logger_decorator
    def post(self,request):
        s = json.loads(request.body)
        try:
            for ss in s:
                p = Master_Package.objects.get(id=ss.get('id'))
                da = {
                    'branch':'master',
                    'repo':p.package_location
                    }
                url = settings.GIT_DELETE_REPO
                r = requests.post(url,data=da)
                result = r.json()
                p.delete()
            return self.write_json({'errno':0,'msg':'success'})
        except Course.DoesNotExist:
            return self.write_json({'errno':1,'msg':'课程不存在！！！'})


class Delete_Assistant(BaseHandler):
    @logger_decorator
    def post(self,request):
        s = json.loads(request.body)
        try:
            for ss in s:
                p = Branch_Package.objects.get(id=ss.get('id'))
                da = {
                    'branch':'master',
                    'del_branch':p.branch,
                    'repo':p.package_location
                    }
                url = settings.GIT_DELETE_BRANCH
                r = requests.post(url,data=da)
                result = r.json()
                p.delete()
            return self.write_json({'errno':0,'msg':'success'})
        except Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！！'})


class Get_Assistant_User(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        user = User_Branch.objects.all()
        data = []
        for us in user:
            data.append({
            'id':us.id,
            'username':us.user.username,
            'phone':us.user.phone,
            'package':us.package.package_name,
            'create_user':us.package.create_user.username,
            'branch':us.branch,
            'create_time':str(us.create_time)[:19]
            })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':user.count(),'data':p.page(page).object_list})


class User_Package(BaseHandler):
    @logger_decorator
    def post(self,request):
        userid = request.POST.get('id')
        user = UserProfile.objects.get(id=userid)
        p = Master_Package.objects.filter(~Q(p_type=2),create_user=user)
        u = UserProfile.objects.filter(~Q(id=userid))
        user = []
        data = []
        for us in u:
            user.append({
            'id':us.id,
            'phone':us.phone
            })
        data.append({
            'id':'',
            'package_name':'无',
            })
        for ps in p:
            data.append({
            'id':ps.id,
            'package_name':ps.package_name,
            })
        return self.write_json({'errno':0,'msg':'success','data':data,'user':user})


class Delete_User(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self,request):
        s = json.loads(request.body)
        for ss in s:
            user = UserProfile.objects.get(id=ss.get('id'))
            up = User.objects.get(username=user.phone)
            user.delete()
            up.delete()
        return self.write_json({'errno':0,'msg':'success'})


class Delete_Buy_Course(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self,request):
        s = json.loads(request.body)
        for ss in s:
            buy = User_Buy_Record.objects.get(id=ss.get('id'))
            buy.delete()
        return self.write_json({'errno':0,'msg':'success'})


class Modify_Course(BaseHandler):
    @logger_decorator
    def post(self, request):
        msg = json.loads(request.body)
        try:
            course = Course.objects.get(id=msg.get('course_id'))
            package = Course.objects.get(id=msg.get('course_id')).master_course.all()
            up = UserProfile.objects.get(id=msg.get('create_user'))
            course.title = msg.get('title')
            course.description = msg.get('description')
            course.host = msg.get('host')
            course.subtitle = msg.get('subtitle')
            course.classify = msg.get('classify')
            course.price = msg.get('price')
            course.cover = msg.get('cover')
            course.price_url = msg.get('price_url')
            course.start_time = msg.get('start_time')
            course.is_fee = msg.get('is_fee')
            course.is_discuss = msg.get('is_discuss')
            course.sign = msg.get('sign')
            course.end_time = msg.get('end_time')
            course_package = msg.get('cp')
            homework_package = msg.get('hp')
            course.save()
            if 1 == msg.get('is_discuss'):
                dis = Master_Package.objects.filter(create_user=up,course=course)
                if not dis:
                    dis_package = Master_Package()
                    dis_package.course = course
                    dis_package.package_name = title +'讨论卡包'
                    dis_package.p_type = 2
                    dis_package.create_user = up
                    data = {
                        'branch':'master',
                        'dirname':title +'讨论卡包'
                    }
                    url = settings.GIT_REPO_URL
                    r = requests.post(url,data=data)
                    result = r.json()
                    if '0' == result.get('errno'):
                        dis_package.package_location = result.get('data')['repo']
                        dis_package.save()

            if course_package:
                try:
                    package = Master_Package.objects.get(id=course_package)
                    package.course = course
                    package.p_type = 0
                    package.create_user = up
                    package.save()
                except Master_Package.DoesNotExist:
                    return self.write_json({'errno':'1','msg':'卡包不存在'})
            if homework_package:
                try:
                    package = Master_Package.objects.get(id=homework_package)
                    package.course = course
                    package.p_type = 1
                    package.create_user = up
                    package.save()
                except Master_Package.DoesNotExist:
                    return self.write_json({'errno':'1','msg':'卡包不存在'})
            if '' == homework_package:
                course.is_homework = 0
                course.save()
            return self.write_json({'errno': 0, 'msg': 'success'})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在课程信息'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡包！！！'})



class Assistant_User_Search(BaseHandler):
    @logger_decorator
    def post(self,request):
        page = request.POST.get('page')
        phone = request.POST.get('phone')
        user = User_Branch.objects.filter(phone__contains=phone)
        data = []
        for us in user:
            data.append({
            'id':us.id,
            'username':us.user.username,
            'phone':us.user.phone,
            'package':us.package.package_name,
            'create_user':us.package.create_user.username,
            'branch':us.branch,
            'create_time':str(us.create_time)[19:]
            })
        p = Paginator(data,request.POST.get('limit'))
        return self.write_json({'code':0,'msg':'success','count':user.count(),'data':p.page(page).object_list})


class User_Assistant(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self, request):
        user_info = json.loads(request.body)
        key  = user_info.get('package')
        try:
            p = Master_Package.objects.get(id=key)
            up = UserProfile.objects.get(id=user_info.get('assi_user'))
            print(up)
            up.role = 3
            up.save()

            def create_file(data, pid, package):
                d = data['children']
                for child in d:
                    child_data = child.get('children')
                    card = Card()
                    card.file_name = child.get('title')
                    card.c_type = child.get('type')
                    card.pid = pid
                    card.card_location = child.get('card_location')
                    card.tags = child.get('tags')
                    card.create_user = p.create_user
                    card.package_id = package.id
                    card.content = child.get('content')
                    card.branch = package.branch
                    card.package_location = package.package_location
                    card.index = child.get('index')
                    card.save()
                    if child_data:
                        create_file(child, card.id, package)

            def create_pack(value):

                assi_package = Branch_Package()
                assi_package.create_user = up
                assi_package.package_name = value.get('title')
                assi_package.branch = up.phone
                assi_package.package_location = p.package_location
                assi_package.role = 1
                data = {
                    'branch':up.phone,
                    'repo':p.package_location
                    }
                url = settings.GIT_BRANCH_URL
                r = requests.post(url,data=data)
                result = r.json()
                print(result)
                if '0' == result.get('errno'):
                    assi_package.branch_name = result.get('data')['branch']
                    assi_package.save()
                    b = User_Branch.objects.filter(user=up,create_package=p,assi_package=assi_package)
                    if not b:
                        user_branch = User_Branch()
                        user_branch.user = up
                        user_branch.create_package = p
                        user_branch.assi_package = assi_package
                        user_branch.branch = up.phone
                        user_branch.save()
                    create_file(value, assi_package.id, assi_package)
                else:
                    return self.write_json({'errno': 1, 'msg': '分支已存在！！！'})
            create_user = UserProfile.objects.get(id=user_info.get('create_user'))
            path = file_path(self,key,False)
            s = create_pack(path.get('data')[0])
            return self.write_json({'errno': 0, 'msg': 'success'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 0, 'msg': '不存在卡包!!!'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户!!!'})
        except User_Branch.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户分支信息!!!'})


class Upd_User_Info(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self, request):
        print(request.body)
        user_info = json.loads(request.body)
        try:
            user = UserProfile.objects.get(id=user_info.get('userid'))
            name = UserProfile.objects.filter(~Q(username=user.username),username=user_info.get('username'))
            if name :
                return self.write_json({'errno': 1, 'msg': '昵称已存在，请换一个昵称！！！'})
            user.username = user_info.get('username')
            user.nickname = user_info.get('nickname')
            user.phone = user_info.get('phone')
            user.role = user_info.get('role')
            user.save()
            up = User.objects.get(username=user.user)
            up.username = user_info.get('phone')
            up.save()
            data = {
             'userid':user.id,
             'token':user.token,
             'username':user.username,
             'nickname':user.nickname,
             'phone':user.phone,
             'head_img':user.head_img
             }
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except User.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在用户'})
        except UserProfile.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在用户'})
        except BaseException:
             return self.write_json({'errno': 1, 'msg': '手机号已存在！！！'})
