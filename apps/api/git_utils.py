from apps import settings
import requests


def create_git_package(package_name):
    data = {
      'branch':'master',
      'dirname':package_name
    }
    url = settings.GIT_REPO_URL
    r = requests.post(url,data=data)
    return r.json()

def delete_file(repo,branch,dir_name): 
    data = {
      'repo':repo,
      'branch':branch,
      'dir_name':dir_name
    }
    url = settings.GIT_DELETE_FILE
    r = requests.post(url,data=data)
    return r.json()

def delete_folder(repo,branch,dir_name): 
    data = {
      'repo':repo,
      'branch':branch,
      'dir_name':dir_name
    }
    url = settings.GIT_DELETE_FOLDER
    r = requests.post(url,data=data)
    return r.json()

def delete_package(repo): 
    data = {
      'repo':repo,
      'branch':'master',
    }
    url = settings.GIT_DELETE_REPO
    r = requests.post(url,data=data)
    return r.json()

def create_file(package_location,branch,path,content): 
    data = {
     'repo':package_location,
     'branch':branch,
     'dir_name':path,
     'file_content': content,
    }
    url = settings.GIT_FILE_URL
    r = requests.post(url,data = data)
    return r.json()

def create_dir(package_location,branch,path): 
    data = {
     'repo':package_location,
     'branch':branch,
     'dir_name':path,
    }
    url = settings.GIT_FILE_URL
    r = requests.post(url,data = data)
    return r.json()


def get_file_content(package_location,branch,path): 
    datas = {
        'repo':package_location,
        'branch':'master',
        'file_path':path
        }
    url = settings.GIT_FILE_CONTENT
    r = requests.post(url,data=datas)
    return r.json()


def modify_file(value,package_location,branch,path,content): 
    data = {
        'type':value,
        'repo':package_location,
        'branch':branch,
        'dir_name':path,
        'file_content':content
        }
    url = settings.GIT_MODIFY_FILE
    r = requests.post(url,data=data)
    return r.json()

def modify_discuss_file(package_location,branch,path,new_name,content): 
    data = {
        'repo':package_location,
        'branch':'master',
        'path':path,
        'new_name':new_name,
        'file_content':content
        }
    url = settings.GIT_DISCUSS_FILE
    r = requests.post(url,data=data)
    return r.json()

def commit_file(value,package_location,branch,merge_branch): 
    data = {
        'type':value,
        'repo':package_location,
        'branch':'master',
        'merge_branch':merge_branch
        }
    url = settings.GIT_COMMIT_FILE
    r = requests.post(url,data=data)
    return r.json()

def copy_file(value,package_location,file_dir,branch,path): 
    data = {
        'type':value,
        'repo':package_location,
        'file_dir':file_dir,
        'branch':branch,
        'dir_name':path
        }
    url = settings.GIT_COPY_FILE
    r = requests.post(url,data=data)
    return r.json()


def delete_branch(package_location,branch,del_branch): 
    data = {
        'repo':package_location,
        'branch':branch,
        'del_branch':del_branch
        }
    url = settings.GIT_DELETE_BRANCHE
    r = requests.post(url,data=data)
    return r.json()


def rename_file(value,package_location,branch,path,folder_dir,old_name,new_name): 
    data = {
        '_type':value,
        'repo':package_location,
        'branch':branch,
        'path':path,
        'folder':folder_dir,
        'old_name':old_name,
        'new_name':new_name,
        }
    url = settings.GIT_RENAME_FILE
    r = requests.post(url,data=data)
    return r.json()
