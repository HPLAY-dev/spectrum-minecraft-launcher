import subprocess as s
import platform
import os
import sys

def get_architecture_key():
    os_type = platform.system().lower()
    arch = get_architecture()
    return os_type + '-' + arch

def get_architecture():
    arch = platform.machine()
    replacer = {
        'amd64': 'x86_64',
        'i686': 'x86',
        'i386': 'x86',
        'aarch64': 'aarch_64',
        'armv8l': 'arm',
        'armv7l': 'arm',
        'armv7b': 'arm',
        'AMD64': 'x86_64',
        'ARM64': 'arm',
        'ARM': 'arm'
    }

    for r in replacer:
        if r == arch:
            arch = replacer[r]

    if native() != 'linux' and arch == 'aarch_64':
        arch = 'arm64'
    return arch
    ret

def get_file_path() -> str:
    """获取当前Python文件路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable).replace('\\', '/') # EXE
    return str(os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')) # .py

def get_system_bits() -> str:
    """ 获取系统位数('32','64')"""
    return platform.architecture()[0][:2]

def get_java_version(java_binary_path='java', detailed=False) -> list:
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

        if detailed:
            return ver_full
        else:
            return major_version
    except:
        return None

def native():
    """返回当前操作系统类型"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        return 'linux'

def maven_to_path(maven_str: str) -> str:
    """将maven坐标转换为路径。

    支持格式：
      - group:artifact:version
      - group:artifact:version:classifier
      - group:artifact:version@packaging
      - group:artifact:version:classifier@packaging

    返回示例：
      group/path/artifact/version/artifact-version[-classifier].packaging
    """
    packaging = 'jar'
    raw = maven_str
    # 支持 @packaging（例如 @zip）
    if '@' in raw:
        raw, packaging = raw.rsplit('@', 1)

    parts = raw.split(':')
    if len(parts) < 3:
        raise ValueError("Invalid Maven coordinate format. Expected at least 'groupId:artifactId:version'.")

    group_id = parts[0]
    artifact_id = parts[1]
    version = parts[2]
    classifier = parts[3] if len(parts) >= 4 and parts[3] else None

    group_path = group_id.replace('.', '/')

    filename = f"{artifact_id}-{version}"
    if classifier:
        filename += f"-{classifier}"
    filename += f".{packaging}"

    return f"{group_path}/{artifact_id}/{version}/{filename}"