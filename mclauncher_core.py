import sys
import shutil
import json
import platform
import os
import random
import requests
import subprocess as s
import locale
import xml.etree.ElementTree as ET
from pathlib import Path


# ModLoader
def is_fabric(minecraft_dir, version_name) -> bool: # necessary & workiing(in a un-beautiful way)
    # if os.path.exists(minecraft_dir+f"/versions/{version_name}/fabric-loader.jar"):
    #     return True
    # else:
    #     return False

    with open(minecraft_dir+'/versions/'+version_name+'/'+version_name+'.json', 'r') as f:
        if "fabric-loader" in f.read():
            print(True)
            return True
        else:
            print(False)
            return False

def deep_merge_dicts(dict1, dict2):
    merged = dict1.copy()
    for key, value in dict2.items():
        if key in merged:
            if isinstance(merged[key], list) and isinstance(value, list):
                merged[key].extend(value)
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value  # 非列表/字典则直接覆盖
        else:
            merged[key] = value
    return merged

def merge_json(path_a, path_b, modify=False): # Merge Jsons
    with open(path_a, 'r') as f:
        json_a = json.loads(f.read()) # fabric
    with open(path_b, 'r') as f:
        json_b = json.loads(f.read()) # mineccraft
        # minecraft_libs = json_b['libraries']
    # if modify:
    #     for lib in range(len(json_b['libraries'])):
    #         if lib+1 < len(json_b['libraries']) and json_b['libraries'][lib]['name'][:16] == 'org.ow2.asm:asm:':
    #             json_b['libraries'].pop(lib)
    lib_b = json_b['libraries']
    json_b.update(json_a)
    json_b['libraries'].extend(lib_b)
    for i in range(len(json_b['libraries'])):
        if json_b['libraries'][i]['name'] == 'org.ow2.asm:asm:9.6':
            json_b['libraries'].pop(i)
            break

    return json_b

    #     json_b['libraries'] = minecraft_libs
    #     for i in range(len(json_a['libraries'])):
    #         # In order to avoid multiple "asm"(others too) lib(1 from minecraft, 1 from fabric), 
    #         # the libraries need to be checked.
    #         a = json_a['libraries'][i]['name'].replace('.', '/').replace(':', '/')
    #         for j in range(len(json_b['libraries'])):
    #             if not json_b['libraries'][j] == 'remove':
    #                 b = json_b['libraries'][j]['name'].replace('.', '/').replace(':', '/')
    #                 if a.split('/')[:4] == b.split('/')[:4]:
    #                     print(json_a['libraries'][i]['name'])
    #                     json_b['libraries'][i] = 'remove'
    #         json_b['libraries'].append(json_a['libraries'][i])
    #     json_b['arguments']['jvm'].append("-DFabricMcEmu= net.minecraft.client.main.Main ")
    # while 'remove' in json_b['libraries']:
    #     json_b['libraries'].pop(json_b['libraries'].index('remove'))

def parse_maven_metadata_xml(url='https://maven.fabricmc.net/net/fabricmc/fabric-loader/maven-metadata.xml'):
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    xml_string = item.text
    """将 XML 字符串转换为 Python 字典"""
    root = ET.fromstring(xml_string)
    
    def parse_element(element):
        """递归解析 XML 元素"""
        if len(element) == 0:
            return element.text
        
        result = {}
        for child in element:
            child_data = parse_element(child)
            
            # 处理 versions 列表
            if child.tag == "versions":
                result[child.tag] = [v.text for v in child]
            else:
                if child.tag in result:
                    if isinstance(result[child.tag], list):
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = [result[child.tag], child_data]
                else:
                    result[child.tag] = child_data
        
        return result
    
    return {root.tag: parse_element(root)}

def get_latest_fabric_version_id():
    return parse_maven_metadata_xml()['metadata']['versioning']['latest']

def get_latest_fabric_installer_version_id():
    return parse_maven_metadata_xml(url="https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml")['metadata']['versioning']['latest']

def download_fabric_installer(path, ver):
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            url = f'https://maven.fabricmc.net/net/fabricmc/fabric-installer/{ver}/fabric-installer-{ver}.jar'
            item = requests.get(url)
            if item.status_code != 200:
                raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
            f.write(item.content)
    

def install_fabric_version_installer(minecraft_dir, version, version_name, path_to_installer, java="", print_status=True, bmclapi=False): # latest fabric as default
    if not os.path.exists(path_to_installer):
        raise FileNotFoundError("FabricInstaller not found")
    if not os.path.exists(java):
        java = 'java'
    command = f'{java} -jar {path_to_installer} client -dir {minecraft_dir} -mcversion {version}'
    print(command)
    os.system(command)
    for folder in os.listdir(minecraft_dir+'/versions'):
        folder_splited = folder.split('-')
        if folder_splited[0] == 'fabric' and folder_splited[1] == 'loader' and version in folder:
            fabric_version_folderpath = folder
            os.rename(f'{minecraft_dir}/versions/{folder}/{folder}.json', f'{minecraft_dir}/versions/{folder}/fabric.json')
            os.rename(f'{minecraft_dir}/versions/{folder}', f'{minecraft_dir}/versions/{version_name}')
            break

