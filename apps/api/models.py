#coding: utf-8
from django.db import models
from django.contrib.auth.models import User
#from apps.api.utils import UUIDTools
import uuid
from django.utils.html import format_html
from django.utils import timezone


class UUIDTools(object):
    """uuid function tools"""

    @staticmethod
    def uuid1_hex():
        """
        return uuid1 hex string

        eg: 23f87b528d0f11e696a7f45c89a84eed
        """
        return uuid.uuid1().hex


class BaseBackBone(models.Model):
    """model docstring"""
    #id = models.CharField(primary_key=True,max_length=199, default=uuid.uuid5(uuid.NAMESPACE_DNS,'kaizhi'),unique=True,editable=True)
    id =  models.CharField(primary_key=True,max_length=199, default=uuid.uuid4, editable=True)

    class Meta:
        abstract = True



class AuthCode(models.Model):
    TYPE = ((1, '注册'), (2, '忘记密码'))

    phone = models.CharField('手机号', max_length=19)
    auth_code = models.CharField('验证码', max_length=10)
    fail_time = models.DateTimeField('失效时间')
    type = models.SmallIntegerField('验证类型', choices=TYPE, default=1)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return self.phone

    class Meta:
        ordering = ['-create_time']
        verbose_name = '手机验证码信息'
        verbose_name_plural = '手机验证码列表'


