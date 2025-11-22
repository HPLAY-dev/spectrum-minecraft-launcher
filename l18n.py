import json
import platform
import locale
import os


def get_system_locale():
    """跨平台获取系统locale"""
    system = platform.system()
    
    if system == "Windows":
        # Windows系统
        import ctypes
        windll = ctypes.windll.kernel32
        lcid = windll.GetUserDefaultUILanguage()
        return locale.windows_locale[lcid]
    
    elif system == "Darwin":
        # macOS系统
        import subprocess
        try:
            result = subprocess.run(['defaults', 'read', '-g', 'AppleLocale'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            pass
    
    # Linux和其他Unix-like系统
    for var in ['LANG', 'LC_ALL', 'LC_MESSAGES']:
        lang = os.environ.get(var)
        if lang and '.' in lang:
            return lang.split('.')[0]
    
    # 最后尝试locale模块
    try:
        return locale.getdefaultlocale()[0]
    except:
        return 'en_US'


lang = get_system_locale().lower()
lang = 'en_us'
if os.path.exists('languages/'+lang+".json"):
    try:
        with open('languages/'+lang+'.json', 'r', encoding='utf-8') as f:
            langfile = json.loads(f.read())
    except Exception as e:
        print('[l18n] Language File Load Error'+str(e))
elif os.path.exists("languages/en_us.json"):
    try:
        with open('languages/en_us.json', 'r', encoding='utf-8') as f:
            langfile = json.loads(f.read())
    except Exception as e:
        print('[l18n] Language File Load Error'+str(e))
else:
    print('[l18n] Language File Missing')