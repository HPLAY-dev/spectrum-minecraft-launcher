import mclauncher_core as launch
import json
import os

bmclapi = False
path = os.path.dirname(os.path.abspath(__file__))
# read json
exec_path = path.replace('\\', '/')
jwrapper_path_guess = exec_path +'/JavaWrapper.jar'
json_path = exec_path + '/config.json'

if os.path.exists(json_path):
    with open(json_path, 'r') as file:
        jsonfile = json.loads(file.read())

if os.path.exists(jwrapper_path_guess):
    java_wrapper_path = jwrapper_path_guess
else:
    java_wrapper_path = input("Enter JavaWrapper.jar Path>")

try:
    java_path = jsonfile['java_path']
    memmax = jsonfile['memmax']
    minecraft_dir = jsonfile['minecraft_dir']
    version = jsonfile['version']
    playername = jsonfile['playername']
except:
    java_path = ''
    memmax = ''
    minecraft_dir = ''
    version = ''
    playername = ''
def rgb(text, bold):
    length = len(text)
    result = []
    for i, char in enumerate(text):
        if i < length / 2:
            r = int(255 * (1 - 2 * i / length))
            g = int(255 * (2 * i / length))
            b = 0
        else:
            r = 0
            g = int(255 * (2 * (1 - i / length)))
            b = int(255 * (2 * i / length - 1))
        if bold:
            color_code = f"\033[1;38;2;{r};{g};{b}m"
        else:
            color_code = f"\033[38;2;{r};{g};{b}m"
        result.append(f"{color_code}{char}")
    result.append("\033[0m")
    return ''.join(result)

def color(text, bold, start_color, end_color):
    length = len(text)
    result = []
    r1, g1, b1 = start_color
    r2, g2, b2 = end_color
    for i, char in enumerate(text):
        ratio = i / (length - 1) if length > 1 else 0
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        style = "1;" if bold else ""
        color_code = f"\033[{style}38;2;{r};{g};{b}m"
        result.append(f"{color_code}{char}")
    result.append("\033[0m")
    return ''.join(result)

def refresh_lines():
    global lines
    if bmclapi:
        bmclapi_yn = 'y'
    else:
        bmclapi_yn = 'n'
    lines = ["Java Executable: " + java_path,    #1
            "Memory:          " + memmax,       #2
            ".minecraft path: " + minecraft_dir,#3
            "Version:         " + version,      #4
            "Player Name:     " + playername,   #5
            "----------------",
            "Start Minecraft",
            "Remove Version",
            "Save Config",
            "Install(Fix) Version",
            "Exit Launcher",  #6,
            f"[{bmclapi_yn}] BMCLAPI",]
tops = [f"{rgb('Spectrum Launcher', True)} ver 1.0",
        "----------------"]

def printmain():
    for top_line in tops:
        print(top_line)
    i = 0
    for line in lines:
        if line != '----------------':
            i += 1
            print(color(f"[{i}]" , False, [0, 122, 255], [0, 122, 255]) + line)
        else:
            print(line)
KeepGoing = True
while KeepGoing:
    minecraft_dir = minecraft_dir.replace("\\", '/')
    refresh_lines()
    printmain()
    choice = input("Enter choice: ")
    try:
        choice = int(choice)
    except:
        input("Invalid Choice\n Press Enter to continue")
        continue

    if choice == 1:
        java_path = input('>')
    elif choice == 2:
        memmax = input('(<int>[M,G])>')
    elif choice == 3:
        minecraft_dir = input('>')
    elif choice == 4:
        try:
            versions = os.listdir(minecraft_dir)
            i = 0
            exclude_folder = ['assets', 'crash-reports', 'libraries', 'versions']
            while i < len(versions):
                if versions[i] in exclude_folder:
                    del versions[i]
                else:
                    i += 1
            print("Installed Versions")
            for i in range(len(versions)):
                print(f'[{i}] ' + versions[i])

            version = int(input('>'))
            if version < len(versions) and version >= 0:
                version = versions[version]

        except:
            print('To list version possible, set a valid ".minecraft path" first.')
            version = input('>')
    elif choice == 5:
        playername = input('>')
    elif choice == 6:
        launch.launch(java_path, memmax, minecraft_dir, version, java_wrapper_path, playername)
        os.system(exec_path+'/latestlaunch.bat'.replace('\\', '/'))
    elif choice == 7:
        if input('Are you sure[y/n]').lower() == 'y':
            launch.rmver(minecraft_dir, version)
    elif choice == 8:
        write = json.dumps({'java_path': java_path,
                    'memmax': memmax,
                    'minecraft_dir': minecraft_dir,
                    'version': version,
                    'playername': playername})
        with open(exec_path+"/config.json", 'w') as f:
            f.write(write)
    elif choice == 9:
        v = input('>')
        vs = launch.get_version_list(bmclapi)
        if v in vs:
            launch.auto_download(minecraft_dir, v, bmclapi=bmclapi)
        else:
            print("version not found")
        # try:
        #     launch.auto_download(minecraft_dir, input('>'))
        # except:
        #     print("Fail to download version")
    elif choice == 10:
        KeepGoing = False
    elif choice == 11:
        bmclapi = not bmclapi
    #     java_path = jsonfile['java_path']
    #     memmax = jsonfile['memmax']
    #     minecraft_dir = jsonfile['minecraft_dir']
    #     version = jsonfile['version']
    #     playername = jsonfile['playername']