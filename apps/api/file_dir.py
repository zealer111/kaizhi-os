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
import json
from django.utils import timezone
from pathlib import Path
from django.db.models import Q
from apps import settings
import operator
import re,glob


def get_package(self,key):

    try:
        master = Master_Package.objects.get(id=key)
        return master
    except Master_Package.DoesNotExist:
        try:
            branch = Branch_Package.objects.get(id=key)
            return branch
        except Branch_Package.DoesNotExist:
            return None

def get_file_path_as_card(self, user, return_json=True):
    package = Master_Package.objects.filter(~Q(p_type=2),create_user=user)
    data = []
    for packages in package:
        data.append({
            'title':packages.package_name,
            'type':0,
            'id':packages.id,
            'pid':0,
            'index':-1,
            'is_assistant':0,
            'tags':0,
            'create_time':str(packages.create_time)[:19],
            'update_time':str(packages.update_time)[:19]

            })
        card = Card.objects.filter(~Q(tags=4),package_id=packages.id)
        for cards in card:
            da = {
            'title':cards.file_name,
            'id':cards.id,
            'type':cards.c_type,
            'index':cards.index,
            'is_assistant':0,
            'pid':cards.pid,
            'tags':cards.tags,
            'create_time':str(cards.create_time)[:19],
            'update_time':str(cards.update_time)[:19]
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
                    'title':obj['title'],
                    'type':obj['type'],
                    'tags':obj['tags'],
                    'create_time':obj['create_time'],
                    'update_time':obj['update_time'],
                    'children':getChildren(obj['id'])})
        return sz
    if return_json:
        return self.write_json({'errno':0, 'msg': 'success','data':getChildren()})
    else:
        return {'errno':0, 'msg': 'success','data':getChildren()}


def get_assi_file_path_as_card(self, user, return_json=True):
    package = Branch_Package.objects.filter(~Q(p_type=2),create_user=user)
    data = []
    for packages in package:
        data.append({
            'title':packages.package_name,
            'type':0,
            'id':packages.id,
            'pid':0,
            'index':-1,
            'is_assistant':0,
            'tags':0,
            'create_time':str(packages.create_time)[:19],
            'update_time':str(packages.update_time)[:19]
            })
        card = Card.objects.filter(~Q(tags=4),package_id=packages.id)
        for cards in card:
            da = {
            'title':cards.file_name,
            'id':cards.id,
            'type':cards.c_type,
            'index':cards.index,
            'is_assistant':0,
            'pid':cards.pid,
            'tags':cards.tags,
            'create_time':str(cards.create_time)[:19],
            'update_time':str(cards.update_time)[:19]
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
                    'title':obj['title'],
                    'type':obj['type'],
                    'tags':obj['tags'],
                    'create_time':obj['create_time'],
                    'update_time':obj['update_time'],
                    'children':getChildren(obj['id'])})
        return sz
    if return_json:
        return self.write_json({'errno':0, 'msg': 'success','data':getChildren()})
    else:
        return {'errno':0, 'msg': 'success','data':getChildren()}


def get_file_paths_as_package(self,key,up,return_json=True):
    try:
        package = Master_Package.objects.get(id=key)
    except Master_Package.DoesNotExist:
        return self.write_json({'errno':'1','msg':'卡包不存在'})

    data = []
    data.append({
        'file':package.package_name,
        'type':0,
        'id':package.id,
        'pid':0,
        'index':-1,
        'is_finish':0,
        'count':0
        })
    card = Card.objects.filter(~Q(tags=4),package_id=package.id)
    for cards in card:
        count = 0
        answer = User_Hw_Record.objects.filter(card=cards,user=up)
        for an in answer:
            count = Card_Comment.objects.filter(card=an.aw_card).count()
        da = {
        'file':cards.file_name,
        'id':cards.id,
        'type':cards.c_type,
        'index':cards.index,
        'count':count,
        'is_finish':User_Hw_Record.objects.filter(card_id=cards.id,user=up).count(),
        'pid':cards.pid,
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
                    'is_finish':obj['is_finish'],
                    'title':obj['file'],
                    'type':obj['type'],
                    'count':obj['count'],
                    'children':getChildren(obj['id'])})
        return sz
    if return_json:
        return self.write_json({'errno':0, 'msg': 'success','sign':package.sign,'data':getChildren()})
    else:
        return {'errno':0, 'msg': 'success','sign':package.sign,'data':getChildren()}


