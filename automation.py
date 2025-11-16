import os, sys
import mclauncher_core.download_funcs as downloader

import mclauncher_core.launcher_funcs as launcher
# from modrinth_api_wrapper import Client

# client = Client()


def err(text):
    print('[ERR] '+text)
def inf(text):
    print('[ERR] '+text)
def war(text):
    print('[ERR] '+text)

def lnparse(ln, v):
    ln = ln.replace('$$', '$DOLLAR_SYMBOL')
    for i in v:
        ln =  ln.replace('$'+i, 
                    str(v[i])
                        .replace('_', '__')
                        .replace(' ', '_')
                )
    ln = ln.replace('$DOLLAR_SYMBOL', '$')

    ln = ln.replace('__', '$ULINE')
    ln = ln.split()
    for i in range(len(ln)):
        ln[i] = ln[i].replace('_', ' ')
        ln[i] = ln[i].replace('$ULINE', '_')
    return ln

def parseenv():
    global minecraft_dir
    if minecraft_dir:
        minecraft_dir = minecraft_dir.replace('\\', '/')
        minecraft_dir = minecraft_dir[:-1] if minecraft_dir[-1] == '/' else minecraft_dir

# 设置程序路径
if len(sys.argv) > 1:
    program_path = sys.argv[1]
else:
    program_path = input('Program Path: ')

# 打开程序
try:
    with open(program_path, 'r') as f:
        program = f.read().split('\n')
except:
    err('Program cannot be opened')

# 处理
v = {}
cmp = [0,0]
minecraft_dir = ''
javaw = ''
name = ''
modloader = ''
version_name = ''
mcversion = ''
xmx = ''
xmn = '128M'
jwrapper = 'JavaWrapper.jar'
if launcher.native() == 'windows' and not os.path.exists('JavaWrapper.jar'):
    l.javawrapper.download_javawrapper()
bmclapi = False
l = -1
while int(l) < len(program):
    l += 1
    # print(l)
    try:
        ln = program[l].lower()
        if ln.startswith('//') or (' '+ln).isspace():
            continue
        parseenv()
        ln = lnparse(ln, v)
        if ln[0] == 'env':
            if ln[1] == 'mcdir':
                minecraft_dir = ln[2]
            elif ln[1] == 'java':
                javaw = ln[2]
            elif ln[1] == 'playername':
                name = ln[2]
            elif ln[1] == 'modloader':
                modloader = ln[2]
            elif ln[1] == 'mcversion':
                mcversion = ln[2]
            elif ln[1] == 'vname':
                version_name = ln[2]
            elif ln[1] == 'xmx':
                xmx = ln[2]
            elif ln[1] == 'xmn':
                xmn = ln[2]

            elif ln[1] == 'bmclapi':
                bmclapi = not bmclapi
                print(str(l)+' BMCLAPI is now '+str(bmclapi))
        
        elif ln[0] == 'dlver':
            if minecraft_dir and version_name and mcversion and modloader in ['fabric', 'vanilla', 'forge', 'neoforge']:
                try:
                    downloader.auto_download(minecraft_dir, mcversion, version_name, modloader, bmclapi)
                except Exception as E:
                    err(str(l)+' Exception in executing auto_download: '+str(E))
            else:
                err(str(l)+' Value not suitable for dlver.')
        
        elif ln[0] == 'launch':
            if minecraft_dir and version_name and javaw and xmx and xmn and javawrapper and name:
                launcher.launch(javaw, xmx, minecraft_dir, version_name, javawrapper, name, xmn)
        
        # Variables
        elif ln[0] == 'set':
            v[ln[1]] = ln[2]

        elif ln[0] == 'add':
            v[ln[1]] = str(int(v[ln[1]]) + int(ln[2]))

        elif ln[0] == 'in':
            v[ln[1]] = input(ln[2])

        elif ln[0] == 'out':
            print(ln[1])
        
        elif ln[0] == 'cmp':
            cmp[0], cmp[1] = int(ln[1]), int(ln[2])
        
        elif ln[0] == 'jmp':
            l = int(ln[1])-1
        
        elif ln[0] == 'je':
            if cmp[0] == cmp[1]:
                print("JUMPED")
                l = int(ln[1])-1
        
        elif ln[0] == 'jne':
            if cmp[0] != cmp[1]:
                l = int(ln[1])-1
        
        elif ln[0] == 'jb':
            if cmp[0] < cmp[1]:
                l = int(ln[1])-1
        
        elif ln[0] == 'jbe':
            if cmp[0] <= cmp[1]:
                l = int(ln[1])-1
        
        elif ln[0] == 'ja':
            if cmp[0] > cmp[1]:
                l = int(ln[1])-1
        
        elif ln[0] == 'jae':
            if cmp[0] >= cmp[1]:
                l = int(ln[1])-1
    except Exception as E:
        # err(str(l)+' Parsing command error: '+str(E))
        raise E