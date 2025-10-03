import requests

BadForgeVersion = Exception('Bad Forge Version')
def get_versions(version):
    url = f"https://bmclapi2.bangbang93.com/optifine/{version}"
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception('Cannot connect to bmclapi')
    data = item.json()
    try:
        if not data['forge'].startswith('Forge #'):
            raise Exception('Bad format')
        result = {
            "forge_version": data['forge'][6:],
            "filename": data['filename'],
            "type": data['type'],
            "patch": data['patch']
        }
        return result
    except:
        return None

def download_optifine(minecraft_dir, version_name, version, forge_version):
    versions = get_versions(version)
    _ = 0
    for v in versions:
        if v['forge'] == forge_version:
            version = v
            _ = 1
            continue
    if not _:
        raise BadForgeVersion

    optifine_type = version['type']
    patch = version['patch']
    filename = version['filename']
    url = f"https://bmclapi2.bangbang93.com/optifine/{version}/{optifine_type}/{patch}"
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception('Cannot connect to bmclapi')
    data = item.content

    with open(f'{minecraft_dir}/versions/{version_name}/mods/{filename}', 'wb') as file:
        file.write(data)