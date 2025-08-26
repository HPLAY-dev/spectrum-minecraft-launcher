import sys
import os
import re
import json
import mclauncher_core as launcher
import shutil
import zipfile as z
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QStringListModel, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QStandardItemModel, QIcon, QStandardItem
from ui import Ui_MainWindow
from tkinter import messagebox as msgbox
from qt_material import apply_stylesheet


def app_path():
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]

    return path

def fpath(path):
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]
    return path

default_save_icon = app_path()+'/assets/default_save_icon.png'
if not os.path.exists(app_path()+'/assets/default_save_icon.png'):
    msgbox.showerror('Assets load fail', '/assets/default_save_icon.png')
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):    
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        
        # 设置版本列表
        self.model = QStringListModel()
        data = launcher.get_version_list()
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
        
        self.load_config()

        self.update_installed_versions()

    def remove_version(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            msgbox.showerror('Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = self.listView.selectionModel().selectedIndexes()[0].data()

        msgbox.showinfo('Spectrum 启动器', f'“{ver}”将会永久消失！（真的很久！）')
        launcher.remove_version(minecraft_dir, ver)
        self.update_installed_versions()

    def remove_save(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if self.comboBox_5.currentText() == '':
            msgbox.showerror('Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_saves.selectionModel().selectedIndexes()) == 0:
            msgbox.showerror('Spectrum 启动器', '你必须选择一个存档。')
            return 1
        save = self.listView_saves.selectionModel().selectedIndexes()[0].data()

        msgbox.showinfo('Spectrum 启动器', f'“{save}”将会永久消失！（真的很久！）')
        launcher.remove_save(minecraft_dir, ver, save)
        self.switch_manager_select_version(version_name=ver)

    def remove_respack(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            return 1

        if self.comboBox_5.currentText() == '':
            msgbox.showerror('Spectrum 启动器', '你必须选择一个版本。')
            return 1
        ver = self.comboBox_5.currentText()

        if len(self.listView_respack.selectionModel().selectedIndexes()) == 0:
            msgbox.showerror('Spectrum 启动器', '你必须选择一个资源包。')
            return 1
        respack = self.listView_respack.selectionModel().selectedIndexes()[0].data()

        msgbox.showinfo('Spectrum 启动器', f'“{respack}”将会永久消失！（真的很久！）')
        launcher.remove_resourcepack(minecraft_dir, ver, respack)
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
        data = launcher.get_saves(minecraft_dir, version_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{version_name}/saves/{i}/icon.png'
            if os.path.exists(save_icon):
                self.model_saves.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_saves.appendRow(QStandardItem(QIcon(default_save_icon), i))
        self.listView_saves.setModel(self.model_saves) # 版本列表

        # 设置资源包列表
        self.model_respacks = QStandardItemModel()
        data = launcher.get_resourcepacks(minecraft_dir, version_name)

        for i in data:
            save_icon = f'{minecraft_dir}/versions/{version_name}/resourcepacks/{i}/pack.png'
            if os.path.exists(save_icon):
                self.model_respacks.appendRow(QStandardItem(QIcon(save_icon), i))
            else:
                self.model_respacks.appendRow(QStandardItem(QIcon(default_save_icon), i))
        self.listView_respack.setModel(self.model_respacks) # 版本列表

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
        print()
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
                                msgbox.showwarning('Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
                                shutil.rmtree(saves_path+'/'+dirname)
                    except zipfile.BadZipFile:
                        msgbox.showwarning('Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
            event.accept()
        elif widget_under_cursor.objectName() == 'listView_respack':
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
                                msgbox.showwarning('Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
                                shutil.rmtree(saves_path+'/'+dirname)
                    except zipfile.BadZipFile:
                        msgbox.showwarning('Spectrum 启动器', '文件不是存档文件夹或压缩为.zip的存档文件夹')
            event.accept()

    def page_process(self, page_index):
        if page_index == 2:
            self.setAcceptDrops(True)
        else:
            self.setAcceptDrops(False)

    def update_installed_versions(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
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
            msgbox.showerror('Spectrum 启动器', 'Minecraft路径不存在。')
            return 1
        
        if self.comboBox_3.currentText() == '':
            msgbox.showerror('Spectrum 启动器', '你必须选择一个版本来启动。')
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
            msgbox.showwarning('Spectrum 启动器', '玩家名称长度>16，可能出现问题。')
        punctuations = "[!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~]"
        pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\uff00-\uffef\s' + punctuations + ']') # CJK chars; symbol; full-width chars; spaces; 
        if bool(pattern.search(username)):
            msgbox.showwarning('Spectrum 启动器', '玩家名称含有其他语言字符，可能出现问题。')

        javawrapper = self.lineEdit_5.text()
        if not os.path.exists(javawrapper):
            msgbox.showerror('Spectrum 启动器', 'JavaWrapper路径不存在。')
            return 1

        cmd = launcher.launch(javaw=javaw, xmx=xmx, minecraft_dir=minecraft_dir, version_name=version_name, javawrapper=javawrapper, username=username)
        with open(app_path()+'/launch.bat', 'w') as f:
            f.write('@echo off\n'+cmd)
        os.system(app_path()+'/launch.bat')
        

    def download(self):
        if len(self.listView.selectionModel().selectedIndexes()) == 0:
            msgbox.showerror('Spectrum 启动器', '你必须选择一个版本来下载。')
            return 1
        version = self.listView.selectionModel().selectedIndexes()[0].data()

        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if not os.path.exists(minecraft_dir):
            msgbox.showerror('Spectrum 启动器', 'Minecraft路径不存在。')
            return 1

        version_name = self.lineEdit_7.text()
        os.makedirs(minecraft_dir+'/versions', exist_ok=True)
        if version_name in os.listdir(minecraft_dir+'/versions'):
            msgbox.showerror('Spectrum 启动器', 'Minecraft路径中已经包含此名称的版本。')
            return 1
        
        modloader = self.comboBox.currentText().lower()
        if modloader == '无':
            modloader = 'vanilla'
        
        modloader_version = self.comboBox_2.currentText()
        if modloader_version == '' and modloader != 'vanilla':
            msgbox.showerror('Spectrum 启动器', '请选择模组加载器的版本。')
            return 1

        r = launcher.auto_download(minecraft_dir=minecraft_dir, version=version, version_name=version_name, modloader=modloader, modloader_version=modloader_version, progress_callback=self.progress_callback)
        if r == 721:
            msgbox.showwarning('Spectrum 启动器', '下载的modloader与minecraft版本不被Spectrum启动器所兼容')
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
            self.lineEdit_5.setText(config['wrapperPath'])
    
    def save_config(self):
        jsonfile = {}
        jsonfile['minecraftPath'] = self.lineEdit.text()
        jsonfile['java8'] = self.lineEdit_2.text()
        jsonfile['java17'] = self.lineEdit_3.text()
        jsonfile['java21'] = self.lineEdit_4.text()
        jsonfile['wrapperPath'] = self.lineEdit_5.text()

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
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='light_blue.xml')
    myWin = MainWindow()
    myWin.show()
    sys.exit(app.exec_())