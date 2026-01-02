DOWNLOAD_MANIFEST_USE_BMCLAPI = 0

import time

import threading

import requests, json, os
from mclauncher_core.launcher_funcs import get_version_manifest, get_assetIndex
from concurrent.futures import ThreadPoolExecutor, as_completed

from mclauncher_core.modloader_fabric import download_fabric_json, fabric_merge_json
from mclauncher_core.modloader_forge import download_forge_json
from mclauncher_core.modloader_neoforge import download_neoforge_json
from mclauncher_core.tool_funcs import *
import zipfile as zipf
import shutil


def get_version_list(show_snapshot=False, show_old=False, show_release=True, bmclapi=False) -> list:
    """获取minecraft版本列表，返回list"""

    def _download_manifest():
        if DOWNLOAD_MANIFEST_USE_BMCLAPI:
            url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
        else:
            url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        raw = requests.get(url)
        with open('version_manifest.temp', 'w') as f:
            f.write(raw.text)
        return raw.json()
    if os.path.exists('version_manifest.temp'):
        file_time = os.path.getmtime('version_manifest.temp')
        current_time = time.time()
        if current_time - file_time < 240:  # 240秒 = 4分钟
            with open('version_manifest.temp', 'r') as f:
                manifest = f.read()
            # 这里需要将文件内容转换为JSON对象
            try:
                manifest = json.loads(manifest)
            except:
                manifest = _download_manifest()
        else:
            manifest = _download_manifest()
    else:
        manifest = _download_manifest()
    returns = []
    for version in manifest['versions']:
        if version["type"] == "release" and not show_release:
            continue
        elif (version["type"] == "old_alpha" or version["type"] == "old_beta") and not show_old:
            continue
        elif version["type"] == "snapshot" and not show_snapshot:
            continue
        returns.append(version['id'])
    return returns

def get_version_json(mcversion, bmclapi=False) -> dict:
    """获取Minecraft为指定版本的json，返回dict"""
    manifest = get_version_manifest()
    if mcversion == "latest":
        mcversion = manifest["latest"]["release"]
    elif mcversion == "latest_snapshot":
        mcversion = manifest["latest"]["snapshot"]
    for current in manifest["versions"]:
        if current["id"] == mcversion:
            url = current["url"]

            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Request Fail: {response.status_code}\nurl: {url}")
            return response.json()

def download_version_json(minecraft_dir, mcversion, instance_name, bmclapi=False) -> None:
    """下载Minecraft为指定版本的json，返回None"""
    manifest = get_version_manifest()
    if mcversion == "latest":
        mcversion = manifest["latest"]["release"]
    elif mcversion == "latest_snapshot":
        mcversion = manifest["latest"]["snapshot"]
    for current in manifest["versions"]:
        if current["id"] == mcversion:
            os.makedirs(f'{minecraft_dir}/versions/{instance_name}', exist_ok=True)
            with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'wb') as f:
                url = current["url"]
                item = requests.get(url)
                if item.status_code != 200:
                    raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                f.write(item.content)

