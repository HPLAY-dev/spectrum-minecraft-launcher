from mclauncher_core.oauth_funcs import get_mc_token, get_mslogin_uuid_name
from mclauncher_core.tool_funcs import *
from mclauncher_core.java import get_java_version
from mclauncher_core.modloader_fabric import is_fabric
from mclauncher_core.tool_funcs import maven_to_path
import json, random, shutil, requests


client_id = "7000942a-0525-4e21-a817-faf950ab6bc4"


def check_java_available(java_binary_path, minecraft_dir, instance_name) -> bool:
    """查看java是否符合要求 (不在launch()中使用), 返回bool"""
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        raw = f.read()
    version_json = json.loads(raw)
    if "javaVersion" in version_json and "majorVersion" in version_json["javaVersion"]:
        required_version = version_json["javaVersion"]["majorVersion"]
        return get_java_version(java_binary_path) == required_version
    else:
        return False

def get_required_java_version(minecraft_dir, instance_name):
    """查看需要的java版本，返回8,17,21类似"""
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        raw = f.read()
    version_json = json.loads(raw)
    if "javaVersion" in version_json and "majorVersion" in version_json["javaVersion"]:
        required_version = version_json["javaVersion"]["majorVersion"]
        return required_version
    else:
        return None

def get_version_manifest(bmclapi=False) -> dict:
    """获取版本列表卷宗，返回dict"""
    if bmclapi:
        url = "https://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
    else:
        url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    raw = requests.get(url)
    try:
        manifest = raw.json()
        return manifest
    except:
        raise Exception(f"Request Fail: {raw.status_code}\nurl: {url}")

def get_mainclass(minecraft_dir, instance_name) -> str:
    """获取Minecraft版本的mainClass，Fabric为'net.fabricmc.loader.impl.launch.knot.KnotClient'，返回str"""
    # if is_fabric(minecraft_dir, instance_name):
    #     return "net.fabricmc.loader.impl.launch.knot.KnotClient"
    version_json_path = f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json'
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except:
        print("json file not found")
    return version_data["mainClass"]


def get_minecraft_libraries(minecraft_dir, instance_name, detailed=False) -> list:
    """获取minecraft的所有需要libraries(库)，返回list"""
    # read json
    version_json_path = f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json'

    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.loads(f.read())
    except FileNotFoundError:
        print("version.JSON not found ")
        return []

    libraries = []

    for lib in version_data['libraries']:
        # check if required
        if not is_library_required(lib):
            continue
        if detailed:
            libraries.append(lib)
            continue
        lib_path = lib.get('downloads', {}).get('artifact', {}).get('path', None) 
        if lib_path is None:  # For fabric stuff format like that
            lib_path = maven_to_path(lib['name'])
        else:
            lib_path = lib["downloads"]["artifact"]["path"]
        local_path = f'{minecraft_dir}/libraries/{lib_path}'
        if local_path not in libraries:
            libraries.append(local_path)
            print(lib['name'])
    return libraries


def get_minecraft_args(minecraft_dir, mcversion, instance_name) -> str:
    """获取Minecraft参数，返回str"""
    # version_json_path = minecraft_dir +'/versions/' + instance_name + '/' + mcversion + '.json'
    version_json_path = f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json'
    with open(version_json_path, 'r', encoding='utf-8') as f:
        version_data = json.loads(f.read())
    if "minecraftArguments" in version_data:
        return version_data["minecraftArguments"]
    else:
        args_list = []
        for key in version_data["arguments"]["game"]:
            if type(key) != dict:
                args_list.append(key)
            else:
                if 'value' in key and 'rules' in key:
                    for rule in key['rules']:
                        if 'features' in rule:
                            continue
                        if 'os' in rule and rule['os'] == native():
                            if rule['action'] == 'allow':
                                args_list.append(key['value'] if type(key['value']) == int else ' '.join(key['value']))
        return ' '.join(args_list)


def is_library_required(library) -> bool:
    """检测Library是否需要，参数library为get_minecraft_libraries()获得的列表中的每一项，返回bool"""
    if "rules" not in library:
        if 'name' in library:  # Fabric
            if 'natives-' in library['name'] and not f'natives-{native()}' in library['name']:
                print(library['name'])
                allow = False
            else:
                allow = True
        else:
            raise SyntaxError("Broken library.")

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


