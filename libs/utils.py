import os
import uuid
import hashlib

def get_package_hash_head(username):
    m5 = hashlib.md5()
    m5.update(username.encode())
    return m5.hexdigest()[-1]
    
    #return hash(username)%32

def get_package_repo(username, package_name):
    return os.path.join(str(get_package_hash_head(username)), username, str(uuid.uuid4()))


if __name__ == '__main__':
    print(get_package_repo("river", "hello"))
