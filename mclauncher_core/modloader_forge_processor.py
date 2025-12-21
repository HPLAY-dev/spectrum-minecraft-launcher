import requests
import os
import typing
import zipfile

def read_main_class_from_zip(zip_path):
    """
    从ZIP文件的META-INF/MANIFEST.MF中读取Main-Class属性
    
    Args:
        zip_path (str): ZIP文件路径
        
    Returns:
        str: Main-Class的值，如果找不到则返回None
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 尝试读取MANIFEST.MF文件
            manifest_path = 'META-INF/MANIFEST.MF'
            
            if manifest_path in zf.namelist():
                # 读取文件内容
                with zf.open(manifest_path) as manifest_file:
                    content = manifest_file.read().decode('utf-8')
                    
                    # 逐行解析，查找Main-Class
                    for line in content.splitlines():
                        # 处理续行情况（以空格开头的行是续行）
                        if line.strip() and not line.startswith(' '):
                            if line.startswith('Main-Class:'):
                                # 提取Main-Class的值
                                main_class = line.split(':', 1)[1].strip()
                                return main_class
                    
                    # 如果没有找到Main-Class
                    return None
            else:
                print(f"未找到 {manifest_path}")
                return None
                
    except FileNotFoundError:
        print(f"文件未找到: {zip_path}")
        return None
    except zipfile.BadZipFile:
        print(f"不是有效的ZIP文件: {zip_path}")
        return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

def processors(install_profile, working_dir: str, minecraft_version_path: str, version, forge_version, minecraft_dir, java_path: str='java'):
    # 处理data
    concatenated_version = version + '-' + forge_version
    libraries_path = os.path.join(minecraft_dir, 'libraries')
    forge_patched = os.path.join(libraries_path, 'net', 'minecraftforge', 'forge', concatenated_version, 'forge-' + concatenated_version + '-client.jar')
    replacer = {
        '{INSTALLER}': os.path.join(working_dir, 'forge_installer.zip'),
        '{ROOT}': os.path.join(working_dir, 'forge_installer', 'data'),
        '{SIDE}': 'client',
        '{MINECRAFT_JAR}': minecraft_version_path + f'/{os.path.basename(minecraft_version_path)}.jar',
        '{MC_UNPACKED}': '{MC_UNPACKED}',
        '{MC_OFF_SHA}': '{MC_OFF_SHA}',
        '{BINPATCH}': '{BINPATCH}',
        '{PATCHED}': forge_patched,
        '{MOJMAPS}': 'MOJMAPS'
    }
    for i in install_profile['data']:
        replacer['{'+i+'}'] = install_profile['data'][i]['client']
    replacer['{MOJMAPS}'] = 'MOJMAPS'
    # net/minecraftforge/forge/1.21.10-60.0.1/forge-1.21.10-60.0.1-client.jar
    replacer['{MC_OFF}'] = os.path.join(minecraft_dir, 'net', 'minecraftforge', 'forge', concatenated_version, f'forge-{concatenated_version}-client.jar')

    
    # 处理libraries
    for i in install_profile['libraries']:
        
        if not ('downloads' in i and 'artifact' in i['downloads']):
            raise Exception('Library download info missing')
        path = os.path.join(working_dir, 'libraries', i['downloads']['artifact']['path'])
        dirpath = os.path.dirname(path)
        os.makedirs(dirpath, exist_ok=True)
        url = i['downloads']['artifact']['url']
        item = requests.get(url)
        if item.status_code != 200:
            raise Exception(f"Request Fail: {item.status_code}\nurl: {url}")
        
        content = item.content
        
        with open(path, 'wb') as f:
            f.write(content)
        
        # brkpnt
    
    #处理processors
    for i in install_profile['processors']:
        # check if needed
        if ('sides' in i and 'client' in i['sides']) or (not 'sides' in i):
            #    e.g. "net.minecraftforge:ForgeAutoRenamingTool:1.0.6"
            # -> working_dir/libraries/net/minecraftforge/ForgeAutoRenamingTool/1.0.6/ForgeAutoRenamingTool-1.0.6.jar

            def coord_to_relpath(coord: str) -> str:
                # support coordinates like:
                #   group:artifact:version
                #   group:artifact:version:classifier
                #   group:artifact:version@packaging
                #   group:artifact:version:classifier@packaging
                packaging = 'jar'
                raw = coord
                if '@' in raw:
                    raw, packaging = raw.rsplit('@', 1)
                parts = raw.split(':')
                if len(parts) < 3:
                    raise ValueError(f"Invalid maven coordinate: {coord}")
                group = parts[0]
                artifact = parts[1]
                version = parts[2]
                classifier = None
                if len(parts) >= 4 and parts[3]:
                    classifier = parts[3]

                filename = artifact + '-' + version
                if classifier:
                    filename += '-' + classifier
                filename += '.' + packaging

                rel = os.path.join(group.replace('.', os.sep), artifact, version, filename)
                return rel

            jar_coord = i.get('jar')
            if not jar_coord:
                raise ValueError('processor entry missing "jar" coordinate')

            jar_relative_path = coord_to_relpath(jar_coord)
            jarpath = os.path.join(working_dir, 'libraries', jar_relative_path)

            if not os.path.exists(jarpath):
                raise FileNotFoundError(f"Processor jar not found: {jarpath}")

            # build classpath (absolute paths to dependent jars)
            classpath_jars = []
            for cp_coord in i.get('classpath', []):
                cp_rel = coord_to_relpath(cp_coord)
                cp_path = os.path.join(working_dir, 'libraries', cp_rel)
                if not os.path.exists(cp_path):
                    raise FileNotFoundError(f"Processor classpath jar not found: {cp_path}")
                classpath_jars.append(cp_path)

            # At this point `jarpath` is the processor jar and `classpath_jars` is a list
            # of dependency jars in `working_dir/libraries/...` ready to be used when
            # invoking the processor (e.g. via java -cp ...)

            # Now, we execute the processor
            sep = ';' if os.name == 'nt' else ':'
            args = ' '.join(i['args'])
            classpath_jars.append(jarpath)
            mainClass = read_main_class_from_zip(jarpath)
            cmd = java_path + ' -cp ' + sep.join(classpath_jars) + ' ' + mainClass + ' ' + args
            if os.name == 'nt':
                cmd = cmd.replace('/', '\\')
            for r in replacer:
                cmd = cmd.replace(r, replacer[r])
            
            print(cmd)