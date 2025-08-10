import sys
import shutil
import json
import platform
import os
import random
import requests
from pathlib import Path


def get_file_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) # EXE
    return os.path.dirname(os.path.abspath(__file__)) # .py

def get_system_bits():
    return platform.architecture()[0][0:2]

def native():
    return platform.system().lower()

def get_version_manifest(bmclapi=False): # get version manifest from mojang: https://launchermeta.mojang.com/mc/game/version_manifest.json
    if bmclapi:
        raw = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
    else:
        raw = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
    if str(raw.status_code) == "200":
        manifest = raw.json()
        return manifest
    else:
        raise("Version Manifest Error:"+str(raw.status_code))

def get_version_list(show_snapshot=False, show_old=False, show_release=True, bmclapi=False):
    if bmclapi:
        raw = requests.get("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")
    else:
        raw = requests.get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
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

def download_version_json(dotminecraft_dir, version, bmclapi=False):
    manifest = get_version_manifest()
    if version == "latest":
        version = manifest["latest"]["release"]
    elif version == "latest_snapshot":
        version = manifest["latest"]["snapshot"]
    if not os.path.exists(f'{dotminecraft_dir}/{version}/{version}.json'):
        for current in manifest["versions"]:
            if current["id"] == version:
                os.makedirs(f'{dotminecraft_dir}/{version}', exist_ok=True)
                with open(f'{dotminecraft_dir}/{version}/{version}.json', 'wb') as f:
                    url = current["url"]
                    if bmclapi:
                        url = url.replace("https://launchermeta.mojang.com/", "https://bmclapi2.bangbang93.com/")
                        url = url.replace("https://launcher.mojang.com/", "https://bmclapi2.bangbang93.com/")
                    f.write(requests.get(url).content)

def get_mainclass(dotminecraft_dir, version):
    version_json_path = dotminecraft_dir +'/' + version + '/' + version + '.json'
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except:
        print("json file not found")
    return version_data["mainClass"]
    
def get_minecraft_args(dotminecraft_dir, version):
    version_json_path = dotminecraft_dir +'/' + version + '/' + version + '.json'
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except:
        print("json file not found")
    if "minecraftArguments" in version_data:
        return [" -cp " + get_cp_args(dotminecraft_dir, version), version_data["minecraftArguments"]]
    else:
        args_list = []
        for key in version_data["arguments"]["game"]:
            if type(key) != dict:
                args_list.append(key)
        return ' '.join(args_list)

