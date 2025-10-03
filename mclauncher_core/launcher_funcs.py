from mclauncher_core.oauth_funcs import get_mc_token, get_mslogin_uuid_name
from mclauncher_core.tool_funcs import *
from mclauncher_core.modloader_fabric import is_fabric
import json, random, shutil, requests


client_id = "7000942a-0525-4e21-a817-faf950ab6bc4"
def check_java_available(java_binary_path, minecraft_dir, version_name) -> bool:
    """查看java是否符合要求 (不在launch()中使用)，返回bool"""
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        raw = f.read()
    version_json = json.loads(raw)
    if "javaVersion" in version_json and "majorVersion" in version_json["javaVersion"]:
        required_version = version_json["javaVersion"]["majorVersion"]
        return get_java_version(java_binary_path)[0] == required_version
    else:
        return False

def get_required_java_version(minecraft_dir, version_name):
    """查看需要的java版本，返回[8,17,21]类似"""
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
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
    if raw.status_code == 200:
        manifest = raw.json()
        return manifest
    else:
        raise Exception(f"Request Fail: {raw.status_code}\nurl: {url}")

def get_mainclass(minecraft_dir, version_name) -> str:
    """获取Minecraft版本的mainClass，Fabric为'net.fabricmc.loader.impl.launch.knot.KnotClient'，返回str"""
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


def get_minecraft_libraries(minecraft_dir, version_name) -> list:
    """获取minecraft的所有需要libraries(库)，返回list"""
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
        """{
            "name": "org.ow2.asm:asm:9.8",
            "url": "https://maven.fabricmc.net/",
            "md5": "f5adf3bfc54fb3d2cd8e3a1f275084bc",
            "sha1": "dc19ecb3f7889b7860697215cae99c0f9b6f6b4b",
            "sha256": "876eab6a83daecad5ca67eb9fcabb063c97b5aeb8cf1fca7a989ecde17522051",
            "sha512": "cbd250b9c698a48a835e655f5f5262952cc6dd1a434ec0bc3429a9de41f2ce08fcd3c4f569daa7d50321ca6ad1d32e131e4199aa4fe54bce9e9691b37e45060e",
            "size": 126113
        },
        {"""
        if not "downloads" in lib:  # For fabric stuff format like that
            # first we need to get the path of file like org/ow2/asm/asm/9.8
            name = lib['name'].split(':')
            # name = lib['name'].replace(':', '$SEP$')
            name[0] = name[0].replace('.', '$SEP$')
            filename = '-'.join(name[1:]) + '.jar'
            # Forge特例
            if lib['name'].split(':')[0] == 'net.minecraftforge':
                filename = filename.replace('.jar', '-universal.jar')
            name = "$SEP$".join(name)
            path = name.replace("$SEP$", '/')
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
            else:  # DEBUG
                if 'downloads' in lib and 'artifact' in lib['downloads'] and 'path' in lib['downloads']['artifact']:
                    lib_path = lib["downloads"]["artifact"]["path"]
                else:
                    name = lib['name'].split(':')  # [org.ow2.asm,asm,9.8]
                    name[0] = name[0].replace('.', '$SEP$')  # [org$SEP$ow2$SEP$asm,asm,9.8]
                    filename = '-'.join(name[1:]) + '.jar'  # asm-9.8.jar
                    name = "$SEP$".join(name)  # org$SEP$ow2$SEP$asm$SEP$asm$SEP$9.8
                    lib_path = name.replace("$SEP$", '/')  # org/ow2/asm/asm/9.8
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
        print(lib['name'])
    return libraries


def get_minecraft_args(minecraft_dir, version, version_name) -> str:
    """获取Minecraft参数，返回str"""
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
        if not '-cp' in args_list:
            args_list.insert(0, "-cp " + get_cp_args(minecraft_dir, version, version_name))
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


def get_cp_args(minecraft_dir, version, version_name) -> str:
    """获取classpath参数，返回str"""
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