class Banner(BaseBackBone):

    img = models.CharField('图片', max_length=19)
    url = models.CharField('链接地址', max_length=10)
    create_time = models.DateTimeField('创建时间', auto_now_add=True,null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ['-create_time']
        verbose_name = '轮播图'
        verbose_name_plural = '课程轮播图信息表'


class UserProfile(BaseBackBone):
    ROLE=((0,'普通用户'),(1,'管理员'),(2,'教师'),(3,'协作者'))
    SEX=((0,'女'),(1,'男'))
    TYPE = ((1, '网站用户'), (2, '小程序用户'))

    user = models.OneToOneField(User,verbose_name='用户信息',related_name='u_user',on_delete=models.CASCADE)
    phone = models.CharField('手机号', unique=True, max_length=19)
    username = models.CharField('用户名', max_length=59,unique=True, blank=True, null=True)
    nickname = models.CharField('昵称', max_length=59, blank=True, null=True)
    head_img = models.TextField('头像',blank=True,null=True)
    role = models.SmallIntegerField('角色',choices=ROLE, default=0)
    token = models.CharField('token',max_length=199,blank=True,null=True)
#    sex = models.SmallIntegerField('性别',choices=SEX,default=0)
    openid = models.CharField("微信OPENID", max_length=256,blank=True,null=True)
    unionid = models.CharField("微信UNIONID", max_length=128,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    type = models.SmallIntegerField('验证类型', choices=TYPE, default=1,blank=True,null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)

    def __str__(self):
        return '{0}'.format(self.username)

    def user_head_img(self):
        return format_html('<img src="{}" style="height:45px;"/>',self.head_img)
    user_head_img.short_description = '用户头像'
    user_head_img.allow_tags = True

    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户信息'
        verbose_name_plural = '用户列表'


class Course(BaseBackBone):
    IS_FEE=((0,'免费'),(1,'收费'))
    IS_DISCUSS=((0,'不讨论'),(1,'讨论'))
    IS_HOMEWORK=((0,'否'),(1,'是'))
    IS_GRADUATE=((0,'未结业'),(1,'已结业'))


    cover = models.CharField('课程封面',max_length=199,blank=True)
    title = models.CharField('标题',max_length=199,blank=True,null=True)
    subtitle = models.CharField('副标题',max_length=199,blank=True,null=True)
    issue = models.IntegerField('期数',blank=True,null=True)
    description = models.TextField('课程描述',max_length=1000,blank=True,null=True)
    is_fee = models.SmallIntegerField('是否收费',choices=IS_FEE,default=1)
    price = models.CharField('费用',max_length=199,blank=True,null=True)
    price_url = models.CharField('收费链接',max_length=199,blank=True,null=True)
    create_user = models.ForeignKey(UserProfile,verbose_name='创建用户',related_name='c_user',on_delete=models.CASCADE)
    is_discuss = models.SmallIntegerField('是否讨论',choices=IS_DISCUSS,default=1)
    is_homework = models.SmallIntegerField('是否作业',choices=IS_HOMEWORK,default=0)
    sign = models.CharField('标记',max_length=199,blank=True,null=True)
    short_url = models.CharField('短连接',max_length=199,blank=True,null=True)
    is_graduate = models.SmallIntegerField('是否结业',choices=IS_GRADUATE,default=0)
    host = models.CharField('讲师',max_length=199,blank=True,null=True)
    classify = models.CharField('分类',max_length=199,blank=True,null=True)
    start_time = models.CharField('开始时间', max_length=199,blank=True,null=True)
    end_time = models.CharField('结束时间', max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '课程表'
        verbose_name_plural = '课程表'

    def __str__(self):
         return '{0}'.format(self.title)

    def course_cover(self):
        return format_html('<img src="{}" style="height:45px;"/>',self.cover)
    course_cover.short_description = '课程封面'
    course_cover.allow_tags = True


class User_Buy_Record(BaseBackBone):
    STATUS=((0,'未付款'),(1,'已付款'))

    user = models.ForeignKey(UserProfile,verbose_name='购买用户',related_name='buy_user',on_delete=models.CASCADE)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='buy_course',on_delete=models.CASCADE)
    price = models.CharField('价格',max_length=199,blank=True,null=True)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)

    def __str__(self):
        return '{0},{1}'.format(self.user,self.course)

    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户购买课程信息'
        verbose_name_plural = '用户购买课程信息表'


class Master_Package(BaseBackBone):
    ROLE = ((0,'创建者'),(1,'协作者'))
    TYPE = ((0,'个人'),(1,'组织'))
    P_TYPE = ((0,'课程'),(1,'作业'),(2,'讨论'))
    ONLINE = ((0,'未上线'),(1,'上线'))

    create_user = models.ForeignKey(UserProfile,verbose_name='创建用户',related_name='master_user',on_delete=models.CASCADE)
    create_type = models.IntegerField('创建类型',choices=TYPE,default=0)
    p_type = models.IntegerField('卡包类型',choices=P_TYPE,default=0)
    role = models.IntegerField('角色',choices=ROLE,default=0)
    package_name = models.CharField('卡包名称',max_length=199,blank=True,null=True)
    package_location = models.CharField('卡包位置',max_length=199,blank=True,null=True)
    branch = models.CharField('分支名称',max_length=199,default='master',blank=True,null=True)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='master_course',on_delete=models.SET_NULL,blank=True,null=True)
    fork = models.CharField('分支来源',max_length=199,blank=True,null=True)
    key = models.CharField('key',max_length=1000,blank=True,null=True)
    aid = models.CharField('aid',max_length=1000,blank=True,null=True)
    title = models.TextField('标题',max_length=199,blank=True,null=True)
    desc = models.TextField('卡包描述',max_length=199,blank=True,null=True)
    sign = models.CharField('标记',max_length=199,blank=True,null=True)
    online = models.SmallIntegerField('是否上线',choices=ONLINE,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    def __str__(self):
         return '{0},{1}'.format(self.id,self.package_name)


    class Meta:
        ordering = ['package_name']
        verbose_name = 'master卡包表'
        verbose_name_plural = 'master卡包表'


class Branch_Package(BaseBackBone):
    ROLE = ((0,'创建者'),(1,'协作者'))
    TYPE = ((0,'个人'),(1,'组织'))
    P_TYPE = ((0,'课程'),(1,'作业'),(2,'讨论'))
    ONLINE = ((0,'未上线'),(1,'上线'))

    create_user = models.ForeignKey(UserProfile,verbose_name='创建用户',related_name='branch_user',on_delete=models.CASCADE)
    create_type = models.IntegerField('创建类型',choices=TYPE,default=0)
    p_type = models.IntegerField('卡包类型',choices=P_TYPE,default=0)
    role = models.IntegerField('角色',choices=ROLE,default=0)
    package_name = models.CharField('卡包名称',max_length=199,blank=True,null=True)
    package_location = models.CharField('卡包位置',max_length=199,blank=True,null=True)
    branch = models.CharField('分支名称',max_length=199,blank=True,null=True)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='branch_course',on_delete=models.SET_NULL,blank=True,null=True)
    fork = models.CharField('分支来源',max_length=199,blank=True,null=True)
    key = models.CharField('key',max_length=1000,blank=True,null=True)
    aid = models.CharField('aid',max_length=1000,blank=True,null=True)
    title = models.TextField('标题',max_length=199,blank=True,null=True)
    desc = models.TextField('卡包描述',max_length=199,blank=True,null=True)
    sign = models.CharField('标记',max_length=199,blank=True,null=True)
    online = models.SmallIntegerField('是否上线',choices=ONLINE,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    def __str__(self):
         return '{0},{1}'.format(self.id,self.package_name)


    class Meta:
        ordering = ['package_name']
        verbose_name = 'Branch卡包表'
        verbose_name_plural = 'Branch卡包表'


class User_Branch(BaseBackBone):

    user = models.ForeignKey(UserProfile,verbose_name='协作用户',related_name='ub_user',on_delete=models.CASCADE)
    create_package = models.ForeignKey(Master_Package,verbose_name='创建卡包',related_name='crete_pac',on_delete=models.CASCADE,blank=True,null=True)
    assi_package = models.ForeignKey(Branch_Package,verbose_name='协作卡包',related_name='assi_pac',on_delete=models.CASCADE,blank=True,null=True)
    branch = models.CharField('分支',max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    def __str__(self):
        return '{0},{1},{2}'.format(self.create_package,self.user,self.assi_package)

    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户分支'
        verbose_name_plural = '用户分支信息表'


class Package_Auth_Info(BaseBackBone):
    USER_TYPE = ((0,'个人'),(1,'组织'))
    AUTH = ((0,'只读'),(1,'协作'),(2,'共同拥有'))

    user = models.ForeignKey(UserProfile,verbose_name='用户',related_name='pai_user',on_delete=models.SET_NULL,blank=True,null=True)
    user_type = models.SmallIntegerField('用户类型',choices=USER_TYPE,default=0)
    auth = models.SmallIntegerField('权限',choices=AUTH,default=0)
    package = models.ForeignKey(Branch_Package,verbose_name='卡包',related_name='p_package',on_delete=models.SET_NULL,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '卡包权限表'
        verbose_name_plural = '卡包权限表'


class Card(BaseBackBone):
    TAGS = ((0,'文本'),(1,'视频'),(2,'测试'),(3,'讨论'),(4,'答案'))
    C_TYPE = ((0,'文件夹'),(1,'文件'))
    STATUS = ((0,'无'),(1,'关闭'))

    card_location = models.CharField('卡片位置',max_length=199,blank=True,null=True)
    package_id = models.CharField('卡包id',max_length=199,blank=True,null=True)
    branch = models.CharField('分支',max_length=199,blank=True,null=True)
    package_location = models.CharField('卡包位置',max_length=199,blank=True,null=True)
    file_name = models.CharField('文件名称',max_length=199,blank=True,null=True)
    tags = models.SmallIntegerField('标签',choices=TAGS,default=0)
    c_type = models.SmallIntegerField('类型',choices=C_TYPE,default=0)
    create_user = models.ForeignKey(UserProfile,verbose_name='创建用户',related_name='card_user',on_delete=models.CASCADE)
    content = models.TextField('文件内容',max_length=1000,blank=True,null=True)
    count = models.IntegerField('评论次数',default=0,blank=True,null=True)
    reset_count = models.IntegerField('撤销次数',default=0,blank=True,null=True)
    modify_count = models.IntegerField('修改次数',default=1,blank=True,null=True)
    commit_count = models.IntegerField('提交次数',default=0,blank=True,null=True)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    index = models.SmallIntegerField('index',default=-1,blank=True,null=True)
    pid = models.CharField('pid',max_length=1000,blank=True,null=True)
    aid = models.CharField('aid',max_length=1000,blank=True,null=True)
    reply_time = models.DateTimeField('回复时间', blank=True, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['file_name']
        verbose_name = '卡片表'
        verbose_name_plural = '卡片表'

    def __str__(self):
        return '{0},{1},{2},{3}'.format(self.id,self.file_name,self.c_type,self.package_id)

    def save(self, *args, **kwargs):
        if not self.reply_time:
            self.reply_time = '2011-11-11 11:11:11' 
        super(Card,self).save(*args, **kwargs)

         
class User_Study_Record(BaseBackBone):
    IS_STUDY = ((0,'未学习'),(1,'已学习'))


    card = models.ForeignKey(Card,verbose_name='卡片',related_name='study_record',on_delete=models.SET_NULL,blank=True,null=True)
    package = models.ForeignKey(Master_Package,verbose_name='卡包',related_name='pst_record',on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile,verbose_name='用户',related_name='user_st_card',on_delete=models.CASCADE)
    is_study = models.SmallIntegerField('状态',choices=IS_STUDY,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户学习记录表'
        verbose_name_plural = '用户学习记录表'

    def __str__(self):
        return '{0},{1}'.format(self.card,self.package)


class User_Course_Record(BaseBackBone):


    user = models.ForeignKey(UserProfile,verbose_name='用户',related_name='user_course',on_delete=models.SET_NULL,blank=True,null=True)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='course_record',on_delete=models.CASCADE)
    progress = models.CharField('学习进度',max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户学习课程记录表'
        verbose_name_plural = '用户学习课程记录表'

    def __str__(self):
        return '{0},{1}'.format(self.course,self.user)


class User_Hw_Record(BaseBackBone):
    IS_FINISH = ((0,'未完成'),(1,'已完成'))


    card = models.ForeignKey(Card,verbose_name='卡片',related_name='hw_record',on_delete=models.SET_NULL,blank=True,null=True)
    aw_card = models.ForeignKey(Card,verbose_name='答案卡片',related_name='hw_card',on_delete=models.SET_NULL,blank=True,null=True)
    package = models.ForeignKey(Master_Package,verbose_name='卡包',related_name='phw_record',on_delete=models.SET_NULL,blank=True,null=True)
    user = models.ForeignKey(UserProfile,verbose_name='用户',related_name='user_hw_record',on_delete=models.SET_NULL,blank=True,null=True)
    is_finish = models.SmallIntegerField('状态',choices=IS_FINISH,default=0)
    answer = models.TextField('答案',max_length=1000,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户作业记录表'
        verbose_name_plural = '用户作业记录表'

    def __str__(self):
        return '{0},{1}'.format(self.card,self.package)



class Card_Action(BaseBackBone):
    IS_FAVOR=((0,'无'),(1,'是'))
    IS_LIKE=((0,'无'),(1,'是'))
    IS_STUDY = ((0,'未学习'),(1,'已学习'))
    IS_FINISH = ((0,'未学习'),(1,'已学习'))

    card = models.ForeignKey(Card,verbose_name='卡片',related_name='card_ac',on_delete=models.CASCADE,blank=True,null=True)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='action_course',on_delete=models.SET_NULL,blank=True,null=True)
    user = models.ForeignKey(UserProfile,verbose_name='评论用户',related_name='ac_user',on_delete=models.CASCADE)
    is_favor = models.IntegerField('是否收藏',choices=IS_FAVOR,default=0)
    is_like = models.IntegerField('是否点赞',choices=IS_LIKE,default=0)
    is_study = models.SmallIntegerField('是否学习',choices=IS_STUDY,default=0)
    is_finish = models.SmallIntegerField('是否完成',choices=IS_FINISH,default=0)
    view_count = models.IntegerField('浏览次数',default=0)
    score = models.IntegerField('评分',choices=IS_LIKE,default=0)
    view_duration = models.CharField('最后一次时间',max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '卡片动态表'
        verbose_name_plural = '卡片动态表'

    def __str__(self):
        return '{0},{1}'.format(self.card,self.user)


class User_Package_Record(BaseBackBone):
    STATUS = ((0,'未学习'),(1,'已学习'))


    package = models.ForeignKey(Master_Package,verbose_name='卡包',related_name='p_record',on_delete=models.SET_NULL,blank=True,null=True)
    card = models.ForeignKey(Card,verbose_name='卡片',related_name='ca_record',on_delete=models.SET_NULL,blank=True,null=True)
    course = models.ForeignKey(Course,verbose_name='课程',related_name='p_c_record',on_delete=models.SET_NULL,blank=True,null=True)
    user = models.ForeignKey(UserProfile,verbose_name='用户',related_name='user_record_package',on_delete=models.SET_NULL,blank=True,null=True)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '用户卡包记录表'
        verbose_name_plural = '用户卡包记录表'

    def __str__(self):
        return '{0},{1},{2}'.format(self.user,self.package,self.card)


class Card_Comment(BaseBackBone):
    STATUS=((0,'无'),(1,'关闭'),(2,'删除'))

    card = models.ForeignKey(Card,verbose_name='卡片',related_name='card_comment',on_delete=models.CASCADE,blank=True,null=True)
    package = models.ForeignKey(Master_Package,verbose_name='卡包',related_name='comment_package',on_delete=models.SET_NULL,blank=True,null=True)
    user = models.ForeignKey(UserProfile,verbose_name='评论用户',related_name='comment_user',on_delete=models.CASCADE,blank=True,null=True)
    to_user = models.ForeignKey(UserProfile,verbose_name='@用户',related_name='to_user',on_delete=models.SET_NULL,blank=True,null=True)
    content = models.TextField('评论内容',max_length=199,blank=True,null=True)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '卡片评论表'
        verbose_name_plural = '卡片评论表'

    def __str__(self):
        return '{0}'.format(self.card)


class Card_Collect(BaseBackBone):
    STATUS=((0,'无'),(1,'收藏'))

    card = models.ForeignKey(Card,verbose_name='卡片收藏',related_name='cc_card',on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile,verbose_name='收藏用户',related_name='cc_user',on_delete=models.CASCADE)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '课程收藏表'
        verbose_name_plural = '课程收藏表'


class System_Message(BaseBackBone):
    STATUS=((0,'未读'),(1,'已读'))
    APPLY_STATUS=((0,'无'),(1,'同意'),(2,'拒绝'))
    IS_APPLY=((0,'未申请'),(1,'已申请'))
    IS_SOLVE=((0,'无'),(1,'未解决'),(2,'已解决'))
    TYPE = ((0, '系统通知'), (1, '合并通知'),(2,'评论通知'))

    user = models.ForeignKey(UserProfile,verbose_name='发送用户',related_name='msg_user',on_delete=models.CASCADE)
    to_user = models.ForeignKey(UserProfile,verbose_name='接收用户',related_name='msg_to_user',on_delete=models.CASCADE,blank=True,null=True)
    message = models.TextField('消息',max_length=1000,blank=True,null=True)
    content = models.TextField('内容',max_length=1000,blank=True,null=True)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    apply_status = models.SmallIntegerField('申请状态',choices=APPLY_STATUS,default=0)
    is_apply = models.SmallIntegerField('是否申请',choices=IS_APPLY,default=0)
    is_solve = models.SmallIntegerField('是否解决冲突',choices=IS_SOLVE,default=0)
    key = models.CharField('协作卡包id',max_length=199,blank=True,null=True)
    card_url = models.CharField('卡片链接',max_length=199,blank=True,null=True)
    card_id = models.CharField('卡片id',max_length=199,blank=True,null=True)
    course_id = models.CharField('课程id',max_length=199,blank=True,null=True)
    card_tags = models.CharField('卡片类型',max_length=199,blank=True,null=True)
    to_userid = models.CharField('对方用户id',max_length=199,blank=True,null=True)
    location = models.CharField('卡包位置',max_length=199,blank=True,null=True)
    type = models.SmallIntegerField('通知类型', choices=TYPE, default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '系统通知表'
        verbose_name_plural = '系统通知信息表'

    def __str__(self):
        return '{0},{1},{2}'.format(self.id,self.user,self.key)


class Message_Status(BaseBackBone):
    STATUS=((0,'已读'),(1,'未读'))

    message = models.ForeignKey(System_Message,verbose_name='系统消息',related_name='sy_mess',on_delete=models.CASCADE)
    status = models.SmallIntegerField('状态',choices=STATUS,default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '消息状态表'
        verbose_name_plural = '消息状态表'


class Merge_Branch_Record(BaseBackBone):

    create_user = models.ForeignKey(UserProfile,verbose_name='创建用户',related_name='mb_user',on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile,verbose_name='提交用户',related_name='commit_user',on_delete=models.CASCADE)
    package = models.ForeignKey(Master_Package,verbose_name='卡包',related_name='mb_package',on_delete=models.CASCADE)
    branch = models.CharField('分支',max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)

    class Meta:
        ordering = ['-create_time']
        verbose_name = '分支合并记录表'
        verbose_name_plural = '分支合并记录表'


class Short_Url(models.Model):

    card = models.ForeignKey(Card,verbose_name='视频卡片',related_name='card_url',on_delete=models.CASCADE)
    long_url = models.CharField('长链接',max_length=199,blank=True,null=True)
    short_code = models.CharField('短码',max_length=199,blank=True,null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True, null=True)
    update_time = models.DateTimeField('更新时间', auto_now=True,null=True)


    class Meta:
        ordering = ['-create_time']
        verbose_name = '视频链接'
        verbose_name_plural = '视频链接信息表'