def download_jar(minecraft_dir, instance_name, bmclapi=False) -> None:
    """下载Minecraft为指定版本的jar，返回None"""
    if os.path.exists(f'{minecraft_dir}/{instance_name}/{instance_name}.jar'):
        return None
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    if not os.path.exists(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.jar'):
        with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.jar', 'wb') as f:
            url = version_json["downloads"]["client"]["url"]
            item = requests.get(url)
            if item.status_code != 200:
                raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
            f.write(item.content)

def download_libraries(minecraft_dir, mcversion, instance_name, print_status=True, bmclapi=False, progress_callback=None,
                       max_workers=5):
    """下载Minecraft为指定版本的libraries(库)，返回None"""
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        version_json = f.read()
    
    replacer = {
        'https://libraries.minecraft.net/': 'https://bmclapi2.bangbang93.com/maven/',
        'https://maven.neoforged.net/releases/': 'https://bmclapi2.bangbang93.com/maven/',
        'https://maven.minecraftforge.net/': 'https://bmclapi2.bangbang93.com/maven/',
        'https://files.minecraftforge.net/maven': 'https://bmclapi2.bangbang93.com/maven/',
        'https://meta.fabricmc.net': 'https://bmclapi2.bangbang93.com/fabric-meta',
        'https://launchermeta.mojang.com/': 'https://bmclapi2.bangbang93.com/',
        'https://launcher.mojang.com/': 'https://bmclapi2.bangbang93.com/',
        'http://resources.download.minecraft.net/': 'https://bmclapi2.bangbang93.com/assets/',
        'https://libraries.minecraft.net/': 'https://bmclapi2.bangbang93.com/maven',
        'http://dl.liteloader.com/versions/versions.json': 'https://bmclapi.bangbang93.com/maven/com/mumfrey/liteloader/versions.json',
        'https://authlib-injector.yushi.moe': 'https://bmclapi2.bangbang93.com/mirrors/authlib-injector',
        'https://maven.fabricmc.net/': 'https://bmclapi2.bangbang93.com/maven/',
    } # God bless BMCLAPI
    version_json = json.loads(version_json)
    file_amount = len(version_json["libraries"])
    current = 0

    # 创建线程池
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 准备所有下载任务
        future_to_lib = {}
        for lib in version_json["libraries"]:
            if not is_library_required(lib):
                continue

            # 提交任务到线程池
            future = executor.submit(
                download_single_library,
                minecraft_dir, instance_name, lib, bmclapi, print_status
            )
            future_to_lib[future] = lib

        # 处理完成的任务
        for future in as_completed(future_to_lib):
            lib = future_to_lib[future]
            current += 1
            if progress_callback:
                progress_callback(current, file_amount, f"[LIB][{current}/{file_amount}]")
            # result = future.result()
            # if print_status:
            #     print(f'{current}/{file_amount}\n- {lib.get("name", "Unknown")}: {result}')
            result = future.result()
            if print_status:
                print(f'{current}/{file_amount}\n- {lib.get("name", "Unknown")}: {result}')

            # try:
            #     result = future.result()
            #     if print_status:
            #         print(f'{current}/{file_amount}\n- {lib.get("name", "Unknown")}: {result}')
            # except Exception as e:
            #     print(f'下载失败: {lib.get("name", "Unknown")}, 错误: {str(e)}')

    natives_path = f'{minecraft_dir}/versions/{instance_name}/{instance_name}-natives'
    for root, dirs, files in os.walk(natives_path):
        for name in files:
            if name.endswith(('.dll', '.dylib', '.so')):
                dest = os.path.join(natives_path, name)
                if not os.path.exists(dest):
                    src = os.path.join(root, name)
                    shutil.copy(src, dest)
    try:
        shutil.rmtree(os.path.join(natives_path, native()))
        shutil.rmtree(os.path.join(natives_path, 'META-INF'))
    except:
        pass

def download_single_library(minecraft_dir, instance_name, lib, bmclapi, print_status):
    """下载单个库文件，返回None"""
    if not "downloads" in lib:  # Fallback
        return download_fallback_library(minecraft_dir, lib, bmclapi)
    else:
        return download_modern_library(minecraft_dir, instance_name, lib, bmclapi)


def download_fallback_library(minecraft_dir, lib, bmclapi):
    """处理旧版格式的库文件，返回None"""
    name = lib['name'].split(':')  # [org.ow2.asm,asm,9.8]
    name[0] = name[0].replace('.', '$SEP$')  # [org$SEP$ow2$SEP$asm,asm,9.8]
    filename = '-'.join(name[1:]) + '.jar'  # asm-9.8.jar
    name = "$SEP$".join(name)  # org$SEP$ow2$SEP$asm$SEP$asm$SEP$9.8
    path = name.replace("$SEP$", '/')  # org/ow2/asm/asm/9.8

    # # 仍然不知道如何下载qaq
    # if lib['name'].split(':')[0] == 'net.minecraftforge':
    #     filename = filename.replace('.jar', '-universal.jar')

    url = url_base + path + '/' + filename
    local_path = f'{minecraft_dir}/libraries/{path}'
    os.makedirs(local_path, exist_ok=True)
    file_path = local_path + '/' + filename

    if os.path.exists(file_path):
        return f"已存在: {file_path}"
    else:
        with open(file_path, 'wb') as f:
            item = requests.get(url)
            if item.status_code != 200:
                raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
            f.write(item.content)
        return f"下载成功: {url}"


def download_modern_library(minecraft_dir, instance_name, lib, bmclapi):
    """处理新版格式的库文件，返回None"""
    # 检查规则
    if not is_library_required(lib):
        return "跳过: 不符合规则"

    if_artifact = "downloads" in lib and "artifact" in lib["downloads"]
    if_natives = "natives" in lib
    if_natives_late_versions = if_artifact and f"natives-{native()}" in lib["name"].lower()

    if if_artifact:
        relative_path = lib["downloads"]["artifact"]["path"]
        url = lib["downloads"]["artifact"]["url"]

    elif 'classifiers' in lib['downloads']:
        if 'natives-' + get_architecture_key() in lib['downloads']['classifiers']:
            relative_path = lib['downloads']['classifiers']['natives-' + get_architecture_key()]['path']
            url = lib['downloads']['classifiers']['natives-' + get_architecture_key()]["url"]

        elif 'natives-' + native() + '-' + get_system_bits() in lib['downloads']['classifiers']:
            relative_path = lib['downloads']['classifiers']['natives-' + native() + '-' + get_system_bits()]['path']
            url = lib['downloads']['classifiers']['natives-' + native() + '-' + get_system_bits()]["url"]

        elif 'natives-' + native() in lib['downloads']['classifiers']:
            relative_path = lib['downloads']['classifiers']['natives-' + native()]['path']
            url = lib["downloads"]['classifiers']['natives-' + native()]['url']
    else:
        return 1
    
    print(url)

    path = f'{minecraft_dir}/libraries/{relative_path}'
    path = path.split('/')[:-1]
    path = '/'.join(path)
    os.makedirs(path, exist_ok=True)
    local_path = f'{minecraft_dir}/libraries/{relative_path}'

    if os.path.exists(local_path):
        if if_natives or if_natives_late_versions:
            download_native_library(minecraft_dir, instance_name, lib, if_natives_late_versions, url,
                                       bmclapi)
        return f"已存在: {local_path}"

    with open(f'{minecraft_dir}/libraries/{relative_path}', 'wb') as f:
        item = requests.get(url)
        f.write(item.content)


    if if_natives or if_natives_late_versions:
        return download_native_library(minecraft_dir, instance_name, lib, if_natives_late_versions, url,
                                       bmclapi)

    return "下载成功"

def download_native_library(minecraft_dir, instance_name, lib, if_natives_late_versions, url='',
                            bmclapi=False):
    """处理natives(原生)库文件，返回None"""
    if if_natives_late_versions:
        natives = []
    elif "classifiers" in lib["downloads"]:
        if "natives-" + native() in lib["downloads"]["classifiers"]:
            natives = lib["downloads"]["classifiers"]["natives-" + native()]
            url = natives['url']
        elif "natives-" + native() + '-' + get_system_bits() in lib["downloads"]["classifiers"]:
            natives = lib["downloads"]["classifiers"]["natives-" + native() + '-' + get_system_bits()]
            url = natives['url']
    else:
        return "无法找到原生库"

    natives_path = f'{minecraft_dir}/versions/{instance_name}/{instance_name}-natives'
    os.makedirs(natives_path, exist_ok=True)

    keep_going = True
    i = 0
    temp_zip = natives_path + f'/temp1.zip'
    while keep_going:
        i += 1
        temp_zip = natives_path + f'/temp{i}.zip'
        if not os.path.exists(temp_zip):
            keep_going = False

    # 下载临时zip文件
    with open(temp_zip, 'wb') as f:
        item = requests.get(url)
        if item.status_code != 200:
            raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
        f.write(item.content)

    # 解压文件到natives目录
    try:
        with zipf.ZipFile(temp_zip, 'r') as f:
            f.extractall(natives_path)
    except zipf.BadZipFile as e:
        1
        2
        4
    # 清理临时文件
    keep_remove = True
    while keep_remove:
        try:
            os.remove(temp_zip)
            keep_remove = False
        except PermissionError:
            keep_remove = True

    # 处理特定库文件（如lwjgl）
    if 'name' in lib and lib['name'].startswith('lwjgl'):
        # 查找并复制原生库文件
        for root, dirs, files in os.walk(natives_path):
            for file in files:
                if file.endswith(('.dll', '.dylib', '.so')):
                    src_path = os.path.join(root, file)
                    dest_path = os.path.join(natives_path, file)
                    if src_path != dest_path:
                        shutil.copy2(src_path, dest_path)

    return f"原生库处理完成: {url}"


def is_library_required(lib):
    """检查库是否是必需的，返回bool"""

    # 从rules判断
    if 'natives-' + native() in lib['name']:
        pass
    elif "rules" in lib:
        for rule in lib["rules"]:
            if rule["action"] == "allow":
                if "os" in rule and not native() in rule["os"]:
                    return False
            elif rule["action"] == "disallow":
                if "os" in rule and native() in rule["os"]:
                    return False

    # 从架构判断 (跨架构真难做啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊啊)
    exclude_archs = [
        'arm64',
        'aarch_64',
        'x86',
        'x86_64',
        'arm'
    ]
    exclude_archs.pop(exclude_archs.index(get_architecture()))
    for i in exclude_archs:
        if i in lib['name']:
            return False
    return True


def download_assets(minecraft_dir, instance_name, print_status=True, bmclapi=False, progress_callback=None,
                    max_workers=8):
    """下载Minecraft为指定版本的assets(素材)，返回None"""
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    asset_index = get_assetIndex(minecraft_dir, instance_name)
    os.makedirs(f'{minecraft_dir}/assets/indexes', exist_ok=True)

    # 下载asset索引文件
    with open(f'{minecraft_dir}/assets/indexes/{asset_index}.json', "wb") as f:
        url = version_json["assetIndex"]["url"]
        item = requests.get(url)
        if item.status_code != 200:
            raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
        f.write(item.content)

    with open(f'{minecraft_dir}/assets/indexes/{asset_index}.json', 'r') as f:
        asset_json = f.read()
    asset_json = json.loads(asset_json)

    # 创建线程安全的进度计数器
    current_count = 0
    total_count = len(asset_json["objects"])
    lock = threading.Lock()

    def update_progress():
        """线程安全的进度更新"""
        nonlocal current_count
        with lock:
            current_count += 1
            if progress_callback:
                progress_callback(current_count, total_count, f"[AST][{current_count}/{total_count}]")
            if print_status:
                pass
                # print(f"{current_count}/{total_count}")

    def download_file(object_info):
        """下载单个文件的函数"""
        object_name, object_data = object_info
        hash = object_data["hash"]
        url = f'https://resources.download.minecraft.net/{hash[0:2]}/{hash}'

        if ("map_to_resources" in asset_json) and (asset_json["map_to_resources"] == True):
            local = f'{minecraft_dir}/versions/{instance_name}/resources/{object_name}'
            current_directory = '/'.join(local.split('/')[0:-1])
            os.makedirs(current_directory, exist_ok=True)
        else:
            os.makedirs(f'{minecraft_dir}/assets/objects/{hash[0:2]}', exist_ok=True)
            local = f'{minecraft_dir}/assets/objects/{hash[0:2]}/{hash}'

        # 如果文件已存在，跳过下载
        if os.path.exists(local):
            update_progress()
            return True

        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                raise Exception(f"Request Fail: {response.status_code}\nurl: {url}")

            # 确保目录存在
            os.makedirs(os.path.dirname(local), exist_ok=True)

            with open(local, "wb") as f:
                f.write(response.content)

            update_progress()
            return True
        except Exception as e:
            print(f"Failed to download {object_name}: {e}")
            return False

    # 准备下载任务
    download_tasks = [(name, asset_json["objects"][name]) for name in asset_json["objects"]]

    # 使用线程池并行下载
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有下载任务
        future_to_object = {
            executor.submit(download_file, task): task[0]
            for task in download_tasks
        }

        # 处理完成的任务
        for future in as_completed(future_to_object):
            object_name = future_to_object[future]
            try:
                success = future.result()
                if success:
                    successful_downloads += 1
            except Exception as e:
                print(f"Error downloading {object_name}: {e}")

    # 下载完成回调
    if progress_callback:
        progress_callback(total_count, total_count, "Download Finish")

    print(f"Download completed: {successful_downloads}/{total_count} files")
    return successful_downloads == total_count


def auto_download(minecraft_dir, mcversion, instance_name, modloader='vanilla', bmclapi=False, modloader_version='latest',
                  progress_callback=None, java='java'):
    """下载整个Minecraft版本，返回None"""
    if not os.path.exists(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json'):
        # 新的版本
        modloader = modloader.lower()
        if modloader == 'fabric': # 手动merge
            fabric_json = f'{minecraft_dir}/versions/{instance_name}/Fabric.json'
            if not os.path.exists(fabric_json):
                download_fabric_json(minecraft_dir, mcversion, instance_name, loader_version='latest')
            download_version_json(minecraft_dir, mcversion, instance_name, bmclapi=bmclapi)
            jsonfile = fabric_merge_json(f'{minecraft_dir}/versions/{instance_name}/Fabric.json',
                                         f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json')
            with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'w') as f:
                f.write(json.dumps(jsonfile))

        elif modloader == 'forge':
            download_forge_json(minecraft_dir, mcversion, instance_name, bmclapi=bmclapi,
                                forge_version=modloader_version, java=java)

        elif modloader == 'neoforge':
            print('download neoforge json')
            if not os.path.exists(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json'):
                download_neoforge_json(minecraft_dir, mcversion, instance_name, bmclapi=bmclapi,
                                       neoforge_version=modloader_version, java=java)

        elif modloader == 'vanilla':
            download_version_json(minecraft_dir, mcversion, instance_name, bmclapi=bmclapi)

        else:
            raise Exception('Modloader not found ' + modloader)

    download_jar(minecraft_dir, instance_name, bmclapi=bmclapi)

    download_libraries(minecraft_dir, mcversion, instance_name, bmclapi=bmclapi, progress_callback=progress_callback)

    # if modloader == 'forge':
    #     install_profile = os.path.join(get_file_path(), 'temp', 'forge_installer', 'install_profile.json')
    #     install_profile = json.loads(open(install_profile, 'r').read())
    #     processors(install_profile=install_profile,
    #                working_dir=get_file_path() + '/temp',
    #                minecraft_version_path=os.path.join(minecraft_dir, 'versions', instance_name),
    #                version=version,
    #                forge_version=modloader_version,
    #                minecraft_dir=minecraft_dir)

    download_assets(minecraft_dir, instance_name, bmclapi=bmclapi, progress_callback=progress_callback)