def get_cp_args(minecraft_dir, mcversion, instance_name) -> str:
    """获取classpath参数，返回str"""
    version_jar = f'{minecraft_dir}/versions/{instance_name}/{instance_name}.jar'

    # get libraries
    libraries = get_minecraft_libraries(minecraft_dir, instance_name)

    # make classpath
    separator = ";" if platform.system() == "Windows" else ":"
    classpath = [str(version_jar)] + libraries

    # check if exist
    missing = [p for p in classpath if not os.path.exists(p)]
    if missing:
        print(missing)
        # input(missing)

    return f'-cp "{separator.join(classpath)}"'.replace("\\", '/')


def get_assetIndex(minecraft_dir, instance_name) -> str:
    """获取assetIndex(素材索引)，返回str"""
    version_json_path = f"{minecraft_dir}/versions/{instance_name}/{instance_name}.json"
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except FileNotFoundError:
        input("version.JSON not found ")
    except json.JSONDecodeError:
        input("version.JSON decode err")
    return version_data["assets"]


def get_assetIndex_json(version_json) -> dict:
    url = version_json['assetIndex']['url']
    item = requests.get(url)
    return json.loads(item.text)

def gen_random_uuid():
    """生成随机uuid，小写，返回str"""
    chars = "1234567890abcdef"
    uuid = ""
    for i in range(32):
        uuid = uuid + chars[random.randint(0, 15)]
    # return uuid.upper()
    return uuid


def get_jvm_args(minecraft_dir, mcversion, instance_name):
    """获取指定版本Minecraft的jvm参数(-D)，返回str"""
    version_json_path = f"{minecraft_dir}/versions/{instance_name}/{instance_name}.json"
    d_args = ["-Dfml.ignoreInvalidMinecraftCertificates=True",
              "-Djdk.lang.Process.allowAmbiguousCommands=true",
              "-Dfml.ignorePatchDiscrepancies=True",
              "-Dlog4j2.formatMsgNoLookups=true",
              f'"-Djava.library.path={minecraft_dir}/versions/{instance_name}/{instance_name}-natives"']
    # if native() == 'windows':
    #     d_args.append("-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump")
    # if native() == 'linux':
    #     d_args.append('-Djava.awt.headless=false')
    #     d_args.append("-Djna.nosys=true")
        # If some problems occurs like AWT... on WSL2(WSLg), just have a look this https://stackoverflow.org.cn/questions/15260989
        # # debug only
        # d_args.append("-Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true -Dorg.lwjgl.opengl.Display.noinput=true")
    cp_args = get_cp_args(minecraft_dir, mcversion, instance_name)
    with open(version_json_path, 'r') as f:
        version_json = json.loads(f.read())
    if is_fabric(minecraft_dir, instance_name):  # --add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED
        d_args.append("--add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED")
    if "arguments" in version_json and "jvm" in version_json["arguments"]:
        args = version_json["arguments"]["jvm"]
        excludes = ['${classpath}', '-cp', '-classpath']
        for i in excludes:
            args.pop(args.index(i)) if i in args else None
        # fix for neoforge '-p' argument
        if '-p' in args:
            position = args.index('-p')
            args.pop(position)  # pop -p
            args.pop(position)  # pop "${library_directory}/net/neoforged/fancymodloader/bootstraplauncher/9.0.18/bootstraplauncher-9.0.18.jar${classpath_separator}${library_directory}/net/neoforged/fancymodloader/securejarhandler/9.0.18/securejarhandler-9.0.18.jar${classpath_separator}${library_directory}/net/neoforged/JarJarFileSystems/0.4.1/JarJarFileSystems-0.4.1.jar"
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
    else:
        args_text = ' '.join(d_args)

    args_text = args_text + ' ' + get_cp_args(minecraft_dir, mcversion, instance_name)
    return args_text


def remove_version(minecraft_dir, instance_name):
    """删除指定版本Minecraft的natives,jar,json文件，libraries与assets将保留，返回None"""
    shutil.rmtree(f'{minecraft_dir}/versions/{instance_name}')


def get_installed_versions(minecraft_dir):
    return os.listdir(minecraft_dir + '/versions')


def get_minecraft_version(minecraft_dir, instance_name):
    """从json中获取Minecraft版本，返回str"""
    with open(f'{minecraft_dir}/versions/{instance_name}/{instance_name}.json', 'r') as f:
        version_json = json.loads(f.read())
    if "id" in version_json:
        return version_json["id"]
    elif "inheritsFrom" in version_json:
        return version_json["inheritsFrom"]
    elif "clientVersion" in version_json: # idk how this appears...
        return version_json["clientVersion"]
    else:
        raise FileNotFoundError("version.json seems invalid")


