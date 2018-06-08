
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
from apps import log_utils
from apps.api import git_utils
import logging

logging.basicConfig(filename='/tmp/kaizhi.log',level=logging.DEBUG)
log_utils.default_logging_config()
logger = log_utils.getLogger(__name__)



def delete_file(self, key, user,role):
    try:
        logger.info("delete file: %s %s %s" % (key, user, role))
        up = UserProfile.objects.get(username=user)
        card = Card.objects.get(id=key)
        logger.debug("delete file: %s %s %s" % (card.branch,card.package_location,card.card_location))
        if settings.GIT_TYPE_FILE  == card.c_type:
            result = git_utils.delete_file(card.package_location,card.branch,card.card_location)
            card.delete()
            return get_file_dir(self,role)
        elif settings.GIT_TYPE_DIR == card.c_type:
            c = Card.objects.filter(pid=card.id)
            logger.debug("delete file dir: %s %s %s" % (card.branch,card.package_location,card.card_location))
            for cs in c:
                cs.delete()
            result = git_utils.delete_folder(card.package_location,card.branch,card.card_location)
            card.delete()
            return get_file_dir(self,role)
    except Card.DoesNotExist:
        return self.write_json({'errno':1,'msg':'不存在文件'})


class Create_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self, request):
        course = json.loads(request.body)
        cover = course.get('cover')
        title = course.get('title')
        subtitle = course.get('subtitle')
        issue = course.get('issue')
        description = course.get('description')
        is_fee = course.get('is_fee')
        price = course.get('price')
        price_url = course.get('price_url')
        short_url = course.get('short_url')
        url = Course.objects.filter(short_url=short_url)
        if url:
           return self.write_json({'errno': 1, 'msg': '该短连接已存在！！!'})
        is_discuss = course.get('is_discuss')
        is_graduate = course.get('is_graduate')
        host = course.get('host')
        classify = course.get('classify')
        start_time = course.get('start_time')
        end_time = course.get('end_time')
        course_package = course.get('coursePackage')
        homework_package = course.get('homeworkPackage')
        up = UserProfile.objects.get(username=request.user)
        course = Course.objects.filter(title=title)
        if course:
           return self.write_json({'errno': 1, 'msg': '该课程已存在！！!'})
        course = Course()
        course.cover = cover
        course.title = title
        course.subtitle = subtitle
        course.issue = issue
        course.description = description
        course.is_fee = is_fee
        course.create_user = up
        course.price = price
        course.price_url = price_url
        course.short_url = short_url
        course.is_discuss = is_discuss
        course.is_graduate = is_graduate
        course.host = host
        course.classify = classify
        course.start_time = start_time
        course.end_time = end_time
        course.save()
        if 1 == is_discuss:
            dis_package = Master_Package()
            dis_package.course = course
            dis_package.package_name = title +'讨论卡包'
            dis_package.p_type = 2
            dis_package.create_user = up
            package_name = title +'讨论卡包'
            result = git_utils.create_git_package(package_name)
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
            except Package.DoesNotExist:
                return self.write_json({'errno':'1','msg':'卡包不存在'})
        if homework_package:
            try:
                package = Master_Package.objects.get(id=homework_package)
                package.course = course
                package.p_type = 1
                package.create_user = up
                package.save()
                course.is_homework = 1
                course.save()
            except Master_Package.DoesNotExist:
                return self.write_json({'errno':'1','msg':'卡包不存在'})
        return self.write_json({'errno': 0, 'msg': 'success'})


class Get_Course(BaseHandler):
    @logger_decorator
    def post(self, request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        if 'classify' in msg:
            if  msg.get('classify') =='' :
                course = Course.objects.all()
                data = []
                for courses in course:
                    num = User_Buy_Record.objects.filter(course=courses).count()
                    data.append({
                        'num':num,
                        'title':courses.title,
                        'course_id':courses.id,
                        'description':courses.description,
                        'host':courses.host,
                        'subtitle':courses.subtitle,
                        'classify':courses.classify,
                        'is_discuss':courses.is_discuss,
                        'is_fee':courses.is_fee,
                        'price':courses.price,
                        'subtitle':courses.subtitle,
                        'cover':courses.cover,
                        'price_url':courses.price_url,
                        'short_url':courses.short_url,
                        'start_time':courses.start_time,
                        'end_time':courses.end_time,
                        'create_time':str(courses.create_time)[19:],
                        'upd_time':str(courses.update_time)[19:]

                    })
                try:
                    p = Paginator(data,count)

                    return self.write_json({'errno': 0, 'msg': 'success','total_count':course.count(),
                                            'total_page':p.num_pages,'data': p.page(page).object_list})

                except EmptyPage:
                    data = []
                    return self.write_json({'errno':1, 'msg': '暂无数据！！','data':data})

            course = Course.objects.filter(classify=msg.get('classify'))
            data = []
            for courses in course:
                num = User_Buy_Record.objects.filter(course=courses).count()
                data.append({
                'num':num,
                'title':courses.title,
                'course_id':courses.id,
                'description':courses.description,
                'host':courses.host,
                'subtitle':courses.subtitle,
                'classify':courses.classify,
                'price':courses.price,
                'is_discuss':courses.is_discuss,
                'subtitle':courses.subtitle,
                'is_fee':courses.is_fee,
                'cover':courses.cover,
                'price_url':courses.price_url,
                'short_url':courses.short_url,
                'start_time':courses.start_time,
                'end_time':courses.end_time,

              })
            try:
                p = Paginator(data,count)

                return self.write_json({'errno': 0, 'msg': 'success','total_count':course.count(),
                                        'total_page':p.num_pages,'data': p.page(page).object_list})
            except EmptyPage:
                data = []
                return self.write_json({'errno':1, 'msg': '暂无数据！！','data':data})
        data = []
        course = Course.objects.all()
        for courses in course:
            num = User_Buy_Record.objects.filter(course=courses).count()
            data.append({
            'num':num,
            'title':courses.title,
            'course_id':courses.id,
            'description':courses.description,
            'host':courses.host,
            'subtitle':courses.subtitle,
            'classify':courses.classify,
            'price':courses.price,
            'subtitle':courses.subtitle,
            'is_discuss':courses.is_discuss,
            'is_fee':courses.is_fee,
            'cover':courses.cover,
            'price_url':courses.price_url,
            'short_url':courses.short_url,
            'start_time':courses.start_time,
            'end_time':courses.end_time,
          })
        try:
            p = Paginator(data,count)
            return self.write_json({'errno': 0,'msg': 'success','total_count':course.count(),
                                    'total_page':p.num_pages,'data': p.page(page).object_list})

        except EmptyPage:
            data = []
            return self.write_json({'errno':1, 'msg': '暂无数据！！','data':data})


class Delete_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            course = Course.objects.get(id=msg.get('course_id'))
            p = Master_Package.objects.filter(course=course,p_type=2)
            for ps in p:
                result = git_utils.delete_package(ps.package_location)
                ps.delete()
            course.delete()
            all_course = Course.objects.filter(create_user=up)
            for courses in all_course:
                data.append ({
                'title':courses.title,
                'course_id':courses.id,
                'description':courses.description,
                'host':courses.host,
                'subtitle':courses.subtitle,
                'classify':courses.classify,
                'price':courses.price,
                'subtitle':courses.subtitle,
                'is_discuss':courses.is_discuss,
                'is_fee':courses.is_fee,
                'cover':courses.cover,
                'price_url':courses.price_url,
                'start_time':courses.start_time,
                'end_time':courses.end_time,
            })
            pages = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':all_course.count(),
                                    'total_page':pages.num_pages,'data': pages.page(page).object_list})
        except Course.DoesNotExist:
            return self.write_json({'errno':1,'msg':'课程不存在!!!'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在!!!'})
        except EmptyPage:
            data = []
            return self.write_json({'errno':1, 'msg': '暂无数据！！','data':data})


class Modify_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        try:
            course = Course.objects.get(id=msg.get('course_id'))
            package = Course.objects.get(id=msg.get('course_id')).master_course.all()
            course.title = msg.get('title')
            course.description = msg.get('description')
            course.host = msg.get('host')
            course.subtitle = msg.get('subtitle')
            course.classify = msg.get('classify')
            course.price = msg.get('price')
            course.cover = msg.get('cover')
            course.price_url = msg.get('price_url')
            url = Course.objects.filter(~Q(short_url=course.short_url),short_url=msg.get('short_url'))
            if url:
                return self.write_json({'errno': 1, 'msg': '该短链接已存在！！!'})
            course.short_url = msg.get('short_url')
            course.start_time = msg.get('start_time')
            course.is_fee = msg.get('is_fee')
            course.is_discuss = msg.get('is_discuss')
            course.end_time = msg.get('end_time')
            course_package = msg.get('coursePackage')
            homework_package = msg.get('homeworkPackage')
            up = UserProfile.objects.get(username=request.user)
            course.save()
            if 1 == msg.get('is_discuss'):
                dis = Master_Package.objects.filter(create_user=up,course=course,p_type=2)
                if not dis:
                    dis_package = Master_Package()
                    dis_package.course = course
                    dis_package.package_name = course.title +'讨论卡包'
                    dis_package.p_type = 2
                    dis_package.create_user = up
                    package_name = course.title +'讨论卡包'
                    result = git_utils.create_git_package(package_name)
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
                    course.is_homework = 1
                    course.save()

                except Master_Package.DoesNotExist:
                    return self.write_json({'errno':'1','msg':'卡包不存在'})

            if not homework_package:
                course.is_homework = 0
                course.save()
            return self.write_json({'errno': 0, 'msg': 'success'})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在课程信息'})


class Course_Detail(BaseHandler):
    @logger_decorator
    def post(self, request):
        msg = json.loads(request.body)
        try:
            if '0' == msg.get('type'):
                course = Course.objects.get(id=msg.get('course_id'))
            if '1' == msg.get('type'):
                course = Course.objects.get(short_url=msg.get('short_url'))
            cp = {}
            hp = {}
            course_package = Master_Package.objects.filter(course=course,p_type=0)
            for cps in course_package:
                cp = {'title':cps.package_name,'key':cps.id}
            if 1 == course.is_homework:
                homework_package = Master_Package.objects.filter(course=course,p_type=1)
                for hps in homework_package:
                    hp = {'title':hps.package_name,'key':hps.id}
            if 0 == course.is_homework:
                hp = {}
            data = {
                'title':course.title,
                'course_id':course.id,
                'description':course.description,
                'host':course.host,
                'subtitle':course.subtitle,
                'classify':course.classify,
                'price':course.price,
                'subtitle':course.subtitle,
                'is_discuss':course.is_discuss,
                'is_fee':course.is_fee,
                'cover':course.cover,
                'price_url':course.price_url,
                'short_url':course.short_url,
                'coursepackage':cp,
                'homeworkpackage':hp,
                'start_time':course.start_time,
                'end_time':course.end_time,
            }
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在课程信息'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡包'})


class My_Create_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            course = Course.objects.filter(create_user=up)
            cp = {}
            hp = {}
            data = []
            for courses in course:
                num = User_Buy_Record.objects.filter(course=courses).count()
                course_package = Course.objects.get(id=courses.id).master_course.filter(p_type=0)
                homework_package = Course.objects.get(id=courses.id).master_course.filter(p_type=1)
                for cps in course_package:
                    cp = {'title':cps.package_name,'key':cps.id}
                for hps in homework_package:
                    hp = {'title':hps.package_name,'key':hps.id}
                data.append({
                    'num':num,
                    'title':courses.title,
                    'course_id':courses.id,
                    'description':courses.description,
                    'host':courses.host,
                    'subtitle':courses.subtitle,
                    'classify':courses.classify,
                    'price':courses.price,
                    'subtitle':courses.subtitle,
                    'is_fee':courses.is_fee,
                    'is_discuss':courses.is_discuss,
                    'cover':courses.cover,
                    'price_url':courses.price_url,
                    'coursepackage':cp,
                    'homeworkpackage':hp,
                    'start_time':courses.start_time,
                    'end_time':courses.end_time,
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':course.count(),
                                    'total_page':p.num_pages,'data': p.page(page).object_list})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '暂无课程信息！！！'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡包'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在课程信息！！！'})
        except EmptyPage:
            data = []
            return self.write_json({'errno': 1, 'msg': '暂无数据！！！','data':data})