def download_jar(dotminecraft_dir, version, bmclapi=False):
    # if os.path.exists(f'{dotminecraft_dir}/{version}/{version}.jar'):
    #     return 'AlE'
    with open(f'{dotminecraft_dir}/{version}/{version}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    if not os.path.exists(f'{dotminecraft_dir}/{version}/{version}.jar'):
        with open(f'{dotminecraft_dir}/{version}/{version}.jar', 'wb') as f:
            url = version_json["downloads"]["client"]["url"]
            print(url)
            if bmclapi:
                url = url.replace("https://launchermeta.mojang.com/", "https://bmclapi2.bangbang93.com/")
                url = url.replace("https://launcher.mojang.com/", "https://bmclapi2.bangbang93.com/")
            f.write(requests.get(url).content)

def download_libs(dotminecraft_dir, version, print_status=True, bmclapi=False, progress_callback=None):
    with open(f'{dotminecraft_dir}/{version}/{version}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    file_amount = len(version_json["libraries"])
    current = 0
    amount = len(version_json["libraries"])
    for lib in version_json["libraries"]:
        current += 1
        if progress_callback:
            progress_callback(current, amount, f"[DL][LIBRARIES][1/2][{current}/{amount}]")
        if print_status:
            print(f'{current}/{file_amount} {lib["name"]}')
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
            if bmclapi:
                url_base = "https://bmclapi2.bangbang93.com/maven/"
            else:
                url_base = lib['url']
            url = url_base + path
            local_path = f'{dotminecraft_dir}/libraries/{path}'
            os.makedirs(local_path, exist_ok=True)
            file_path = local_path + '/' + filename
            with open(file_path, 'wb') as f:
                f.write(requests.get(url).content)
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
                path = dotminecraft_dir+'/libraries/'+lib["downloads"]["artifact"]["path"]
                path = path.split('/')[0:-1]
                path = '/'.join(path)
                os.makedirs(path, exist_ok=True)
                if os.path.exists(f'{dotminecraft_dir}/libraries/{lib["downloads"]["artifact"]["path"]}') and not if_natives and not if_natives_late_versions:
                    continue
                with open(f'{dotminecraft_dir}/libraries/{lib["downloads"]["artifact"]["path"]}', 'wb') as f:
                    url = lib["downloads"]["artifact"]["url"]
                    if bmclapi:
                        url = url.replace("https://libraries.minecraft.net/", "https://bmclapi2.bangbang93.com/maven/")
                    f.write(requests.get(url).content)
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
                #     path = dotminecraft_dir+'/libraries/'+natives["path"]
                # elif if_natives_late_versions:
                #     path = dotminecraft_dir+'/libraries/'+lib["downloads"]["artifact"]["path"]
                # path = path.split('/')[0:-1]
                # path = '/'.join(path)
                # os.makedirs(path, exist_ok=True)
                # if os.path.exists(dotminecraft_dir+'/libraries/'+natives["path"]):
                #     continue

                # get natives path
                natives_path = dotminecraft_dir+'/'+version+'/'+version+'-natives'.replace("/",'\\')
                os.makedirs(natives_path, exist_ok=True)
                # get exclude
                if if_natives:
                    excludes = []
                    for exclude in lib["extract"]["exclude"]:
                        excludes.append(exclude)
                    excludes = '-x '+' '.join(excludes)
                elif if_natives_late_versions:
                    excludes = '-x META-INF\\*'
                # excludes = "META-INF/"
                # with open(dotminecraft_dir+'/libraries/'+natives["path"], 'wb') as f:
                late = "artifact" in lib["downloads"] and "path" in lib["downloads"]["artifact"]
                if late:
                    filename = lib["downloads"]["artifact"]["path"].split('/')[-1]
                else:
                    filename = "temp.zip"
                temp_zip = natives_path+'\\'+filename
                # write temporarily zip file
                with open(temp_zip, 'wb') as f:
                    if if_natives:
                        f.write(requests.get(natives["url"]).content)
                    elif if_natives_late_versions:
                        f.write(requests.get(lib["downloads"]["artifact"]["url"]).content)
                # unzip it
                program_path = get_file_path()
                unzip_exe = program_path.replace('/', '\\')+'\\unzip\\unzip.exe'
                if os.path.exists(unzip_exe):
                    if native() == 'windows':
                        # cmd = f'cd {natives_path} && {unzip_exe} -o {temp_zip} {excludes} && del {temp_zip}'.replace('/', '\\')
                        cmd = f'cd {natives_path} && {unzip_exe} -o {temp_zip} {excludes} && del {temp_zip}'.replace('/', '\\')
                        path = filename.split("-")
                        if path[0] == 'lwjgl':
                            guess_path = f'{native()}\\x{get_system_bits()}\\org\\{path[0]}\\{path[1]}\\*.*'
                            program_path1 = program_path.replace('/','\\')
                            cmd = cmd+f" && copy .\\{guess_path} ."
                            if os.path.exists(natives_path+"/windows/x64/org/lwjgl/lwjgl.dll"): # .minecraft\1.21\1.21-natives\windows\x64\org\lwjgl\lwjgl.dll
                                shutil.copy(natives_path+"/windows/x64/org/lwjgl/lwjgl.dll", natives_path)
                    else:
                        cmd = f'cd {natives_path} && {unzip_exe} -o {temp_zip} {excludes} && rm {temp_zip}'
                        path = filename.split("-")
                        if path[0] == 'lwjgl':
                            if get_system_bits() == '64':
                                arch = "x64"
                            else:
                                arch = "x86"
                            guess_path = f'{native()}/{arch}/org/{path[0]}/{path[1]}/*.*'
                            cmd = cmd+f" && cp {natives_path}/{guess_path} .".replace('\\', '/')
                    os.system(cmd)
                else:
                    print("unzip not found, extract GNU Unzip to <path of launcher>\\unzip")

def download_assets(dotminecraft_dir, version, print_status=True, bmclapi=False, progress_callback=None):
    with open(f'{dotminecraft_dir}/{version}/{version}.json', 'r') as f:
        version_json = f.read()
    version_json = json.loads(version_json)
    # get_assetIndex(dotminecraft_dir, version)
    os.makedirs(f'{dotminecraft_dir}/assets/indexes', exist_ok=True)
    with open(f'{dotminecraft_dir}/assets/indexes/{version}.json', "wb") as f:
        url = version_json["assetIndex"]["url"]
        if bmclapi:
            url = url.replace("http://resources.download.minecraft.net/", "https://bmclapi2.bangbang93.com/assets/")
        f.write(requests.get(url).content)
    with open(f'{dotminecraft_dir}/assets/indexes/{get_assetIndex(dotminecraft_dir, version)}.json', "wb") as f:
        f.write(requests.get(url).content)
    with open(f'{dotminecraft_dir}/assets/indexes/{version}.json', 'r') as f:
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
                progress_callback(current, file_amount, f"[DL][ASSETS][2/2][{current}/{file_amount}]")
            if print_status:
                print(f"{current}/{file_amount}")
            hash = asset_json["objects"][object]["hash"]
            url = f'https://resources.download.minecraft.net/{hash[0:2]}/{hash}'
            local = f'{dotminecraft_dir}/{version}/resources/{object}'
            current_directory = '/'.join(local.split('/')[0:-1])
            os.makedirs(current_directory, exist_ok=True)
            if os.path.exists(local):
                continue
            with open(local, "wb") as f:
                f.write(requests.get(url).content)
    else: #针对 没有行 "map_to_resources": true, 的情况
        file_amount = len(asset_json["objects"])
        current = 0
        for object in asset_json["objects"]:
            current += 1
            if progress_callback:
                progress_callback(current, file_amount, f"[DL][ASSETS][2/2][{current}/{file_amount}]")
            if print_status:
                print(f"{current}/{file_amount}")
            hash = asset_json["objects"][object]["hash"]
            url = f'https://resources.download.minecraft.net/{hash[0:2]}/{hash}'
            os.makedirs(f'{dotminecraft_dir}/assets/objects/{hash[0:2]}', exist_ok=True)
            local = f'{dotminecraft_dir}/assets/objects/{hash[0:2]}/{hash}'
            if os.path.exists(local):
                continue
            with open(local, "wb") as f:
                f.write(requests.get(url).content)
    progress_callback(current, file_amount, f"Download Finish")

def auto_download(dotminecraft_dir, version, print_status=True, bmclapi=False, progress_callback=None):
    if print_status:
        print("Downloading version .json File")
    download_version_json(dotminecraft_dir, version, bmclapi=bmclapi)
    if print_status:
        print("Downloading version .jar File")
    download_jar(dotminecraft_dir, version, bmclapi=bmclapi)
    if print_status:
        print("Downloading version Library File")
    download_libs(dotminecraft_dir, version, bmclapi=bmclapi, progress_callback=progress_callback)
    if print_status:
        print("Downloading version Assets File")
    download_assets(dotminecraft_dir, version, bmclapi=bmclapi, progress_callback=progress_callback)

def get_native_key(natives) -> str:
    system = platform.system().lower()
    if system == "windows":
        return natives.get("windows", "natives-windows")
    elif system == "linux":
        return natives.get("linux", "natives-linux")
    elif system == "darwin":
        return natives.get("osx", "natives-osx")
    else: # seems to be useless (natives-java? xd)
        return "natives-" + system

def get_minecraft_libraries(dotminecraft_dir, version):
    # read json
    version_json_path = f'{dotminecraft_dir}/{version}/{version}.json'
    
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except FileNotFoundError:
        pass
        # input("version.JSON not found " + str(version_json_path))
    except json.JSONDecodeError:
        pass
        # input("version.JSON decode err")

    libraries = []
    
    for lib in version_data.get("libraries", []):
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
            local_path = f'{dotminecraft_dir}/libraries/{path}/{filename}'
        else:
            late = "artifact" in lib["downloads"] and "path" in lib["downloads"]["artifact"]
            # get main libs
            if late and not "natives" in lib["downloads"]["artifact"]["path"] and "downloads" in lib and "artifact" in lib["downloads"]:
                lib_path = lib["downloads"]["artifact"]["path"]
                full_path = f'{dotminecraft_dir}/libraries/{lib_path}'
                libraries.append(str(full_path))
    
    return libraries

def is_library_required(library) -> bool:
    if "rules" not in library:
        return True
        
    allow = False
    os_name = {"windows": "windows", "linux": "linux", "osx": "osx"}.get(platform.system().lower(), "")
    
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

def get_cp_args(dotminecraft_dir, version) -> str:
    version_jar = Path(dotminecraft_dir) / version / f"{version}.jar"
    
    # get libraries
    libraries = get_minecraft_libraries(dotminecraft_dir, version)
    
    # make classpath
    separator = ";" if platform.system() == "Windows" else ":"
    classpath = [str(version_jar)] + libraries
    
    # check if exist
    missing = [p for p in classpath if not os.path.exists(p)]
    if missing:
        print(missing)
        # input(missing)
    
    return f'"{separator.join(classpath)}"'.replace("\\", '/')

def get_assetIndex(dotminecraft_dir, version) -> str:
    version_json_path = f"{dotminecraft_dir}/{version}/{version}.json"
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except FileNotFoundError:
        input("version.JSON not found ")
    except json.JSONDecodeError:
        input("version.JSON decode err")
    return version_data["assets"]

def gen_random_uuid():
    chars = "1234567890abcdef"
    uuid = ""
    for i in range(32):
        uuid = uuid + chars[random.randint(0,15)]
    return uuid

def get_jvm_args(dotminecraft_dir, version):
    version_json_path = f"{dotminecraft_dir}/{version}/{version}.json"
    d_args = ["-Dfml.ignoreInvalidMinecraftCertificates=True", 
            "-Djdk.lang.Process.allowAmbiguousCommands=true", 
            "-Dfml.ignorePatchDiscrepancies=True", 
            "-Dlog4j2.formatMsgNoLookups=true", 
            f'"-Djava.library.path={dotminecraft_dir}/{version}/{version}-natives"']
    cp_args = get_cp_args(dotminecraft_dir, version)
    with open(version_json_path, 'r') as f:
        version_json = json.loads(f.read())
    if os.path.exists(f"{dotminecraft_dir}/{version}/.fabric"): # --add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED
        d_args.append("--add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED")
    if "arguments" in version_json and "jvm" in version_json["arguments"]:
        args = version_json["arguments"]["jvm"]
        replacer = {"${natives_directory}": f'{dotminecraft_dir}/{version}/{version}-natives',
                    "${classpath}": cp_args,
                    "${launcher_name}": "minecraft-launcher",
                    "${launcher_version}": "1.0.0.0"}
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
    return args_text

def rmver(dotminecraft_dir, version):
    shutil.rmtree(f'{dotminecraft_dir}/{version}')

def launch(javaw, xmx, dotminecraft_dir, version, javawrapper, username="steve", xmn="256M") -> str: #dotminecraft_dir: "xxx/xxx/.minecraft"; version: "1.8.9"
    # all of the items in lists are NOT ended with space!!!
    # -x args (JVM stuff)
    dotminecraft_dir = dotminecraft_dir.replace('\\', '/')
    x_args = [f"-Xmx{xmx}", 
            f"-Xmn{xmn}", 
            "-XX:+UseG1GC", 
            "-XX:-UseAdaptiveSizePolicy", 
            "-XX:-OmitStackTraceInFastThrow"]
    # -d args (jvm system properties)
    d_args = get_jvm_args(dotminecraft_dir, version)
    # class path args (powered by DeepSeek) -> get_jvm_args() so needless line
    # cp_args = get_cp_args(dotminecraft_dir, version)
    # minecraft args
    uuid = gen_random_uuid()
    minecraft_args = get_minecraft_args(dotminecraft_dir, version)
    if type(minecraft_args) == list:
        minecraft_args_cp = minecraft_args[0]
        minecraft_args_minecraft = minecraft_args[1]
        split_cp_from_minecraft_args = True
    else:
        minecraft_args_minecraft = minecraft_args
        split_cp_from_minecraft_args = False
    mainClass = get_mainclass(dotminecraft_dir, version)
    minecraft_args = mainClass + ' ' + minecraft_args_minecraft + " -width 854 -height 480"
    replacer = {"${auth_player_name}": username,
                "${version_name}": version, 
                "${auth_session}": uuid, 
                "${game_directory}": dotminecraft_dir+'/'+version,
                "${assets_root}": dotminecraft_dir+'/assets',
                "${game_assets}": dotminecraft_dir+f'/{version}/resources', # C:\Users\magic\Documents\projects\LauncherX\.minecraft\1.0\resources
                "${assets_index_name}": get_assetIndex(dotminecraft_dir, version),
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
    if split_cp_from_minecraft_args:
        final = f'{javaw} {x_args} {d_args} {minecraft_args_cp} -jar "{javawrapper}" {mainClass} {minecraft_args_minecraft}'
    else:
        final = f'{javaw} {x_args} {d_args} -jar "{javawrapper}" {minecraft_args}'
    # final = final.replace('/', '\\')
    return final