def download_fabric_json(minecraft_dir, version, version_name, loader_version='latest'):
    if loader_version == 'latest':
        loader_version = get_latest_fabric_version_id()
    url = f'https://maven.fabricmc.net/net/fabricmc/fabric-loader/{loader_version}/fabric-loader-{loader_version}.json'
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    jsonfile = item.text
    jsonfile = json.loads(jsonfile)
    # Parse JSON
    jsonfile["inheritsFrom"] = version
    jsonfile["mainClass"] = jsonfile["mainClass"]['client']
    jsonfile.pop("version")
    jsonfile.pop("min_java_version")
    libraries = []
    for item in jsonfile['libraries']['client']:
        libraries.append(item)
    for item in jsonfile['libraries']['common']:
        libraries.append(item)
    jsonfile["libraries"] = libraries
    jsonfile["releaseTime"] = '0' # Needs Fix......
    jsonfile["id"] = f"fabric-loader-{loader_version}-{version}"
    jsonfile["time"] = '0' # Fix need......
    jsonfile["type"] = 'release'

    # Add FabricLoader to libraries
    # .minecraft/libraries/net/fabricmc/fabric-loader/0.17.2
    loader_json = {
        "name": f"net.fabricmc:fabric-loader:{loader_version}",
        "url": "https://maven.fabricmc.net/"
    }
    intermediary_json = {
        "name": f"net.fabricmc:intermediary:{version}",
        "url": "https://maven.fabricmc.net/"
    }
    jsonfile["libraries"].append(loader_json)
    jsonfile["libraries"].append(intermediary_json)

    content = json.dumps(jsonfile)

    os.makedirs(f'{minecraft_dir}/versions/{version_name}', exist_ok=True)
    with open(f'{minecraft_dir}/versions/{version_name}/Fabric.json', 'w') as f:
        f.write(content)

def get_file_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) # EXE
    return os.path.dirname(os.path.abspath(__file__)) # .py

def get_system_bits():
    return platform.architecture()[0][0:2]

def native() -> str: # 
    return platform.system().lower()

def detect_error(stdout, stderr) -> str:
    stdout = stdout.decode(encoding='utf-8').split('\r\n')
    stderr = stderr.decode(encoding='utf-8')
    if stderr == '':
        return 0
    else:
        stderr = stderr.split('\r\n')
        for line in stderr:
            line = line.split(': ')
            if len(line) == 3:
                return(1,line[1],line[2])

def get_version_manifest(bmclapi=False) -> dict: # get version_manifest, returns a dict
    if bmclapi:
        url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
    else:
        url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    raw = requests.get(url)
    if raw.status_code == 200:
        manifest = raw.json()
        return manifest
    else:
        raise Exception(f"Request Fail: {raw.status_code}\nurl: {url}")

def get_java_version(java_binary_path='java') -> list: # parses java -version and returns the version, example=[8, '1.8.0_452'],[21, "21.0.7"]
    p = s.Popen([java_binary_path, '-version'], stdout=s.PIPE, stderr=s.PIPE)
    stdout, stderr = p.communicate()
    ver_full = stderr.decode().split('\n')[0].split(' version ')[1][1:-1] # the line should be 'openjdk version "1.8.0_462"'
    if ver_full.split('.')[0] == '1':
        major_version = ver_full.split(".")[1]
    else:
        major_version = ver_full.split('.')[0]

    return [major_version, ver_full]

def chk_java_available(java_binary_path, minecraft_dir, version_name):
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        raw = f.read()
    version_json = json.loads(raw)
    if "javaVersion" in version_json and "majorVersion" in version_json["javaVersion"]:
        required_version = version_json["javaVersion"]["majorVersion"]
        return get_java_version(java_binary_path) == required_version
    else:
        return False

def get_version_list(show_snapshot=False, show_old=False, show_release=True, bmclapi=False):
    if bmclapi:
        url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
    else:
        url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    raw = requests.get(url)
    if raw.status_code != 200:
        raise Exception(f"Request Fail: {raw.status_code}\nurl: {url}")
    manifest = raw.json()
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

def get_version_json(version, bmclapi=False) -> dict: # get version json => dict
    manifest = get_version_manifest()
    for current in manifest["versions"]:
        1
        if current['id'] == version:
            raw = requests.get(current['url'])
            if raw.status_code != 200:
                raise Exception(f"Request Fail: {raw.status_code}\nurl: {current['url']}")
            return json.loads(raw.text)
    raise Exception("version not found")