class Search_My_Create_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        title = msg.get('title')
        try:
            up = UserProfile.objects.get(username=request.user)
            course = Course.objects.filter(title__contains=title,create_user=up)
            cp = {}
            hp = {}
            data = []
            for courses in course:
                num = User_Buy_Record.objects.filter(course=courses).count()
                course_package = Course.objects.get(id=courses.id).master_course.filter(p_type=0)
                homework_package = Course.objects.get(id=courses.id).master_course.filter(p_type=1)
                for cps in course_package:
                    cp = {'title':cps.package_name,'key':cps.id}
                for hps in homework_package:
                    hp = {'title':hps.package_name,'key':hps.id}
                data.append({
                    'num':num,
                    'title':courses.title,
                    'course_id':courses.id,
                    'description':courses.description,
                    'host':courses.host,
                    'subtitle':courses.subtitle,
                    'classify':courses.classify,
                    'price':courses.price,
                    'subtitle':courses.subtitle,
                    'is_fee':courses.is_fee,
                    'is_discuss':courses.is_discuss,
                    'cover':courses.cover,
                    'price_url':courses.price_url,
                    'coursepackage':cp,
                    'homeworkpackage':hp,
                    'start_time':courses.start_time,
                    'end_time':courses.end_time,
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':course.count(),
                                    'total_page':p.num_pages,'data': p.page(page).object_list})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '暂无课程信息！！！'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡包'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在课程信息！！！'})
        except EmptyPage:
            data = []
            return self.write_json({'errno': 1, 'msg': '暂无数据！！！','data':data})


class My_Course(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        try:
            up = UserProfile.objects.get(username=request.user)
            course = User_Buy_Record.objects.filter(user=up)
            data = []
            pros = 0
            for courses in course:
                progress = User_Course_Record.objects.filter(user=up,course=courses.course)
                for pro in progress:
                    pros = pro.progress
                data.append({
                    'title':courses.course.title,
                    'progress':pros,
                    'is_study':User_Course_Record.objects.filter(course_id=courses.course.id,user=up).count(),
                    'course_id':courses.course.id,
                    'description':courses.course.description,
                    'host':courses.course.host,
                    'subtitle':courses.course.subtitle,
                    'classify':courses.course.classify,
                    'price':courses.course.price,
                    'subtitle':courses.course.subtitle,
                    'is_discuss':courses.course.is_discuss,
                    'cover':courses.course.cover,
                    'is_fee':courses.course.is_fee,
                    'price_url':courses.course.price_url,
                    'start_time':courses.course.start_time,
                    'end_time':courses.course.end_time,
                })
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except User_Buy_Record.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '暂无课程信息！！！'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在课程信息！！！'})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在课程信息！！！'})
        except Course.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在课程信息！！！'})


class Course_Search(BaseHandler):
    @logger_decorator
    def post(self, request):
        info = json.loads(request.body)
        title = info.get('title')
        page = info.get('page')
        count = info.get('count')
        course = Course.objects.filter(title__contains=title)
        data = []
        for courses in course:
            data.append({
                'title':courses.title,
                'course_id':courses.id,
                'description':courses.description,
                'host':courses.host,
                'subtitle':courses.subtitle,
                'classify':courses.classify,
                'price':courses.price,
                'is_discuss':courses.is_discuss,
                'is_fee':courses.is_fee,
                'subtitle':courses.subtitle,
                'cover':courses.cover,
                'price_url':courses.price_url,
                'short_url':courses.short_url,
                'start_time':courses.start_time,
                'end_time':courses.end_time,
            })
        try:
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                    'total_count':course.count(),'data': p.page(page).object_list})
        except EmptyPage:
            data = []
            return self.write_json({'errno':1, 'msg': '暂无数据！！','data':data})



class Card_Search(BaseHandler):
    @logger_decorator
    def post(self, request):
        info = json.loads(request.body)
        file_name = info.get('file_name')
        page = info.get('page')
        count = info.get('count')

        try:
            card = Card.objects.filter(file_name__contains=file_name,c_type=1)
            data = []
            for cards in card:
               data.append({
                    'file':cards.file_name,
                    'id':cards.id,
                    'type':cards.c_type,
                    'pid':cards.pid,
                    'index':cards.index,
             })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                    'total_count':card.count(),'data': p.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '无信息!!!',})


class My_Create_Card_Search(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        info = json.loads(request.body)
        file_name = info.get('file_name')
        page = info.get('page')
        count = info.get('count')
        try:
            p = get_package(self,info.get('key'))
            up = UserProfile.objects.get(username=request.user)
            data = []
            if p :
                card = Card.objects.filter(~Q(tags=4),~Q(tags=3),file_name__contains=file_name,
                                               c_type=1,create_user=up,package_id=p.id)
                for cards in card:
                        data.append({
                            'title':cards.file_name,
                            'key':cards.id,
                            'type':cards.c_type,
                            'pid':cards.pid,
                            'index':cards.index,
                            'is_assistant':0,
                         })

                p = Paginator(data,count)
                return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                        'total_count':card.count(),'data': p.page(page).object_list})
            elif '0' == info.get('key'):
                mastet_pacakge = Master_Package.objects.filter(create_user=up)
                for ms in mastet_pacakge:
                    card = Card.objects.filter(file_name__contains=file_name,c_type=1,create_user=up,package_id=ms.id)
                    for cards in card:
                        data.append({
                            'title':cards.file_name,
                            'key':cards.id,
                            'type':cards.c_type,
                            'pid':cards.pid,
                            'index':cards.index,
                            'is_assistant':0,
                         })
                p = Paginator(data,count)
                return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                        'total_count':card.count(),'data': p.page(page).object_list})

            elif '1' == info.get('key'):
                branch_pacakge = Branch_Package.objects.filter(create_user=up)
                for bs in branch_pacakge:
                    card = Card.objects.filter(file_name__contains=file_name,c_type=1,create_user=up,package_id=bs.id)
                    for cards in card:
                        data.append({
                            'title':cards.file_name,
                            'key':cards.id,
                            'type':cards.c_type,
                            'pid':cards.pid,
                            'index':cards.index,
                            'is_assistant':0,
                         })
                    p = Paginator(data,count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                            'total_count':card.count(),'data': p.page(page).object_list})

            else:
                folder = Card.objects.get(id=info.get('key'))
                def search_file(pid):
                    da = []
                    other = Card.objects.filter(c_type=0,pid=pid)
                    for o in other:
                        card = Card.objects.filter(file_name__contains=file_name,c_type=1,pid=o.id,create_user=up)
                        for c in card:
                            da.append(c.id)
                    if other:
                        for os in other:
                            search_file(os.id)
                    else:
                        card = Card.objects.filter(file_name__contains=file_name,c_type=1,pid=pid,create_user=up)
                        for c in card:
                            da.append(c.id)
                    return da

                s = search_file(folder.id)
                for ss in s:
                    card = Card.objects.filter(id=ss)
                    for cards in card:
                        data.append({
                            'title':cards.file_name,
                            'key':cards.id,
                            'type':cards.c_type,
                            'pid':cards.pid,
                            'index':cards.index,
                            'is_assistant':0,
                        })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                    'total_count':len(data),'data': p.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '无信息!!!',})


class Discuss_Card_Search(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        info = json.loads(request.body)
        file_name = info.get('file_name')
        page = info.get('page')
        count = info.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            package = Master_Package.objects.get(id=info.get('key'))
            card = Card.objects.filter(tags=3,file_name__contains=file_name,c_type=1,package_id=package.id)
            data = []
            for cards in card:
               data.append({
                    'key':cards.id,
                    'title':cards.file_name,
                    'content':'',
                    'status':cards.status,
                    'user':cards.create_user.username,
                    'head_img':cards.create_user.head_img,
                    'count':Card_Comment.objects.filter(card=cards).count(),
                    'create_time':str(cards.create_time)[19:],
                    'update_time':str(cards.update_time)[19:],
             })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                    'total_count':card.count(),'data': p.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '无信息!!!',})


class Card_Sort(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        info = json.loads(request.body)
        key = info.get('key_list')
        try:
            up = UserProfile.objects.get(username=request.user)
            for keys in key:
                card = Card.objects.get(id=keys.get('key'))
                card.index = keys.get('index')
                card.save()
            return file_path(self,up)
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '卡片不存在！！！',})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '用户不存在！！！',})


class My_Assistant(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        try:
            user = UserProfile.objects.get(username=request.user)
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '用户不存在'})
        data = []
        package = Branch_Package.objects.filter(~Q(p_type=2),create_user=user)
        for packages in package:
            data.append({
                'file': packages.package_name,
                'type': 0,
                'id': packages.id,
                'pid':0,
                'index':-1,
                'is_assistant':1,
            })
            card = Card.objects.filter(~Q(tags=4),package_id=packages.id)
            for cards in card:
                da={
                    'file':cards.file_name,
                    'id':cards.id,
                    'is_assistant':1,
                    'type':cards.c_type,
                    'pid':cards.pid,
                    'index':cards.index,
                 }
                data.append(da)

        def getChildren(id=0):
            sz=[]
            for obj in data:
                if  obj['pid'] ==id:
                    sz.append({
                        'key': obj["id"],
                        'pid': obj['pid'],
                        'title': obj['file'],
                        'is_assistant': obj['is_assistant'],
                        'type': obj['type'],
                        'index':obj['index'],
                        'children':getChildren(obj['id'])
                    })
            return sz
        return self.write_json({'errno':0, 'msg': 'success','data':getChildren()})


class Upload_File(BaseHandler):
    @logger_decorator
    @transaction.atomic
    def post(self, request):
        key = request.POST.get('key')
        userid = request.POST.get('userid')
        token = request.POST.get('token')
        file_field = request.FILES.getlist('file')
        try:
            up = UserProfile.objects.get(id=userid,token=token)
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':'1','msg':'用户不存在'})
        if 'file' not in request.FILES:
            return self.write_json({'errno':'1','msg':'文件为空'})
        for f in file_field:
            md_file = os.path.join('upload',str(f))
            with open(md_file, 'w+') as ff:
               for chunk in f.chunks():
                    ff.write(chunk.decode('utf-8'))
               ff.close()
            fs = open(md_file,'r')
            lines = fs.read()
            content = ''
            for line in lines:
                content += line
            verify = verify_content(self,content)
            print(verify)
            if 0 == verify.get('errno'):
                package = get_package(self,key)
                if package:
                    branch = package.branch
                    pid = package.id
                    package_id = package.id
                    package_location = package.package_location
                    path = os.path.join(package.package_location,f.name)
                else:
                    folder = Card.objects.get(id=key)
                    branch = package.branch
                    pid = folder.id
                    package_id = folder.package.id
                    package_location = folder.package_location
                    path = os.path.join(folder.card_location,f.name)
                card = Card.objects.filter(file_name=f.name,pid=pid)
                if not card:
                    card = Card()
                    card.package_id = package_id
                    card.package_location = package_location
                    card.branch = branch
                    card.file_name = f.name
                    card.content = content
                    card.create_user = up
                    card.c_type = 1
                    card.pid = pid
                    result = git_utils.create_file(card.package_location,card.branch,content)
                    card.card_location = path
                    video = re.search('video',content)
                    if video:
                       card.tags = 1
                       card.save()
                    if 'SQ' in content or 'MQ' in content:
                       card.tags = 2
                       card.save()
                    if '0' == result.get('errno'):
                        card.save()
                        return get_file_dir(self,request.POST.get('role'))
                    else :
                        return self.write_json({'errno': 1,'msg':'上传文件失败!'})
                else:
                    return self.write_json({'errno': 1,'msg':'文件已存在！！！!'})
            else :
                return self.write_json({'errno': 1,'msg':'文件格式错误！！！!'})
        return self.write_json({'errno': 0,'msg':'success'})


