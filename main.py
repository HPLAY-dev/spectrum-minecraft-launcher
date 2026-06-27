from modrinth_api_wrapper import Client

modrinth = Client()

USE_OS_SYSTEM_TO_EXECUTE = 0
# version = '3.5.0'

import sys
import os

# spectrum_core 包位于 python/ 目录
_PYTHON_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python")
if _PYTHON_ROOT not in sys.path:
    sys.path.insert(0, _PYTHON_ROOT)

from PySide6.QtCore import QStringListModel, QProcess, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QInputDialog
from PySide6.QtGui import QStandardItemModel, QIcon, QStandardItem, QPixmap
from PySide6.QtCore import Qt

import re
import json
from spectrum_core.javawrapper import download_javawrapper
import spectrum_core.launcher_funcs as launcher
import spectrum_core.oauth_funcs as oa
import spectrum_core.manager as manager
import spectrum_core.download_funcs as downloader
import spectrum_core.java as java
import spectrum_core.modloader_fabric as fabric
import spectrum_core.modloader_forge as forge
import spectrum_core.modloader_neoforge as neoforge
import spectrum_core.labymod as labymod
import spectrum_core as spectrum_core_mod
import stylesheets
# import hashlib

import shutil
import zipfile as z
import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor
from ui import Ui_MainWindow
import time

import l18n

Ui_MainWindow.retranslateUi = l18n.retranslateUi

def fpath(path):
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]
    return path
    

if getattr(sys, 'frozen', False):
    app_path = os.path.dirname(sys.executable)
else:
    app_path = os.path.dirname(os.path.abspath(__file__))

app_path = fpath(app_path)
lang_path = app_path + '/languages'
log_level = 0


# Init argv
l18n.load_lang(path=lang_path)
for i in sys.argv:
    if i.startswith('lang='):
        l18n.load_lang(i.replace('lang=', ''), path=lang_path)

def hide_ctrl(ctrl):
    ctrl.setEnabled(False)
    ctrl.hide()
    ctrl.setFocusPolicy(Qt.NoFocus)

def show_ctrl(ctrl):
    ctrl.setEnabled(True)
    ctrl.show()
    ctrl.setFocusPolicy(Qt.StrongFocus)

def log(string: str, log_type='STD', level=1, file=sys.stdout):
    # level: 0 - ALWAYS Level
    #        1 - Standard Level
    #        2 - Verbose Level
    t = time.strftime("%H:%M:%S", time.localtime(time.time()))
    line = f'[{t}][{log_type}] {str(string)}'
    print(line, file=file)
    if level <= 1 and _log_listener is not None:
        try:
            _log_listener(line)
        except Exception:
            pass

_log_listener = None

def set_log_listener(listener):
    global _log_listener
    _log_listener = listener

def check_update():
    pass
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


default_icon = app_path + '/assets/default_icon.png'

log("Checking Assets", "INIT", 1)
if not os.path.exists(default_icon):
    log("No Assets Path found", "FATAL", 0)
    QMessageBox.critical(None, l18n.string("assetLoadFail"), default_icon)
    sys.exit(1)

