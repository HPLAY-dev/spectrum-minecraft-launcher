import requests, json, os
import xml.etree.ElementTree as ET


def is_fabric(minecraft_dir, version_name) -> bool:
    '''检测版本是否为Fabric，返回bool'''
    with open(minecraft_dir + '/versions/' + version_name + '/' + version_name + '.json', 'r') as f:
        if "fabric-loader" in f.read():
            return True
        else:
            return False

def fabric_merge_json(path_a, path_b, modify=True) -> dict:
    '''合并Fabric与Minecraft的Json并进行处理，返回dict'''
    with open(path_a, 'r') as f:
        json_a = json.loads(f.read())  # fabric
    with open(path_b, 'r') as f:
        json_b = json.loads(f.read())  # mineccraft
    lib_b = json_b['libraries']
    json_b.update(json_a)
    json_b['libraries'].extend(lib_b)
    for i in range(len(json_b['libraries'])):
        if json_b['libraries'][i][
            'name'] == 'org.ow2.asm:asm:9.6':  # 我怎么感觉这么写会出事呢awa， 本意是要丢掉minecraft版本json里与fabric重复的asm项，有空(也不一定)改，（主打一个能跑就行awa）
            json_b['libraries'].pop(i)
            break

    return json_b

def parse_xml(url=str) -> dict:
    '''处理xml，返回dict'''
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

def get_fabric_installer_versions() -> list:
    '''搜索metadata获得所有Fabric-Loader版本，最后一项最新，返回list，'''
    return \
    parse_xml(url='https://maven.fabricmc.net/net/fabricmc/fabric-loader/maven-metadata.xml')['metadata']['versioning'][
        'versions']

def download_fabric_api(minecraft_dir, version, version_name, mod_version='latest') -> None:
    '''下载Fabric API(一个Mod)'''
    metadata = parse_xml('https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/maven-metadata.xml')
    available = []
    for i in metadata['metadata']['versioning']['versions']:
        if '+' + version in i:
            available.append(i)
    if mod_version == 'latest':
        mod_version = available[-1]
    url = f'https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/{mod_version}/fabric-api-{mod_version}.jar'
    raw = requests.get(url)
    if raw.status_code != 200:
        raise Exception(f"Request Fail: {raw.status_code}\nurl: {url}")
    with open(f'{minecraft_dir}/versions/{version_name}/mods/fabric-api-{mod_version}.jar', 'wb') as f:
        f.write(raw.content)

def get_latest_fabric_loader_version() -> str:
    '''搜索metadata获得最新Fabric-Loader版本，返回str'''
    return \
    parse_xml(url='https://maven.fabricmc.net/net/fabricmc/fabric-loader/maven-metadata.xml')['metadata']['versioning'][
        'release']

def get_fabric_versions() -> list:
    '''获得所有fabric版本'''
    return \
    parse_xml(url='https://maven.fabricmc.net/net/fabricmc/fabric-loader/maven-metadata.xml')['metadata']['versioning'][
        'versions']

def download_fabric_json(minecraft_dir, version, version_name, loader_version='latest') -> None:
    '''下载Fabric-Loader的JSON文件到.minecraft/versions/{version_name}/Fabric.json，用于和当前版本的Minecraft的json合并'''
    if loader_version == 'latest':
        loader_version = get_latest_fabric_loader_version()
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