class Create_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self, request):
        card_info = json.loads(request.body)
        types = card_info.get('types')
        role = card_info.get('role')
        logger.info("create file: %s %s %s" % (role, types, card_info))
        try:
            up = UserProfile.objects.get(username=request.user)
            if str(settings.GIT_TYPE_DIR) == types:
                key = card_info.get('key')
                folder_name = card_info.get('file_name')
                card_info = Card.objects.filter(id=key,c_type=1)
                if card_info:
                    return self.write_json({'errno':1,'msg':'文件下无法再创建文件夹'})
                package = get_package(self,key)
                if package:
                    folder = Card.objects.filter(pid=package.id,package_id=package.id,file_name=folder_name)
                    if folder :
                        return self.write_json({'errno':1,'msg':'文件夹已存在'})

                    folder_location = package.package_location
                    package_id = package.id
                    folder_id = package.id
                    folder_branch = package.branch
                    path = os.path.join(package.package_location,folder_name)

                else:
                    folder = Card.objects.get(id=key)
                    f = Card.objects.filter(pid=folder.id,file_name=folder_name)
                    if f :
                        return self.write_json({'errno':1,'msg':'文件夹已存在'})

                    folder_location = folder.package_location
                    package_id = folder.package_id
                    folder_branch = folder.branch
                    folder_id = folder.id
                    path = os.path.join(folder.card_location,folder_name)

                logger.debug("PARAM: %s %s %s %s %s" % (str(folder_location), str(package_id), str(folder_branch), str(folder_id), str(path)))
                card = Card()
                card.package_id = package_id
                card.branch = folder_branch
                card.package_location = folder_location
                card.c_type = settings.GIT_TYPE_DIR
                card.file_name = folder_name
                card.create_user = up
                card.pid = folder_id
                card.card_location = path
                #FIXME:DOUBLECHECK
                result = git_utils.create_dir(folder_location,folder_branch,path)
                card.save()

                return get_file_dir(self,role)
                #else :
                #   return self.write_json({'errno': 1,'msg':'新建文件失败！！!'})

            #FIXME
            elif str(settings.GIT_TYPE_FILE) == types:
                key = card_info.get('key')
                folder_name = card_info.get('file_name')
                tags = card_info.get('tags')
                content = card_info.get('content')
                package = get_package(self,key)
              #  logger.info("create_file: %s %s %s %s %s" % (key, folder_name, tags, content, package))
                if  package:
                    if '0' == tags:
                        card = Card.objects.filter(pid=package.id,file_name=folder_name +'.md')
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                        file_name = folder_name +'.md'
                    elif '1' == tags:
                        card = Card.objects.filter(pid=package.id,file_name=folder_name +'.video')
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                        file_name = folder_name +'.video'
                    elif '2' == tags:
                        card = Card.objects.filter(pid=package.id,file_name=folder_name +'.exam')
                        file_name = folder_name +'.exam'
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                    package_id = package.id
                    branch = package.branch
                    package_location = package.package_location
                    pid = package.id
                    path = os.path.join(package.package_location,file_name)
                else:
                    folder = Card.objects.get(id=key)
                    if '0' == tags:
                        card = Card.objects.filter(pid=folder.id,file_name=folder_name +'.md')
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                        file_name = folder_name +'.md'
                    elif '1' == tags:
                        card = Card.objects.filter(pid=folder.id,file_name=folder_name +'.video')
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                        file_name = folder_name +'.video'
                    elif '2' == tags:
                        card = Card.objects.filter(pid=folder.id,file_name=folder_name +'.exam')
                        file_name = folder_name +'.exam'
                        if card:
                            return self.write_json({'errno': 1, 'msg': '文件已存在'})
                        card_info = Card.objects.filter(id=key,c_type=1)
                        if card_info:
                            return self.write_json({'errno':1,'msg':'文件下无法再创建'})
                    package_id = folder.package_id
                    branch = folder.branch
                    package_location = folder.package_location
                    pid = folder.id
                    path = os.path.join(folder.card_location,file_name)

                cards = Card()
                cards.package_id = package_id
                cards.branch = branch
                cards.package_location =package_location
                cards.tags = tags
                cards.create_user = up
                cards.c_type = 1
                cards.pid = pid
                cards.content = content
                cards.file_name = file_name
                result = git_utils.create_file(package_location,branch,path,content)
                cards.card_location = path
                cards.save()
                return get_file_dir(self,role,up)
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡片不存在！！！'})


class Create_Discuss_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        key = msg.get('key')
        try:
            package = Master_Package.objects.get(id=key)
            up = UserProfile.objects.get(username=request.user)
            c = Card.objects.filter(package_id=package.id,file_name=(msg.get('title')))
            if c:
                return self.write_json({'errno':1,'msg':'讨论已存在！！！'})
            card = Card()
            path = os.path.join(package.package_location,(msg.get('title')))
            card.package_id = package.id
            card.branch = package.branch
            card.package_location = package.package_location
            card.create_user = up
            card.file_name = msg.get('title')
            card.content = msg.get('content')
            card.c_type = 1
            card.pid = package.id
            card.tags = 3
            card.card_location = path
            result = git_utils.create_file(card.package_location,'master',path,msg.get('content'))
            card.save()
            dis_package = Master_Package.objects.get(course=package.course,p_type=2)
            other = Card.objects.filter(package_id=dis_package.id)
            other_disc = []
            for others in other:
                result = git_utils.get_file_content(others.package_location,'master',others.card_location)
                content = result['data'].get('content')
                other_disc.append({
                    'key':others.id,
                    'title':others.file_name,
                    'content':content,
                    'status':others.status,
                    'user':others.create_user.username,
                    'head_img':others.create_user.head_img,
                    'create_time':str(others.create_time)[:19],
                    'update_time':str(card.update_time)[:19],
                })
            comment = []
            detail = {
                'key':str(card.id),
                'title':card.file_name,
                'content':card.content,
                'is_my':1,
                'user':card.create_user.username,
                'status':card.status,
                'head_img':card.create_user.head_img,
                'create_time':str(card.create_time)[:19],
                'comment':comment,
            }
            message = {'all_disc':other_disc,'disc_detail':detail}
            return self.write_json({'errno':0,'msg':'success','data':message})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！!'})


class Delete_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        up = UserProfile.objects.get(username=request.user)
        keys = msg.get('key_list')

        logger.info("Delete_File: %s %s" % (request.user, keys))
        role = msg.get('role')

        ### BAT DELETE
        #r = delete_files(self, keys, up, role)
        ### OLD METHOD
        for key in keys:
            r = delete_file(self,key,up,role)
        return r

#FIXME
class Modify_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        content = msg.get('content')
        role = msg.get('role')
        try:
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=msg.get('key'))
            result = git_utils.modiyf_file('0',card.package_location,card,branch,card.card_location,content)
            card.content = content
            card.create_user = up
            card.modify_count += 1
            card.save()
            return get_file_dir(self,role,up)
        except UserProfile.DoesNotExist:
             return self.write_json({'errno':1,'msg':'用户不存在！！!'})
        except Card.DoesNotExist:
             return self.write_json({'errno':1,'msg':'不存在卡片！！!'})


class Modify_Discuss_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        content = msg.get('content')
        new_name = msg.get('new_name')
        logger.info("modify file: %s %s %s" % (msg, content, new_name))
        try:
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=msg.get('key'))
            master_package = Master_Package.objects.get(id=card.package_id)
            result = git_utils.modify_discuss_file(card.package_location,card.branch,card.card_location,new_name,content)
            card.content = content,
            card.file_name = new_name
            card.card_location = result.get('data')['repo']
            card.save()
            dis_package = Master_Package.objects.get(course=master_package.course,p_type=2)
            other = Card.objects.filter(package_id=dis_package.id)
            other_disc = []
            for others in other:
                result = git_utils.get_file_content(others.package_location,others.branch,others.card_location)
                content = result['data'].get('content')
                other_disc.append({
                    'key':others.id,
                    'title':others.file_name,
                    'content':content,
                    'status':others.status,
                    'user':others.create_user.username,
                    'head_img':others.create_user.head_img,
                    'create_time':str(others.create_time)[19:]
                })
            comment = []
            card_comment = Card_Comment.objects.filter(card=card)
            for coms in card_comment:
                comment.append({
                    'is_my':1,
                    'user':coms.user.username,
                    'head_img':coms.user.head_img,
                    'content':coms.content,
                    'create_time':str(coms.create_time)[19:]
            })
            detail = {
                'key':str(card.id),
                'title':card.file_name,
                'content':msg.get('content'),
                'is_my':1,
                'user':card.create_user.username,
                'status':card.status,
                'head_img':card.create_user.head_img,
                'create_time':str(card.create_time)[19:],
                'comment':comment,
            }
            message = {'all_disc':other_disc,'disc_detail':detail}
            return self.write_json({'errno':0,'msg':'success','data':message})
        except UserProfile.DoesNotExist:
             return self.write_json({'errno':1,'msg':'用户不存在！！!'})
        except Master_Package.DoesNotExist:
             return self.write_json({'errno':1,'msg':'卡包不存在！！!'})
        except Card.DoesNotExist:
             return self.write_json({'errno':1,'msg':'不存在卡片！！!'})


class Homework_Page(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            path = file_paths(self,msg.get('key'),up)
            return path
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在用户！！!'})


class Discuss_Page(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            p = Master_Package.objects.get(id=msg.get('key'))
            data = []
            if '0'== msg.get('type'):
                if '0' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0).order_by('-create_time')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0).order_by('-create_time')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0,create_user=up)
                elif '1' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1).order_by('-create_time')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1).order_by('-create_time')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1,create_user=up)
            elif '1' == msg.get('type'):
                if '0' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0).order_by('-reply_time')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0).order_by('-reply_time')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0,create_user=up)
                elif '1' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1).order_by('-reply_time')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1).order_by('-reply_time')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1,create_user=up)
            elif '2'== msg.get('type'):
                if '0' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0).order_by('-count')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0).order_by('-count')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=0,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=0,create_user=up)
                elif '1' == msg.get('status'):
                    if '0' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1).order_by('-count')
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1).order_by('-count')
                    elif '1' == msg.get('is_my'):
                        if msg.get('title'):
                            card = Card.objects.filter(file_name__contains=msg.get('title'),package_id=p.id,c_type=1,status=1,create_user=up)
                        else:
                            card = Card.objects.filter(package_id=p.id,c_type=1,status=1,create_user=up)
            is_my = 0
            for cards in card:
                if cards.create_user == up:
                    is_my = 1
                else:
                     is_my = 0
                datas = {
                    'branch':'master',
                    'repo':cards.package_location,
                    'file_path':cards.card_location
                    }
                url = settings.GIT_FILE_CONTENT
                r = requests.post(url,data=datas)
                result = r.json()
                content = result['data'].get('content')
                data.append({
                    'title':cards.file_name,
                    'key':cards.id,
                    'is_my':is_my,
                    'type':cards.c_type,
                    'pid':cards.pid,
                    'content':content,
                    'status':cards.status,
                    'user':cards.create_user.username,
                    'head_img':cards.create_user.head_img,
                    'count':Card_Comment.objects.filter(card=cards).count(),
                    'reply_time':str(cards.reply_time)[:19],
                    'create_time':str(cards.create_time)[:19],
                    'update_time':str(cards.update_time)[:19],
               })
            if msg.get('title'):
               comment = Card_Comment.objects.filter(card__file_name__contains=msg.get('title'),user=up,package_id=p.id)
            else:
               comment = Card_Comment.objects.filter(user=up,package_id=p.id)
            if comment:
                for com in comment:
                    result = git_utils.get_file_content(com.card.package_location,com.card.branch,com.card.card_location)
                    contents = result['data'].get('content')
                    if str(com.card.status) == msg.get('status'):
                        data.append({
                            'title':com.card.file_name,
                            'key':com.card.id,
                            'type':com.card.c_type,
                            'pid':com.card.pid,
                            'content':contents,
                            'status':com.card.status,
                            'head_img':com.card.create_user.head_img,
                            'user':com.card.create_user.username,
                            'count':Card_Comment.objects.filter(card=com.card).count(),
                            'reply_time':str(com.card.reply_time)[:19],
                            'create_time':str(com.card.create_time)[:19],
                            'update_time':str(com.card.update_time)[:19],
                        })
                    l4=[]
                    if len(data) > 0:
                        l4.append(data[0])
                        for dict in data:
                            k=0
                            for item in l4:
                                if dict['key'] != item['key']:
                                    k=k+1
                                else:
                                    break
                                if k == len(l4):
                                    l4.append(dict)
                if '0' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['create_time']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

                if '1' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['reply_time']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

                if '2' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['count']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

            else:
                l4=[]
                if len(data) > 0:
                    l4.append(data[0])
                    for dict in data:
                        k=0
                        for item in l4:
                            if dict['key'] != item['key']:
                                k=k+1
                            else:
                                break
                            if k == len(l4):
                                l4.append(dict)
                if '0' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['create_time']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

                if '1' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['reply_time']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

                if '2' == msg.get('type') and '1' == msg.get('is_my'):
                    pag = Paginator(sorted(l4,key=lambda x:(x['count']),reverse=True),count)
                    return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})

            l4=[]
            if len(data) > 0:
                l4.append(data[0])
                for dict in data:
                    k=0
                    for item in l4:
                        if dict['key'] != item['key']:
                            k=k+1
                        else:
                            break
                        if k == len(l4):
                            l4.append(dict)

            pag = Paginator(l4,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':len(l4),
                                    'total_page':pag.num_pages,'data': pag.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡片！！!'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡包！！!'})