class MainWindow(QMainWindow, Ui_MainWindow):
    # signal emitted from any thread to report progress (current, total, description)
    download_progress = Signal(int, int, str)
    # signal emitted when a download task finished (result, instance_name, minecraft_dir)
    download_finished = Signal(object, str, str)

    def __init__(self, parent=None):
        # check_update()
        log("Create Window", "INIT", level=2)
        super(MainWindow, self).__init__(parent)
        log("setupUi(self) & initialize", "INIT", level=2)
        self.setupUi(self)
        # Executor and tracking for background download tasks
        self._dl_executor = ThreadPoolExecutor(max_workers=3)
        self._downloads_in_progress = set()
        self._dl_lock_dir = os.path.join(app_path, 'temp', 'download_locks')
        os.makedirs(self._dl_lock_dir, exist_ok=True)
        # Connect signals (thread-safe) for progress and completion
        self.download_progress.connect(self._on_download_progress)
        self.download_finished.connect(self._on_download_finished)

        self.launch_version = None
        # Stuff
        self.autodl_fabric_api = False

        self.javas = {}
        self.accounts = []
        self.listView_4_Model = []
        '''
        format:
        {
            'name': 'account name',
            'type: 'microsoft|offline',
            'refresh_token': 'xxxxxx', # Only for microsoft account
        }
        '''

        temp_access_token = ''
        temp_refresh_token = ''

        hide_ctrl(self.create_account)
        # hide_ctrl(self.offline)
        hide_ctrl(self.microsoft)

        self.mainTabWidget.setCurrentIndex(0)
        log("Setting Stylesheets", "INIT", level=2)
        # self.setStyleSheet(stylesheets.main_window)
        self.launchBtn.setStyleSheet(stylesheets.button1)
        # self.label_6.setStyleSheet(stylesheets.bg_label)
        
        log('Loading Config & Accounts', "INIT", level=1)
        self.load_config()
        self.load_accounts()

        log('Loading LabyMod versions', "INIT", level=1)
        try:
            self.listView_5.setModel(QStringListModel(labymod.get_versions()))
        except:
            log('FAIL TO RETRIEVE LABYMOD VERSIONS', 'WARN', level=0)

        # 设置版本列表
        self.update_version_list()
        
        log('Binding Functions', "INIT", level=1)

        self.checkBox.stateChanged.connect(self.update_version_list)   # 下载页面右边四个CheckBox
        self.checkBox_2.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox
        self.checkBox_3.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox
        self.checkBox_4.stateChanged.connect(self.update_version_list) # 下载页面右边四个CheckBox

        self.pushButton.clicked.connect(self.save_config) # 保存设置按钮

        self.pushButton_3.clicked.connect(self.download) # 下载按钮

        self.lineEdit.editingFinished.connect(self.update_installed_versions) # 更新Minecraft目录

        self.launchBtn.clicked.connect(self.launch) # 启动

        self.comboBox.currentTextChanged.connect(self.update_ml_version_list)

        self.mainTabWidget.currentChanged.connect(self.page_process) # change tab

        self.comboBox_5.currentTextChanged.connect(self.switch_manager_select_version) # Resourcepack manager
        self.pushButton_20.clicked.connect(self.switch_manager_select_version)

        self.pushButton_4.clicked.connect(self.remove_version) # Remove ver

        self.pushButton_5.clicked.connect(self.remove_save) # Remove save

        self.pushButton_6.clicked.connect(self.remove_respack) # Remove respack

        self.DownloadFixBtn.clicked.connect(self.download_fix)
        
        # self.pushButton_2.clicked.connect(self.oauth)
        # self.lineEdit_6.textChanged.connect(self.disable_mslogin)
        
        self.checkBox_5.clicked.connect(self.toggle_fabric_api_autodownload)

        self.pushButton_10.clicked.connect(lambda: self.download_java(8, callback=self.progressBar_3.setValue))
        self.pushButton_11.clicked.connect(lambda: self.download_java(17, callback=self.progressBar_3.setValue))
        self.pushButton_12.clicked.connect(lambda: self.download_java(21, callback=self.progressBar_3.setValue))

        self.pushButton_9.clicked.connect(self.rename_version)

        self.pushButton_13.clicked.connect(lambda: self.lineEdit.setText(self.open_folder()))
        self.pushButton_21.clicked.connect(lambda: self.add_java(self.open_file("Java (*.*);;Java.exe (*.exe)")))
        self.pushButton_15.clicked.connect(self.ver_visibility_toggle)
        self.listView_2.clicked.connect(self.launch_version_select)
        
        self.listView_2.setVisible(False)

        self.pushButton_16.clicked.connect(lambda: self.lineEdit_9.setText(self.open_file("Java (*.*);;Java.exe (*.exe)")))

        self.pushButton_17.clicked.connect(self.save_version_config)
        
        self.lineEdit_11.setText('')
        

        self.mods = []
        self.pushButton_18.clicked.connect(self.search_modrinth)
        self.pushButton_19.clicked.connect(self.install_modrinth)
        
        self.pushButton_14.clicked.connect(self.open_version_folder)
        # self.pushButton_14.clicked.connect(lambda: os.system(f'cmd /c set /p a={self.comboBox_5.currentText()}'))

        self.comboBox_9.currentIndexChanged.connect(self.change_account_mode)
        self.pushButton_23.clicked.connect(self.save_accounts)
        self.pushButton_24.clicked.connect(self.oauth)
        self.pushButton_22.clicked.connect(lambda: show_ctrl(self.create_account))
        self.pushButton_2.clicked.connect(self.save_accounts)
        self.pushButton_25.clicked.connect(lambda: hide_ctrl(self.create_account))
        self.pushButton_26.clicked.connect(self.remove_account)
        self.pushButton_23.clicked.connect(self.add_account)
        self.pushButton_27.clicked.connect(self.remove_java)
        self.pushButton_28.clicked.connect(self.download_labymod)
        log("Getting Installed Versions", "INIT", level=2)
        self.update_installed_versions()
        log("Window created", "INIT", level=1)

    def change_account_mode(self, index):
        if index == 0:
            show_ctrl(self.offline)
            hide_ctrl(self.microsoft)
        elif index == 1:
            hide_ctrl(self.offline)
            show_ctrl(self.microsoft)

    def add_account(self, microsoft=False, access_token=None, refresh_token=None):
        log(f"Adding Account\t{str(microsoft)}\t{access_token}\t{refresh_token}", "MAIN", level=2)
        if microsoft:
            uuid, name = oa.get_mslogin_uuid_name(access_token)
            self.accounts.append({
                "type": "microsoft",
                "refresh_token": refresh_token,
                "name": name,
                "uuid": uuid
            })
        elif self.comboBox_9.currentIndex() == 0: # Offline
            name = self.lineEdit_2.text()
            self.accounts.append({
                "type": "offline",
                "name": name
            })
        elif self.comboBox_9.currentIndex() == 1: # Microsoft
            uuid, name = oa.get_mslogin_uuid_name(self.temp_access_token)
            self.accounts.append({
                "type": "microsoft",
                "refresh_token": temp_refresh_token,
                "name": name,
                "uuid": uuid
            })
        self.comboBox_8.addItem(name+f' ({l18n.string("ui", "microsoftAccount")})' if microsoft else name+f' ({l18n.string("ui", "offlineAccount")})')
        self.listView_4_Model.append(name+f'\t{l18n.string("ui", "microsoftAccount")}' if microsoft else name+f' ({l18n.string("ui", "offlineAccount")})')
        self.listView_4.setModel(QStringListModel(self.listView_4_Model))
        hide_ctrl(self.create_account)

    def remove_account(self):
        log(f"Removing Account", "MAIN", level=2)
        index = self.listView_4.selectionModel().selectedIndexes()[0].row()
        self.listView_4_Model.pop(self.listView_4.selectionModel().selectedIndexes()[0].row())
        self.listView_4.setModel(QStringListModel(self.listView_4_Model))
        self.accounts.pop(index)
        self.comboBox_8.removeItem(index)
        

    def open_version_folder(self):
        log(f"Call File Explorer", "MAIN", level=2)
        open_bin = 'explorer.exe' if downloader.native() == 'windows' else 'xdg-open'
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        log(f'{l18n.string("opening")} {minecraft_dir}/versions/{self.comboBox_5.currentText()}')
        cmd = f'{open_bin} {minecraft_dir}/versions/{self.comboBox_5.currentText()}'
        if launcher.native() == 'windows':
            cmd = cmd.replace('/', '\\')
        os.system(cmd)

    def launch_version_select(self):
        self.launch_version = self.listView_2.selectionModel().selectedIndexes()[0].data()
        self.launchBtn.setText(l18n.string("launch")+"\n"+self.launch_version)
        self.ver_visibility_toggle()

    def ver_visibility_toggle(self):
        _ = self.listView_2.isVisible()
        if _:
            self.pushButton_15.setText(l18n.string("ui", "upArrow"))
        else:
            self.pushButton_15.setText(l18n.string("ui", "downArrow"))
        self.listView_2.setVisible(not _)

    def open_folder(self):
        log(f"Call QFileDialog", "MAIN", level=2)
        return QFileDialog.getExistingDirectory(self, l18n.string("selectFolder"), app_path)

    def open_file(self, filters):
        log(f"Call QFileDialog", "MAIN", level=2)
        filename, _ = QFileDialog.getOpenFileName(self, l18n.string("selectFile"), app_path, filters)
        return filename
        
    def rename_version(self):
        log(f"Rename Version", "MAIN", level=2)
        if self.lineEdit_5.text() == "":
            QMessageBox.warning(None, l18n.string("appName"), l18n.string("noName"))
        new_name = self.lineEdit_5.text()
        instance_name = self.comboBox_5.currentText()
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        manager.rename_version(minecraft_dir, instance_name, new_name)
        self.update_installed_versions()

    def download_java(self, major_version: int, callback=None):
        log(f"Downloading Java {str(major_version)}", "JAVA", level=1)
        log('Retrieving url', "JAVA", level=1)
        url = java.get_url(major_version, 'jre', tuna=True).replace('https://github.com/',
                                                                        'https://ghfast.top/https://github.com/')
        log('Trying: ' + url, "JAVA", level=1)

        try:

            # 首先获取文件大小
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                raise Exception(l18n.string("downloadFailColon") + str(response.status_code))

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
                                log(f"\r{l18n.string("downloadProgress")}: {progress_percent}%", end='', flush=True)
                            else:
                                # 默认行为：打印进度
                                log(f"\r{l18n.string("downloadProgress")}: {progress_percent}%", end='', flush=True)

            # 下载完成
            if callback:
                callback(100)
            else:
                log("Download Finished")

        except Exception as e:
            log(f"Error while downloading: {e}")
            raise

        os.system(f'cmd /c start msiexec /i {app_path}/java_installer.msi')


    def toggle_fabric_api_autodownload(self, stat=''):
        self.autodl_fabric_api = stat

    def debug_log(self, b=''):
        log(b)
        
    def oauth(self):
        log("Call OAUTH", "OAUTH", level=1)
        # try:
        temp_access_token, temp_refresh_token = oa.get_mc_token(need_refresh_token=True)
        self.add_account(microsoft=True, access_token=temp_access_token, refresh_token=temp_refresh_token)
        # except Exception as e:
        #     print('OAUTH EXCEPTION: '+str(e))
        #     # self.label_18.setText(self.lineEdit_6.text())

    def remove_version(self):
        log("remove version", "OAUTH", level=1)
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        log(str(self.comboBox_5.currentText()))
        if len(str(self.comboBox_5.currentText())) == 0:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        ver = str(self.comboBox_5.currentText())

        QMessageBox.information(None, l18n.string("appName"), ver+l18n.string("willBeDeleted"))
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
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_saves.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectSave"))
            return 1
        save = self.listView_saves.selectionModel().selectedIndexes()[0].data()

        QMessageBox.information(None, l18n.string("appName"), save+l18n.string("willBeDeleted"))
        manager.remove_save(minecraft_dir, ver, save)
        self.switch_manager_select_version(instance_name=ver)

    def remove_respack(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if self.comboBox_5.currentText() == '':
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_respacks.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectRespack"))
            return 1
        respack = self.listView_respacks.selectionModel().selectedIndexes()[0].data()

        QMessageBox.information(None, l18n.string("appName"), respack+l18n.string("willBeDeleted"))
        manager.remove_resourcepack(minecraft_dir, ver, respack)
        self.switch_manager_select_version(instance_name=ver)


    def switch_manager_select_version(self, instance_name=None):
        if not instance_name:
            instance_name = self.comboBox_5.currentText()
        self.checkBox_6.setChecked(False)
        self.lineEdit_9.setText('')
        if instance_name in self.versions_config:
            try:
                self.checkBox_6.setChecked(self.versions_config[instance_name]['if_override_java'])
                self.lineEdit_9.setText(self.versions_config[instance_name]['override_java_path'])
            except:
                pass
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1
        
        if self.comboBox_5.currentText() == '':
            return 1
        instance_name = self.comboBox_5.currentText()

        # 设置存档列表
        self.model_saves = QStandardItemModel()
        data = manager.get_saves(minecraft_dir, instance_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{instance_name}/saves/{i}/icon.png'
            if os.path.exists(save_icon):
                self.model_saves.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_saves.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_saves.setModel(self.model_saves) # 版本列表

        # 设置资源包列表
        self.model_respacks = QStandardItemModel()
        data = manager.get_resourcepacks(minecraft_dir, instance_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{instance_name}/resourcepacks/{i}/pack.png'
            if os.path.exists(save_icon):
                self.model_respacks.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_respacks.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_respacks.setModel(self.model_respacks) # 版本列表

        # 设置Mod列表
        self.model_mods = QStandardItemModel()
        data = manager.get_mods(minecraft_dir, instance_name)

        for i in data:
            self.model_mods.appendRow(QStandardItem(QIcon(default_icon), i))
        self.listView_mods.setModel(self.model_mods) # 版本列表

        # 设置光影d列表
        self.model_shaderpacks = QStandardItemModel()
        data = manager.get_shaderpacks(minecraft_dir, instance_name)

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
        instance_name = self.comboBox_5.currentText()

        saves_path = f'{minecraft_dir}/versions/{instance_name}/saves'
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
                                QMessageBox.warning(None, l18n.string("appName"), l18n.string("fileIsNotSaveFolderSaveZip"))
                                shutil.rmtree(saves_path+'/'+dirname)
                    except z.BadZipFile:
                        QMessageBox.warning(None, l18n.string("appName"), l18n.string("fileIsNotSaveFolderSaveZip"))
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
                                QMessageBox.warning(None, l18n.string("appName"), l18n.string("fileIsNotRespackFolderRespackZip"))
                                shutil.rmtree(saves_path+'/'+dirname)
                    except z.BadZipFile:
                        QMessageBox.warning(None, l18n.string("appName"), l18n.string("fileIsNotRespackFolderRespackZip"))
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

            _ = QStringListModel()
            _.setStringList(versions)
            self.listView_2.setModel(_)
            self.comboBox_5.setModel(_)
            self.comboBox_6.setModel(_)
    
    def launch(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("minecraftPathInvalid"))
            return 1
        
        if self.launch_version == None:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        instance_name = self.launch_version

        if instance_name in self.versions_config and self.versions_config[instance_name]['if_override_java']:
            javaw = self.versions_config[instance_name]['override_java_path']
        else:
            java_major_version = launcher.get_required_java_version(minecraft_dir, instance_name)
            javaw = self.get_java(version=java_major_version)
            if not javaw:
                QMessageBox.critical(None, l18n.string("appName"), l18n.string("ui", "javaNotFoundOrNoSuitable")\
                    .replace('${version}', str(java_major_version))\
                    .replace('${hint_url}', java.get_url(java_major_version, 'jre', tuna=True)))
                return 1
        xmx = self.comboBox_4.currentText()

        username = self.accounts[self.comboBox_8.currentIndex()]['name']
        # if len(username) > 16:
        #     QMessageBox.warning(None, l18n.string("appName"), '玩家名称长度>16，可能出现问题。')
        # punctuations = "[!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~]"
        # pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\uff00-\uffef\s' + punctuations + ']') # CJK chars; symbol; full-width chars; spaces; 
        # if bool(pattern.search(username)):
        #     QMessageBox.warning(None, l18n.string("appName"), '玩家名称含有其他语言字符，可能出现问题。')

        if launcher.native() == 'windows':
            javawrapper = app_path + '/JavaWrapper.jar'
            if not os.path.exists(javawrapper):
                QMessageBox.critical(None, l18n.string("appName"), l18n.string("javaWrapperInvalid"))
                return 1
        else:
            javawrapper = None

        if self.accounts[self.comboBox_8.currentIndex()]['type'] == 'offline':
            access_token = None
        else:
            access_token = oa.refresh_token(self.accounts[self.comboBox_8.currentIndex()]['refresh_token'])

        uuid = self.accounts[self.comboBox_8.currentIndex()].get('uuid', None)
        # 使用QProcess启动Minecraft而不阻塞UI\
        if self.lineEdit_10.text() != '':
            version_type = self.lineEdit_10.text()
        else:
            version_type = '§l§1S§9p§2e§ac§3t§br§9u§1m§r Launcher'
            # version_type = 'NullPointerException'
        cmd = launcher.launch(javaw=javaw, xmx=xmx, minecraft_dir=minecraft_dir, 
                            instance_name=instance_name, javawrapper=javawrapper, 
                            username=username, ms_login=self.accounts[self.comboBox_8.currentIndex()]['type'] == 'microsoft', 
                            access_token=access_token,
                            version_type=version_type,
                            jvm_args=self.lineEdit_11.text(),
                            game_args_extend=self.lineEdit_12.text(),
                            uuid=uuid)
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
                self.minecraft_process.start(app_path+'/launch.bat')
            else:
                # 对于Linux/Mac，使用bash
                self.minecraft_process.start('bash', ['-c', cmd])

    def handle_minecraft_output(self):
        data = self.minecraft_process.readAllStandardOutput()
        stdout = bytes(data).decode("gbk", errors='ignore')
        log(f"{l18n.string("minecraftOut")}: {stdout}")

    def handle_minecraft_error(self):
        data = self.minecraft_process.readAllStandardError()
        stderr = bytes(data).decode("gbk", errors='ignore')
        log(f"{l18n.string("minecraftErr")}: {stderr}")

    def handle_minecraft_finished(self, exit_code, exit_status):
        log(f"{l18n.string("minecraftExit")}: {exit_code}")
        
    def download(self):
        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        mcversion = self.listView.selectionModel().selectedIndexes()[0].data()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]

        instance_name = self.lineEdit_7.text()
        os.makedirs(minecraft_dir+'/versions', exist_ok=True)
        if instance_name in os.listdir(minecraft_dir+'/versions'):
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("nameAlreadyExists"))
            return 1
        
        modloader = self.comboBox.currentText().lower()
        if modloader == '无':
            modloader = 'vanilla'
        
        modloader_version = self.comboBox_2.currentText()
        if modloader_version == '' and modloader != 'vanilla':
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectModLoaderVersion"))
            return 1

        
        java_major_version = downloader.get_version_json(mcversion).get('javaVersion', {}).get('majorVersion', 0)
        if not java_major_version:
            java_major_version = 8  # default to Java 8 if not specified
        javaw = self.get_java(version=java_major_version)

        # Start asynchronous download to avoid blocking the UI
        self.start_download(minecraft_dir=minecraft_dir, mcversion=mcversion, instance_name=instance_name, modloader=modloader, modloader_version=modloader_version, java=javaw, bmclapi=self.checkBox.isChecked())
        # update will be handled when finished via signal handler

    def download_labymod(self):
        if len(self.listView_5.selectionModel().selectedIndexes()) == 0:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        mcversion = self.listView_5.selectionModel().selectedIndexes()[0].data()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]

        instance_name = self.lineEdit_14.text()
        os.makedirs(minecraft_dir+'/versions', exist_ok=True)
        if instance_name in os.listdir(minecraft_dir+'/versions'):
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("nameAlreadyExists"))
            return 1
        
        labymod.download(minecraftDirectory=minecraft_dir, version=4, mcversion=mcversion, instance_name=instance_name)
        downloader.auto_download(minecraft_dir, mcversion, instance_name, bmclapi=self.checkBox_7.isChecked())


        



    def download_fix(self):
        if self.comboBox_5.currentText() == None:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("selectVersion"))
            return 1
        instance_name = self.comboBox_5.currentText()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]

        # Start async download instead of blocking the UI
        mcversion = launcher.get_minecraft_version(minecraft_dir, instance_name)
        self.start_download(minecraft_dir=minecraft_dir, mcversion=mcversion, instance_name=instance_name)

    def _emit_progress(self, current, total, description):
        """Emit progress safely from background threads."""
        try:
            self.download_progress.emit(int(current), int(total), str(description))
        except Exception:
            pass

    def _on_download_progress(self, current, total, description):
        """Runs in main thread via Qt signal to update UI."""
        try:
            self.progress_callback(current, total, description)
        except Exception:
            pass

    def _on_download_finished(self, result, instance_name, minecraft_dir):
        """Handle completion in main thread."""
        # 重新启用UI
        try:
            self.pushButton_3.setEnabled(True)
            self.progressBar.setValue(0)
            self.progressBar_2.setValue(0)
        except Exception:
            pass
        
        # 无论结果如何都更新已安装版本
        try:
            self.update_installed_versions()
        except Exception:
            pass
        
        # 根据结果显示消息
        if isinstance(result, dict):
            if result.get('status') == 'exists':
                QMessageBox.information(None, l18n.string("appName"), l18n.string("downloadInProgress"))
                return
            if result.get('status') == 'error':
                QMessageBox.warning(None, l18n.string("appName"), 
                                l18n.string("downloadFail") + str(result.get('exc')))
                return
        
        # 如果downloader返回了魔法数字721，显示特定警告
        if result == 721:
            QMessageBox.warning(None, l18n.string("appName"), l18n.string("modloaderDownloadFail"))
            return
        
        # 成功下载
        # if result == 0 or result is None or (isinstance(result, dict) and result.get('status') == 'success'):
        #     QMessageBox.information(None, l18n.string("appName"), l18n.string("downloadComplete"))
        
        # 可选地在后台自动下载Fabric API
        try:
            if self.autodl_fabric_api and instance_name:
                # 在后台运行fabric下载以避免阻塞UI
                self._dl_executor.submit(
                    fabric.download_fabric_api, 
                    minecraft_dir, 
                    launcher.get_minecraft_version(minecraft_dir, instance_name), 
                    instance_name
                )
        except Exception:
            pass
        
    def _create_lock_file(self, key):
        """Atomically create a lock file for a given key. Returns True if created, False if exists."""
        path = os.path.join(self._dl_lock_dir, f"{key}.lock")
        
        # 首先检查内存中的集合
        if key in self._downloads_in_progress:
            return False
        
        try:
            # 尝试创建锁文件
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            # 创建成功后添加到内存集合
            self._downloads_in_progress.add(key)
            return True
        except FileExistsError:
            # 文件已存在，也添加到内存集合（避免重复检查）
            if key not in self._downloads_in_progress:
                self._downloads_in_progress.add(key)
            return False
        except Exception:
            # 其他错误，保守处理，认为已存在
            if key not in self._downloads_in_progress:
                self._downloads_in_progress.add(key)
            return False

    def _remove_lock_file(self, key):
        path = os.path.join(self._dl_lock_dir, f"{key}.lock")
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        try:
            if key in self._downloads_in_progress:
                self._downloads_in_progress.discard(key)
        except Exception:
            pass

    def _run_download_task(self, minecraft_dir, mcversion, instance_name, modloader, modloader_version, java, bmclapi):
        """Runs the blocking download in background thread while managing lock files.
        This is executed inside executor threads."""
        # Create a stable key based on minecraft_dir and instance_name
        key = hashlib.md5(minecraft_dir.encode('utf-8')).hexdigest() + '_' + str(instance_name)

        created = self._create_lock_file(key)
        if not created:
            return {'status': 'exists'}

        try:
            # Call into the existing downloader while forwarding progress via _emit_progress
            res = downloader.auto_download(minecraft_dir=minecraft_dir, mcversion=mcversion, instance_name=instance_name, modloader=modloader, modloader_version=modloader_version, progress_callback=self._emit_progress, java=java, bmclapi=bmclapi)
            return res
        except Exception as e:
            return {'status': 'error', 'exc': str(e)}
        finally:
            self._remove_lock_file(key)

    def start_download(self, minecraft_dir, mcversion, instance_name, modloader='vanilla', modloader_version='latest', java='java', bmclapi=False):
        """Public method to start a download asynchronously without blocking the UI."""
        # 快速检查实例名是否为空
        if not instance_name:
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("pleaseEnterInstanceName"))
            self.pushButton_3.setEnabled(True)
            return
        
        # 检查Minecraft目录是否存在
        if not os.path.exists(minecraft_dir):
            QMessageBox.critical(None, l18n.string("appName"), l18n.string("minecraftPathInvalid"))
            self.pushButton_3.setEnabled(True)
            return
        
        # 创建versions目录
        os.makedirs(os.path.join(minecraft_dir, 'versions'), exist_ok=True)
        
        # 检查实例是否已存在
        versions_dir = os.path.join(minecraft_dir, 'versions')
        # if os.path.exists(versions_dir) and instance_name in os.listdir(versions_dir):
        #     reply = QMessageBox.question(None, l18n.string("appName"), 
        #                                 l18n.string("nameAlreadyExists") + l18n.string("confirmOverwrite"),
        #                                 QMessageBox.Yes | QMessageBox.No)
        #     if reply == QMessageBox.No:
        #         self.pushButton_3.setEnabled(True)
        #         return
        
        # 防止重复点击UI
        self.pushButton_3.setEnabled(False)
        
        # 生成唯一的key
        key = hashlib.md5(f"{minecraft_dir}_{instance_name}".encode('utf-8')).hexdigest()
        
        # 先检查是否已在下载中
        if key in self._downloads_in_progress:
            QMessageBox.information(None, l18n.string("appName"), l18n.string("downloadInProgress"))
            self.pushButton_3.setEnabled(True)
            return
        
        # 添加到进行中的下载集合
        self._downloads_in_progress.add(key)
        
        # 在UI上显示下载开始
        self.progressBar.setValue(0)
        self.progressBar_2.setValue(0)
        
        # 提交阻塞工作到执行器
        future = self._dl_executor.submit(
            self._run_download_task, 
            minecraft_dir, 
            mcversion, 
            instance_name, 
            modloader, 
            modloader_version, 
            java, 
            bmclapi
        )
        
        def _done(fut):
            try:
                res = fut.result()
            except Exception as e:
                res = {'status': 'error', 'exc': str(e)}
            
            # 从内存跟踪中移除
            try:
                self._downloads_in_progress.discard(key)
            except Exception:
                pass
            
            # 移除锁文件
            lock_path = os.path.join(self._dl_lock_dir, f"{key}.lock")
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except Exception:
                pass
            
            # 发送完成信号（在主线程处理程序中运行）并包含目录
            self.download_finished.emit(res, instance_name, minecraft_dir)
        
        future.add_done_callback(_done)

    def progress_callback(self, current, total, description):
        if description[1:-1].split('][')[0] == 'LIB':
            self.progressBar.setValue(int(current/total*100))
        elif description[1:-1].split('][')[0] == 'AST':
            self.progressBar_2.setValue(int(current/total*100))

    def load_config(self):
        if os.path.exists(app_path+'/cfg.json'):
            with open(app_path+'/cfg.json', 'r') as f:
                config = json.loads(f.read())
                self.lineEdit_10.setText(config.get('launcher', {}).get('launcher_info', ''))
                self.lineEdit_11.setText(config.get('launcher', {}).get('jvm_args', ''))
                self.lineEdit.setText(config.get('launcher', {}).get('minecraftPath', ''))
                self.lineEdit_12.setText(config.get('launcher', {}).get('game_extend', ''))
                self.checkBox_5.setChecked(config.get('launcher', {}).get('auto_download_fabric_api_mod', False))
                memory = config.get('launcher', {}).get('memory', '2048M')
                self.comboBox_4.setCurrentText(memory)
                self.javas.clear()
                for i in config.get('javas', []):
                    self.javas[i] = java.get_java_version(i)
                self.refresh_java_combo()
        else:
            self.lineEdit.setText('.minecraft')


        if os.path.exists(app_path+'/versions.json'):
            with open(app_path+'/versions.json', 'r') as f:        
                self.versions_config = json.loads(f.read())
        else:
            self.versions_config = {}
    
    def save_config(self):
        jsonfile = {'launcher': {}}
        jsonfile['launcher']['wrapperPath'] = './JavaWrapper.jar'
        jsonfile['launcher']['minecraftPath'] = self.lineEdit.text()
        jsonfile['launcher']['auto_download_fabric_api_mod'] = self.checkBox_5.isChecked()
        jsonfile['launcher']['launcher_info'] = self.lineEdit_10.text()
        jsonfile['launcher']['jvm_args'] = self.lineEdit_11.text()
        jsonfile['launcher']['game_extend'] = self.lineEdit_12.text()
        jsonfile['launcher']['memory'] = self.comboBox_4.currentText()
        jsonfile['javas'] = list(self.javas.keys())

        with open(app_path+'/cfg.json', 'w') as f:
            f.write(json.dumps(jsonfile))
    
    def save_accounts(self):
        jsonfile = []
        for i in self.accounts:
            jsonfile.append(i)
        with open(app_path+'/accounts.json', 'w') as f:
            f.write(json.dumps(jsonfile))
    
    def load_accounts(self):
        if os.path.exists(app_path+'/accounts.json'):
            with open(app_path+'/accounts.json', 'r') as f:
                self.accounts = json.loads(f.read())
                if not isinstance(self.accounts, list):
                    self.accounts = []
                    return
            for i in self.accounts:
                self.comboBox_8.addItem(i['name']+f' ({l18n.string("ui", "microsoftAccount")})' if i['type']=='microsoft' else i['name']+f' ({l18n.string("ui", "offlineAccount")})')
                self.listView_4_Model = []
                for i in self.accounts:
                    self.listView_4_Model.append(i['name']+f'\t{l18n.string("ui", "microsoftAccount")}' if i['type']=='microsoft' else i['name']+f'\t{l18n.string("ui", "offlineAccount")}')
                self.listView_4.setModel(QStringListModel(self.listView_4_Model))
        else:
            self.accounts = []

    def save_version_config(self):
        version=self.comboBox_5.currentText()
        data = {
            'if_override_java': self.checkBox_6.isChecked(),
            'override_java_path': self.lineEdit_9.text()
        }
        jsonfile = {}
        try:
            if os.path.exists(app_path+'/versions.json'):
                with open(app_path+'/versions.json', 'r') as f:
                    jsonfile = json.loads(f.read())
        except:
            pass
        jsonfile[version] = data
        self.versions_config = jsonfile

        with open(app_path+'/versions.json', 'w') as f:
            f.write(json.dumps(jsonfile))

    def update_version_list(self, state=None):
        try:
            current_list = downloader.get_version_list(self.checkBox_2.isChecked(), self.checkBox_3.isChecked(), self.checkBox_4.isChecked(), self.checkBox.isChecked())
        except:
            current_list = []
            log('FAIL TO RETRIEVE MINECRAFT VERSIONS', 'WARN', level=0)
        self.listView.setModel(QStringListModel(current_list)) # 版本列表

    def update_ml_version_list(self, state):
        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            return 0
        version = self.listView.selectionModel().selectedIndexes()[0].data()
        modloader = self.comboBox.currentText().lower()
        if modloader == 'forge':
            current_dict = forge.get_forge_version(version)
            current_list = []
            for item in current_dict:
                current_list.append(item["version"])
        elif modloader == 'fabric':
            current_list = fabric.get_fabric_versions()
        elif modloader == 'neoforge':
            current_dict = neoforge.get_neoforge_version(version)
            current_list = []
            for item in current_dict:
                current_list.append(item["version"])
        else:
            current_list = []

        self.comboBox_2.clear()
        for ver in current_list:
            self.comboBox_2.addItem(ver)

    # Modrinth stuff (quite simple, thx for the api author)
    def load_icon(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 将数据转换为QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            # 创建QIcon
            icon = QIcon(pixmap)
            return icon
        except Exception as e:
            print(l18n.string("iconLoadFail")+e)
            return QIcon()

    def search_modrinth(self):
        AddMod = Exception
        # Get arguments needed
        keyword = self.lineEdit_13.text()
        if len(keyword) <= 3:
            log(l18n.string("modrinthKeywordTooShort"))

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return
        
        try:
            instance_name = self.comboBox_6.currentText()
            mcversion = launcher.get_minecraft_version(minecraft_dir, instance_name)
        except Exception as E:
            log(l18.cannotGetMinecraftVersion)

        modloader = self.comboBox_3.currentText()

        # Search
        results = modrinth.search_project(query=keyword)
        mods = []

        _ = QStandardItemModel()
        for project in results.hits:
            versions = modrinth.list_project_versions(project.project_id)
            try:
                for ver in versions:
                    if (mcversion in ver.game_versions and modloader.lower() in ver.loaders):
                        raise AddMod()
            except AddMod:
                mods.append(project.project_id)
                _.appendRow(QStandardItem(project.title+'\n'+project.description))
        self.listView_3.setModel(_)
        self.mods = mods

    def install_modrinth(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return
        
        try:
            instance_name = self.comboBox_6.currentText()
            mcversion = launcher.get_minecraft_version(minecraft_dir, instance_name)
        except Exception as E:
            log(l18n.string("cannotGetMinecraftVersion"))

        modloader = self.comboBox_3.currentText()

        
        selected_indexes = self.listView_3.selectionModel().selectedIndexes()
        if not selected_indexes:
            return
        
        project_id = self.mods[selected_indexes[0].row()]
        versions = modrinth.list_project_versions(project_id)
        for ver in versions:
            if (mcversion in ver.game_versions and modloader.lower() in ver.loaders):
                mods_path = f'{minecraft_dir}/versions/{instance_name}/mods'
                os.makedirs(mods_path, exist_ok=True)
                url = ver.files[0].url
                destination = mods_path+'/'+ver.files[0].filename
                raw = requests.get(url)
                with open(destination, 'wb') as f:
                    f.write(raw.content)
                    return

    def refresh_java_combo(self):
        self.comboBox_7.clear()
        for path, version in sorted(
            self.javas.items(), key=lambda item: item[1], reverse=True
        ):
            self.comboBox_7.addItem(f"Java {version} — {path}", path)

    def scan_system_javas(self):
        log("Scanning system Java installations", "JAVA", level=1)
        for entry in java.find_javas():
            path = entry["path"] if isinstance(entry, dict) else entry.path
            self.add_java(path)
        self.refresh_java_combo()

    def prompt_download_java(self):
        version, ok = QInputDialog.getItem(
            self,
            "下载 Java",
            "选择 Java 主版本:",
            ["8", "17", "21"],
            0,
            False,
        )
        if ok and version:
            self.download_java(int(version))

    def add_java(self, file_path):
        if file_path in self.javas:
            return
        v = java.get_java_version(file_path)
        if not v:
            log('Bad java path: '+file_path)
            return
        self.javas[file_path] = v
    
    def remove_java(self):
        current_java = self.comboBox_7.currentData() or self.comboBox_7.currentText()
        if current_java in self.javas:
            del self.javas[current_java]
        self.refresh_java_combo()

    def get_java(self, version):
        for java in self.javas:
            if self.javas[java] == version:
                return java



log(l18n.string("startingMainIs")+__name__)
if __name__ in ("__main__", "__compiled__", "__mp_main__"):
    if spectrum_core_mod.rust_available():
        spectrum_core_mod.require_native().init(
            use_bmclapi=os.environ.get("SPECTRUM_USE_BMCLAPI", "1").lower()
            not in ("0", "false", "no")
        )
    if launcher.native() == "windows" and not os.path.exists(app_path+'/JavaWrapper.jar'):
        log(l18n.string("javaWrapper"), "INIT", level=1)
        download_javawrapper()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