def download_version_json(minecraft_dir, version, version_name, bmclapi=False): # VERSIONSPLITFIXED
    manifest = get_version_manifest()
    if version == "latest":
        version = manifest["latest"]["release"]
    elif version == "latest_snapshot":
        version = manifest["latest"]["snapshot"]
    for current in manifest["versions"]:
        if current["id"] == version:
            os.makedirs(f'{minecraft_dir}/versions/{version_name}', exist_ok=True)
            with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'wb') as f:
                url = current["url"]
                if bmclapi:
                    url = url.replace("https://launchermeta.mojang.com/", "https://bmclapi2.bangbang93.com/")
                    url = url.replace("https://launcher.mojang.com/", "https://bmclapi2.bangbang93.com/")
                item = requests.get(url)
                if item.status_code != 200:
                    raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                f.write(item.content)

def get_mainclass(minecraft_dir, version, version_name):
    if is_fabric(minecraft_dir, version_name):
        return "net.fabricmc.loader.impl.launch.knot.KnotClient"
    # version_json_path = minecraft_dir +'/versions/' + version + '/' + version + '.json'
    version_json_path = f'{minecraft_dir}/versions/{version_name}/{version_name}.json'
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except:
        print("json file not found")
    return version_data["mainClass"]
    
def get_minecraft_args(minecraft_dir, version, version_name): # VERSIONSPLITFIXED
    # version_json_path = minecraft_dir +'/versions/' + version_name + '/' + version + '.json'
    version_json_path = f'{minecraft_dir}/versions/{version_name}/{version_name}.json'
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_data = json.loads(f.read())
    if "minecraftArguments" in version_data:
        return [" -cp " + get_cp_args(minecraft_dir, version, version_name), version_data["minecraftArguments"]]
    else:
        args_list = []
        for key in version_data["arguments"]["game"]:
            if type(key) != dict:
                args_list.append(key)
        return ' '.join(args_list)

def download_jar(minecraft_dir, version_name, bmclapi=False): # VERSIONSPLITFIXED
    # if os.path.exists(f'{minecraft_dir}/{version}/{version}.jar'):
    #     return 'AlE'
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    if not os.path.exists(f'{minecraft_dir}/versions/{version_name}/{version_name}.jar'):
        with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.jar', 'wb') as f:
            url = version_json["downloads"]["client"]["url"]
            
            if bmclapi:
                url = url.replace("https://launchermeta.mojang.com/", "https://bmclapi2.bangbang93.com/")
                url = url.replace("https://launcher.mojang.com/", "https://bmclapi2.bangbang93.com/")
            item = requests.get(url)
            if item.status_code != 200:
                raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
            f.write(item.content)

