from mclauncher_core.tool_funcs import get_java_version

USE_OS_SYSTEM_TO_EXECUTE = 0
version = '3.5.0'

import sys
import os
from PyQt5.QtCore import Qt, QStringListModel, QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QIcon, QStandardItem
import re
import json
from mclauncher_core.javawrapper import download_javawrapper
import mclauncher_core.launcher_funcs as launcher
import mclauncher_core.manager as manager
import mclauncher_core.download_funcs as downloader
import mclauncher_core.java as java
import shutil
import zipfile as z
import requests
from ui import Ui_MainWindow


def check_update():
    pass
    # import requests
    # try:
    #     release_info = requests.get('https://api.github.com/repos/hplay-dev/spectrum-minecraft-launcher/releases/latest')
    #     if release_info.status_code == 403:
    #         return 0
    #     if release_info.status_code != 200:
    #         raise BaseException('非200的状态码: '+str(release_info.status_code))
    #     release_info = release_info.json()
    #     latest_version = release_info['tag_name']
    #     latest_url = release_info['assets'][0]["browser_download_url"]
    #     1
    #     1
    #     if version == latest_version:
    #         return True
    #     else:
    #         QMessageBox.information(None, '检查更新', '请下载最新二进制文件: \n'+latest_url)
    #         return 
    # except Exception as e:
    #     QMessageBox.warning(None, '检查更新', '失败: '+str(e))
    
def app_path():
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]

    return str(path)

def fpath(path):
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]
    return path


default_icon = app_path() + '/assets/default_icon.png'

