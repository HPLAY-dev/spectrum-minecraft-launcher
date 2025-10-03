# https://mirrors.tuna.tsinghua.edu.cn/Adoptium/21/jre/x64/windows/
# https://mirrors.tuna.tsinghua.edu.cn/Adoptium/21/jre/x64/windows/OpenJDK21U-jre_x64_windows_hotspot_21.0.8_9.msi
import requests
import platform
import os


java_major_versions = ['8',
                       '17',
                       '21']
java_types = ['jre',
              'jdk']
platforms = ['alpine-linux',
             'linux',
             'macos',
             'windows']
file_types = [
    '.msi',
    '.zip',
    '.tar.gz'
]

def get_arch():
    arch = platform.machine().lower()
    replacer = {
        'amd64': 'x64'
    }
    for i in replacer:
        arch = arch.replace(i, replacer[i])
    return arch

def get_url(java_major_version: int, java_type, arch=get_arch(), platform=platform.system().lower(), file_type='.msi', tuna=False):
    """获取Java(Adoptium)的tuna源最新下载地址"""
    java_major_version = str(java_major_version)
    # check format for args
    if not java_major_version in java_major_versions:
        raise SyntaxError('java_major_version')
    if not java_type in java_types:
        raise SyntaxError('java_type')
    if not platform in platforms:
        raise SyntaxError('platform')
    if not file_type in file_types:
        if '.'+file_type in file_types:
            file_type = '.'+file_type
        else:
            raise SyntaxError('file_type')
    if java_major_version == '8' and java_type == 'jre':
        raise SyntaxError('Only JDK for Java 8 is legal')

    # 利用github api从Adoptium github仓库获取最新java版本号
    gh_api_url = f'https://api.github.com/repos/adoptium/temurin{java_major_version}-binaries/releases/latest'
    api_result = requests.get(gh_api_url)
    if api_result.status_code != 200:
        raise Exception('Failed to get api result: '+str(api_result.status_code)+'\n'+gh_api_url)
    api_result = api_result.json()
    # 从Tuna下载
    if tuna:
        filename = ''
        for asset in api_result['assets']:
            if asset['name'].startswith(f'OpenJDK{java_major_version}U-{java_type}_{arch}_{platform}_hotspot') and asset['name'].endswith(f'{file_type}'):
                filename = asset['name']
        if filename == '':
            return None
        url = f"https://mirrors.tuna.tsinghua.edu.cn/Adoptium/{java_major_version}/{java_type}/{arch}/{platform}/{filename}"
        return url

    else:
        for asset in api_result['assets']:
            if asset['name'].startswith(f'OpenJDK{java_major_version}U-{java_type}_{arch}_{platform}_hotspot') and asset['name'].endswith(f'{file_type}'):
                return asset['browser_download_url']
        return None

def find_javas() -> list:
    javas = []
    for path in os.getenv("path").split(';'):
        try:
            if 'java.exe' in os.listdir(path):
                fpath = path.replace('\\', '/')
                if fpath[-1]=='/':
                    fpath = fpath[:-1]
                javas.append(fpath+'/java.exe')
        except:
            pass
    return javas

if __name__ == '__main__':
    print(get_arch())
    print(get_url(8, 'jdk'))