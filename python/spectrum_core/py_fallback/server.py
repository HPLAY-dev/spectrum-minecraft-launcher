import json
import requests
import subprocess
import os
import shutil


version_manifest_url = 'https://launchermeta.mojang.com/mc/game/version_manifest.json'
version_manifest_url_bmclapi = 'https://bmclapi2.bangbang93.com/mc/game/version_manifest.json'
'''
Version JSON to {server_path}/versions/{instance_name}/{instance_name}.json
Version JAR(server side) to {server_path}/versions/{instance_name}/server.jar
Version EULA to {server_path}/versions/{instance_name}/eula.txt
'''

def download_server(mcversion, server_path, instance_name, bmclapi=False, server_properties=None):
    '''Download server-side stuff
    Using this function means you agree to the Minecraft EULA.'''
    manifest = requests.get(version_manifest_url).json()
    os.makedirs(f'{server_path}/instances/{instance_name}', exist_ok=True)

    # Download version JSON
    for version in manifest['versions']:
        if version['id'] == mcversion:
            version_json = requests.get(version['url']).json()
            with open(f'{server_path}/instances/{instance_name}/{instance_name}.json', 'w') as f:
                f.write(json.dumps(version_json, indent=4))
            break
    
    # Download server JAR
    server_jar_url = version_json['downloads']['server']['url']
    server_jar_data = requests.get(server_jar_url).content
    with open(f'{server_path}/instances/{instance_name}/server.jar', 'wb') as f:
        f.write(server_jar_data)
    
    # Setup EULA
    with open(f'{server_path}/instances/{instance_name}/eula.txt', 'w') as f:
        f.write('eula=true')
    
    # Setup server.properties
    if server_properties is not None:
        with open(f'{server_path}/instances/{instance_name}/server.properties', 'w') as f:
            f.write(server_properties)

def run_server(server_path, instance_name, java_path='java', xmx='1024M', xms='1024M'):
    '''Run the Minecraft server'''
    command = [
        f'{java_path}'.replace('/', '\\'),
        f"-Xmx{xmx}",
        f"-Xms{xms}",
        "-jar",
        server_path+'/instances/'+instance_name+'/server.jar'.replace('/', '\\'),
        "nogui"
    ]
    print('Running server with command:', ' '.join(command), 'at', server_path+'/instances/'+instance_name)
    result = subprocess.run(
        command,
        cwd=server_path+'/instances/'+instance_name, # 设置工作目录为server.jar所在目�?
        creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    # print(result.stdout)

def get_ip_address() -> str:
    """获取本机IP地址"""
    command = "ipconfig"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    output = result.stdout
    ip_addresses = []
    for line in output.splitlines():
        if "IPv4 地址" in line or "IPv4 Address" in line:
            ip_addresses.append(line.split(":")[-1].strip())
    return ip_addresses

def change_world(server_path, instance_name, world_path):
    '''Set the world for the server'''
    dest_path = f'{server_path}/instances/{instance_name}/world'
    if os.path.exists(dest_path):
        print(f"Removing existing world at {dest_path}")
        shutil.rmtree(dest_path)
    print(f"Copying world from {world_path} to {dest_path}")
    shutil.copytree(world_path, dest_path)

def clean_logs(server_path, instance_name):
    '''Clean the logs folder'''
    logs_path = f'{server_path}/instances/{instance_name}/logs'
    if os.path.exists(logs_path):
        print(f"Cleaning logs at {logs_path}")
        shutil.rmtree(logs_path)
        os.makedirs(logs_path, exist_ok=True)

def whitelist(server_path, instance_name, players: list):
    '''Set the whitelist for the server'''
    whitelist_path = f'{server_path}/instances/{instance_name}/whitelist.json'
    with open(whitelist_path, 'w') as f:
        json.dump(players, f, indent=4)

if __name__ == "__main__":
    # change_world('C:/Users/magic/Documents/projects/LauncherX/.minecraft', 'server', r'C:\Users\magic\Documents\projects\LauncherX\.minecraft\versions\A26-1\saves\1234')
    # print(get_ip_address())
    run_server('C:\\Users\\magic\\Documents\\projects\\LauncherX\\.minecraft', 'server', java_path=r'C:\Program Files\Eclipse Adoptium\jre-25.0.1.8-hotspot\bin\java.exe')