class All_Close_Discuss(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            p = Master_Package.objects.get(id=msg.get('package_key'))
            card = Card.objects.filter(package_id=p.id,c_type=1,status=1)
            data = []
            for cards in card:
                result = git_utils.get_file_content(cards.package_location,cards.branch,cards.card_location)
                content = result['data'].get('content')
                data.append({
                    'title':cards.file_name,
                    'key':cards.id,
                    'type':cards.c_type,
                    'pid':cards.pid,
                    'content':content,
                    'status':cards.status,
                    'head_img':cards.create_user.head_img,
                    'count':Card_Comment.objects.filter(card=cards).count(),
                    'create_time':str(cards.create_time)[:19],
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':card.count(),
                                    'total_page':p.num_pages,'data': p.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡片！！!'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡包！！!'})



class Comment_Page(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            c = Card.objects.get(id=msg.get('key'))
            card = Card_Comment.objects.filter(card=c)
            data = []
            is_my_comment = 0
            for cs in card:
                if cs.user == up:
                    is_my_comment = 1
                else:
                    is_my_comment = 0
                data.append({
                    'id':cs.id,
                    'is_my_comment':is_my_comment,
                    'user':cs.user.username,
                    'head_img':cs.user.head_img,
                    'content':cs.content,
                    'create_time':str(cs.create_time)[19:]
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':Card_Comment.objects.filter(card=c).count(),
                                'total_page':p.num_pages,'data': p.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡片！！!'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在用户！！!'})


class Batch_Modify_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        content_list = msg.get('content_list')
        up = UserProfile.objects.get(username=request.user)
        role = msg.get('role')
        try:
            if msg.get('messageid'):
                mess = System_Message.objects.get(id=msg.get('messageid'))
                mess.is_solve = 2
                mess.save()
                for content in content_list:
                    card = Card.objects.get(id=content.get('key'))
                    result = git_utils.modify_file('1',card.package_location,card.branch,card.card_location,content.get('content'))
                    card.content = content.get('content')
                    card.create_user = up
                    card.modify_count +=1
                    card.save()
                else:
                    branch = Branch_Package.objects.get(id=mess.key)
                    result = git_utils.commit_file('1',branch.package_location,'master',branch.branch)

            if '1' == msg.get('is_conflict'):
                for content in content_list:
                    card = Card.objects.get(id=content.get('key'))
                    result = git_utils.modify_file('1',card.package_location,card.branch,card.card_location,content.get('content'))
                    card.content = content.get('content')
                    card.create_user = up
                    card.modify_count +=1
                    card.save()
                else:
                    result = git_utils.commit_file('2',card.package_location,'master',card.branch)
            else:
                for content in content_list:
                    card = Card.objects.get(id=content.get('key'))
                    result = git_utils.modify_file('0',card.package_location,card.branch,card.card_location,content.get('content'))
                    card.content = content.get('content')
                    card.create_user = up
                    card.modify_count +=1
                    card.save()
            return get_file_dir(self,up)
        except Card.DoesNotExist:
             return self.write_json({'errno':1,'msg':'不存在卡片！！!'})


class Copy_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        copy_key = msg.get('key_list')
        copy_to_key = msg.get('to_key')
        _type = msg.get('_type')
        role = msg.get('role')
        if '0' == _type:
            try:
                up = UserProfile.objects.get(username=request.user)
                package_dir = get_package(self,copy_to_key)
                if package_dir: #FIXME
                    for keys in copy_key:
                        card = Card.objects.get(id=keys)
                        _card = Card.objects.filter(pid=package_dir.id,file_name=card.file_name)
                        if _card:
                           return self.write_json({'errno':'1','msg':'文件已存在'})
                        cp_card = Card()
                        cp_card.package_id = package_dir.id
                        cp_card.branch = package_dir.branch
                        cp_card.package_location = package_dir.package_location
                        cp_card.file_name = card.file_name
                        cp_card.c_type = 1
                        cp_card.tags = card.tags
                        cp_card.content = card.content
                        cp_card.create_user = up
                        cp_card.pid = package_dir.id
                        result = git_utils.copy_file('0',package_dir.package_location,package_dir.package_location
                                                        ,cp_card.branch,card.card_location)
                        cp_card.card_location = os.path.join(package_dir.package_location,card.file_name)
                        cp_card.save()
                    return get_file_dir(self,role,up)
                else:
                    for keys in copy_key:
                        try:
                            card_dir = Card.objects.get(id=copy_to_key)
                            c = Card.objects.get(id=keys)
                        except Card.DoesNotExist:
                            return self.write_json({'errno':1,'msg':'卡片不存在！！！'})
                        _card = Card.objects.filter(pid=card_dir.id,file_name=c.file_name)
                        if _card:
                            return self.write_json({'errno':'1','msg':'文件已存在！！！'})
                        cp_card = Card()
                        cp_card.package_id = card_dir.package_id
                        cp_card.branch = card_dir.branch
                        cp_card.package_location = card_dir.package_location
                        cp_card.file_name = card.file_name
                        cp_card.c_type = 1
                        cp_card.tags = card.tags
                        cp_card.content = card.content
                        cp_card.create_user = up
                        cp_card.pid = card_dir.id
                        result = git_utils.copy_file('0',card_dir.package_location,card_dir.card_location,cp_card.branch,
                                                       card.card_location)
                        cp_card.card_location = os.path.join(card_dir.card_location,c.file_name)
                        cp_card.save()

                return get_file_dir(self,role,up)
            except Card.DoesNotExist:
                return self.write_json({'errno':1,'msg':'卡片不存在！！！'})
        elif '1' == _type:
            try:
                up = UserProfile.objects.get(username=request.user)
                package_dir = get_package(self,copy_to_key)
                if package_dir:
                    for keys in copy_key:
                        card = Card.objects.get(id=keys)
                        _card = Card.objects.filter(pid=package_dir.id,file_name=card.file_name)
                        if _card:
                           return self.write_json({'errno':'1','msg':'文件已存在！！！'})
                        cp_card = Card()
                        cp_card.package_id = package_dir.id
                        cp_card.branch = package_dir.branch
                        cp_card.package_location = package_dir.package_location
                        cp_card.file_name = card.file_name
                        cp_card.c_type = 1
                        cp_card.tags = card.tags
                        cp_card.content = card.content
                        cp_card.create_user = up
                        cp_card.pid = package_dir.id
                        result = git_utils.copy_file('1',package_dir.package_location,package_dir.package_location
                                                        ,cp_card.branch,card.card_location)
                        cp_card.card_location = os.path.join(package_dir.package_location,card.file_name)
                        cp_card.save()
                        card.delete()
                    return get_file_dir(self,role,up)

                else:
                    for keys in copy_key:
                        try:
                            card_dir = Card.objects.get(id=copy_to_key)
                            c = Card.objects.get(id=keys)
                        except Card.DoesNotExist:
                            return self.write_json({'errno':'1','msg':'文件不存在！！！'})
                        _card = Card.objects.filter(pid=card_dir.id,file_name=c.file_name)
                        if _card:
                            return self.write_json({'errno':'1','msg':'文件已存在！！！'})
                        cp_card = Card()
                        cp_card.package_id = card_dir.package_id
                        cp_card.branch = card_dir.branch
                        cp_card.package_location = card_dir.package_location
                        cp_card.file_name = card.file_name
                        cp_card.c_type = 1
                        cp_card.tags = card.tags
                        cp_card.content = card.content
                        cp_card.create_user = up
                        cp_card.pid = card_dir.id
                        result = git_utils.copy_file('0',card_dir.package_location,card_dir.card_location,cp_card.branch,
                                                       card.card_location)
                        cp_card.card_location = os.path.join(card_dir.card_location,c.file_name)
                        cp_card.save()
                        c.delete()
                return get_file_dir(self,role,up)
            except Card.DoesNotExist:
                return self.write_json({'errno':1,'msg':'卡片不存在！！！'})


class Rename_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        file_name = msg.get('file_name')
        role = msg.get('role')
        try:
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=msg.get('key'))
            c = Card.objects.filter(~Q(file_name=card.file_name),package_id=card.package_id,file_name=file_name)
            if c:
                return self.write_json({'errno':1,'msg':'文件已存在！！！'})
            if 0 == card.c_type:
                new_name = file_name
                result = git_utils.rename_file('0',card.package_location,card.branch,card.card_location,'',card.file_name,new_name)
                card.file_name = new_name
                card.card_location = result.get('data')['repo']
                new_dir = Card.objects.filter(pid=card.id)
                for dirs in new_dir:
                    dir_path = os.path.join(card.card_location,dirs.file_name)
                    dirs.card_location = dir_path
                    dirs.create_user = up
                    dirs.save()
                card.save()
                return get_file_path(self,role,up)
            elif 1 == card.c_type:
                folder_dir = Card.objects.get(id=card.pid)
                if  0 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.md')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})
                    new_name = file_name +'.md'
                elif 1 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.video')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})
                    new_name = file_name +'.video'
                elif 2 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.exam')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})
                    new_name = file_name +'.exam'
                result = git_utils.rename_file('1',card.package_location,card.branch,card.card_location,
                                                folder_dir.card_location,card.file_name,new_name)
                card.file_name = new_name
                card.card_location = result.get('data')['repo']
                card.save()
                return get_file_path(self,role,up)
            return self.write_json({'errno':0,'msg':'修改成功'})
        except Card.DoesNotExist:
            folder_dir = get_package(self,card.pid)
            if folder_dir:
                if  0 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.md')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})
                    new_name = file_name +'.md'
                elif 1 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.video')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})

                    new_name = file_name +'.video'
                elif 2 == card.tags:
                    c = Card.objects.filter(~Q(file_name=card.file_name),pid=folder_dir.id,file_name=file_name +'.exam')
                    if c:
                        return self.write_json({'errno':1,'msg':'文件已存在！！！'})
                    new_name = file_name +'.exam'

            result = git_utils.rename_file('1',card.package_location,card.branch,card.card_location,
                                            folder_dir.package_location,card.file_name,new_name)
            card.file_name = new_name
            card.card_location = result['data'].get('repo')
            card.save()
            return get_file_path(self,role,up)


class Rename_Package(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            package = Master_Package.objects.get(id=msg.get('key'))

            """
            #FIXME
            data = {
              'branch':package.branch,
              'dirname':up.username + package.package_name,
              'path':package.package_location,
              'new_dirname':up.username + msg.get('package_name')
             }
            url = settings.GIT_RENAME_REPO
            r = requests.post(url,data=data)
            result = r.json()
            """

            #if '0' == result.get('errno'):
            package.package_name = msg.get('package_name')
            #package.package_location = result['data'].get('repo')
            package.save()
            #FIXME: DOUBLECHECK
            """
                _dir = Card.objects.filter(pid=package.id)
                for dirs in _dir:
                    if 0 == dirs.c_type:
                        dir_path = os.path.join(package.package_location,dirs.file_name)
                        dirs.card_location = dir_path
                        dirs.package_location = package.package_location
                        dirs.save()
                        card_dir = Card.objects.filter(pid=dirs.id)
                        for cards in card_dir:
                            card_path = os.path.join(dirs.card_location,cards.file_name)
                            cards.card_location = card_path
                            cards.package_location = package.package_location
                            cards.save()
                    elif 1 == dirs.c_type:
                        dir_path = os.path.join(package.package_location,dirs.file_name)
                        dirs.card_location = dir_path
                        dirs.package_location = package.package_location
                        dirs.save()
            """
            return file_path(self,up)
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在'})


class Get_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        file_info = json.loads(request.body)
        file_key= file_info.get('card_list')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            for key in file_key:
                card = Card.objects.get(id=key,c_type=1)
                logger.info("get file: %s %s " % (up, card.branch))
                result = git_utils.get_file_content(card.package_location,card.branch,card.card_location)
                content = result['data'].get('content')
                if 0 == card.tags:
                    rule = r'title:([\s\S]*)\nsign'
                    rule1 = r'# front([\s\S]*?)# back'
                    rule2 = r'# back([\s\S]*)'
                    title = re.search(rule, content).group(1)
                    back = re.search(rule2, content).group(1)
                    front = {
                    'content': re.search(rule1, content).group(1),
                    }
                    data.append({'key':key,'type':0,'title':title,'front':front,'back':back})
                    card.content = content
                    card.save()
                elif 1 == card.tags:
                    rule = r'title:([\s\S]*)\nsign'
                    rule2 =r'url:([\s\S]*)```'
                    rule3 =r'# back([\s\S]*)'
                    front = {
                      'url' : re.search(rule2,content).group(1),
                     }
                    data.append({'key':key,'type':1,'title': re.search(rule,content).group(1),
                                 'front':front,'back': re.search(rule3,content).group(1)})
                    card.content = content
                    card.save()
                elif 2 == card.tags:
                    if 'SQ' in content and 'MQ' not in content:
                        rule = r'title:([\s\S]*)\nsign'
                        rule1 = r'# front([\s\S]*)# back'
                        rule2 = r'```SQ([\s\S]*?)```'
                        rule4 = r'Q:(.*)'
                        rule5 = r'ASW(.*)'
                        rule6 = r'ASWT:(.*)'
                        rule7 = r'# back([\s\S]*)'
                        title = re.search(rule,content).group(1)
                        back = re.search(rule7,content).group(1)
                        cont = re.findall(rule1,content)
                        result1 = re.findall(rule2,cont[0])
                        def fs(arr):
                                    s = []
                                    for e in arr:
                                        s.append(e[2:])
                                    return s

                        result3 = list(map(lambda array:{'is_single':'true','sq':re.findall(rule4,array),
                                                    'asw':fs(re.findall(rule5,array)),'aswt':re.findall(rule6,array)},result1))
                        front = {'exam': result3}
                        data.append({'key':key,'type':2,'title':title,'front':front,'back':back})
                        card.content = content
                        card.save()
                    elif 'MQ' in content and 'SQ' not in content:
                        rule = r'title:([\s\S]*)\nsign'
                        rule1 = r'# front([\s\S]*)# back'
                        rule3 = r'```MQ([\s\S]*?)```'
                        rule4 = r'Q:(.*)'
                        rule5 = r'ASW(.*)'
                        rule6 = r'ASWT:(.*)'
                        rule7 = r'# back([\s\S]*)'
                        title = re.search(rule,content).group(1)
                        back = re.search(rule7,content).group(1)
                        cont = re.findall(rule1,content)
                        result2 = re.findall(rule3,cont[0])
                        def fs(arr):
                                    s = []
                                    for e in arr:
                                        s.append(e[2:])
                                    return s

                        result4 = list(map(lambda array:{'is_single':'false','mq':re.findall(rule4,array),
                                                    'asw':fs(re.findall(rule5,array)),'aswt':re.findall(rule6,array)},result2))

                        front = {'exam':result4}
                        data.append({'key':key,'type':2,'title':title,'front':front,'back':back})
                        card.content = content
                        card.save()
                    else:
                        rule = r'title:([\s\S]*)\nsign'
                        rule1 = r'# front([\s\S]*)# back'
                        rule2 = r'```SQ([\s\S]*?)```'
                        rule3 = r'```MQ([\s\S]*?)```'
                        rule4 = r'Q:(.*)'
                        rule5 = r'ASW(.*)'
                        rule6 = r'ASWT:(.*)'
                        rule7 = r'# back([\s\S]*)'
                        title = re.search(rule,content).group(1)
                        back = re.search(rule7,content).group(1)
                        cont = re.findall(rule1,content)
                        result1 = re.findall(rule2,cont[0])
                        result2 = re.findall(rule3,cont[0])
                        def fs(arr):
                                    s = []
                                    for e in arr:
                                        s.append(e[2:])
                                    return s

                        result3 = list(map(lambda array:{'is_single':'true','sq':re.findall(rule4,array),
                                                    'asw':fs(re.findall(rule5,array)),'aswt':re.findall(rule6,array)},result1))
                        result4 = list(map(lambda array:{'is_single':'false','mq':re.findall(rule4,array),
                                                    'asw':fs(re.findall(rule5,array)),'aswt':re.findall(rule6,array)},result2))

                        front = {'exam': result3 + result4}
                        data.append({'key':key,'type':2,'title':title,'front':front,'back':back})
                        card.content = content
                        card.save()
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})