def download_libraries(minecraft_dir, version, version_name, print_status=True, bmclapi=False, progress_callback=None): # VERSIONSPLITFIXED
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    file_amount = len(version_json["libraries"])
    current = 0
    amount = len(version_json["libraries"])
    for lib in version_json["libraries"]:
        current += 1
        if progress_callback:
            progress_callback(current, amount, f"[LIB][{current}/{amount}]")
        if print_status:
            if 'name' in lib:
                print(f'{current}/{file_amount}\n- {lib["name"]}')
        if not is_library_required(lib):
            continue
        '''{
            "name": "org.ow2.asm:asm:9.8",
            "url": "https://maven.fabricmc.net/",
            "md5": "f5adf3bfc54fb3d2cd8e3a1f275084bc",
            "sha1": "dc19ecb3f7889b7860697215cae99c0f9b6f6b4b",
            "sha256": "876eab6a83daecad5ca67eb9fcabb063c97b5aeb8cf1fca7a989ecde17522051",
            "sha512": "cbd250b9c698a48a835e655f5f5262952cc6dd1a434ec0bc3429a9de41f2ce08fcd3c4f569daa7d50321ca6ad1d32e131e4199aa4fe54bce9e9691b37e45060e",
            "size": 126113
        },
        {'''
        if not "downloads" in lib: # For fabric stuff format like that
            # first we need to get the path of file like org/ow2/asm/asm/9.8
            name = lib['name'].split(':') # [org.ow2.asm,asm,9.8]
            # name = lib['name'].replace(':', '$SEP$')
            name[0] = name[0].replace('.', '$SEP$') # [org$SEP$ow2$SEP$asm,asm,9.8]
            filename = '-'.join(name[1:])+'.jar' # asm-9.8.jar
            name = "$SEP$".join(name) # org$SEP$ow2$SEP$asm$SEP$asm$SEP$9.8
            path = name.replace("$SEP$",'/') # org/ow2/asm/asm/9.8
            if bmclapi:
                url_base = "https://bmclapi2.bangbang93.com/maven/"
            else:
                url_base = lib['url']
            url = url_base + path + '/' + filename
            local_path = f'{minecraft_dir}/libraries/{path}'
            os.makedirs(local_path, exist_ok=True)
            file_path = local_path + '/' + filename
            
            if os.path.exists(file_path) and "size" in lib and os.path.getsize(file_path) == lib['size']:
                pass
            else:
                with open(file_path, 'wb') as f:
                    item = requests.get(url)
                    if item.status_code != 200:
                        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                    f.write(item.content)
        else:
            if_artifact = "downloads" in lib and "artifact" in lib["downloads"]
            if_natives = "natives" in lib
            late = "artifact" in lib["downloads"] and "path" in lib["downloads"]["artifact"]
            if_natives_late_versions = late and f"-natives-{native()}.jar" in lib["downloads"]["artifact"]["path"]
            if_natives_late_versions = late and (if_natives_late_versions or f"-natives-{native()}-{platform.machine().lower()}.jar" in lib["downloads"]["artifact"]["path"]) # to x86 n arm64 needs fix
            if "rules" in lib:
                for rule in lib["rules"]:
                    if rule["action"] == "allow":
                        if "os" in rule and not native() in rule["os"]:
                            continue
                    elif rule["action"] == "disallow":
                        if "os" in rule and native() in rule["os"]:
                            continue

            if if_artifact:
                path = minecraft_dir+'/libraries/'+lib["downloads"]["artifact"]["path"]
                path = path.split('/')[0:-1]
                path = '/'.join(path)
                os.makedirs(path, exist_ok=True)
                local_path = f'{minecraft_dir}/libraries/{lib["downloads"]["artifact"]["path"]}'
                if os.path.exists(local_path) and not if_natives and not if_natives_late_versions and os.path.getsize(local_path) == lib['downloads']['artifact']['size']:
                    print(lib['downloads']['artifact']['size'])
                    continue
                with open(f'{minecraft_dir}/libraries/{lib["downloads"]["artifact"]["path"]}', 'wb') as f:
                    url = lib["downloads"]["artifact"]["url"]
                    if bmclapi:
                        fallback_url = url
                        url = url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/")
                        # if unable to download use original url.
                        item = requests.get(url)
                        if item.status_code != 200:
                            raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                        f.write(item.content)
            if if_natives or if_natives_late_versions:
                # if not allow continue
                if if_natives_late_versions:
                    natives = []
                elif "natives-"+native() in lib["downloads"]["classifiers"]:
                    natives = lib["downloads"]["classifiers"]["natives-"+native()]
                elif "natives-"+native()+'-'+get_system_bits() in lib["downloads"]["classifiers"]:
                    natives = lib["downloads"]["classifiers"]["natives-"+native()+'-'+get_system_bits()]
                else:
                    print("cannot find key")
                # if if_natives:
                #     path = minecraft_dir+'/libraries/'+natives["path"]
                # elif if_natives_late_versions:
                #     path = minecraft_dir+'/libraries/'+lib["downloads"]["artifact"]["path"]
                # path = path.split('/')[0:-1]
                # path = '/'.join(path)
                # os.makedirs(path, exist_ok=True)
                # if os.path.exists(minecraft_dir+'/libraries/'+natives["path"]):
                #     continue

                # get natives path
                # natives_path = minecraft_dir+'/'+version+'/'+version+'-natives'.replace("/",'\\')
                natives_path = f'{minecraft_dir}/versions/{version_name}/{version_name}-natives'
                os.makedirs(natives_path, exist_ok=True)
                # get exclude
                if if_natives:
                    excludes = []
                    if 'extract' in lib and 'exclude' in lib['extract']:
                        for exclude in lib["extract"]["exclude"]:
                            excludes.append(exclude)
                        excludes = '-x '+' '.join(excludes)
                    else:
                        excludes = ''
                elif if_natives_late_versions:
                    excludes = '-x META-INF/*'
                # excludes = "META-INF/"
                # with open(minecraft_dir+'/libraries/'+natives["path"], 'wb') as f:
                late = "artifact" in lib["downloads"] and "path" in lib["downloads"]["artifact"]
                if late:
                    filename = lib["downloads"]["artifact"]["path"].split('/')[-1]
                else:
                    filename = "temp.zip"
                temp_zip = natives_path+'/'+filename
                # write temporarily zip file
                with open(temp_zip, 'wb') as f:
                    if if_natives:
                        url = natives["url"]
                    elif if_natives_late_versions:
                        url = lib["downloads"]["artifact"]["url"]
                    item = requests.get(url)
                    if item.status_code != 200:
                        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                    f.write(item.content)
                try:
                    shutil.copy(temp_zip, minecraft_dir+'/libraries/'+lib['downloads']['artifact']['path'])
                except:
                    pass

                # unzip it
                program_path = get_file_path()
                unzip_exe = program_path.replace('/', '\\')+'\\unzip\\unzip.exe'
                if os.path.exists(unzip_exe):
                    if native() == 'windows':
                        natives_path = natives_path.replace("/", '\\')
                        excludes = excludes.replace("/", '\\')
                        # cmd = f'cd {natives_path} && {unzip_exe} -o {temp_zip} {excludes} && del {temp_zip}'.replace('/', '\\')
                        cmd = f'cd {natives_path} && {unzip_exe} -o "{temp_zip}" {excludes}'.replace('/', '\\')
                        path = filename.split("-")
                        if path[0] == 'lwjgl':
                            guess_path = f'{native()}\\x{get_system_bits()}\\org\\{path[0]}\\{path[1]}\\*.*'
                            program_path1 = program_path.replace('/','\\')
                            cmd = cmd+f" && copy .\\{guess_path} ."
                            if os.path.exists(natives_path+"/windows/x64/org/lwjgl/lwjgl.dll"): # .minecraft\1.21\1.21-natives\windows\x64\org\lwjgl\lwjgl.dll
                                shutil.copy(natives_path+"/windows/x64/org/lwjgl/lwjgl.dll", natives_path)
                else:
                    if os.path.exists("/usr/bin/unzip"):
                        unzip_bin = "/usr/bin/unzip"
                    elif os.path.exists("/bin/unzip"):
                        unzip_bin = "/bin/unzip"
                    else:
                        raise Exception("Cannot unzip native dlls, no unzip binary found (in /usr/bin & /bin)")
                    cmd = f'cd {natives_path} && unzip -o {temp_zip} {excludes}'
                    path = filename.split("-")
                    if path[0] == 'lwjgl':
                        if get_system_bits() == '64':
                            arch = "x64"
                        else:
                            arch = "x86"
                        guess_path = f'{native()}/{arch}/org/{path[0]}/{path[1]}/*.*'
                        cmd = cmd+f" && cp {natives_path}/{guess_path} ."
                os.system(cmd)
        print(f'- {url}')

