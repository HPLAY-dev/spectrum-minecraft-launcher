import os, requests, json, shutil, zipfile as zipf
from mclauncher_core.tool_funcs import *
from mclauncher_core.manifest_funcs import get_version_json


def get_neoforge_version(mcversion) -> dict:
    """获取支持此Minecraft版本的Neoforge"""
    url = 'https://bmclapi2.bangbang93.com/neoforge/list/' + mcversion
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    return item.json()


def download_neoforge_json(minecraft_dir, mcversion, instance_name, neoforge_version='latest', bmclapi=False, java='java') -> None:
    """极度推荐使用BMCLAPI否则基本不可能成功下载！！！！！！"""
    if neoforge_version == 'latest':
        neoforge_version = get_neoforge_version(mcversion)[-1]
        path = neoforge_version['installerPath']
        path = '/'.join(path.split('/')[2:])
        url = 'https://maven.neoforged.net/' + path
    else:
        for i in get_neoforge_version(mcversion):
            if i['version'] == neoforge_version:
                path = i['installerPath']
        if path.split('/')[1] == 'maven':
            path = '/'.join(path.split('/')[2:])
        else:
            raise Exception("Format Unknown")
        url = 'https://maven.neoforged.net/' + path
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")

    os.makedirs(get_file_path() + "/temp", exist_ok=True)
    with open(get_file_path() + "/temp/neoforge_installer.zip",
              'wb') as f:
        f.write(item.content)

    if bmclapi:
        # repack installer with bmclapi maven url
        with zipf.ZipFile(get_file_path() + "/temp/neoforge_installer.zip", 'r') as file:
            file.extractall(get_file_path() + "/temp/neoforge_installer")
        
        profile_path = os.path.join(get_file_path(), "temp", "neoforge_installer", "install_profile.json")
        # Read, replace, and overwrite the profile file
        with open(profile_path, 'r', encoding='utf-8') as f:
            new_profile = f.read().replace("https://maven.neoforged.net/releases/", "https://bmclapi2.bangbang93.com/maven/")
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(new_profile)

        version_path = os.path.join(get_file_path(), "temp", "neoforge_installer", "version.json")
        with open(version_path, 'r', encoding='utf-8') as f:
            new_version = f.read().replace("https://maven.neoforged.net/releases/", "https://bmclapi2.bangbang93.com/maven/")
        with open(version_path, 'w', encoding='utf-8') as f:
            f.write(new_version)

        # Repack the modified installer directory into a jar file
        jar_path = os.path.join(get_file_path(), "temp", "neoforge_installer_fix.jar")
        root_dir = os.path.join(get_file_path(), "temp", "neoforge_installer")
        with zipf.ZipFile(jar_path, 'w', zipf.ZIP_DEFLATED) as jar:
            for root, dirs, files in os.walk(root_dir):
                for fname in files:
                    fullpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fullpath, root_dir)
                    jar.write(fullpath, arcname)
    else:
        jar_path = get_file_path() + "/temp/neoforge_installer.zip"

    cmd = f'{java} -jar "{jar_path}" --installClient {minecraft_dir}'
    os.system(cmd)

    version_name = 'neoforge-' + neoforge_version
    shutil.move(os.path.join(minecraft_dir, 'versions', version_name, version_name + '.json'),
                os.path.join(minecraft_dir, 'versions', version_name, instance_name + '.json'))
    shutil.move(os.path.join(minecraft_dir, 'versions', version_name),
                os.path.join(minecraft_dir, 'versions', instance_name))

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

    
    neoforge_version_json_path = os.path.join(minecraft_dir, 'versions', instance_name, instance_name + '.json')
    with open(neoforge_version_json_path, 'r') as f:
        neoforge_version_json = json.load(f)
    version_json = get_version_json(mcversion, bmclapi)
    
    merged_json = deep_merge(neoforge_version_json, version_json)
    # 确保 libraries 字段使用专门的合并策略以去重并保留两边的条目
    merged_json['libraries'] = deep_merge(version_json.get('libraries', []), neoforge_version_json.get('libraries', []))

    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'w') as f:
        f.write(json.dumps(merged_json))

    # processors(install_profile, get_file_path() + "/temp", os.path.join(minecraft_dir, 'versions', instance_name))
    clean_temp()

def clean_temp():
    """清理临时文件"""
    shutil.rmtree(get_file_path() + "/temp")