class Discuss_File_Detail(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        page = msg.get('page')
        count = msg.get('count')
        try:
            up = UserProfile.objects.get(username=request.user)
            comment = []
            card = Card.objects.get(id=key)
            result = git_utils.get_file_content(card.package_location,'master',card.card_location)
            cont = result['data'].get('content')
            msg_card = Card_Comment.objects.filter(card=card)
            is_my = 0
            is_my_comment = 0
            for mc in msg_card:
                result = git_utils.get_file_content(mc.card.package_location,'master',mc.card.card_location)
                content = result['data'].get('content')
                if up == mc.user:
                    is_my_comment = 1
                else :
                    is_my_comment = 0
                comment.append({
                'id':mc.id,
                'is_my_comment':is_my_comment,
                'user':mc.user.username,
                'head_img':mc.user.head_img,
                'content':mc.content,
                'create_time':str(mc.create_time)[:19]
                })
            p = Paginator(comment,count)
            if up == card.create_user:
                is_my = 1
            data = {
            'key':card.id,
            'title':card.file_name,
            'status':card.status,
            'is_my':is_my,
            'user':card.create_user.username,
            'head_img':card.create_user.head_img,
            'content':cont,
            'total_count':msg_card.count(),
            'total_page':p.num_pages,
            'create_time':str(card.create_time)[:19],
            'comment':p.page(page).object_list
            }
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在卡片!!!'})
        except Card_Comment.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在评论信息!!!'})


class Colse_Discuss(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        try:
            card = Card.objects.get(id=key)
            card.status = 1
            card.save()
            dis_package = Master_Package.objects.get(id=card.package_id,p_type=2)
            other = Card.objects.filter(package_id=dis_package.id)
            other_disc = []
            for others in other:
                result = git_utils.get_file_content(others.package_location,'master',others.card_location)
                content = result['data'].get('content')
                other_disc.append({
                'key':others.id,
                'title':others.file_name,
                'content':content,
                'status':others.status,
                'user':others.create_user.username,
                'head_img':others.create_user.head_img,
                'create_time':str(others.create_time)[19:]
                })
            data = {'all_disc':other_disc}
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡包！！！'})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡片！！！'})



class Delete_Card_Comment(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            c = Card.objects.get(id=msg.get('key'))
            card = Card_Comment.objects.get(id=msg.get('id'))
            card.delete()
            c.count - 1
            c.save()
            is_my_comment = 0
            msg_card = Card_Comment.objects.filter(card=c)
            for mc in msg_card:
                if mc.user == up:
                    is_my_comment = 1
                else:
                    is_my_comment = 0
                data.append({
                    'is_my_comment':is_my_comment,
                    'id':mc.id,
                    'user':mc.user.username,
                    'head_img':mc.user.head_img,
                    'content':mc.content,
                    'create_time':str(mc.create_time)[19:]
               })
            pages = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':msg_card.count(),
                                     'total_page':pages.num_pages, 'data':pages.page(page).object_list})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡片！！！'})
        except Card_Comment.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在评论！！！'})


class Card_Comments(BaseHandler):
    @logger_decorator
    @transaction.atomic
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key = msg.get('key')
        page = msg.get('page')
        count = msg.get('count')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=key)
            master_package = Master_Package.objects.get(id=card.package_id)
            card_comment = Card_Comment()
            card_comment.card = card
            card_comment.content = msg.get('content')
            card_comment.user = up
            card_comment.package = master_package
            card_comment.to_user = up
            card_comment.save()
            card.count += 1
            card.reply_time = card_comment.create_time
            card.save()
            if 1 == master_package.p_type:
                hw_card = User_Hw_Record.objects.get(package=master_package,aw_card=card)
                if up != card.create_user:
                    mess = System_Message()
                    mess.user = up
                    mess.to_user = card.create_user
                    mess.card_id = hw_card.card.id
                    mess.message =  up.username + '评论了你的作业：' + hw_card.card.file_name
                    mess.type = 2
                    mess.course_id = master_package.course.id
                    mess.card_tags = card.tags
                    mess.content = msg.get('content')
                    mess.save()

            if 2 == master_package.p_type:
                if up != card.create_user:
                    mess = System_Message()
                    mess.user = up
                    mess.to_user = card.create_user
                    mess.message = up.username + '评论了你的讨论：' + card.file_name
                    mess.type = 2
                    mess.card_id = card.id
                    mess.course_id = master_package.course.id
                    mess.card_tags = card.tags
                    mess.content = msg.get('content')
                    mess.save()
            msg_card = Card_Comment.objects.filter(card=card)
            is_my_comment = 0
            for mc in msg_card:
                if mc.user == up:
                    is_my_comment = 1
                else:
                    is_my_comment = 0
                data.append({
                    'id':mc.id,
                    'is_my_comment':is_my_comment,
                    'user':mc.user.username,
                    'head_img':mc.user.head_img,
                    'content':mc.content,
                    'create_time':str(mc.create_time)[:19]
               })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':msg_card.count(),
                                     'total_page':p.num_pages, 'data':p.page(page).object_list})

        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})
        except User_Hw_Record.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在提交记录!!!'})



class Comment_Detail(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        page = msg.get('page')
        count = msg.get('count')
        try:
            data = []
            is_my_comment = 0
            card = Card.objects.get(id=key).card_comment.all()
            up = UserProfile.objects.get(username=request.user)
            for cards in card:
                if cards.user == up:
                    is_my_comment = 1
                else:
                    is_my_comment = 0
                data.append({
                    'id':cards.id,
                    'user':cards.user.username,
                    'head_img':cards.user.head_img,
                    'content':cards.content,
                    'create_time':str(cards.create_time)[:19]
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','data':p.page(page).object_list,
                                    'total_count':card.count(),'total_page':p.num_pages})
        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})


class Card_Collect(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=key)
            c = Card_Action.objects.filter(card=card,user=up)
            course = Course.objects.get(id=msg.get('course_id'))
            if not c:
                card_action = Card_Action()
                card_action.card = card
                card_action.user = up
                card_action.course = course
                card_action.is_favor = 1
                card_action.save()

            return self.write_json({'errno': 0, 'msg': 'success'})
        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})
        except Card_Action.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在收藏信息!!!'})
        except Course.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在课程!!!'})


class Cancel_Collect(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=key)
            card_action = Card_Action.objects.filter(card=card,user=up)
            for c in card_action:
                c.delete()
            return self.write_json({'errno': 0, 'msg': 'success'})
        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})


class My_Collect(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        key= msg.get('key')
        page = msg.get('page')
        count = msg.get('count')
        file_name = msg.get('file_name')
        try:
            data = []
            up = UserProfile.objects.get(username=request.user)
            course = Course.objects.get(id=msg.get('course_id'))
            if '0' == msg.get('type'):
                card = Card_Action.objects.filter(user=up,course=course)
            if '1' == msg.get('type'):
                card = Card_Action.objects.filter(user=up,course=course).order_by('create_time')
            if file_name:
                package = Master_Package.objects.get(id=msg.get('key'))
                coll_card = Card_Action.objects.filter(card__file_name__contains=file_name,user=up,course=course)
                for cards in coll_card:
                    data.append({
                        'key':cards.card.id,
                        'title':cards.card.file_name,
                        'user':cards.user.username,
                        'tags':cards.card.tags,
                        'index':cards.card.index,
                        'card':cards.card.file_name
                        })
                p = Paginator(data,count)
                return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                        'total_count':card.count(),'data': p.page(page).object_list})

            for cards in card:
                data.append({
                    'key':cards.card.id,
                    'title':cards.card.file_name,
                    'user':cards.user.username,
                    'tags':cards.card.tags,
                    'index':cards.card.index,
                    'card':cards.card.file_name
                    })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_page':p.num_pages,
                                    'total_count':card.count(),'data': p.page(page).object_list})
        except UserProfile.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在用户!!!'})
        except Card_Action.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在卡片收藏信息!!!'})
        except Course.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存课程信息!!!'})
        except Master_Package.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在卡包!!!'})



class Get_User_Answer(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        file_id= msg.get('key')
        try:
            other_answer = []
            comment = []
            data = []
            my = {}
            up = UserProfile.objects.get(username=request.user)
            card_content = file_content(self,file_id,up)
            card = Card.objects.get(id=file_id)
            my_answer = User_Hw_Record.objects.filter(card=card,user=up)
            other = User_Hw_Record.objects.filter(~Q(user=up),card=card)
            for others in other:
                result = git_utils.get_file_content(card.package_location,'master',others.aw_card.card_location)
                content = result['data'].get('content')
                other_answer.append({
                    'aw_key':others.aw_card.id,
                    'user':others.user.username,
                    'head_img':others.user.head_img,
                    'answer':content,
                    'create_time':str(others.create_time)[:19]
                    })
            for mys in my_answer:
                result = git_utils.get_file_content(mys.aw_card.package_location,'master',mys.aw_card.card_location)
                content = result['data'].get('content')
                my = {
                    'aw_key':mys.aw_card.id,
                    'answer':content,
                    'head_img':mys.user.head_img,
                    'create_time':str(mys.create_time)[:19]
                    }
                card_comment = Card_Comment.objects.filter(card=mys.aw_card)
                is_my = 0
                for coms in card_comment:
                    if coms.user == up:
                        is_my_comment = 1
                    else:
                        is_my_comment = 0
                    comment.append({
                        'id':coms.id,
                        'is_my_comment':is_my_comment,
                        'user':coms.user.username,
                        'head_img':coms.user.head_img,
                        'content':coms.content,
                        'create_time':str(coms.create_time)[:19]
                    })
            data.append({
                'key':card.id,
                'content':card_content,
                'comment':comment,
                'my_answer':my,
                'other_answer':other_answer,
                })
            return self.write_json({'errno': 0, 'msg': 'success','data':data})
        except Card.DoesNotExist:
             return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})


class My_Study_Record(BaseHandler):
     @auth_decorator
     @logger_decorator
     @transaction.atomic
     def post(self,request):
        user_info = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            card = Card.objects.get(id=user_info.get('key'),c_type=1)
            card.status=1
            card.save()
            master_package = Master_Package.objects.get(id=card.package_id)
            msg = User_Study_Record.objects.filter(user=up,card=card)
            if not msg :
                study_record = User_Study_Record()
                study_record.user = up
                study_record.card = card
                study_record.is_study = 1
                study_record.package = master_package
                study_record.save()
            all_card = Card.objects.filter(~Q(tags=3),~Q(tags=4),package_id=card.package_id,c_type=1).count()
            study_card = User_Study_Record.objects.filter(user=up,package=master_package).count()
            print('******')
            print(all_card)
            print(study_card)
            if all_card == study_card:
                msg = User_Course_Record.objects.filter(user=up,course=master_package.course)
                if not msg:
                    course_record = User_Course_Record()
                    course_record.user = up
                    course_record.course = master_package.course
                    course_record.progress = study_card / all_card
                    course_record.save()
            card_content = file_content(self,card.id,up)
            datas ={
                'is_col': Card_Action.objects.filter(card_id=card.id,user=up).count(),
                'study_num':User_Study_Record.objects.filter(package=master_package,card=card).count(),
                'data':card_content,
             }
            return self.write_json({'errno': 0,'msg':'success','data':datas})
        except Card.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在卡片!!!'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户!!!'})
        except User_Study_Record.DoesNotExist:
            return self.write_json({'errno': 1, 'msg': '不存在用户学习记录!!!'})