def download_assets(minecraft_dir, version_name, print_status=True, bmclapi=False, progress_callback=None):
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    assetIndex = get_assetIndex(minecraft_dir, version_name)
    os.makedirs(f'{minecraft_dir}/assets/indexes', exist_ok=True)
    with open(f'{minecraft_dir}/assets/indexes/{assetIndex}.json', "wb") as f:
        url = version_json["assetIndex"]["url"]
        if bmclapi:
            url = url.replace("http://resources.download.minecraft.net/", "https://bmclapi2.bangbang93.com/assets/")
        item = requests.get(url)
        if item.status_code != 200:
            raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
        f.write(item.content)
    with open(f'{minecraft_dir}/assets/indexes/{assetIndex}.json', 'r') as f:
        asset_json = f.read()
    asset_json = json.loads(asset_json)
    ''' 获取assets索引文件：
            从版本清单中获取特定版本对应的assets索引文件URL
            通常位于https://launchermeta.mojang.com/v1/packages/<hash>/<version>.json
        解析assets索引：
            下载并解析JSON格式的assets索引文件
            该文件包含了所有资源文件的哈希值和大小信息
        下载objects文件：
            根据索引中的哈希值，从Mojang的CDN下载文件
            文件URL格式为：https://resources.download.minecraft.net/<前2字符哈希>/<完整哈希>
            例如，哈希为abc123...的文件位于.../ab/abc123...'''
    
    if "map_to_resources" in asset_json and asset_json["map_to_resources"] == True: # #针对 "map_to_resources": true,
        file_amount = len(asset_json["objects"])
        current = 0
        for object in asset_json["objects"]:
            current += 1
            if progress_callback:
                progress_callback(current, file_amount, f"[AST][{current}/{file_amount}]")
            if print_status:
                print(f"{current}/{file_amount}")
            hash = asset_json["objects"][object]["hash"]
            url = f'https://resources.download.minecraft.net/{hash[0:2]}/{hash}'
            local = f'{minecraft_dir}/versions/{version_name}/resources/{object}'
            current_directory = '/'.join(local.split('/')[0:-1])
            os.makedirs(current_directory, exist_ok=True)
            if os.path.exists(local):
                continue
            with open(local, "wb") as f:
                item = requests.get(url)
                if item.status_code != 200:
                    raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                f.write(item.content)
    else: #针对 没有行 "map_to_resources": true, 的情况
        file_amount = len(asset_json["objects"])
        current = 0
        for object in asset_json["objects"]:
            current += 1
            if progress_callback:
                progress_callback(current, file_amount, f"[AST][{current}/{file_amount}]")
            if print_status:
                print(f"{current}/{file_amount}")
            hash = asset_json["objects"][object]["hash"]
            url = f'https://resources.download.minecraft.net/{hash[0:2]}/{hash}'
            os.makedirs(f'{minecraft_dir}/assets/objects/{hash[0:2]}', exist_ok=True)
            local = f'{minecraft_dir}/assets/objects/{hash[0:2]}/{hash}'
            if os.path.exists(local):
                continue
            with open(local, "wb") as f:
                item = requests.get(url)
                if item.status_code != 200:
                    raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
                f.write(item.content)
    progress_callback(current, file_amount, f"Download Finish")

