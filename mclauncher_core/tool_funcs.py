import subprocess as s
import platform
import os
import sys

def get_file_path() -> str:
    """获取当前Python文件路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable).replace('\\', '/') # EXE
    return str(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')) # .py

def get_system_bits() -> str:
    """ 获取系统位数('32','64')"""
    return platform.architecture()[0][:2]

def get_java_version(java_binary_path='java') -> list:
    """执行java -version并获得返回值，格式为[8, '1.8.0_452']或[21, "21.0.7"]等，返回list"""
    try: # need fix
        p = s.Popen([java_binary_path, '-version'], stdout=s.PIPE, stderr=s.PIPE)
        stdout, stderr = p.communicate()
        ver_full = stderr.decode().split('\n')
        if ver_full[-1] == '':
            ver_full = ver_full[:-1]
        ver_full = ver_full[-3].split(' version ')[1][1:-1]
        # 行类似 'openjdk version "1.8.0_462"'
        if ver_full.split('.')[0] == '1':
            major_version = ver_full.split(".")[1]
        else:
            major_version = ver_full.split('.')[0]

        return [major_version, ver_full]
    except:
        return [0,""]

def native():
    """返回当前操作系统类型"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        return 'linux'