if not os.path.exists(default_icon):
    QMessageBox.critical(None, 'Assets load fail', default_icon)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        check_update()

        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

        # Stuff
        self.using_mc_login = False
        self.mc_token = None
        self.autodl_fabric_api = False

        # 设置版本列表
        self.model = QStringListModel()
        data = downloader.get_version_list()
        self.model.setStringList(data)
        self.listView.setModel(self.model) # 版本列表

        self.checkBox.stateChanged.connect(self.update_version_list)   # 下载页面右边四个CheckBox
        self.checkBox_2.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox
        self.checkBox_3.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox
        self.checkBox_4.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox

        self.pushButton.clicked.connect(self.save_config) # 保存设置按钮

        self.pushButton_3.clicked.connect(self.download) # 下载按钮

        self.lineEdit.editingFinished.connect(self.update_installed_versions) # 更新Minecraft目录

        self.LaunchBtn.clicked.connect(self.launch) # 启动

        self.comboBox.currentTextChanged.connect(self.update_ml_version_list)

        self.mainTabWidget.currentChanged.connect(self.page_process) # change tab

        self.comboBox_5.currentTextChanged.connect(self.switch_manager_select_version) # Resourcepack manager

        self.pushButton_4.clicked.connect(self.remove_version) # Remove ver

        self.pushButton_5.clicked.connect(self.remove_save) # Remove save

        self.pushButton_6.clicked.connect(self.remove_respack) # Remove respack

        self.DownloadFixBtn.clicked.connect(self.download_fix)
        
        self.pushButton_2.clicked.connect(self.oauth)
        self.lineEdit_6.textChanged.connect(self.disable_mslogin)
        
        self.checkBox_5.clicked.connect(self.toggle_fabric_api_autodownload)

        self.pushButton_10.clicked.connect(lambda: self.download_java(8, callback=self.progressBar_3.setValue))
        self.pushButton_11.clicked.connect(lambda: self.download_java(17, callback=self.progressBar_3.setValue))
        self.pushButton_12.clicked.connect(lambda: self.download_java(21, callback=self.progressBar_3.setValue))

        self.pushButton_9.clicked.connect(self.rename_version)

        self.pushButton_13.clicked.connect(lambda: self.lineEdit.setText(self.open_folder()))

        self.load_config()

        self.update_installed_versions()

    def open_folder(self):
        return QFileDialog.getExistingDirectory(self, "选择文件夹", app_path())
    def open_file(self):
        return QFileDialog.getOpenFileName(self, self, "选择文件", app_path())
    def rename_version(self):
        if self.lineEdit_5.text() == "":
            QMessageBox.warning(None, 'Spectrum 启动器', '你必须输入一个名称。')
        new_name = self.lineEdit_5.text()
        version_name = self.comboBox_5.currentText()
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        manager.rename_version(minecraft_dir, version_name, new_name)
        self.update_installed_versions()

    def download_java(self, major_version: int, callback=None):
        print('Retrieving url')
        url = java.get_url(major_version, 'jdk', tuna=False).replace('https://github.com/',
                                                                        'https://ghfast.top/https://github.com/')
        print('Trying: ' + url)

        try:

            # 首先获取文件大小
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception('Download failed: ' + str(response.status_code))

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open('java_installer.msi', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 计算并显示进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            progress_percent = round(progress, 1)

                            # 如果有回调函数，调用回调函数
                            if callback:
                                callback(int(progress_percent))
                                print(f"\r下载进度: {progress_percent}%", end='', flush=True)
                            else:
                                # 默认行为：打印进度
                                print(f"\r下载进度: {progress_percent}%", end='', flush=True)

            # 下载完成
            if callback:
                callback(100)
            else:
                print("\r下载进度: 100% - 下载完成!")

        except Exception as e:
            print(f"下载过程中出现错误: {e}")
            raise

        os.system(f'cmd /c start msiexec /i {app_path()}/java_installer.msi')


    def toggle_fabric_api_autodownload(self, stat=''):
        self.autodl_fabric_api = stat

    def debug_print(self, b=''):
        print(b)
        print(self.using_mc_login)
        print(self.mc_token)

    def disable_mslogin(self):
        self.using_mc_login = False
        
    def oauth(self):
        try:
            self.using_mc_login = True
            self.mc_token = launcher.get_mc_token()
        except Exception as e:
            input('EXCEPTION: '+str(e))
            self.using_mc_login = False
            self.mc_token = None

    def remove_version(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        print(str(self.comboBox_5.currentText()))
        if len(str(self.comboBox_5.currentText())) == 0:
            
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = str(self.comboBox_5.currentText())

        QMessageBox.information(None, 'Spectrum 启动器', f'“{ver}”将会永久消失！（真的很久！）')
        launcher.remove_version(minecraft_dir, ver)
        self.update_installed_versions()
        return None

    def remove_save(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if self.comboBox_5.currentText() == '':
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_saves.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个存档。')
            return 1
        save = self.listView_saves.selectionModel().selectedIndexes()[0].data()

        QMessageBox.information(None, 'Spectrum 启动器', f'“{save}”将会永久消失！（真的很久！）')
        manager.remove_save(minecraft_dir, ver, save)
        self.switch_manager_select_version(version_name=ver)

    def remove_respack(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if self.comboBox_5.currentText() == '':
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_respacks.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个资源包。')
            return 1
        respack = self.listView_respacks.selectionModel().selectedIndexes()[0].data()

        QMessageBox.information(None, 'Spectrum 启动器', f'“{respack}”将会永久消失！（真的很久！）')
        manager.remove_resourcepack(minecraft_dir, ver, respack)
        self.switch_manager_select_version(version_name=ver)


    def switch_manager_select_version(self, version_name):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        
        if self.comboBox_5.currentText() == '':
            return 1
        version_name = self.comboBox_5.currentText()

        # 设置存档列表
        self.model_saves = QStandardItemModel()
        data = manager.get_saves(minecraft_dir, version_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{version_name}/saves/{i}/icon.png'
            if os.path.exists(save_icon):
                self.model_saves.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_saves.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_saves.setModel(self.model_saves) # 版本列表

        # 设置资源包列表
        self.model_respacks = QStandardItemModel()
        data = manager.get_resourcepacks(minecraft_dir, version_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{version_name}/resourcepacks/{i}/pack.png'
            if os.path.exists(save_icon):
                self.model_respacks.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_respacks.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_respacks.setModel(self.model_respacks) # 版本列表

        # 设置Mod列表
        self.model_mods = QStandardItemModel()
        data = manager.get_mods(minecraft_dir, version_name)

        for i in data:
            self.model_mods.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_mods.setModel(self.model_mods) # 版本列表

        # 设置光影d列表
        self.model_shaderpacks = QStandardItemModel()
        data = manager.get_shaderpacks(minecraft_dir, version_name)

        for i in data:
            self.model_shaderpacks.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_shaderpacks.setModel(self.model_shaderpacks) # 版本列表

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        
        if self.comboBox_5.currentText() == '':
            return 1
        version_name = self.comboBox_5.currentText()

        saves_path = f'{minecraft_dir}/versions/{version_name}/saves'
        if not os.path.exists(saves_path):
            return 1

        pos = event.pos()
        widget_under_cursor = self.childAt(pos)
        while widget_under_cursor and widget_under_cursor.metaObject().className() == 'QWidget':
            widget_under_cursor = widget_under_cursor.parent()


        if not event.mimeData().hasUrls():
            event.ignore()

        elif widget_under_cursor.objectName() == 'listView_saves':
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                file = fpath(file)
                if os.path.isdir(file) and os.path.exists(file+'/level.dat'):
                    dirname = file.split('/')[-1]
                    shutil.copytree(file, saves_path+'/'+dirname)
                else:
                    try:
                        with z.ZipFile(file) as f:
                            dirname = '.'.join(file.split('.')[:-1]).split('/')[-1]
                            f.extractall(saves_path+'/'+dirname)
                            if not os.path.exists(saves_path+'/'+dirname+'/level.dat'):
                                QMessageBox.warning(None, 'Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
                                shutil.rmtree(saves_path+'/'+dirname)
                    except z.BadZipFile:
                        QMessageBox.warning(None, 'Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
            event.accept()

        elif widget_under_cursor.objectName() == 'listView_respacks':
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            for file in files:
                file = fpath(file)
                if os.path.isdir(file) and os.path.exists(file+'/pack.mcmeta'):
                    dirname = file.split('/')[-1]
                    shutil.copytree(file, saves_path+'/'+dirname)
                else:
                    try:
                        with z.ZipFile(file) as f:
                            dirname = '.'.join(file.split('.')[:-1]).split('/')[-1]
                            f.extractall(saves_path+'/'+dirname)
                            if not os.path.exists(saves_path+'/'+dirname+'/pack.mcmeta'):
                                QMessageBox.warning(None, 'Spectrum 启动器', '文件不是资源包文件夹或压缩为.zip的资源包文件夹')
                                shutil.rmtree(saves_path+'/'+dirname)
                    except z.BadZipFile:
                        QMessageBox.warning(None, 'Spectrum 启动器', '文件不是资源包文件夹或压缩为.zip的资源包文件夹')
            event.accept()

    def page_process(self, page_index):
        if page_index == 2:
            self.setAcceptDrops(True)
        else:
            self.setAcceptDrops(False)

    def update_installed_versions(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir == '':
            return 1
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if os.path.exists(minecraft_dir+'/versions'):
            versions = os.listdir(minecraft_dir+'/versions')

            self.comboBox_3.clear()
            for ver in versions:
                self.comboBox_3.addItem(ver)

            self.comboBox_5.clear()
            for ver in versions:
                self.comboBox_5.addItem(ver)
    
    def launch(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            QMessageBox.critical(None, 'Spectrum 启动器', 'Minecraft路径不存在。')
            return 1
        
        if self.comboBox_3.currentText() == '':
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本来启动。')
            return 1
        version_name = self.comboBox_3.currentText()

        java_major_version = launcher.get_required_java_version(minecraft_dir, version_name)
        if java_major_version == 21:
            javaw = self.lineEdit_4.text()
        elif java_major_version == 17:
            javaw = self.lineEdit_3.text()
        elif java_major_version == 8:
            javaw = self.lineEdit_2.text()
        else:
            javaw = self.lineEdit_8.text()

        xmx = self.comboBox_4.currentText()

        username = self.lineEdit_6.text()
        if len(username) > 16:
            QMessageBox.warning(None, 'Spectrum 启动器', '玩家名称长度>16，可能出现问题。')
        punctuations = "[!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~]"
        pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\uff00-\uffef\s' + punctuations + ']') # CJK chars; symbol; full-width chars; spaces; 
        if bool(pattern.search(username)):
            QMessageBox.warning(None, 'Spectrum 启动器', '玩家名称含有其他语言字符，可能出现问题。')

        if launcher.native() == 'windows':
            javawrapper = './JavaWrapper.jar'
            if not os.path.exists(javawrapper):
                QMessageBox.critical(None, 'Spectrum 启动器', 'JavaWrapper路径不存在。')
                return 1
        else:
            javawrapper = None

        # 使用QProcess启动Minecraft而不阻塞UI\
        print(self.mc_token)
        cmd = launcher.launch(javaw=javaw, xmx=xmx, minecraft_dir=minecraft_dir, 
                            version_name=version_name, javawrapper=javawrapper, 
                            username=username, ms_login=self.using_mc_login, 
                            access_token=self.mc_token)
        with open('launch.bat', 'w') as f:
            f.write(cmd)
        if USE_OS_SYSTEM_TO_EXECUTE:
            os.system(cmd)
        else:
            # 创建QProcess对象
            self.minecraft_process = QProcess()
            self.minecraft_process.readyReadStandardOutput.connect(self.handle_minecraft_output)
            self.minecraft_process.readyReadStandardError.connect(self.handle_minecraft_error)
            self.minecraft_process.finished.connect(self.handle_minecraft_finished)
            
            # 如果是Windows，使用cmd.exe来执行命令
            if launcher.native() == 'windows':
                self.minecraft_process.start(app_path()+'/launch.bat')
            else:
                # 对于Linux/Mac，使用bash
                self.minecraft_process.start('bash', ['-c', cmd])

    def handle_minecraft_output(self):
        data = self.minecraft_process.readAllStandardOutput()
        stdout = bytes(data).decode("gbk", errors='ignore')
        print(f"Minecraft输出: {stdout}")

    def handle_minecraft_error(self):
        data = self.minecraft_process.readAllStandardError()
        stderr = bytes(data).decode("gbk", errors='ignore')
        print(f"Minecraft错误: {stderr}")

    def handle_minecraft_finished(self, exit_code, exit_status):
        print(f"Minecraft进程结束，退出码: {exit_code}")
        
    def download(self):
        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本来下载。')
            return 1
        version = self.listView.selectionModel().selectedIndexes()[0].data()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            QMessageBox.critical(None, 'Spectrum 启动器', 'Minecraft路径不存在。')
            return 1

        version_name = self.lineEdit_7.text()
        os.makedirs(minecraft_dir+'/versions', exist_ok=True)
        if version_name in os.listdir(minecraft_dir+'/versions'):
            QMessageBox.critical(None, 'Spectrum 启动器', 'Minecraft路径中已经包含此名称的版本。')
            return 1
        
        modloader = self.comboBox.currentText().lower()
        if modloader == '无':
            modloader = 'vanilla'
        
        modloader_version = self.comboBox_2.currentText()
        if modloader_version == '' and modloader != 'vanilla':
            QMessageBox.critical(None, 'Spectrum 启动器', '请选择模组加载器的版本。')
            return 1

        r = launcher.auto_download(minecraft_dir=minecraft_dir, version=version, version_name=version_name, modloader=modloader, modloader_version=modloader_version, progress_callback=self.progress_callback)
        if self.autodl_fabric_api == True:
            launcher.download_fabric_api(minecraft_dir, version, version_name)
        if r == 721:
            QMessageBox.warning(None, 'Spectrum 启动器', '下载的modloader与minecraft版本不被Spectrum启动器所兼容')
        self.update_installed_versions()

    def download_fix(self):
        if len(self.comboBox_3.currentText()) == 0:
            QMessageBox.critical(None, 'Spectrum 启动器', '你必须选择一个版本来补全。')
            return 1
        version_name = self.comboBox_3.currentText()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            QMessageBox.critical(None, 'Spectrum 启动器', 'Minecraft路径不存在。')
            return 1

        r = launcher.auto_download(minecraft_dir=minecraft_dir, version=launcher.get_minecraft_version(minecraft_dir, version_name), version_name=version_name, progress_callback=self.progress_callback)
        if r == 721:
            QMessageBox.warning(None, 'Spectrum 启动器', '下载的modloader与minecraft版本不被Spectrum启动器所兼容')
        self.update_installed_versions()

    def progress_callback(self, current, total, description):
        if description[1:-1].split('][')[0] == 'LIB':
            self.progressBar.setValue(int(current/total*100))
        elif description[1:-1].split('][')[0] == 'AST':
            self.progressBar_2.setValue(int(current/total*100))

    def load_config(self):
        if os.path.exists(app_path()+'/cfg.json'):
            with open(app_path()+'/cfg.json', 'r') as f:
                config = json.loads(f.read())

            self.lineEdit.setText(config['minecraftPath'])
            self.lineEdit_2.setText(config['java8'])
            self.lineEdit_3.setText(config['java17'])
            self.lineEdit_4.setText(config['java21'])
        else:
            self.lineEdit.setText('.minecraft')
            javas = java.find_javas()
            for java_exe in javas:
                java_ver = get_java_version(java_exe)[0]
                if java_ver == 21:
                    self.lineEdit_4.setText(java_exe)
                elif java_ver == 17:
                    self.lineEdit_3.setText(java_exe)
                elif java_ver == 8:
                    self.lineEdit_2.setText(java_exe)
    
    def save_config(self):
        jsonfile = {}
        jsonfile['minecraftPath'] = self.lineEdit.text()
        jsonfile['java8'] = self.lineEdit_2.text()
        jsonfile['java17'] = self.lineEdit_3.text()
        jsonfile['java21'] = self.lineEdit_4.text()
        jsonfile['wrapperPath'] = './JavaWrapper.jar'

        with open(app_path()+'/cfg.json', 'w') as f:
            f.write(json.dumps(jsonfile))

    def update_version_list(self, state):
        current_list = self.model.stringList()
        current_list = launcher.get_version_list(self.checkBox_2.isChecked(), self.checkBox_3.isChecked(), self.checkBox_4.isChecked(), self.checkBox.isChecked())
        self.model.setStringList(current_list)

    def update_ml_version_list(self, state):
        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            return 0
        version = self.listView.selectionModel().selectedIndexes()[0].data()
        modloader = self.comboBox.currentText().lower()
        if modloader == 'forge':
            current_dict = launcher.get_forge_version(version)
            current_list = []
            for item in current_dict:
                current_list.append(item["version"])
        elif modloader == 'fabric':
            current_list = launcher.get_fabric_versions()
        elif modloader == 'neoforge':
            current_dict = launcher.get_neoforge_version(version)
            current_list = []
            for item in current_dict:
                current_list.append(item["version"])
        else:
            current_list = []

        self.comboBox_2.clear()
        for ver in current_list:
            self.comboBox_2.addItem(ver)
        
if __name__ == "__main__":
    # load_plugins()
    # for control in controls:
    if not os.path.exists(app_path()+'/JavaWrapper.jar'):
        download_javawrapper()
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MainWindow()
    myWin.show()
    # myWin.load_controls(controls)
    sys.exit(app.exec_())