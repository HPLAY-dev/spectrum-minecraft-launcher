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

v_snapshot = False
v_release = True
v_old = False
bmclapi = False

lang = 'en_US'
text = {
    "zh_CN": {
        "Fail:Int": "无法整数化",
        "Title:Version": '版本',
        "Title:Launch": '启动设置',
        "Title:Download": '下载设置',
        "Title:Misc": '其他',
        "Title:DownloadStatus": "下载进度",
        "Ctrl:MinecraftPath": "Minecraft 文件夹",
        "Ctrl:Version": '版本',
        "Ctrl:JavaPath": 'Java 目录',
        "Ctrl:PlayerName": '玩家名称',
        "Ctrl:MaxMem": 'JVM 内存大小',
        "Ctrl:WrapperPath": 'JavaWrapper 目录',
        "Ctrl:VersionName": '版本名称',
        "Ctrl:UseBMCLAPI": 'BMCLAPI',
        "Ctrl:DownloadFabric": 'Fabric',
        "Ctrl:Download": '下载',
        "Ctrl:Launch": '启动',
        "Ctrl:SaveCfg": '保存设置',
        "Ctrl:OpenCfg": '打开设置',
        "Ctrl:RefVerList": '更新版本列表',
        "Ctrl:ShowSnapshot": '显示快照版本',
        "Ctrl:ShowAncient": '显示早期版本',
        "Ctrl:DownloadJavaWrapper": '下载JavaWrapper',
        "Other:Enter Text": '输入文本',
        "Other:JavaWrapperNeedless": 'JavaWrapper 在此操作系统上不需要'
    },
    "en_US": {
        "Fail:Int": "Fail to Int",
        "Title:Version": 'Version',
        "Title:Launch": 'Launch Options',
        "Title:Download": 'Download Options',
        "Title:Misc": 'Misc Options',
        "Title:DownloadStatus": "Download Progress",
        "Ctrl:MinecraftPath": ".minecraft Folder",
        "Ctrl:Version": 'Version',
        "Ctrl:JavaPath": 'Java Path',
        "Ctrl:PlayerName": 'Player Name',
        "Ctrl:MaxMem": 'JVM Memory Size',
        "Ctrl:WrapperPath": 'JavaWrapper Path',
        "Ctrl:VersionName": 'Version Name',
        "Ctrl:UseBMCLAPI": 'BMCLAPI',
        "Ctrl:DownloadFabric": 'Fabric',
        "Ctrl:Download": 'Download',
        "Ctrl:Launch": 'Launch',
        "Ctrl:SaveCfg": 'Save Config',
        "Ctrl:OpenCfg": 'Open Config',
        "Ctrl:RefVerList": 'Update Version List',
        "Ctrl:ShowSnapshot": 'Show Snapshot Versions',
        "Ctrl:ShowAncient": 'Show Old Versions',
        "Ctrl:DownloadJavaWrapper": 'Download JavaWrapper',
        "Other:Enter Text": 'Enter Text',
        "Other:JavaWrapperNeedless": 'JavaWrapper not needed on this OS'
    }
}
if locale.getdefaultlocale()[0] in text:
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
            v_list.insert(0,'[Installed] '+dir_files[i])
    # return v_list
    versions = v_list

def get_file_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable) # EXE
    return os.path.dirname(os.path.abspath(__file__)) # .py