def auto_download(minecraft_dir, version, version_name, java='', fabric=False, print_status=True, bmclapi=False, progress_callback=None):
    if fabric:
        # # Download via Installer (dead, too lazy 2 fix)
        # path_to_installer = minecraft_dir+'/fabric-installer.jar'
        # download_fabric_installer(path_to_installer, get_latest_fabric_installer_version_id())
        # install_fabric_version_installer(minecraft_dir, version, version_name, path_to_installer, java=java)
        
        # Download JSON directly: (bug need fix)
        fabric_json = f'{minecraft_dir}/versions/{version_name}/Fabric.json'
        if not os.path.exists(fabric_json):
            download_fabric_json(minecraft_dir, version, version_name)
    if print_status:
        print("Downloading version .json File")
    download_version_json(minecraft_dir, version, version_name, bmclapi=bmclapi)
    # 
    if fabric:
        jsonfile = merge_json(f'{minecraft_dir}/versions/{version_name}/Fabric.json', f'{minecraft_dir}/versions/{version_name}/{version_name}.json')
        with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'w') as f:
            f.write(json.dumps(jsonfile))
    if print_status:
        print("Downloading version .jar File")
    download_jar(minecraft_dir, version_name, bmclapi=bmclapi)

    if print_status:
        print("Downloading version Library File")
    download_libraries(minecraft_dir, version, version_name, bmclapi=bmclapi, progress_callback=progress_callback)

    if print_status:
        print("Downloading version Assets File")
    download_assets(minecraft_dir, version_name, bmclapi=bmclapi, progress_callback=progress_callback)

def get_native_key(natives) -> str: # VERSIONSPLITNEEDLESS
    system = platform.system().lower()
    if system == "windows":
        return natives.get("windows", "natives-windows")
    elif system == "linux":
        return natives.get("linux", "natives-linux")
    elif system == "darwin":
        return natives.get("osx", "natives-osx")
    else: # seems to be useless (natives-java? xd)
        return "natives-" + system

def get_minecraft_libraries(minecraft_dir, version_name): # VERSIONSPLITFIXED
    # read json
    version_json_path = f'{minecraft_dir}/versions/{version_name}/{version_name}.json'
    
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.loads(f.read())
    except FileNotFoundError:
        pass
        # input("version.JSON not found " + str(version_json_path))
    except json.JSONDecodeError:
        pass
        # input("version.JSON decode err")

    libraries = []
    
    for lib in version_data['libraries']:
        # check if required
        if not is_library_required(lib):
            continue
        '''{
            "name": "org.ow2.asm:asm:9.8",
            "url": "https://maven.fabricmc.net/",
            "md5": "f5adf3bfc54fb3d2cd8e3a1f275084bc",
            "sha1": "dc19ecb3f7889b7860697215cae99c0f9b6f6b4b",
            "sha256": "876eab6a83daecad5ca67eb9fcabb063c97b5aeb8cf1fca7a989ecde17522051",
            "sha512": "cbd250b9c698a48a835e655f5f5262952cc6dd1a434ec0bc3429a9de41f2ce08fcd3c4f569daa7d50321ca6ad1d32e131e4199aa4fe54bce9e9691b37e45060e",
            "size": 126113
        },
        {'''
        if not "downloads" in lib: # For fabric stuff format like that
            # first we need to get the path of file like org/ow2/asm/asm/9.8
            name = lib['name'].split(':')
            # name = lib['name'].replace(':', '$SEP$')
            name[0] = name[0].replace('.', '$SEP$')
            filename = '-'.join(name[1:])+'.jar'
            name = "$SEP$".join(name)
            path = name.replace("$SEP$",'/')
            local_path = f'{minecraft_dir}/libraries/{path}/{filename}'
            if not os.path.exists(local_path):
                raise FileNotFoundError("Library not found")
            libraries.append(local_path)
        else:
            late = "artifact" in lib["downloads"] and "path" in lib["downloads"]["artifact"]
            # get main libs
            if late and not "natives" in lib["downloads"]["artifact"]["path"]:
                lib_path = lib["downloads"]["artifact"]["path"]
                full_path = f'{minecraft_dir}/libraries/{lib_path}'
                libraries.append(full_path)
            elif "natives" in lib["downloads"]["artifact"]["path"]: #DEBUG
                lib_path = lib["downloads"]["artifact"]["path"]
                full_path = f'{minecraft_dir}/libraries/{lib_path}'
                libraries.append(full_path)
    # check is fabric. if True,add fabric loader jar
    # if is_fabric(minecraft_dir, version_name):
    #     libraries.append(f'{minecraft_dir}/versions/{version_name}/fabric-loader.jar')
    #     # for i in os.listdir(f'{minecraft_dir}/versions/{version_name}/'):
    #     #     filename_splited = i.split('.')[0].split('-')
    #     #     print(filename_splited)
    #     #     if len(filename_splited) == 3 and filename_splited[0] == 'fabric' and filename_splited[1] == 'loader' and filename_splited[2] == '0':
    #     #         libraries.append(f'{minecraft_dir}/versions/{version_name}/'+i)
    return libraries

