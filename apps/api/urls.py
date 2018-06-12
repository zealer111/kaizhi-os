#coding:utf-8
from django.conf.urls import url

from .views import teacher,views,xcx,basic,auth_code

from .youzan import youzan

#base
urlpatterns = [
    url('^login', basic.Login.as_view()),
    url('^logout', basic.Logout.as_view()),
    url('^register', basic.Register.as_view()),
    url('^user_upd_password', basic.User_Upd_Password.as_view()),
    url('^upd_head_img', basic.Upd_Head_Img.as_view()),
    url('^user_set_new_password', basic.User_Set_New_Password.as_view()),
    url('^upd_user_info', basic.Upd_User_Info.as_view()),
    url('^get_auth_code', auth_code.Get_Auth_Code.as_view()),
    url('^create_course', views.Create_Course.as_view()),
    url('^delete_course', views.Delete_Course.as_view()),
    url('^modify_course', views.Modify_Course.as_view()),
    url('^create_package', views.Create_Package.as_view()),
    url('^get_course', views.Get_Course.as_view()),
    url('^get_user_answer', views.Get_User_Answer.as_view()),
    url('^course_search', views.Course_Search.as_view()),
    url('^search_my_create_course', views.Search_My_Create_Course.as_view()),
    url('^discuss_card_search', views.Discuss_Card_Search.as_view()),
    url('^discuss_file_detail', views.Discuss_File_Detail.as_view()),
    url('^upload_file', views.Upload_File.as_view()),
    url('^teacher_package$', views.Teacher_Package.as_view()),
    url('^card_comments$', views.Card_Comments.as_view()),
    url('^create_file', views.Create_File.as_view()),
    url('^create_discuss_file', views.Create_Discuss_File.as_view()),
    url('^get_file', views.Get_File.as_view()),
    url('^card_sort', views.Card_Sort.as_view()),
    url('^my_assistant', views.My_Assistant.as_view()),
    url('^my_create_course', views.My_Create_Course.as_view()),
    url('^my_course', views.My_Course.as_view()),
    url('^my_study_record', views.My_Study_Record.as_view()),
    url('^my_collect', views.My_Collect.as_view()),
    url('^my_create_card_search', views.My_Create_Card_Search.as_view()),
    url('^course_detail', views.Course_Detail.as_view()),
    url('^course_dir', views.Course_Dir.as_view()),
    url('^delete_package', views.Delete_Package.as_view()),
    url('^delete_file', views.Delete_File.as_view()),
    url('^rename_package', views.Rename_Package.as_view()),
    url('^rename_file', views.Rename_File.as_view()),
    url('^modify_file', views.Modify_File.as_view()),
    url('^modify_discuss_file', views.Modify_Discuss_File.as_view()),
    url('^batch_modify_file', views.Batch_Modify_File.as_view()),
    # 教学中心
    url('^copy_file', teacher.Copy_File.as_view()),
    url('^commit_hw', views.Commit_Hw.as_view()),
    url('^colse_discuss', views.Colse_Discuss.as_view()),
    url('^delete_card_comment', views.Delete_Card_Comment.as_view()),
    url('^comment_detail', views.Comment_Detail.as_view()),
    url('^qiniu_token', views.Qiniu_Token.as_view()),
    url('^card_collect', views.Card_Collect.as_view()),
    url('^card_search', views.Card_Search.as_view()),
    url('^cancel_collect', views.Cancel_Collect.as_view()),
    url('^upload_zip', views.Upload_Zip.as_view()),
    url('^file_diff', views.File_Diff.as_view()),
    url('^homework_page', views.Homework_Page.as_view()),
    url('^discuss_page', views.Discuss_Page.as_view()),
    url('^comment_page', views.Comment_Page.as_view()),
    url('^all_close_discuss', views.All_Close_Discuss.as_view()),
    url('^modify_hw', views.Modify_Hw.as_view()),
    url('^merge_branch', views.Merge_Branch.as_view()),
    url('^merge_master', views.Merge_Master.as_view()),
    url('^apply_merge_branch', views.Apply_Merge_Branch.as_view()),
    url('^refuse_merge_branch', views.Refuse_Merge_Branch.as_view()),
    url('^my_message', views.My_Message.as_view()),
    url('^check_message', views.Check_Message.as_view()),
    url('^recover_file', views.Recover_File.as_view()),
    url('^delete_some_file', views.Delete_Some_File.as_view()),
    url('^banners', views.Banners.as_view()),
    url('^test', views.Test.as_view()),
]

urlpatterns +=[
    url('^youzan/callback', youzan.Get_Order.as_view()),
    url('^my_buy_course_info', youzan.My_Buy_Course_Info.as_view()),
    url('^user_apply_course', youzan.User_Apply_Course.as_view()),
    url('^buy_course_info', youzan.Buy_Course_Info.as_view()),
    url('^msg', auth_code.Msg.as_view()),
]

# 小程序API
urlpatterns +=[
    url('^xcx/auth-code', xcx.AuthCode.as_view()),#获取验证码
    url('^xcx/auth-phone', xcx.AuthPhone.as_view()),#根据验证码验证手机号
    url('^xcx/set-password', xcx.SetPassword.as_view()),#设置密码
    url('^xcx/courses-list', xcx.CoursesList.as_view()),#课程列表
    url('^xcx/course-detail', xcx.CourseDetail.as_view()),#课程详情
    url('^xcx/messages', xcx.Messages.as_view()),#消息中心
    url('^xcx/my-colloections', xcx.MyCollections.as_view()),#我的收藏
    url('^xcx/course-list', xcx.CourseList.as_view()),#课程列表目录
    url('^xcx/card-detail', xcx.CardDetail.as_view()),#卡片详情
    url('^xcx/collect-card', xcx.CollectCard.as_view()), #收藏卡片
    url('^xcx/get-ordernum', xcx.GetOrderNum.as_view()), #获取购买课程订单号
    url('^xcx/get-payinfo', xcx.GetPayInfo.as_view()), #获取付款信息
    url('^xcx/get-payresult', xcx.GetPayResult.as_view()), #获取付款结果信息
]