class Create_Package(BaseHandler):
    @auth_decorator
    @logger_decorator
    @transaction.atomic
    def post(self,request):
        pack = json.loads(request.body)
        package_name = pack.get('package_name')
        up = UserProfile.objects.get(username=request.user)
        try:
            package = Master_Package.objects.filter(package_name=package_name,create_user=up)
            if package:
                return self.write_json({'errno':1,'msg':'该卡包名称已被占用!!!'})
            packages = Master_Package()
            packages.package_name = package_name.strip()
            packages.create_user = up
            packages.branch_name = 'master'
            package_name = up.username + package_name.strip()
            result = git_utils.create_git_package(package_name)

            data = []
            data.append(result.get('data'))
            if '0' == result.get('errno'):
                packages.package_location = result.get('data')['repo']
                packages.save()
                return file_path(self,up)
            else :
                return self.write_json({'errno':1,'msg':'创建卡包失败!!!'})
        except ValueError:
            return self.write_json({'errno':1,'msg':'卡包已存在!!!'})


class Delete_Package(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            package = Master_Package.objects.get(id=msg.get('key'))
            assi_package = Branch_Package.objects.filter(package_location=package.package_location)
            for assi in assi_package:
                assi.delete()
            all_card = Card.objects.filter(package_location=package.package_location)
            all_card.delete()

            #FIXME
            result =git_utils.delete_package(package.package_location)
            package.delete()
            return file_path(self,up)
        except Master_Package.DoesNotExist:
            try:
                package = Branch_Package.objects.get(id=msg.get('key'))
                all_card = Card.objects.filter(package_id=package.id,package_location=package.package_location)
                all_card.delete()

                #FIXME
                result = git_utils.delete_branch(package.package_location,'master',package.branch)
                package.delete()

                return assi_path(self,package.id)
            except Branch_Package.DoesNotExist:
                return self.write_json({'errno':1,'msg':'卡包不存在'})


class Course_Dir(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        course_id = msg.get('course_id')
        p_type = msg.get('p_type')
        up = UserProfile.objects.get(username=request.user)
        try:
            course = Course.objects.get(id=course_id)
            num = User_Buy_Record.objects.filter(course=course).count()
        except Course.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '课程不存在!!!'})

        c_package = Master_Package.objects.filter(course=course,p_type=0)
        c_data = []
        sign = ''
        for c_packages in c_package:
            if not None  == c_packages.sign:
                sign = c_packages.sign
            c_data.append({
                    'file':c_packages.package_name,
                    'coll_count':0,
                    'type':0,
                    'id':c_packages.id,
                    'index':-1,
                    'pid':0,
                    'is_study':0,
                    'is_finish':0
                })
            c_card = Card.objects.filter(~Q(tags=4),package_id=c_packages.id)
            coll_count = 0
            for c_cards in c_card:
                coll_count = Card_Action.objects.filter(card=c_cards).count()
                c_da={
                'coll_count':coll_count,
                'file':c_cards.file_name,
                'id':c_cards.id,
                'type':c_cards.c_type,
                'pid':c_cards.pid,
                'index':c_cards.index,
                'is_study':User_Study_Record.objects.filter(card_id=c_cards.id,user=up).count(),
                'is_finish':User_Hw_Record.objects.filter(card_id=c_cards.id,user=up).count()
                }
                c_data.append(c_da)

        def getcp(id=0):
            cp=[]
            for obj in c_data:
                if  obj['pid'] ==id:
                    cp.append({
                        'key':obj["id"],
                        'pid':obj['pid'],
                        'coll_count':obj['coll_count'],
                        'is_study':obj['is_study'],
                        'is_finish':obj['is_finish'],
                        'index':obj['index'],
                        'title':obj['file'],
                        'type':obj['type'],
                        'children':getcp(obj['id'])})
            return cp
        homework_key = 0
        h_package = Master_Package.objects.filter(course=course,p_type=1)
        for hps in  h_package:
            homework_key = hps.id
        disc_key = 0
        dis_package = Master_Package.objects.filter(course=course,p_type=2)
        for dis in  dis_package:
            disc_key = dis.id
        message = {
            'sign':sign,
            'is_homework':course.is_homework,
            'is_disc':course.is_discuss,
            'homework_key':homework_key,
            'num':num,
            'cover':course.cover,
            'title':course.title,
            'disc_key':disc_key,
            'course':getcp()
            }
        return self.write_json({'errno':0, 'msg': 'success','data':message})


class Commit_Hw(BaseHandler):
        @logger_decorator
        @transaction.atomic
        @auth_decorator
        def post(self,request):
            msg = json.loads(request.body)
            try:
                up = UserProfile.objects.get(username=request.user)
                pa = Card.objects.get(id=msg.get('pid'))
                _file = Card.objects.get(id=msg.get('key'))
                master_package = Master_Package.objects.get(id=_file.package_id)
                c = Card.objects.filter(file_name=(up.id+'.aw'),pid=pa.id)
                my = {}
                if c:
                   upd_card = Card.objects.get(id=msg.get('key'))
                   upd_card.content = msg.get('content')
                   upd_card.save()
                if not c:
                    aw_card = Card()
                    aw_card.package_id = pa.package_id
                    aw_card.branch = pa.branch
                    aw_card.package_location = pa.package_location
                    aw_card.c_type = 1
                    aw_card.tags = 4
                    aw_card.file_name = up.id +'.aw'
                    aw_card.content = msg.get('content')
                    aw_card.create_user = up
                    aw_card.pid = pa.id
                    path = os.path.join(pa.card_location,up.id+'.aw')
                    aw_card.card_location = path
                    data = {
                        'branch':'master',
                        'repo':pa.package_location,
                        'dir_name':path,
                        'file_content':msg.get('content')
                    }
                    url = settings.GIT_FILE_URL
                    r = requests.post(url,data=data)
                    result = r.json()
                    if '0' == result.get('errno'):
                        aw_card.save()
                        _file.commit_count += 1
                        _file.save()
                        _aw_card = User_Hw_Record.objects.filter(card=_file,aw_card=aw_card,user=up)
                        if not _aw_card:
                            user_hw = User_Hw_Record()
                            user_hw.user = up
                            user_hw.answer = msg.get('content')
                            user_hw.package = master_package
                            user_hw.card = _file
                            user_hw.aw_card = aw_card
                            user_hw.is_finish = 1
                            user_hw.save()
                            my = {
                                'id':str(user_hw.id),
                                'aw_key':str(aw_card.id),
                                'answer':msg.get('content'),
                                'head_img':up.head_img,
                                'create_time':str(user_hw.create_time)[19:]
                                }
                aw_detail = []
                aw_detail.append({
                    'key':_file.id,
                    'content':file_content(self,_file.id,up),
                    'comment':[],
                    'my_answer':my,
                    'other_answer':[],
                    })
                return self.write_json({'errno':0, 'msg': 'success','data':aw_detail})
            except Card.DoesNotExist:
                return self.write_json({'errno':1, 'msg': '不存在卡片信息！！！'})
            except UserProfile.DoesNotExist:
                return self.write_json({'errno':1, 'msg': '不存在用户！！！'})
            except Master_Package.DoesNotExist:
                return self.write_json({'errno':1, 'msg': '不存在卡包！！！'})


class Modify_Hw(BaseHandler):
    @logger_decorator
    @transaction.atomic
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            file_card = Card.objects.get(id=msg.get('file_key'))
            aw_card = Card.objects.get(id=msg.get('key'))
            hw_card = User_Hw_Record.objects.filter(aw_card=aw_card,user=up,package_id=aw_card.package_id)
            aw_card.content = msg.get('content')
            data = {
                'branch':'master',
                'repo':aw_card.package_location,
                'dir_name':aw_card.card_location,
                'file_content':msg.get('content')
                }
            url = settings.GIT_MODIFY_FILE
            r = requests.post(url,data=data)
            result = r.json()
            my = {}
            for hw in hw_card:
                hw.answer = msg.get('content')
                hw.save()
                my = {
                    'id':hw.id,
                    'aw_key':aw_card.id,
                    'answer':msg.get('content'),
                    'head_img':up.head_img,
                    'create_time':str(hw.create_time)[19:]
                 }
          #  if '0' == result.get('errno'):
            aw_card.save()
            aw_detail = []
            comment = []
            card_comment = Card_Comment.objects.filter(card=aw_card)
            for coms in card_comment:
                comment.append({
                    'is_my':1,
                    'user':coms.user.username,
                    'head_img':coms.user.head_img,
                    'content':coms.content,
                    'create_time':str(coms.create_time)[19:]
                    })

            aw_detail.append({
                'key':aw_card.id,
                'content':file_content(self,file_card.id,up),
                'comment':comment,
                'my_answer':my,
                'other_answer':[],
                })
            return self.write_json({'errno':0, 'msg': 'success','data':aw_detail})
        except Package.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '不存在卡包！！！'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '不存在用户！！！'})


class File_Diff(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            if '0' == msg.get('type'):
                c = Card.objects.get(id=msg.get('key'))
                data = {
                    'type':'0',
                    'branch':'master',
                    'assi_branch':c.branch,
                    'repo':c.package_location,
                    'file_path':c.card_location,
                    }
                url = settings.GIT_DIFF
                r = requests.post(url,data=data)
                result = r.json()
                if '0' == result.get('errno'):
                    s = result.get('data')
                    return self.write_json({'errno':0, 'msg': 'success','data':s})
                else:
                    return self.write_json({'errno':1, 'msg': '新创建文件无法对比！！！'})
            elif '1' == msg.get('type'):
                p = Branch_Package.objects.get(id=msg.get('key'))
                up = UserProfile.objects.get(username=request.user)
                message = {}
                if msg.get('messageid'):
                    mess = System_Message.objects.get(id=msg.get('messageid'))
                    mess.status = 1
                    mess.save()
                    message = {
                        'user':mess.user.username,
                        'head_img':mess.user.head_img,
                        'message':mess.message,
                        'content':mess.content,
                        'create_time':str(mess.create_time)[19:]
                        }
                data = {
                    'role':msg.get('role'),
                    'type':'1',
                    'branch':'master',
                    'assi_branch':p.branch,
                    'repo':p.package_location,
                    }
                url = settings.GIT_DIFF
                r = requests.post(url,data=data)
                result = r.json()
                if '0' == result.get('errno'):
                    s = result.get('data')
                    ss = s[0] if type(s)==list else s
                    return self.write_json({'errno':0, 'msg': 'success','message':message,'data':ss})
            elif '2' == msg.get('type'):
                card = Card.objects.get(id=msg.get('key'))
                if 0 == card.c_type:
                    cards = Card.objects.filter(pid=card.id)
                    for c in cards:
                        data = {
                            'type':'2',
                            'repo':c.package_location,
                            'branch':c.branch,
                            'file_path':c.card_location,
                        }
                        url = settings.GIT_DIFF
                        r = requests.post(url,data=data)
                        result = r.json()
                        if '0' == result.get('errno'):
                            s = result.get('data')
                            return self.write_json({'errno':0, 'msg': 'success','data':s})
                        else:
                            return self.write_json({'errno':1, 'msg': '新创建文件无法还原！！！'})

                elif 1 == card.c_type:
                    data = {
                        'type':'2',
                        'repo':card.package_location,
                        'branch':card.branch,
                        'file_path':card.card_location
                    }
                    url = settings.GIT_DIFF
                    r = requests.post(url,data=data)
                    result = r.json()
                    if '0' == result.get('errno'):
                        s = result.get('data')
                        return self.write_json({'errno':0, 'msg': 'success','data':s})
                    else:
                        return self.write_json({'errno':1, 'msg': '新创建文件无法还原！！！'})

            return self.write_json({'errno':1, 'msg': '文件冲突未解决！！！','data':''})
        except Branch_Package.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '已合并文件！！！'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '不存在用户！！！'})
        except User_Branch.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '不存在分支信息！！！'})
        except Card.DoesNotExist:
            return self.write_json({'errno':1, 'msg': '卡片不存在！！！'})


class Teacher_Package(BaseHandler):
    @logger_decorator
    @auth_decorator
    def post(self, request):
        up = UserProfile.objects.get(username=request.user)
        path = file_path(self, up, False)
        return self.write_json(path)