def get_assetIndex(minecraft_dir, version_name) -> str:
    """获取assetIndex(素材索引)，返回str"""
    version_json_path = f"{minecraft_dir}/versions/{version_name}/{version_name}.json"
    try:
        with open(version_json_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    except FileNotFoundError:
        input("version.JSON not found ")
    except json.JSONDecodeError:
        input("version.JSON decode err")
    return version_data["assets"]


def gen_random_uuid():
    """生成随机uuid，小写，返回str"""
    chars = "1234567890abcdef"
    uuid = ""
    for i in range(32):
        uuid = uuid + chars[random.randint(0, 15)]
    # return uuid.upper()
    return uuid


def get_jvm_args(minecraft_dir, version, version_name):
    """获取指定版本Minecraft的jvm参数(-D)，返回str"""
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
    if os.path.exists(
            f"{minecraft_dir}/versions/{version_name}/.fabric"):  # --add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED
        d_args.append("--add-exports cpw.mods.bootstraplauncher/cpw.mods.bootstraplauncher=ALL-UNNAMED")
    if "arguments" in version_json and "jvm" in version_json["arguments"]:
        args = version_json["arguments"]["jvm"]
        # fix for neoforge '-p' argument
        if '-p' in args:
            position = args.index('-p')
            args.pop(position)  # pop -p
            args.pop(
                position)  # pop "${library_directory}/net/neoforged/fancymodloader/bootstraplauncher/9.0.18/bootstraplauncher-9.0.18.jar${classpath_separator}${library_directory}/net/neoforged/fancymodloader/securejarhandler/9.0.18/securejarhandler-9.0.18.jar${classpath_separator}${library_directory}/net/neoforged/JarJarFileSystems/0.4.1/JarJarFileSystems-0.4.1.jar"
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


def remove_version(minecraft_dir, version_name):
    """删除指定版本Minecraft的natives,jar,json文件，libraries与assets将保留，返回None"""
    shutil.rmtree(f'{minecraft_dir}/versions/{version_name}')


def get_installed_versions(minecraft_dir):
    return os.listdir(minecraft_dir + '/versions')


def get_minecraft_version(minecraft_dir, version_name):
    """从json中获取Minecraft版本，返回str"""
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'r') as f:
        version_json = json.loads(f.read())
    if 'id' in version_json:
        return version_json['id']
    elif "inheritsFrom" in version_json:
        return version_json["inheritsFrom"]
    else:
        raise FileNotFoundError("version.json seems invalid")


def launch(javaw, xmx, minecraft_dir, version_name, javawrapper=None, username="steve", xmn="256M", ms_login=False,
           access_token=None) -> str:
    """生成启动脚本，返回str"""
    # all of the items in lists are NOT ended with space!!!
    # -x args (JVM stuff)
    version = get_minecraft_version(minecraft_dir, version_name)
    minecraft_dir = minecraft_dir.replace('\\', '/')
    x_args = [f"-Xmx{xmx}",
              f"-Xmn{xmn}",
              "-XX:+UseG1GC",
              "-XX:-UseAdaptiveSizePolicy",
              "-XX:-OmitStackTraceInFastThrow"]
    # -d args (jvm system properties)
    d_args = get_jvm_args(minecraft_dir, version, version_name)
    # minecraft args
    # 处理正版登录
    if ms_login:
        if access_token == None:
            access_token = get_mc_token()
        uuid = get_mslogin_uuid_name(access_token)[0]
    else:
        uuid = gen_random_uuid()
        access_token = uuid
    minecraft_args = get_minecraft_args(minecraft_dir, version, version_name)

    if type(minecraft_args) == list:
        minecraft_args_cp = minecraft_args[0]
        minecraft_args_minecraft = minecraft_args[1]
        split_cp_from_minecraft_args = True
    else:
        minecraft_args_minecraft = minecraft_args
        split_cp_from_minecraft_args = False
    mainClass = get_mainclass(minecraft_dir, version_name)
    minecraft_args = mainClass + ' ' + minecraft_args_minecraft + " -width 854 -height 480"

    replacer = {"${auth_player_name}": username,
                "${version_name}": version_name,
                "${auth_session}": uuid,
                "${game_directory}": minecraft_dir + '/versions/' + version_name,
                "${assets_root}": minecraft_dir + '/assets',
                "${game_assets}": minecraft_dir + f'/versions/{version_name}/resources',
                "${assets_index_name}": get_assetIndex(minecraft_dir, version_name),
                "${auth_uuid}": uuid,
                "${auth_access_token}": access_token,
                "${user_properties}": "{}",
                "${user_type}": "msa",
                "${version_type}": '"Ciallo uwu."'}
    if ms_login:
        replacer['${auth_player_name}'] = get_mslogin_uuid_name(access_token)[1]
    print(ms_login)
    for i in replacer:
        if split_cp_from_minecraft_args:
            minecraft_args_minecraft = minecraft_args_minecraft.replace(i, replacer[i])
        else:
            minecraft_args = minecraft_args.replace(i, replacer[i])
    x_args = ' '.join(x_args)
    final_pt1 = f'"{javaw}" {x_args} {d_args}'
    if native() == 'windows':
        if javawrapper != None:
            javawrapper_arg = f'-jar "{javawrapper}"'
        else:
            raise SyntaxError("Unspecified JavaWrapper on Windows Platform.")
    else:
        javawrapper_arg = ''
    if split_cp_from_minecraft_args:
        final_pt2 = f'{minecraft_args_cp} {javawrapper_arg} {mainClass} {minecraft_args_minecraft}'
    else:
        final_pt2 = f'{javawrapper_arg} {minecraft_args}'
    # final = final.replace('/', '\\')
    final = final_pt1 + ' ' + final_pt2
    final = final.replace('${version_name}', version_name)
    final = final.replace('${library_directory}', f'{minecraft_dir}/libraries')

    replacer_mslogin = {
        '${clientid}': client_id
    }

    final = final.split(' ')

    i = len(final)
    while final.count('-cp') != 1:
        i -= 1
        if final[i] == '-cp':
            final.pop(i)
            final.pop(i)
            break

    final = ' '.join(final)

    return final