def is_library_required(library) -> bool:  # VERSIONSPLITNEEDLESS
    if "rules" not in library:
        if 'name' in library: # Fabric
            if 'natives-' in library['name'] and not f'natives-{native()}' in library['name']:
                print(library['name'])
                allow = False
            else:
                allow = True
        else:
            raise Exception("Broken library.")
            
        return allow
    
    allow = False
    os_name = native()
    
    for rule in library["rules"]:
        if rule["action"] == "allow":
            if "os" not in rule:
                allow = True
            elif rule["os"].get("name") == os_name:
                allow = True
        elif rule["action"] == "disallow":
            if "os" not in rule:
                allow = False
            elif rule["os"].get("name") == os_name:
                allow = False

    return allow

def get_cp_args(minecraft_dir, version, version_name) -> str:  # VERSIONSPLITFIXED
    version_jar = f'{minecraft_dir}/versions/{version_name}/{version_name}.jar'
    
    # get libraries
    libraries = get_minecraft_libraries(minecraft_dir, version_name)
    
    # make classpath
    separator = ";" if platform.system() == "Windows" else ":"
    classpath = [str(version_jar)] + libraries
    
    # check if exist
    missing = [p for p in classpath if not os.path.exists(p)]
    if missing:
        print(missing)
        # input(missing)
    
    return f'"{separator.join(classpath)}"'.replace("\\", '/')

def get_assetIndex(minecraft_dir, version_name) -> str: # VERSIONSPLITFIXED
    version_json_path = f"{minecraft_dir}/versions/{version_name}/{version_name}.json"
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except FileNotFoundError:
        input("version.JSON not found ")
    except json.JSONDecodeError:
        input("version.JSON decode err")
    return version_data["assets"]

def gen_random_uuid(): # VERSIONSPLITNEEDLESS
    chars = "1234567890abcdef"
    uuid = ""
    for i in range(32):
        uuid = uuid + chars[random.randint(0,15)]
    return uuid

def get_jvm_args(minecraft_dir, version, version_name): # VERSIONSPLITNEEDLESS
    version_json_path = f"{minecraft_dir}/versions/{version_name}/{version_name}.json"
    d_args = ["-Dfml.ignoreInvalidMinecraftCertificates=True", 
            "-Djdk.lang.Process.allowAmbiguousCommands=true", 
            "-Dfml.ignorePatchDiscrepancies=True", 
            "-Dlog4j2.formatMsgNoLookups=true", 
            f'"-Djava.library.path={minecraft_dir}/versions/{version_name}/{version_name}-natives"']
    if native() == 'windows':
        d_args.append("-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump")
    if native() == 'linux':
        d_args.append('-Djava.awt.headless=false')
        d_args.append("-Djna.nosys=true")
        # If some problems occurs like AWT... on WSL2(WSLg), just have a look this https://stackoverflow.org.cn/questions/15260989
        # # debug only
        # d_args.append("-Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true -Dorg.lwjgl.opengl.Display.noinput=true")
    cp_args = get_cp_args(minecraft_dir, version, version_name)
    with open(version_json_path, 'r') as f:
        version_json = json.loads(f.read())
    if os.path.exists(f"{minecraft_dir}/versions/{version_name}/.fabric"): # --add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED
        d_args.append("--add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED")
    if "arguments" in version_json and "jvm" in version_json["arguments"]:
        args = version_json["arguments"]["jvm"]
        replacer = {"${natives_directory}": f'{minecraft_dir}/versions/{version_name}/{version_name}-natives',
                    "${classpath}": cp_args,
                    "${launcher_name}": "minecraft-launcher",
                    "${launcher_version}": "1.0.0.0",
                    "-Dos.name=Windows 10": '-Dos.name="Windows 10"'}
        args_text = ''
        for arg in args:
            if type(arg) == dict:
                rules = arg["rules"]
                value = arg["value"]
                allow = False
                if get_system_bits() == '64':
                    arch = "x64"
                else:
                    arch = "x86"
                for rule in rules:
                    if rule["action"] == "allow":
                        if "os" not in rule:
                            allow = True
                        elif "name" in rule["os"] and rule["os"]["name"] == native():
                            allow = True
                        elif "arch" in rule["os"] and rule["os"]["arch"] == arch:
                            allow = True
                    elif rule["action"] == "disallow":
                        if "os" not in rule:
                            allow = False
                        elif "name" in rule["os"] and rule["os"]["name"] == native():
                            allow = False
                        elif "arch" in rule["os"] and rule["os"]["arch"] == arch:
                            allow = False
                if not allow:
                    continue
                else:
                    if type(value) == list:
                        value = ' '.join(value)
                    args_text = args_text + value + ' '
            else:
                args_text = args_text + arg + ' '
        args_text = args_text[:-1]
        for i in replacer:
            args_text = args_text.replace(i, replacer[i])
    else:
        args_text = ' '.join(d_args)

    # final modifier
    replacer = {'-DFabricMcEmu= net': '-DFabricMcEmu=net'}
    for i in replacer:
        args_text = args_text.replace(i, replacer[i])
    return args_text

