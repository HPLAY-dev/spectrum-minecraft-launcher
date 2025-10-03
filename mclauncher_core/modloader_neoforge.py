import requests, json, shutil, zipfile as zipf
from mclauncher_core.tool_funcs import *
from mclauncher_core.manifest_funcs import get_version_json


def get_neoforge_version(version) -> dict:
    """获取支持此Minecraft版本的Neoforge"""
    url = 'https://bmclapi2.bangbang93.com/neoforge/list/' + version
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
    return item.json()


def download_neoforge_json(minecraft_dir, version, version_name, neoforge_version='latest', bmclapi=False) -> None:
    if neoforge_version == 'latest':
        neoforge_version = get_neoforge_version(version)[-1]
        path = neoforge_version['installerPath']
        if path.split('/')[1] == 'maven':
            path = '/'.join(path.split('/')[2:])
        else:
            raise Exception("Format Unknown")
        url = 'https://maven.neoforged.net/' + path
    else:
        for i in get_neoforge_version(version):
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

    with zipf.ZipFile(get_file_path() + "/temp/neoforge_installer.zip", 'r') as file:
        file.extractall(get_file_path() + "/temp/neoforge_installer")

    if not os.path.exists(get_file_path() + "/temp/neoforge_installer/version.json"):
        raise Exception("Cannot find version.json in downloaded neoforge installer")

    with open(get_file_path() + "/temp/neoforge_installer/version.json", 'r') as f:
        neoforge_json = json.loads(f.read())

    version_json = get_version_json(version, bmclapi)
    original_libs = version_json['libraries']
    version_json.update(neoforge_json)
    version_json['libraries'].extend(original_libs)

    os.makedirs(f'{minecraft_dir}/versions/{version_name}/', exist_ok=True)

    with open(f'{minecraft_dir}/versions/{version_name}/{version_name}.json', 'w') as f:
        f.write(json.dumps(version_json))

    shutil.rmtree(get_file_path() + "/temp")