def assi_path(self,key, return_json=True):
    p = Branch_Package.objects.filter(id=key)
    if p:
        package = Branch_Package.objects.get(id=key)
    else:
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
                    'tags':obj['tags'],
                    'card_location':obj['card_location'],
                    'children':getChildren(obj['id'])})
        return sz
    if return_json:
        return self.write_json({'errno':0, 'msg': 'success','data':getChildren()})
    else:
        return {'errno':0, 'msg': 'success','data':getChildren()}


def file_content(self, key,user):
    try:
        data = {}
        card = Card.objects.get(id=key,c_type=1)
        if 0 == card.tags:
            datas = {
            'branch':card.branch,
            'repo':card.package_location,
            'file_path':card.card_location
            }
            url = settings.GIT_FILE_CONTENT
            r = requests.post(url,data=datas)
            result = r.json()
            content = result['data'].get('content')

            rule = r'title:([\s\S]*)\nsign'
            rule1 = r'# front([\s\S]*?)# back'
            rule2 = r'# back([\s\S]*)'
            title = re.search(rule, content).group(1)
            back = re.search(rule2, content).group(1)
            front = {
            'content': re.search(rule1, content).group(1),
            }
            data = {'key':key,'type':0,'title':title,'front':front,'back':back}
        elif 1 == card.tags:

            datas = {
            'branch':card.branch,
            'repo':card.package_location,
            'file_path':card.card_location
            }
            url = settings.GIT_FILE_CONTENT
            r = requests.post(url,data=datas)
            result = r.json()
            content = result['data'].get('content')
            rule = r'title:([\s\S]*)\nsign'
            rule2 =r'url:([\s\S]*)```'
            rule3 =r'# back([\s\S]*)'
            front = {
              'url' : re.search(rule2,content).group(1),
             }
            data = {'key':key,'type':1,'title': re.search(rule,content).group(1),
                    'front':front,'back': re.search(rule3,content).group(1)}
        elif 2 == card.tags:
            datas = {
            'branch':card.branch,
            'repo':card.package_location,
            'file_path':card.card_location
            }
            url = settings.GIT_FILE_CONTENT
            r = requests.post(url,data=datas)
            result = r.json()
            content = result['data'].get('content')
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
                data = {'key':key,'type':2,'title':title,'front':front,'back':back}
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
                data = {'key':key,'type':2,'title':title,'front':front,'back':back}
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
                data = {'key':key,'type':2,'title':title,'front':front,'back':back}
        return data
    except Card.DoesNotExist:
         return self.write_json({'errno': 1, 'msg': '不存在文件!!!'})


def verify_content(self,content):
    try:
        if 'video' in content:
            rule = r'title:([\s\S]*)\nsign'
            rule2 =r'url:([\s\S]*)```'
            rule3 =r'# back([\s\S]*)'
            front = {
              'url' : re.search(rule2,content).group(1),
             }
            data = {'errno':0,'type':1,'title': re.search(rule,content).group(1),
                    'front':front,'back': re.search(rule3,content).group(1)}
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
            data = {'errno':0,'type':2,'title':title,'front':front,'back':back}
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
            data = {'errno':0,'type':2,'title':title,'front':front,'back':back}
        elif 'MQ' in content and 'SQ'  in content:
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
            data = {'errno':0,'type':2,'title':title,'front':front,'back':back}
        else:
            rule = r'title:([\s\S]*)\nsign'
            rule1 = r'# front([\s\S]*?)# back'
            rule2 = r'# back([\s\S]*)'
            title = re.search(rule, content).group(1)
            back = re.search(rule2, content).group(1)
            front = {
            'content': re.search(rule1, content).group(1),
            }
            data = {'errno':0,'type':0,'title':title,'front':front,'back':back}
        return data
    except BaseException:
         return self.write_json({'errno': 1, 'msg': '文件格式错误!!!'})

def get_file_dir(self,role,up):        
    if settings.GIT_ROLE_MASTER == role:
        path = get_file_path_as_card(self,up)
    elif  settings.GIT_ROLE_BRANCH  == role:
        path = get_assi_file_path_as_card(self,up)
    return path

