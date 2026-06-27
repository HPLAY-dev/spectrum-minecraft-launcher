import requests


BadForgeVersion = Exception('Bad Forge Version')
def get_versions(mcversion):
    url = f"https://bmclapi2.bangbang93.com/optifine/{mcversion}"
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

def download_optifine(minecraft_dir, instance_name, mcversion, forge_version):
    versions = get_versions(mcversion)
    _ = 0
    for v in versions:
        if v['forge'] == forge_version:
            selected = v
            _ = 1
            continue
    if not _:
        raise BadForgeVersion

    optifine_type = selected['type']
    patch = selected['patch']
    filename = selected['filename']
    url = f"https://bmclapi2.bangbang93.com/optifine/{mcversion}/{optifine_type}/{patch}"
    item = requests.get(url)
    if item.status_code != 200:
        raise Exception('Cannot connect to bmclapi')
    data = item.content

    with open(f'{minecraft_dir}/versions/{instance_name}/mods/{filename}', 'wb') as file:
        file.write(data)