class App(CTk):

    def update_download_progress(self, current, total, message):
        self.after(0, self._update_log, message)
        
    def _update_log(self, message):
        self.log_entry.delete(0, "end")
        self.log_entry.insert(0, message)
        if message[0:5] == "[LIB]":
            prog = message[6:-1].split('/')
            try:
                amount = int(prog[1])
                now = int(prog[0])
            except:
                raise(text[lang]['FailInt'])
            self.progressbar_lib.set(now/amount)
        elif message[0:5] == "[AST]":
            prog = message[6:-1].split('/')
            try:
                amount = int(prog[1])
                now = int(prog[0])
            except:
                raise(text[lang]['FailInt'])
            self.progressbar_assets.set(now/amount)

    def __init__(self, *kargs, **kwargs):
        super().__init__(*kargs, **kwargs)
        if native() == 'windows':
            titlefont = ("Segoe UI", 24, "bold")
        elif native() == 'osx':
            titlefont = ("San Francisco", 24, "bold")
        else:
            titlefont = ("Noto Sans", 24, "bold")

        self.main_frame = CTkFrame(self, fg_color=self.cget("bg"))

        self.main_frame.grid(row=0, column=0, padx=10, pady=10)

        self.title_label = CTkLabel(master=self.main_frame, text=text[lang]["Title:Version"], font=titlefont)
        self.title_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.mc_path_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:MinecraftPath"])
        self.mc_path_label.grid(row=1, column=0, sticky="w", pady=(0, 10))
        self.mc_path_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
        self.mc_path_entry.grid(row=1, column=1, pady=(0, 10), padx=10)

        self.ver_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:Version"])
        self.ver_label.grid(row=2, column=0, sticky="w", pady=(0, 10))
        # versions = get_version_list(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi)
        refresh_versions(show_snapshot=v_snapshot, show_old=v_old, show_release=v_release, bmclapi=bmclapi, minecraft_dir=self.mc_path_entry.get())
        self.ver_combobox = CTkComboBox(master=self.main_frame, state='readonly', values=versions)
        self.ver_combobox.grid(row=2, column=1, pady=(0, 10), padx=10)
        
        self.title2_label = CTkLabel(master=self.main_frame, text=text[lang]["Title:Launch"], font=titlefont)
        self.title2_label.grid(row=4, column=0, sticky="w", pady=(0, 10))

        self.javaw_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:JavaPath"])
        self.javaw_label.grid(row=3, column=0, sticky="w", pady=(0, 10))
        self.javaw_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
        self.javaw_entry.grid(row=3, column=1, pady=(0, 10), padx=10)

        self.name_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:PlayerName"])
        self.name_label.grid(row=5, column=0, sticky="w", pady=(0, 10))
        self.name_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
        self.name_entry.grid(row=5, column=1, pady=(0, 10), padx=10)

        self.memmax_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:MaxMem"])
        self.memmax_label.grid(row=6, column=0, sticky="w", pady=(0, 10))
        self.memmax_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
        self.memmax_entry.grid(row=6, column=1, pady=(0, 10), padx=10)

        # Windows only
        if native() == "windows":
            self.wrapper_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:WrapperPath"])
            self.wrapper_label.grid(row=7, column=0, sticky="w", pady=(0, 10))
            self.wrapper_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
            self.wrapper_entry.grid(row=7, column=1, pady=(0, 10), padx=10)
        else:
            self.wrapper_label = CTkLabel(master=self.main_frame, text=text[lang]["Other:JavaWrapperNeedless"])
            self.wrapper_label.grid(row=7, column=0, sticky="w", pady=(0, 10))
        
        self.title_label = CTkLabel(master=self.main_frame, text=text[lang]["Title:Download"], font=titlefont)
        self.title_label.grid(row=8, column=0, sticky="w", pady=(0, 10))

        self.ver_name_label = CTkLabel(master=self.main_frame, text=text[lang]["Ctrl:VersionName"])
        self.ver_name_label.grid(row=9, column=0, sticky="w", pady=(0, 10))
        self.ver_name_entry = CTkEntry(master=self.main_frame, placeholder_text=text[lang]["Other:Enter Text"])
        self.ver_name_entry.grid(row=9, column=1, pady=(0, 10), padx=10)

        self.dl_bmcl_checkbox = CTkCheckBox(master=self.main_frame, text=text[lang]["Ctrl:UseBMCLAPI"])
        self.dl_bmcl_checkbox.grid(row=10, column=0, sticky="w", pady=(0, 10))

        self.dl_fabric_checkbox = CTkCheckBox(master=self.main_frame, text=text[lang]["Ctrl:DownloadFabric"])
        self.dl_fabric_checkbox.grid(row=10, column=1, sticky="w", pady=(0, 10))
        
        self.launch_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:Launch"], command=self.launch)
        self.launch_button.grid(row=11, column=1, pady=(0, 10))
        
        self.launch_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:Download"], command=self.download)
        self.launch_button.grid(row=11, column=0, pady=(0, 10))

        self.title_label = CTkLabel(master=self.main_frame, text=text[lang]["Title:Misc"], font=titlefont)
        self.title_label.grid(row=0, column=3, sticky="w", pady=(0, 10))

        self.opencfg_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:OpenCfg"], command=self.opencfg)
        self.opencfg_button.grid(row=1, column=3, pady=(0, 10))

        self.savecfg_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:SaveCfg"], command=self.savecfg)
        self.savecfg_button.grid(row=2, column=3, pady=(0, 10))

        self.refresh_versions_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:RefVerList"], command=self.refresh_versions)
        self.refresh_versions_button.grid(row=3, column=3, pady=(0, 10))

        self.snapshot_checkbox = CTkCheckBox(master=self.main_frame, text=text[lang]["Ctrl:ShowSnapshot"], command=self.toggle_snapshot)
        self.snapshot_checkbox.grid(row=4, column=3, sticky="w", pady=(0, 10))

        self.old_checkbox = CTkCheckBox(master=self.main_frame, text=text[lang]["Ctrl:ShowAncient"], command=self.toggle_old)
        self.old_checkbox.grid(row=5, column=3, sticky="w", pady=(0, 10))

        self.title_label = CTkLabel(master=self.main_frame, text=text[lang]["Title:DownloadStatus"], font=titlefont)
        self.title_label.grid(row=6, column=3, sticky="w", pady=(0, 10))

        self.log_entry = CTkEntry(master=self.main_frame, width=200)
        # self.log_entry.grid(row=7, column=3, sticky="w", pady=(0, 10))

        self.progressbar_lib = CTkProgressBar(master=self.main_frame, width=200)
        self.progressbar_lib.grid(row=7, column=3, sticky="w", pady=(0, 10))
        self.progressbar_lib.set(0)

        self.progressbar_assets = CTkProgressBar(master=self.main_frame, width=200)
        self.progressbar_assets.grid(row=8, column=3, sticky="w", pady=(0, 10))
        self.progressbar_assets.set(0)

        self.dl_jwrapper_button = CTkButton(master=self.main_frame, text=text[lang]["Ctrl:DownloadJavaWrapper"], command=self.download_javawrapper)
        self.dl_jwrapper_button.grid(row=9, column=3, pady=(0, 10))

    def download(self):
        if not hasattr(self, 'download_thread') or not self.download_thread.is_alive():
            mcdir = self.mc_path_entry.get().replace("\\", '/')
            if not os.path.exists(mcdir):
                messagebox.showerror('Argument Error', 'Cannot find Minecraft Path')
                return 1
            if self.ver_combobox.get()[0:12] == "[Installed] ": # [Installed] 
                version_name = self.ver_combobox.get()[12:]
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
                if version_name == '':
                    self.log_entry.delete(0, "end")
                    self.log_entry.insert(0, "Version Name not set")
            bmclapi = self.dl_bmcl_checkbox.get()
            fabric = self.dl_fabric_checkbox.get()
            java = self.javaw_entry.get()
            if fabric and java and java == '':
                messagebox.showwarning('Argument Warning', 'Java is necessary for downloading a version with Fabric. If you don\'t specify a Java.exe path, java in PATH is automatically used.')
            self.download_thread = threading.Thread(
                target=auto_download,
                args=(mcdir, version, version_name),
                kwargs={
                    "print_status": False, 
                    "bmclapi": bmclapi,
                    "progress_callback": self.update_download_progress,
                    "fabric": fabric,
                    "java": java
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
        javaw = self.javaw_entry.get()
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
        if self.ver_combobox.get()[0:12] == "[Installed] ": # [Installed] 
            version_name = self.ver_combobox.get()[12:]
            version = get_minecraft_version(mcdir, version_name)
            player = self.name_entry.get()
            cmd = launch(javaw, xmx, mcdir, version, version_name, wrapper, username=player)

            if native() == 'windows':
                path = get_file_path()
                path = path.replace('\\', '/') + '/launch.bat'
                with open(path, 'w') as file:
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
            self.log_entry.delete(0, "end")
            self.log_entry.insert(0, "Version not Installed")

    def download_javawrapper(self):
        path = self.wrapper_entry.get()
        path = path.replace('\\', '/')
        dir_path = '/'.join(path.split('/')[0:-1])
        os.mkdirs(dir_path, exist_ok=True)
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
app.title("Spectrum Launcher")
app.geometry("600x480+100+100")
app.mainloop()