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


def download_forge_json(minecraft_dir, version, version_name, forge_version='latest', bmclapi=False):
    """下载一个包含了Forge的东西的版本json"""
    if forge_version == 'latest':
        forge_versions = get_forge_version(version)
        versions = []
        for ver in forge_versions:
            versions.append(ver["version"])
        forge_version = versions[0]

    url = 'https://bmclapi2.bangbang93.com/forge/download'
    url = url + f'?mcversion={version}&version={forge_version}&category=installer&format=jar'
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    os.makedirs(get_file_path() + "/temp", exist_ok=True)
    with open(get_file_path() + "/temp/forge_installer.zip",
              'wb') as f:  # Of course we downloaded a .jar file, but in order to identify the format, we use .zip
        f.write(item.content)

    with zipf.ZipFile(get_file_path() + "/temp/forge_installer.zip", 'r') as file:
        file.extractall(get_file_path() + "/temp/forge_installer")

    if not os.path.exists(get_file_path() + "/temp/forge_installer/install_profile.json"):
        shutil.rmtree(get_file_path() + "/temp/forge_installer/")
        raise Exception("INSTALL_PROFILE.JSON not found")
    with open(get_file_path() + "/temp/forge_installer/install_profile.json", 'r') as f:
        install_profile = json.loads(f.read())

    if 'versionInfo' in install_profile:
        forge_version_json = install_profile['versionInfo']
        version_json = get_version_json(version, bmclapi)
        original_libs = version_json['libraries']
        version_json.update(forge_version_json)
        version_json['libraries'].extend(original_libs)

    # elif 'libraries' in install_profile:
    #     forge_version_json = install_profile['libraries']
    #     version_json = get_version_json(version, bmclapi)
    #     original_libs = version_json['libraries']
    #     version_json.update(forge_version_json)
    #     version_json['libraries'].extend(original_libs)

    elif os.path.exists(get_file_path() + "/temp/forge_installer/version.json"):
        print(1)
        with open(get_file_path() + "/temp/forge_installer/version.json", 'r') as f:
            forge_version_json = json.loads(f.read())
        version_json = get_version_json(version, bmclapi)
        original_libs = version_json['libraries']
        version_json.update(forge_version_json)
        version_json['libraries'].extend(original_libs)

        for i in range(len(version_json['libraries'])):
            lib = version_json['libraries'][i]
            print(lib['name'])
            if lib['name'] == 'net.minecraftforge:forge:1.21.8-58.0.10:client':
                version_json['libraries'][i][
                    'url'] = 'https://github.com/HPLAY-dev/spectrum-minecraft-launcher/raw/refs/heads/main/misc/forge-1.21.8-58.0.10-client.jar'
    else:
        raise Exception('Error parsing forge json')
    os.makedirs(f'{minecraft_dir}/versions/{version_name}', exist_ok=True)
    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'w') as f:
        f.write(json.dumps(version_json))

    shutil.rmtree(get_file_path() + "/temp")
