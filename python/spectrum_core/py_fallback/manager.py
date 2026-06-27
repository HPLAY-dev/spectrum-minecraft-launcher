import shutil, os


def get_saves(minecraft_dir, instance_name):
    saves_path = f'{minecraft_dir}/versions/{instance_name}/saves'
    if os.path.exists(saves_path):
        return os.listdir(saves_path)
    else:
        return []

def remove_save(minecraft_dir, instance_name, save):
    path = f'{minecraft_dir}/versions/{instance_name}/saves/{save}'
    if os.path.exists(path):
        shutil.rmtree(path)

def get_resourcepacks(minecraft_dir, instance_name):
    path = f'{minecraft_dir}/versions/{instance_name}/resourcepacks'
    if os.path.exists(path):
        return os.listdir(path)
    else:
        return []

def remove_resourcepack(minecraft_dir, instance_name, pack):
    path = f'{minecraft_dir}/versions/{instance_name}/resourcepacks/{pack}'
    if os.path.exists(path):
        shutil.rmtree(path)

def get_mods(minecraft_dir, instance_name):
    path = f'{minecraft_dir}/versions/{instance_name}/mods'
    if os.path.exists(path):
        return os.listdir(path)
    else:
        return []

def remove_mod(minecraft_dir, instance_name, mod):
    path = f'{minecraft_dir}/versions/{instance_name}/mods/{mod}'
    if os.path.exists(path):
        shutil.rmtree(path)

def get_shaderpacks(minecraft_dir, instance_name):
    path = f'{minecraft_dir}/versions/{instance_name}/shaderpacks'
    if os.path.exists(path):
        return os.listdir(path)
    else:
        return []

def remove_shaderpack(minecraft_dir, instance_name, pack):
    path = f'{minecraft_dir}/versions/{instance_name}/shaderpacks/{pack}'
    if os.path.exists(path):
        shutil.rmtree(path)

def rename_version(minecraft_dir, instance_name, new_name):
    version_root = minecraft_dir+'/versions/'+instance_name+'/'
    new_root = minecraft_dir+'/versions/'+new_name+'/'
    if (not os.path.exists(version_root)) or (not os.path.exists(version_root+'/')):
        raise Exception('Invalid minecraft version')
    if os.path.exists(f'{version_root}/{instance_name}.json'):
        os.rename(f'{version_root}/{instance_name}.json', f'{version_root}/{new_name}.json')
    if os.path.exists(f'{version_root}/{instance_name}.jar'):
        os.rename(f'{version_root}/{instance_name}.jar', f'{version_root}/{new_name}.jar')
    if os.path.exists(f'{version_root}/{instance_name}-natives'):
        os.rename(f'{version_root}/{instance_name}-natives', f'{version_root}/{new_name}-natives')
    if os.path.exists(version_root):
        os.rename(version_root, new_root)