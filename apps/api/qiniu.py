#coding:utf-8
"""七牛存储api"""
from qiniu import Auth, etag, put_file, put_data
import os
import uuid

#import urllib3


ACCESS_KEY = 'Zt5y9AOFeTCFtX1HllY4bXkHRW08VHQP68SG8_HG' #'Zt5y9AOFeTCFtX1HllY4bXkHRW08VHQP68SG8_HG'
SECRET_KEY = 'zoNb7G8gh9l3RYqVXeYedi8iqg9jQfZkVSSTvM6N' #'zoNb7G8gh9l3RYqVXeYedi8iqg9jQfZkVSSTvM6N'
BACKET_NAME = 'kaizhi'
DOMAIN = 'http://p55e2xuty.bkt.clouddn.com/' #'http://7xspkg.com2.z0.glb.qiniucdn.com/'

class Uploader(object):
    #image = request.FILES.get('wangEditorH5File')
    #key = Uploader().save_file_to_qiniu(image)
    mime_type = "text/plain"
    q = Auth(ACCESS_KEY, SECRET_KEY)

    def save_file_to_qiniu(self, upload_file, key='', path='attach', return_domain=True):
        """web上传文件"""
        #key= set name
        #ext = os.path.splitext(upload_file)[1] #拓展名
        ext = os.path.splitext(upload_file.name)[1]
        key = str(uuid.uuid1()).replace('-', '')
        key = "%s/%s%s" % (path, key, ext)
        token = self.q.upload_token(BACKET_NAME, key, 3600)
        ret, info = put_data(token, key, upload_file)
        if ret.get('key',None) == None:
            raise Exception('upload error')
        else:
            if return_domain:
                return u"%s%s" % (DOMAIN, key)
            else:
                return key


    def get_token(self):
        policy = {}
        key = None
        token = self.q.upload_token(BACKET_NAME, key, 3600, policy)
        return token



    def save_qiniu(self, file_path, path='attach', return_domain=True):
        """上传本地文件"""
        ext = os.path.splitext(file_path)[1]
        key = str(uuid.uuid1()).replace('-', '')
        key = "%s/%s%s" % (path, key, ext)

        token = self.q.upload_token(BACKET_NAME, key, 3600)
        ret, info = put_file(token, key, file_path)
        if ret.get('key',None) == None:
            raise Exception('upload error')
        else:
            if return_domain:
                return u"%s%s" % (DOMAIN, key)
            else:
                return key


def get_attach_path(key):
    url = "%s%s" % (DOMAIN, key)
    return u"%s%s" % (DOMAIN, key)


def get_avatar_path(key, prefix='avatar'):
    return u"%s%s/%s" % (DOMAIN, prefix, key)

