import sys
import os
import re
import json
import mclauncher_core as launcher
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui import Ui_MainWindow
from tkinter import messagebox as msgbox


def app_path():
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    else:
        path = os.path.dirname(os.path.abspath(__file__))
    
    path = path.replace('\\', '/')
    if path[-1] == '/':
        path = path[:-1]

    return path

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

        self.load_config()

        self.update_installed_versions()

    def update_installed_versions(self):
        minecraft_dir = self.lineEdit.text().replace('\\', '/')
        if minecraft_dir[-1] == '/':
            minecraft_dir = minecraft_dir[:-1]
        if os.path.exists(minecraft_dir+'/versions'):
            versions = os.listdir(minecraft_dir+'/versions')

            self.comboBox_3.clear()
            for ver in versions:
                self.comboBox_3.addItem(ver)
    
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
        
        modloader = self.comboBox.currentText()
        if modloader == '无':
            modloader = 'vanilla'
        
        modloader_version = self.comboBox_2.currentText()
        if modloader_version == '' and modloader != 'vanilla':
            msgbox.showerror('Spectrum 启动器', '请选择模组加载器的版本。')
            return 1

        launcher.auto_download(minecraft_dir=minecraft_dir, version=version, version_name=version_name, modloader=modloader, modloader_version=modloader_version, progress_callback=self.progress_callback)
        self.update_installed_versions()

    def progress_callback(self, current, total, description):
        if description[1:-1].split('][')[0] == 'LIB':
            self.progressBar.setValue(int(current/total*100))
        elif description[1:-1].split('][')[0] == 'AST':
            self.progressBar_2.setValue(int(current/total*100))

    def set_version_list(self, version_list: list):
        current_list = self.model.stringList()
        current_list = version_list
        self.model.setStringList(current_list)
    
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

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MainWindow()
    myWin.show()
    sys.exit(app.exec_())