def launch(javaw, xmx, minecraft_dir, instance_name, javawrapper=None, username: str = "steve", xmn: str="256M", ms_login=False,
           access_token=None, width: int = 854, height: int = 480, version_type: str='§1R§2e§3d§4s§5t§6o§7n§8e §9C§ar§be§ca§dt§ei§fo§1n§2s', 
           jvm_args: str='', game_args_extend: str='', uuid=None) -> str:
    """生成启动脚本，返回str"""
    # all of the items in lists are NOT ended with space!!!
    # -x args (JVM stuff)
    mcversion = get_minecraft_version(minecraft_dir, instance_name)
    minecraft_dir = minecraft_dir.replace('\\', '/')
    if jvm_args == '':
        x_args = [f"-Xmx{xmx}",
                f"-Xmn{xmn}",
                "-XX:+UseG1GC",
                "-XX:-UseAdaptiveSizePolicy",
                "-XX:-OmitStackTraceInFastThrow"]
        if jvm_args != '':
            x_args.append(jvm_args)
        x_args = ' '.join(x_args)

        # -d args (jvm system properties)
        d_args = get_jvm_args(minecraft_dir, mcversion, instance_name)
    jvm_args = x_args+' '+d_args


    # minecraft args
    # 处理正版登录
    if ms_login:
        if access_token == None:
            access_token = get_mc_token() # shouldnt be here...
        if uuid is None:
            uuid = get_mslogin_uuid_name(access_token)[0]
    else:
        if uuid is None:
            uuid = gen_random_uuid()
        access_token = uuid
    minecraft_args = get_minecraft_args(minecraft_dir, mcversion, instance_name)
    if game_args_extend != '':
        minecraft_args.append(game_args_extend)
    mainClass = get_mainclass(minecraft_dir, instance_name)
    minecraft_args = mainClass + ' ' + minecraft_args + f" -width {str(width)} -height {str(height)}"

    if ms_login:
        replacer['${auth_player_name}'] = get_mslogin_uuid_name(access_token)[1]
    print(ms_login)
    if (not "--version" in minecraft_args) and (not "--version" in minecraft_args):
        minecraft_args = minecraft_args + f" --version {version}"
    if (not "-accessToken" in minecraft_args) and (not "--accessToken" in minecraft_args):
        minecraft_args = minecraft_args + f" --accessToken {access_token}"

    # classpath = get_cp_args(minecraft_dir, mcversion, instance_name)
    final_pt1 = f'"{javaw}" {jvm_args}'
    if native() == 'windows':
        if javawrapper != None:
            javawrapper_arg = f'-jar "{javawrapper}"'
        else:
            pass
            # raise SyntaxError("Unspecified JavaWrapper on Windows Platform.")
    else:
        javawrapper_arg = ''
    final_pt2 = f'{javawrapper_arg} {minecraft_args}'
    
    final = final_pt1 + ' ' + final_pt2
    final = final.replace('${version_name}', instance_name)
    final = final.replace('${library_directory}', f'{minecraft_dir}/libraries')


    replacer = {"${auth_player_name}": username,
                "${version_name}": instance_name,
                "${auth_session}": uuid,
                "${game_directory}": minecraft_dir + '/versions/' + instance_name,
                "${assets_root}": minecraft_dir + '/assets',
                "${game_assets}": minecraft_dir + f'/versions/{instance_name}/resources',
                "${assets_index_name}": get_assetIndex(minecraft_dir, instance_name),
                "${auth_uuid}": uuid,
                "${auth_access_token}": access_token,
                "${user_properties}": "{}",
                "${user_type}": "msa",
                "${version_type}": '"'+version_type+'"',
                '-DFabricMcEmu= net': '-DFabricMcEmu=net',
                "${natives_directory}": f'"{minecraft_dir}/versions/{instance_name}/{instance_name}-natives"',
                "${launcher_name}": "minecraft-launcher",
                "${launcher_version}": "1.0.0.0",
                "-Dos.name=Windows 10": '-Dos.name="Windows 10"',
                '{minecraft_dir}': minecraft_dir,
                '${clientid}': client_id,
                '{version}': mcversion}

    for i in replacer:
        final = final.replace(i, replacer[i])
    
    final = f'cd {minecraft_dir}/versions/{instance_name} && ' + final
    return final