class Merge_Branch(BaseHandler):
    @logger_decorator
    @transaction.atomic
    @auth_decorator
    def post(self, request):
        try:
            msg = json.loads(request.body)
            up = UserProfile.objects.get(username=request.user)
            user = UserProfile.objects.get(id=msg.get('id'))
            assi_pack = Branch_Package.objects.get(id=msg.get('assi_key'))
            u_branch = User_Branch.objects.get(user=user,assi_package=assi_pack)
            create_pack = u_branch.create_package
            assi_card = Card.objects.filter(package_id=assi_pack.id).order_by('create_time')
            assi_key = ''

            logger.info("Merge_Branch")

            #FIXME
            def copy_assi_file(data, pid, package):
                d = data['children']
                for child in d:
                    child_data = child.get('children')
                    card = Card()
                    card.file_name = child.get('title')
                    card.c_type = child.get('type')
                    card.pid = pid
                    card.card_location = child.get('card_location')
                    card.tags = child.get('tags')
                    card.content = child.get('content')
                    card.create_user = assi_pack.create_user
                    card.package_id = package.id
                    card.branch = package.branch
                    card.package_location = package.package_location
                    card.index = child.get('index')
                    card.save()
                    if child_data:
                        copy_assi_file(child, card.id, package)

            def copy_assi_package(value):
                copy_assi_package = Branch_Package()
                copy_assi_package.create_user = assi_pack.create_user
                copy_assi_package.package_name = value.get('title')
                copy_assi_package.branch = assi_pack.create_user.phone
                copy_assi_package.package_location = assi_pack.package_location
                copy_assi_package.role = 1
                copy_assi_package.save()
                assi_key = copy_assi_package.id
                message = System_Message.objects.get(id=msg.get('messageid'))
                message.apply_status = 1
                message.key = assi_key
                message.save()
                #b = User_Branch.objects.filter(user=assi_pack.create_user,create_package=create_pack,
                #                                assi_package=copy_assi_package)
                #if not b:
                user_branch = User_Branch()
                user_branch.user = assi_pack.create_user
                user_branch.create_package = create_pack
                user_branch.assi_package = copy_assi_package
                user_branch.branch = assi_pack.create_user.phone
                user_branch.save()
                #
                copy_assi_file(value,copy_assi_package.id,copy_assi_package)

            assi_package_path = assi_path(self,msg.get('assi_key'),False)
            copy_data = copy_assi_package(assi_package_path.get('data')[0])
            delete_data = []

            #FIXME: var folder=>card
            for folder in assi_card:
                logger.debug("card_location: %s %s" % (create_pack.id, folder.card_location,))
                folder_dir = Card.objects.filter(package_id=create_pack.id, card_location=folder.card_location)

                if len(folder_dir):
                    delete_data.append(folder)

                if folder.pid == assi_pack.id:
                    #  第一层目录
                    #great_dir(folder, create_pack)
                    folder.pid = create_pack.id
                    folder.package_id = create_pack.id
                    folder.branch = create_pack.branch
                    folder.save()
                else:
                    parent_card = Card.objects.get(id=folder.pid)
                    master_card = Card.objects.filter(package_id=create_pack.id, card_location=parent_card.card_location)
                    if len(master_card):
                        folder.pid = master_card[0].id
                        folder.package_id = create_pack.id
                        folder.branch = create_pack.branch
                        folder.save()
            # 删除重复数据
            for delete_card in delete_data:
                delete_card.delete()

            #FIXME
            # git合并
            data = {
                'type':'0',
                'branch':create_pack.branch,
                'merge_branch':assi_pack.branch,
                'repo':create_pack.package_location
                }
            url = settings.GIT_MERGE_BRANCH
            r = requests.post(url,data=data)
            result = r.json()

            all_card = Card.objects.filter(package_id=assi_pack.id)
            for ac in all_card:
                ac.delete()
            assi_pack.delete()
            if '0' == result.get('errno'):
                mess = System_Message()
                mess.user = up
                mess.to_user = assi_pack.create_user
                mess.type = 1
                mess.apply_status = 1
                mess.message = '您申请的' + create_pack.package_name + '卡包已同意合并变更'
                mess.content = '该卡包已合并到主版本中'
                mess.save()
                path = file_path(self,up,False);
                return self.write_json({'errno':0,'msg':'success'})
            else:
                conflict_card = result.get('data')
                if conflict_card:
                    message = System_Message.objects.get(id=msg.get('messageid'))
                    message.is_solve = 1
                    message.save()
                    data = []
                    for cc in conflict_card:
                        logger.warning("conflict: %s" % (repr(cc.get('file')),)) #warn
                        card = Card.objects.filter(card_location=cc.get('file'),branch=cc.get('branch'))
                        for cs in card:
                            data.append({
                                'type':1,
                                'key':cs.id,
                                'tags':cs.tags,
                                'title':cs.file_name,
                                'content':cc.get('content'),
                            })
                    return self.write_json({'errno':1,'msg':'合并文件有冲突','data':data})
                else:
                    return self.write_json({'errno':1,'msg':'合并文件有冲突,请联系卡包创建者'})
        except Master_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在'})
        except Branch_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在'})


#FIXME
class Merge_Master(BaseHandler):
    @logger_decorator
    @transaction.atomic
    @auth_decorator
    def post(self, request):
        try:
            msg = json.loads(request.body)
            up = UserProfile.objects.get(username=request.user)
            assi_pack = Branch_Package.objects.get(id=msg.get('assi_key'))
            u_branch = User_Branch.objects.get(user=up,assi_package=assi_pack)
            create_pack = u_branch.create_package
            def copy_master_file(data, pid, package):
                d = data['children']
                for child in d:
                    child_data = child.get('children')
                    card = Card()
                    card.file_name = child.get('title')
                    card.c_type = child.get('type')
                    card.pid = pid
                    card.card_location = child.get('card_location')
                    card.tags = child.get('tags')
                    card.content = child.get('content')
                    card.create_user = create_pack.create_user
                    card.package_id = package.id
                    card.branch = package.branch
                    card.package_location = package.package_location
                    card.index = child.get('index')
                    card.save()
                    if child_data:
                        copy_master_file(child, card.id, package)

            def copy_master_package(value):
                copy_master = Master_Package()
                copy_master.create_user = create_pack.create_user
                copy_master.package_name = value.get('title')
                copy_master.branch = create_pack.branch
                copy_master.package_location = create_pack.package_location
                copy_master.role = 0
                copy_master.save()
                #b = User_Branch.objects.filter(user=assi_pack.create_user,create_package=copy_master,
                #                                assi_package=assi_pack)
                #if not b:
            #    user_branch = User_Branch()
            #    user_branch.user = assi_pack.create_user
            #    user_branch.create_package = copy_master
            #    user_branch.assi_package = assi_pack
            #    user_branch.branch = assi_pack.create_user.phone
            #    user_branch.save()
            #    #
                copy_master_file(value,copy_master.id,copy_master)
                delete_data = []
                master_card = Card.objects.filter(package_id=copy_master.id)
                #FIXME
                for folder in master_card:
                    folder_dir = Card.objects.filter(package_id=assi_pack.id, card_location=folder.card_location)
                    if len(folder_dir):
                        delete_data.append(folder)

                    logger.debug("card_location: %s %s" % (create_pack.id, folder.card_location,))
                    if folder.pid == str(copy_master.id):
                        #  第一层目录
                        #great_dir(folder, create_pack)
                        folder.pid = assi_pack.id
                        folder.package_id = assi_pack.id
                        folder.branch = assi_pack.branch
                        folder.package_location = assi_pack.package_location
                        folder.save()

                    else:
                        parent_card = Card.objects.get(id=folder.pid)
                        master_card = Card.objects.filter(package_id=assi_pack.id, card_location=parent_card.card_location)
                        if len(master_card):
                            folder.pid = master_card[0].id
                            folder.package_id = assi_pack.id
                            folder.branch = assi_pack.branch
                            folder.package_location = assi_pack.package_location
                            folder.save()

                # 删除重复数据
                for delete_card in delete_data:
                    delete_card.delete()

                all_card = Card.objects.filter(package_id=copy_master.id)
                for ac in all_card:
                    print(ac.file_name)
                    ac.delete()
                copy_master.delete()

            # merge master start
            master_package_path = assi_path(self,create_pack.id,False)
            copy_data = copy_master_package(master_package_path.get('data')[0])
            data = {
                'type':'1',
                'branch':create_pack.branch,
                'merge_branch':assi_pack.branch,
                'repo':create_pack.package_location
                }
            url = settings.GIT_MERGE_BRANCH
            r = requests.post(url,data=data)
            result = r.json()
            if '0' == result.get('errno'):
                path = assi_file_path(self,up,False);
                return self.write_json(path)
            else:
                conflict_card = result.get('data')
                if conflict_card:
                    data = []
                    for cc in conflict_card:
                        print(cc.get('file'))
                        card = Card.objects.filter(card_location=cc.get('file'),branch=cc.get('branch'))
                        for cs in card:
                            data.append({
                                'type':1,
                                'key':cs.id,
                                'tags':cs.tags,
                                'title':cs.file_name,
                                'content':cc.get('content'),
                            })
                    return self.write_json({'errno':1,'msg':'合并文件有冲突！！！','data':data})
                else:
                    return self.write_json({'errno':1,'msg':'合并文件有冲突,请联系卡包创建者！！！'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！！'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡包不存在！！！'})



class Recover_File(BaseHandler):
    @logger_decorator
    @auth_decorator
    @transaction.atomic
    def post(self, request):
        msg = json.loads(request.body)
        try:
           c = Card.objects.get(id=msg.get('key'))
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'卡片不存在！！！'})
        if 1 == c.c_type:
            c.reset_count += 1
            c.save()
            data = {
                'branch':c.branch,
                'repo':c.package_location,
                'path':c.card_location,
                'count':c.modify_count - c.reset_count
            }
            url = settings.GIT_RECOVER_FILE
            r = requests.post(url,data=data)
            result = r.json()
            if '0' ==  result.get('errno'):
                c.content = result.get('content')
                c.save()
            return self.write_json({'errno':0,'msg':'ok'})
        elif 0 == c.c_type:
            cards = Card.objects.filter(pid=c.id)
            for cs in cards:
                cs.reset_count += 1
                cs.save()
                data = {
                    'branch':cs.branch,
                    'repo':cs.package_location,
                    'path':cs.card_location,
                    'count':cs.modify_count - cs.reset_count
                }
                url = settings.GIT_RECOVER_FILE
                r = requests.post(url,data=data)
                result = r.json()
                print(result)
                if '0' ==  result.get('errno'):
                    cs.content = result.get('content')
                    cs.save()
                return self.write_json({'errno':0,'msg':'ok'})



class Qiniu_Token(BaseHandler):
    def post(self,request):
        img = Uploader()
        token = img.get_token()
        data = {
            'token':token
            }
        return self.write_json({'errno':0,'msg':'ok','data':data})


class Banners(BaseHandler):
    def post(self,request):
        return self.write_json({'errno':0,'msg':'ok'})


class Delete_Some_File(BaseHandler):
    def post(self,request):
        msg = json.loads(request.body)
        c = Card.objects.all()
        for cs in c:
            cs.delete()
        return self.write_json({'errno':0,'msg':'ok'})


class Apply_Merge_Branch(BaseHandler):
    @transaction.atomic
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            assi_package = Branch_Package.objects.get(id=msg.get('key'))
            user_info = User_Branch.objects.get(user=up,assi_package=assi_package)
            message = System_Message()
            message.user = up
            message.message = up.username + '提交了卡包' + assi_package.package_name + '的变更申请'
            message.content = '变更说明：'+ msg.get('message')
            message.key = msg.get('key')
            message.to_user = user_info.create_package.create_user
            message.type = 1
            message.is_apply = 1
            message.save()
            data = {
                'branch':user_info.create_package.branch,
                'repo':user_info.create_package.package_location
                }
            url = settings.GIT_CHECKOUT_MASTER
            r = requests.post(url,data=data)
            results = r.json()
            return self.write_json({'errno':0,'msg':'ok'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})
        except Branch_Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡包！！！'})
        except User_Branch.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在分支信息！！！'})


class Check_Message(BaseHandler):
    @transaction.atomic
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            message = System_Message.objects.get(id=msg.get('messageid'))
            message.status = 1
            message.save()
            file_info = {}
            content = ''
            if  msg.get('key'):
                card = Card.objects.get(id=msg.get('key'))
                content = file_content(self,msg.get('key'),up)
                file_info = {
                    'title':card.file_name,
                    'content':content,
                    }
            else:
                content = ''
            return self.write_json({'errno':0,'msg':'ok','data':content})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})
        except User_Branch.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在分支信息！！！'})
        except Card.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡片信息！！！'})


