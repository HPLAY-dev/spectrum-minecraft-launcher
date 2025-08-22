from customtkinter import *
from mclauncher_core import *
from tkinter import messagebox
import locale
import threading
import tkinter as tk
import os
import sys
import json
import subprocess
import platform

def detect_error(stdout, stderr) -> str:
    stdout = stdout.decode(encoding='gbk').split('\r\n')
    stderr = stderr.decode(encoding='gbk')
    if stderr == '':
        return 0
    else:
        stderr = stderr.split('\r\n')
        for line in stderr:
            line = line.split(': ')
            if len(line) == 3:
                return(1,line[1],line[2])

def get_file_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) # EXE
    return os.path.dirname(os.path.abspath(__file__)) # .py

v_snapshot = False
v_release = True
v_old = False
bmclapi = False

lang = 'en_US'
translate = {'en_US': 
    {
        "WindowTitle": "Spectrum Launcher",
        "Fail:Int": "Fail to Int",
        "Title:Version": "Version",
        "Title:Launch": "Launch Options",
        "Title:Download": "Download Options",
        "Title:Misc": "Misc Options",
        "Title:DownloadStatus": "Download Progress",
        "Ctrl:MinecraftPath": ".minecraft Folder",
        "Ctrl:Version": "Version",
        "Ctrl:JavaPath": "Java Path",
        "Ctrl:PlayerName": "Player Name",
        "Ctrl:MaxMem": "JVM Memory Size",
        "Ctrl:WrapperPath": "JavaWrapper Path",
        "Ctrl:VersionName": "Version Name",
        "Ctrl:UseBMCLAPI": "BMCLAPI",
        "Ctrl:DownloadFabric": "Fabric",
        "Ctrl:Download": "Download",
        "Ctrl:Launch": "Launch",
        "Ctrl:SaveCfg": "Save Config",
        "Ctrl:OpenCfg": "Open Config",
        "Ctrl:RefVerList": "Update Version List",
        "Ctrl:ShowSnapshot": "Show Snapshot Versions",
        "Ctrl:ShowAncient": "Show Old Versions",
        "Ctrl:DownloadJavaWrapper": "Download JavaWrapper",
        "Other:Enter Text": "Enter Text",
        "Other:JavaWrapperNeedless": "JavaWrapper not needed on this OS",
        "Text:Installed": "[Installed] ",
        "Title:Language": "Language",
        "Text:None": "None",
        "Ctrl:ModLoader": "ModLoader"
    }
}
if os.path.exists(get_file_path()+'/lang'):
    langs = os.listdir(get_file_path()+'/lang')
    for langname in langs:
        with open(get_file_path()+'/lang/'+langname, 'r', encoding='utf-8') as f:
            jsonfile = json.loads(f.read())
        translate[langname] = jsonfile

if 'default' in langs:
    lang = 'default'
elif locale.getdefaultlocale()[0] in langs:
    lang = locale.getdefaultlocale()[0]
else:
    lang = 'en_US'

def refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=''):
    global versions
    v_list = get_version_list(show_snapshot=show_snapshot, show_old=show_old, show_release=show_release, bmclapi=bmclapi)
    if minecraft_dir == '':
        dir_files = []
    else:
        dir_files = os.listdir(f'{minecraft_dir}/versions')
        if 'assets' in dir_files:
            dir_files.pop(dir_files.index('assets'))
        if 'crash-reports' in dir_files:
            dir_files.pop(dir_files.index('crash-reports'))
        if 'libraries' in dir_files:
            dir_files.pop(dir_files.index('libraries'))
        for i in range(len(dir_files)):
            v_list.insert(0,translate[lang]['Text:Installed']+dir_files[i])
    # return v_list
    versions = v_list

