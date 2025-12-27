import shutil, os
import requests, json, shutil, zipfile as zipf
from mclauncher_core.manifest_funcs import get_version_json
from mclauncher_core.tool_funcs import *


def get_all_forgeable_versions():
    """获取Forge支持的所有Minecraft版本"""
    url = 'https://bmclapi2.bangbang93.com/forge/minecraft'
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    return item.json()


def get_forge_version(version):
    """获取支持此Minecraft版本的Forge"""
    url = 'https://bmclapi2.bangbang93.com/forge/minecraft/' + version
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    return item.json()


def download_forge_json(minecraft_dir, version, version_name, forge_version='latest', bmclapi=False, java='java'):
    """下载一个包含了Forge的东西的版本json，附赠一份forge client jar于Libraries(其实无非就是调用安装器罢了)"""
    if forge_version == 'latest':
        forge_versions = get_forge_version(version)
        versions = []
        for ver in forge_versions:
            versions.append(ver["version"])
        forge_version = versions[0]

    # url = 'https://bmclapi2.bangbang93.com/forge/download'
    # url = url + f'?mcversion={version}&version={forge_version}&category=installer&format=jar'
    url = f'https://maven.minecraftforge.net/net/minecraftforge/forge/{version}-{forge_version}/forge-{version}-{forge_version}-installer.jar'
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    os.makedirs(get_file_path() + "/temp", exist_ok=True)
    with open(get_file_path() + "/temp/forge_installer.jar",
              'wb') as f:
        f.write(item.content)
    
    cmd = f'{java} -jar "{get_file_path() + "/temp/forge_installer.jar"}" --installClient {minecraft_dir}'
    os.system(cmd)
    installer_version_name = f'{version}-forge-{forge_version}'
    shutil.move(os.path.join(minecraft_dir, 'versions', installer_version_name),
                os.path.join(minecraft_dir, 'versions', version_name))
    shutil.move(os.path.join(minecraft_dir, 'versions', version_name, installer_version_name + '.json'),
                os.path.join(minecraft_dir, 'versions', version_name, version_name + '.json'))


    # if not os.path.exists(get_file_path() + "/temp/forge_installer/install_profile.json"):
    #     shutil.rmtree(get_file_path() + "/temp/forge_installer/")
    #     raise Exception("INSTALL_PROFILE.JSON not found")
    # with open(get_file_path() + "/temp/forge_installer/install_profile.json", 'r') as f:
    #     install_profile = json.loads(f.read())

    # if 'versionInfo' in install_profile:
    forge_version_json_path = os.path.join(minecraft_dir, 'versions', version_name, version_name + '.json')
    with open(forge_version_json_path, 'r') as f:
        forge_version_json = json.load(f)
    version_json = get_version_json(version, bmclapi)

    # 深度合并：保留两边的条目（非重复），并对子字典递归合并
    def deep_merge(a, b):
        if isinstance(a, dict) and isinstance(b, dict):
            out = dict(a)
            for k, v in b.items():
                if k in out:
                    out[k] = deep_merge(out[k], v)
                else:
                    out[k] = v
            return out
        if isinstance(a, list) and isinstance(b, list):
            merged = []
            seen = set()
            # 以 b（来自 Forge 的条目）先加入，保持 Forge 条目靠前
            for item in b:
                merged.append(item)
                if isinstance(item, dict) and 'name' in item:
                    seen.add(item['name'])
                else:
                    seen.add(json.dumps(item, sort_keys=True))
            for item in a:
                key = item['name'] if isinstance(item, dict) and 'name' in item else json.dumps(item, sort_keys=True)
                if key in seen:
                    # 如果是字典并且已存在，递归合并
                    if isinstance(item, dict):
                        for idx, ex in enumerate(merged):
                            if isinstance(ex, dict) and ex.get('name') == key:
                                merged[idx] = deep_merge(ex, item)
                                break
                    continue
                merged.append(item)
                seen.add(key)
            return merged
        # 对于标量或类型不匹配，优先保留 a（原版数据）以避免覆盖已存在设置
        return a if a is not None else b

    merged_json = deep_merge(forge_version_json, version_json)
    # 确保 libraries 字段使用专门的合并策略以去重并保留两边的条目
    merged_json['libraries'] = deep_merge(version_json.get('libraries', []), forge_version_json.get('libraries', []))

    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'w') as f:
        f.write(json.dumps(merged_json))

    # processors(install_profile, get_file_path() + "/temp", os.path.join(minecraft_dir, 'versions', version_name))
    clean_temp()

def clean_temp():
    """清理临时文件"""
    shutil.rmtree(get_file_path() + "/temp")