def rmver(minecraft_dir, version_name): # VERSIONSPLITFIXED
    shutil.rmtree(f'{minecraft_dir}/versions/{version_name}')

def get_minecraft_version(minecraft_dir, version_name):
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        version_json = json.loads(f.read())
    if 'id' in version_json:
        return version_json['id']
    elif "inheritsFrom" in version_json:
        return version_json["inheritsFrom"]
    else:
        raise Exception("versionjson seems invalid")

def launch(javaw, xmx, minecraft_dir, version, version_name, javawrapper=None, username="steve", xmn="256M") -> str: #minecraft_dir: "xxx/xxx/.minecraft"; version: "1.8.9"
    # all of the items in lists are NOT ended with space!!!
    # -x args (JVM stuff)
    minecraft_dir = minecraft_dir.replace('\\', '/')
    x_args = [f"-Xmx{xmx}", 
            f"-Xmn{xmn}", 
            "-XX:+UseG1GC", 
            "-XX:-UseAdaptiveSizePolicy", 
            "-XX:-OmitStackTraceInFastThrow"]
    # -d args (jvm system properties)
    d_args = get_jvm_args(minecraft_dir, version, version_name)
    # minecraft args
    uuid = gen_random_uuid()
    minecraft_args = get_minecraft_args(minecraft_dir, version, version_name)
    
    if type(minecraft_args) == list:
        minecraft_args_cp = minecraft_args[0]
        minecraft_args_minecraft = minecraft_args[1]
        split_cp_from_minecraft_args = True
    else:
        minecraft_args_minecraft = minecraft_args
        split_cp_from_minecraft_args = False
    mainClass = get_mainclass(minecraft_dir, version, version_name)
    minecraft_args = mainClass + ' ' + minecraft_args_minecraft + " -width 854 -height 480"
    replacer = {"${auth_player_name}": username,
                "${version_name}": version_name, 
                "${auth_session}": uuid, 
                "${game_directory}": minecraft_dir+'/versions/'+version_name,
                "${assets_root}": minecraft_dir+'/assets',
                "${game_assets}": minecraft_dir+f'/versions/{version_name}/resources', # C:\Users\magic\Documents\projects\LauncherX\.minecraft\1.0\resources
                "${assets_index_name}": get_assetIndex(minecraft_dir, version_name),
                "${auth_uuid}": uuid,
                "${auth_access_token}": uuid,
                "${user_properties}": "{}",
                "${user_type}": "msa",
                "${version_type}": '"ciallo"'}
    for i in replacer:
        if split_cp_from_minecraft_args:
            minecraft_args_minecraft = minecraft_args_minecraft.replace(i, replacer[i])
        else:
            minecraft_args = minecraft_args.replace(i, replacer[i])
    x_args = ' '.join(x_args)
    final_pt1 = f'{javaw} {x_args} {d_args}'
    if native() == 'windows':
        if javawrapper != None:
            javawrapper_arg = f'-jar "{javawrapper}"'
        else:
            raise Exception("Unspecified JavaWrapper on Windows Platform.")
    else:
        javawrapper_arg = ''
    if split_cp_from_minecraft_args:
        final_pt2 = f'{minecraft_args_cp} {javawrapper_arg} {mainClass} {minecraft_args_minecraft}'
    else:
        final_pt2 = f'{javawrapper_arg} {minecraft_args}'
    # final = final.replace('/', '\\')
    return final_pt1+' '+final_pt2

if __name__ == '__main__':
    url = 'https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml'
    print(download_fabric_installer('C:/users/magic/Documents/projects/LauncherX/.minecraft/fabric-installer.jar',get_latest_fabric_version_id()))