class Refuse_Merge_Branch(BaseHandler):
    @transaction.atomic
    @logger_decorator
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        try:
            up = UserProfile.objects.get(username=request.user)
            assi_package = Branch_Package.objects.get(id=msg.get('key'))
            apply_user = UserProfile.objects.get(id=msg.get('id'))
            user_info = User_Branch.objects.get(user=apply_user,assi_package=assi_package)
            mess = System_Message.objects.get(id=msg.get('messageid'))
            mess.apply_status = 2
            mess.save()

            message = System_Message()
            message.user = up
            message.message = up.username + '拒绝了你对' + assi_package.package_name + '的变更申请'
            message.content = '拒绝原因:'+ msg.get('message')
            message.key = msg.get('key')
            message.to_user = apply_user
            message.apply_status = 2
            message.type = 1
            message.save()
            return self.write_json({'errno':0,'msg':'ok'})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})
        except Package.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在卡包！！！'})
        except User_Branch.DoesNotExist:
            return self.write_json({'errno':1,'msg':'不存在分支信息！！！'})


class My_Message(BaseHandler):
    @transaction.atomic
    @auth_decorator
    def post(self,request):
        msg = json.loads(request.body)
        page = msg.get('page')
        count = msg.get('count')
        try:
            # 1、检查session 是否有记录，如果有记录则将session 中的消息id 修改为已读
            # 2、将未读消息id list 保存到session
       #     news = request.session.get('message')
       #     if news:
       #         for news_id in json.loads(news):
       #             sm = System_Message.objects.get(id=news_id)
       #             sm.status = 1
       #             sm.save()
       #     unread = System_Message.objects.filter(status=0).values_list('id', flat=True)
       #     request.session['message'] = json.dumps(list(unread))
       #     news = request.session.get('message')

            up = UserProfile.objects.get(username=request.user)
            if '0' == msg.get('type'):
                message = System_Message.objects.filter(to_user=up,type=0).order_by('-create_time')
            if '1' == msg.get('type'):
                message = System_Message.objects.filter(to_user=up,type=1).order_by('-create_time')
            if '2' == msg.get('type'):
                message = System_Message.objects.filter(to_user=up,type=2).order_by('-create_time')
            data = []
            card_info = {}
            for m in message:
                card = Card.objects.filter(id=m.card_url)
                if card:
                    card_info = {
                        'title':card[0].file_name,
                        'key':card[0].id,
                        'tags':card[0].tags
                    }
                else:
                    card_info = {}
                confilct_card = []
                user = UserProfile.objects.get(id=m.user.id)
                if 1 == m.is_solve:
                    assi_pack = Branch_Package.objects.get(id=m.key)
                    u_branch = User_Branch.objects.get(user=user,assi_package=assi_pack)
                    create_pack = u_branch.create_package
                    da = {
                        'type':'0',
                        'branch':create_pack.branch,
                        'merge_branch':assi_pack.branch,
                        'repo':create_pack.package_location
                        }
                    url = settings.GIT_MERGE_BRANCH
                    r = requests.post(url,data=da)
                    result = r.json()
                    if '0' == result.get('errno'):
                        return self.write_json({'errno':0,'msg':'success','data':''})
                    else:
                        conflict_card = result.get('data')
                        if conflict_card:
                            data = []
                            for cc in conflict_card:
                                print(cc.get('file'))
                                card = Card.objects.filter(card_location=cc.get('file'),branch=cc.get('branch'))
                                for cs in card:
                                    confilct_card.append({
                                        'type':1,
                                        'key':cs.id,
                                        'tags':cs.tags,
                                        'title':cs.file_name,
                                        'content':cc.get('content'),
                                    })
                data.append({
                    'messageid':m.id,
                    'userid':user.id,
                    'user':user.username,
                    'head_img':user.head_img,
                    'message':m.message,
                    'card_url':m.card_url,
                    'card_id':m.card_id,
                    'course_id':m.course_id,
                    'card_tags':m.card_tags,
                    'content':m.content,
                    'confilt_card':confilct_card,
                    'status':m.status,
                    'apply_status':m.apply_status,
                    'is_apply':m.is_apply,
                    'is_solve':m.is_solve,
                    'location':m.location,
                    'to_userid':m.to_userid,
                    'key':m.key,
                    'card':card_info,
                    'create_time':str(m.create_time)[19:]
                })
            p = Paginator(data,count)
            return self.write_json({'errno': 0, 'msg': 'success','total_count':message.count(),
                                    'apply_count': System_Message.objects.filter(to_user=up,type=1,status=0).count(),
                                    'system_count': System_Message.objects.filter(to_user=up,type=0,status=0).count(),
                                    'comment_count': System_Message.objects.filter(to_user=up,type=2,status=0).count(),
                                    'total_page':p.num_pages,'data': p.page(page).object_list})
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})


class Upload_Zip(BaseHandler):
    @transaction.atomic
    @logger_decorator
    def post(self,request):
        def get_parent_path(spath):
            s = '/'.join(list(filter(lambda x: x, spath.split('/')))[:-1])
            return s
        def folder_name(spath):
            k = spath.count('/')
            if 1 == k:
                s = spath.split('/')[0]
            else:
                 s = spath.split('/')[-2]
            return s
        def file_name(fpath):
            s = fpath.split('/')[-1]
            return s
        try:
            file_field = request.FILES.getlist('file')
            dirname = 'upload'
            result = {}
            userid = request.POST.get('userid')
            token = request.POST.get('token')
            role = request.POST.get('role')
            up = UserProfile.objects.get(id=userid,token=token)
            p = get_package(self,request.POST.get('key'))
            unuse = []
            if p:
                for f in file_field:
                    if zipfile.is_zipfile(f):
                        zfobj = zipfile.ZipFile(f)
                        for name in zfobj.namelist():
                            if name:
                                filename = os.path.join(dirname,name)
                                if 'MACOSX' not in filename and 'Store' not in filename:
                                    dn = os.path.dirname(filename)
                                    if not os.path.exists(dn):
                                        os.makedirs(dn)
                                    base_dir = os.path.dirname(filename)
                                    jk = get_parent_path(filename[7:])
                                    p_path = os.path.join(p.package_location,jk)
                                    pid = Card.objects.filter(card_location=p_path)
                                    fid = p.id
                                    for ps in pid:
                                        fid = ps.id
                                    if os.path.isdir(filename):
                                        c = Card.objects.filter(file_name=folder_name(filename[7:]),pid=fid)
                                        if not c:
                                            path = os.path.join(p.package_location,filename[7:])
                                            card = Card()
                                            card.package_id = p.id
                                            card.branch = p.branch
                                            card.package_location = p.package_location
                                            card.file_name = folder_name(filename[7:])
                                            card.c_type = 0
                                            card.pid = fid
                                            card.create_user = up
                                            card.card_location = path[:-1]
                                            data = {
                                                'branch':p.branch,
                                                'repo':p.package_location,
                                                'dir_name':path[:-1]
                                            }
                                            url = settings.GIT_DIRPATH
                                            r = requests.post(url,data=data)
                                            result = r.json()
                                            card.save()
                                    else:
                                        outfile = open(filename,'wb')
                                        outfile.write(zfobj.read(name))
                                        outfile.close()
                                        fs = open(filename,'r')
                                        lines = fs.read()
                                        content = ''
                                        for line in lines:
                                            content += line
                                        jd = get_parent_path(filename)
                                        fname = (file_name(filename))
                                        name, ext = os.path.splitext(fname)
                                        if ext not in ['.md', '.video', '.exam']:
                                            unuse.append({'file':filename[7:],'type':0})
                                        fpath = os.path.join(p.package_location,filename[7:])
                                        c = Card.objects.filter(file_name=fname,card_location=fpath)
                                        if not c:
                                            if  ext in ['.md', '.video', '.exam']:
                                                card = Card()
                                                card.package_id = p.id
                                                card.branch = p.branch
                                                card.package_location = p.package_location
                                                card.file_name = fname
                                                card.card_location = fpath
                                                card.content = content
                                                card.c_type = 1
                                                if '.video' in fname:
                                                    card.tags = 1
                                                    verify = verify_content(self,content)
                                                    if 0 == verify.get('errno'):
                                                        card.save()
                                                        pass
                                                    else:
                                                        unuse.append({'file':filename[7:],'type':1})
                                                elif '.exam' in fname:
                                                    card.tags = 2
                                                    verify = verify_content(self,content)
                                                    if 0 == verify.get('errno'):
                                                        card.save()
                                                        pass
                                                    else:
                                                        unuse.append({'file':filename[7:],'type':1})
                                                card.create_user = up
                                                card.pid = fid
                                                data = {
                                                    'branch':p.branch,
                                                    'repo': p.package_location,
                                                    'dir_name': fpath,
                                                    'file_content': content
                                                }
                                                url = settings.GIT_FILE_URL
                                                r = requests.post(url,data=data)
                                                result = r.json()
                                                verify = verify_content(self,content)
                                                if 0 == verify.get('errno'):
                                                    card.save()
                                                    pass
                                                else:
                                                    unuse.append({'file':filename[7:],'type':1})
            if '0' == role:
                file_dir = file_path(self, up, False)
            elif '1' == role:
                file_dir = assi_file_path(self, up, False)
            file_dir['error_file'] = unuse
            return self.write_json(file_dir)
        except UserProfile.DoesNotExist:
            return self.write_json({'errno':1,'msg':'用户不存在！！！'})
        else:
            try:
                folder = Card.objects.get(id=request.POST.get('key'))
            except Card.DoesNotExist:
                return self.write_json({'errno':1,'msg':'文件不存在！！！'})
            for f in file_field:
                if zipfile.is_zipfile(f):
                    zfobj = zipfile.ZipFile(f)
                    for name in zfobj.namelist():
                        if name:
                            filename = os.path.join(dirname,name)
                            if 'MACOSX' not in filename and 'Store' not in filename:
                                dn = os.path.dirname(filename)
                                if not os.path.exists(dn):
                                    os.makedirs(dn)
                                base_dir = os.path.dirname(filename)
                                jk = get_parent_path(filename[7:])
                                p_path = os.path.join(folder.card_location,jk)
                                pid = Card.objects.filter(card_location=p_path)
                                fid = folder.id
                                for ps in pid:
                                    fid = ps.id
                                if os.path.isdir(filename):
                                    c = Card.objects.filter(file_name=folder_name(filename[7:]),pid=fid)
                                    if not c:
                                        path = os.path.join(folder.card_location,filename[7:])
                                        card = Card()
                                        card.package_id = folder.package_id
                                        card.branch = folder.branch
                                        card.package_location = folder.package_location
                                        card.file_name = folder_name(filename[7:])
                                        card.c_type = 0
                                        card.pid = fid
                                        card.create_user = up
                                        card.card_location = path[:-1]
                                        data = {
                                            'branch':folder.branch,
                                            'repo':folder.package_location,
                                            'dir_name':path[:-1],
                                            }
                                        url = settings.GIT_DIRPATH
                                        r = requests.post(url,data=data)
                                        result = r.json()
                                        card.save()
                                else:
                                    outfile = open(filename,'wb')
                                    outfile.write(zfobj.read(name))
                                    outfile.close()
                                    fs = open(filename,'r')
                                    lines = fs.read()
                                    content = ''
                                    for line in lines:
                                        content += line
                                    jd = get_parent_path(filename)
                                    fname = file_name(filename)
                                    name, ext = os.path.splitext(fname)
                                    if ext not in ['.md', '.video', '.exam']:
                                        unuse.append({'file':filename[7:],'type':0})
                                    fpath = os.path.join(folder.card_location,filename[7:])
                                    c = Card.objects.filter(file_name=fname,card_location=fpath)
                                    if not c:
                                        if  ext in ['.md', '.video', '.exam']:
                                            card = Card()
                                            card.package_id = folder.package_id
                                            card.file_name = fname
                                            card.card_location = fpath
                                            card.create_user = up
                                            card.c_type = 1
                                            card.content = content
                                            if '.video' in fname:
                                                card.tags = 1
                                                verify = verify_content(self,content)
                                                if 0 == verify.get('errno'):
                                                    card.save()
                                                    pass
                                                else:
                                                    unuse.append({'file':filename[7:],'type':1})
                                            elif '.exam' in fname:
                                                card.tags = 2
                                                verify = verify_content(self,content)
                                                if 0 == verify.get('errno'):
                                                    card.save()
                                                    pass
                                                else:
                                                    unuse.append({'file':filename[7:],'type':1})
                                            card.pid = fid
                                            data = {
                                                'branch':folder.branch,
                                                'repo':folder.package_location,
                                                'dir_name':fpath,
                                                'file_content':content
                                                }
                                            url = settings.GIT_FILE_URL
                                            r = requests.post(url,data=data)
                                            result = r.json()
                                            verify = verify_content(self,content)
                                            if 0 == verify.get('errno'):
                                                card.save()
                                                pass
                                            else:
                                                unuse.append({'file':filename[7:],'type':1})
            if '0' == role:
                file_dir = file_path(self, up, False)
            elif '1' == role:
                file_dir = assi_file_path(self, up, False)
            file_dir['error_file'] = unuse
            return self.write_json(file_dir)