class App(CTk):

    def update_download_progress(self, current, total, message):
        self.after(0, self._update_log, message)
        
    def _update_log(self, message):
        if message[0:5] == "[LIB]":
            prog = message[6:-1].split('/')
            try:
                amount = int(prog[1])
                now = int(prog[0])
            except:
                raise(translate[lang]['FailInt'])
            self.progressbar_lib.set(now/amount)
        elif message[0:5] == "[AST]":
            prog = message[6:-1].split('/')
            try:
                amount = int(prog[1])
                now = int(prog[0])
            except:
                raise(translate[lang]['FailInt'])
            self.progressbar_assets.set(now/amount)

    def __init__(self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)
        if native() == 'windows':
            titlefont = ("SimSun", 24, "bold")
        elif native() == 'osx':
            titlefont = ("San Francisco", 24, "bold")
        else:
            titlefont = ("Noto Sans", 24, "bold")

        if native() == 'windows':
            defaultfont = ("SimSun", 13)
        elif native() == 'osx':
            defaultfont = ("San Francisco", 13)
        else:
            defaultfont = ("Noto Sans", 13)
        

        self.main_frame = CTkFrame(self, fg_color=self.cget("bg"))

        self.main_frame.grid(row=0, column=0, padx=10, pady=10)
        i = 0
        self.title_label = CTkLabel(master=self.main_frame, text=translate[lang]["Title:Version"], font=titlefont)
        self.title_label.grid(row=i, column=0, sticky="w", pady=(0, 10))

        i += 1
        self.mc_path_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:MinecraftPath"], font=defaultfont)
        self.mc_path_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.mc_path_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
        self.mc_path_entry.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        self.ver_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:ModLoader"], font=defaultfont)
        self.ver_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        # versions = get_version_list(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi)
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.ver_combobox = CTkComboBox(master=self.main_frame, state='readonly', values=versions, font=defaultfont)
        self.ver_combobox.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        self.modloader_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:Version"], font=defaultfont)
        self.modloader_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        # versions = get_version_list(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi)
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.modloader_combobox = CTkComboBox(master=self.main_frame, state='readonly', values=['None','Fabric', 'Forge'], font=defaultfont)
        self.modloader_combobox.grid(row=i, column=1, pady=(0, 10), padx=10)
        
        i += 1
        self.title2_label = CTkLabel(master=self.main_frame, text=translate[lang]["Title:Launch"], font=titlefont)
        self.title2_label.grid(row=i, column=0, sticky="w", pady=(0, 10))

        i += 1
        self.javaw_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:JavaPath"], font=defaultfont)
        self.javaw_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.javaw_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
        self.javaw_entry.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        self.name_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:PlayerName"], font=defaultfont)
        self.name_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.name_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
        self.name_entry.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        self.memmax_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:MaxMem"], font=defaultfont)
        self.memmax_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.memmax_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
        self.memmax_entry.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        # Windows only
        if native() == "windows":
            self.wrapper_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:WrapperPath"], font=defaultfont)
            self.wrapper_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
            self.wrapper_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
            self.wrapper_entry.grid(row=i, column=1, pady=(0, 10), padx=10)
        else:
            self.wrapper_label = CTkLabel(master=self.main_frame, text=translate[lang]["Other:JavaWrapperNeedless"], font=defaultfont)
            self.wrapper_label.grid(row=i, column=0, sticky="w", pady=(0, 10))

        i += 1        
        self.title_label = CTkLabel(master=self.main_frame, text=translate[lang]["Title:Download"], font=titlefont)
        self.title_label.grid(row=i, column=0, sticky="w", pady=(0, 10))

        i += 1
        self.ver_name_label = CTkLabel(master=self.main_frame, text=translate[lang]["Ctrl:VersionName"], font=defaultfont)
        self.ver_name_label.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.ver_name_entry = CTkEntry(master=self.main_frame, placeholder_text=translate[lang]["Other:Enter Text"], font=defaultfont)
        self.ver_name_entry.grid(row=i, column=1, pady=(0, 10), padx=10)

        i += 1
        self.dl_bmcl_checkbox = CTkCheckBox(master=self.main_frame, text=translate[lang]["Ctrl:UseBMCLAPI"], font=defaultfont)
        self.dl_bmcl_checkbox.grid(row=i, column=0, sticky="w", pady=(0, 10))
        self.dl_fabric_checkbox = CTkCheckBox(master=self.main_frame, text=translate[lang]["Ctrl:DownloadFabric"], font=defaultfont)
        self.dl_fabric_checkbox.grid(row=i, column=1, sticky="w", pady=(0, 10))

        i += 1        
        self.launch_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:Launch"], font=defaultfont, command=self.launch)
        self.launch_button.grid(row=i, column=1, pady=(0, 10))
        self.launch_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:Download"], font=defaultfont, command=self.download)
        self.launch_button.grid(row=i, column=0, pady=(0, 10))
        
        i = 0
        self.title_label = CTkLabel(master=self.main_frame, text=translate[lang]["Title:Misc"], font=titlefont)
        self.title_label.grid(row=i, column=3, sticky="w", pady=(0, 10))

        i += 1
        self.opencfg_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:OpenCfg"], font=defaultfont, command=self.opencfg)
        self.opencfg_button.grid(row=i, column=3, pady=(0, 10))

        i += 1
        self.savecfg_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:SaveCfg"], font=defaultfont, command=self.savecfg)
        self.savecfg_button.grid(row=i, column=3, pady=(0, 10))

        i += 1
        self.refresh_versions_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:RefVerList"], font=defaultfont, command=self.refresh_versions)
        self.refresh_versions_button.grid(row=i, column=3, pady=(0, 10))

        i += 1
        if native() == 'windows':
            self.dl_jwrapper_button = CTkButton(master=self.main_frame, text=translate[lang]["Ctrl:DownloadJavaWrapper"], font=defaultfont, command=self.download_javawrapper)
            self.dl_jwrapper_button.grid(row=i, column=3, pady=(0, 10))

        i += 1
        self.snapshot_checkbox = CTkCheckBox(master=self.main_frame, text=translate[lang]["Ctrl:ShowSnapshot"], font=defaultfont, command=self.toggle_snapshot)
        self.snapshot_checkbox.grid(row=i, column=3, sticky="w", pady=(0, 10))

        i += 1
        self.old_checkbox = CTkCheckBox(master=self.main_frame, text=translate[lang]["Ctrl:ShowAncient"], font=defaultfont, command=self.toggle_old)
        self.old_checkbox.grid(row=i, column=3, sticky="w", pady=(0, 10))

        i += 1
        self.title_label = CTkLabel(master=self.main_frame, text=translate[lang]["Title:DownloadStatus"], font=titlefont)
        self.title_label.grid(row=i, column=3, sticky="w", pady=(0, 10))

        i += 1
        self.progressbar_lib = CTkProgressBar(master=self.main_frame, width=200)
        self.progressbar_lib.grid(row=i, column=3, sticky="w", pady=(0, 10))
        self.progressbar_lib.set(0)

        i += 1
        self.progressbar_assets = CTkProgressBar(master=self.main_frame, width=200)
        self.progressbar_assets.grid(row=i, column=3, sticky="w",pady=(0, 10))
        self.progressbar_assets.set(0)

        i += 1
        self.title_label = CTkLabel(master=self.main_frame, text=translate['en_US']["Title:Language"], font=titlefont)
        self.title_label.grid(row=i, column=3, sticky="w", pady=(0, 10))

        i += 1
        self.language_combobox = CTkComboBox(master=self.main_frame, state='readonly', values=langs, font=defaultfont, command=self.change_language)
        self.language_combobox.grid(row=i, column=3, pady=(0, 10))

        i += 1
    def change_language(self, value):
        global lang
        lang = value
        
        if value == 'default':
            os.remove(get_file_path()+'/lang/default')
        with open(get_file_path()+'/lang/default', 'w') as f:
            f.write(json.dumps(translate[value]))

    def download(self):
        if not hasattr(self, 'download_thread') or not self.download_thread.is_alive():
            mcdir = self.mc_path_entry.get().replace("\\", '/')
            if not os.path.exists(mcdir):
                messagebox.showerror('Argument Error', 'Cannot find Minecraft Path')
                return 1
            if self.ver_combobox.get()[:len(translate[lang]['Text:Installed'])] == translate[lang]['Text:Installed']: # [Installed] 
                version_name = self.ver_combobox.get()[len(translate[lang]['Text:Installed']):]
                if version_name == '':
                    messagebox.showerror('Argument Error', 'Version Name is blank')
                    return 1
                elif ' ' in version_name:
                    messagebox.showerror('Argument Error', 'Space in Version Name, could cause problem')
                    return 1
                version = get_minecraft_version(mcdir, version_name)
            else:
                version = self.ver_combobox.get()
                version_name = self.ver_name_entry.get()
            modloader = self.modloader_combobox.get()
            if modloader == '' or modloader == translate[lang]['Text:None']:
                modloader = 'vanilla'
            else:
                modloader = modloader.lower()
            bmclapi = self.dl_bmcl_checkbox.get()
            fabric = self.dl_fabric_checkbox.get()
            java = self.javaw_entry.get()
            self.download_thread = threading.Thread(
                target=auto_download,
                args=(mcdir, version, version_name),
                kwargs={
                    "modloader": modloader,
                    "bmclapi": bmclapi,
                    "progress_callback": self.update_download_progress,
                },
                daemon=True)
            self.download_thread.start()

    def refresh_versions(self):
        # global versions
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.ver_combobox.configure(values=versions)

    def toggle_snapshot(self):
        global v_snapshot
        v_snapshot = not v_snapshot
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.ver_combobox.configure(values=versions)

    def toggle_old(self):
        global v_old
        v_old = not v_old
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.ver_combobox.configure(values=versions)

    def launch(self):
        java = self.javaw_entry.get()
        if java == '':
            messagebox.showerror('Argument Error', 'Java is blank')
            return 1
        if native() == 'windows':
            wrapper = self.wrapper_entry.get()
            if not os.path.exists(wrapper):
                messagebox.showerror('Argument Error', 'Cannot find JavaWrapper.jar. Download it first.')
                return 1
        else:
            wrapper = None
        xmx = self.memmax_entry.get()
        if not (xmx[-1] in ['M', 'G'] and xmx[:-1].isdigit):
            messagebox.showerror('Argument Error', 'Max Memory should be a format like this (NUMBER)+(M or G) without parentheses')
            return 1

        mcdir = self.mc_path_entry.get().replace("\\", '/')
        
        if not os.path.exists(mcdir):
            messagebox.showerror('Argument Error', 'Cannot find Minecraft Path')
            return 1
        if self.ver_combobox.get()[:len(translate[lang]['Text:Installed'])] == translate[lang]['Text:Installed']: # [Installed] 
            version_name = self.ver_combobox.get()[len(translate[lang]['Text:Installed']):]
            version = get_minecraft_version(mcdir, version_name)
            player = self.name_entry.get()
            cmd = launch(java, xmx, mcdir, version, version_name, wrapper, username=player)

            if native() == 'windows':
                path = get_file_path()
                path = path.replace('\\', '/') + '/launch.bat'
                with open(path, 'w', encoding='utf-8') as file:
                    file.write(cmd)
            else:
                path = get_file_path()
                path = path + '/launch.sh'
                with open(path, 'w') as file:
                    file.write(cmd)
            if native() == 'windows':
                out = subprocess.Popen(path.replace('/', '\\'), stdout=s.PIPE, stderr=s.PIPE)
                stdout,stderr = out.communicate()
                err = detect_error(stdout,stderr)
                if err != 0:
                    print('Error occured')
                    text = 'Error Type: '+err[1]+'\n'
                    text = text+'Description: '+err[2]
                    messagebox.showerror('Launch Error', text)
            else:
                os.system("bash "+path)
        else:
            version = self.ver_combobox.get()

    def download_javawrapper(self):
        path = self.wrapper_entry.get()
        path = path.replace('\\', '/')
        dir_path = '/'.join(path.split('/')[0:-1])
        os.makedirs(dir_path, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(requests.get('https://github.com/00ll00/java_launch_wrapper/releases/download/v1.4.4/java_launch_wrapper-1.4.4.jar').content)

    def opencfg(self):
        path = get_file_path()
        path = path.replace('\\', '/') + '/config.json'
        with open(path, 'r') as file:
            cfg = json.loads(file.read())
        self.mc_path_entry.delete(0, "end")
        self.mc_path_entry.insert(0, cfg["minecraft_dir"])
        self.javaw_entry.delete(0, "end")
        self.javaw_entry.insert(0, cfg["javaw_path"])
        self.memmax_entry.delete(0, "end")
        self.memmax_entry.insert(0, cfg["xmx"])
        if native() == 'windows':
            self.wrapper_entry.delete(0, "end")
            self.wrapper_entry.insert(0, cfg["wrapper"])
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, cfg["player"])

    def savecfg(self):
        javaw = self.javaw_entry.get()
        if native() == 'windows':
            wrapper = self.wrapper_entry.get()
        else:
            wrapper = None
        xmx = self.memmax_entry.get()
        mcdir = self.mc_path_entry.get()
        player = self.name_entry.get()
        path = get_file_path()
        path = path.replace('\\', '/') + '/config.json'
        content = {
            "minecraft_dir": mcdir,
            "javaw_path": javaw,
            "xmx": xmx,
            "wrapper": wrapper,
            "player": player
        }
        with open(path, 'w') as file:
            file.write(json.dumps(content))

set_appearance_mode("light")
app = App()
app.title(translate[lang]['WindowTitle'])
app.geometry("600x540+100+100")
app.mainloop()