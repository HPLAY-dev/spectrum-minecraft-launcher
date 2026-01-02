import json
import platform
import locale
import os

from PySide6.QtCore import QCoreApplication

_langfile = {}


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
if os.path.exists('languages/'+lang+".json"):
    try:
        with open('languages/'+lang+'.json', 'r', encoding='utf-8') as f:
            _langfile = json.loads(f.read())
    except Exception as e:
        print('[l18n] Language File Load Error'+str(e))
elif os.path.exists("languages/en_us.json"):
    print('[l18n] Language File Using Fallback')
    try:
        with open('languages/en_us.json', 'r', encoding='utf-8') as f:
            _langfile = json.loads(f.read())
    except Exception as e:
        print('[l18n] Language File Load Error'+str(e))
else:
    print('[l18n] Language File Missing')

def string(*key: str):
    """递归获取语言文件中的值。

    使用方式：
      - string('ui') -> 返回 _langfile['ui']（通常是 dict）
      - string('ui', 'windowTitle') -> 返回 _langfile['ui']['windowTitle']

    若任一键不存在，打印警告并返回空字符串（fallback 使用当前加载的语言文件）。
    """
    if not key:
        return ''

    node = _langfile
    for k in key:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            print(f"[l18n] Cannot find key: {'/'.join(key)}")
            return ''
    return node



def retranslateUi(self, MainWindow):
    MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", string("ui", "windowTitle"), None))
    self.LaunchBtn.setText(QCoreApplication.translate("MainWindow", string("ui", "launchBtn"), None))
    self.pushButton_2.setText(QCoreApplication.translate("MainWindow", string("ui", "useBrowserNextStep"), None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", string("ui", "officialLoginTab"), None))
    self.lineEdit_6.setText(QCoreApplication.translate("MainWindow", string("ui", "alpha"), None))
    self.label_19.setText(QCoreApplication.translate("MainWindow", string("ui", "name"), None))
    self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", string("ui", "offlineLoginTab"), None))
    self.comboBox_4.setItemText(0, QCoreApplication.translate("MainWindow", string("ui", "memory2048M"), None))
    self.comboBox_4.setItemText(1, QCoreApplication.translate("MainWindow", string("ui", "memory256M"), None))
    self.comboBox_4.setItemText(2, QCoreApplication.translate("MainWindow", string("ui", "memory512M"), None))
    self.comboBox_4.setItemText(3, QCoreApplication.translate("MainWindow", string("ui", "memory768M"), None))
    self.comboBox_4.setItemText(4, QCoreApplication.translate("MainWindow", string("ui", "memory1024M"), None))
    self.comboBox_4.setItemText(5, QCoreApplication.translate("MainWindow", string("ui", "memory1536M"), None))
    self.comboBox_4.setItemText(6, QCoreApplication.translate("MainWindow", string("ui", "memory3G"), None))
    self.comboBox_4.setItemText(7, QCoreApplication.translate("MainWindow", string("ui", "memory4G"), None))
    self.comboBox_4.setItemText(8, QCoreApplication.translate("MainWindow", string("ui", "memory6G")))
    self.comboBox_4.setItemText(9, QCoreApplication.translate("MainWindow", string("ui", "memory8G"), None))

    self.label_10.setText(QCoreApplication.translate("MainWindow", string("ui", "memoryAllocation"), None))
    self.DownloadFixBtn.setText(QCoreApplication.translate("MainWindow", string("ui", "downloadFixFiles"), None))
    self.pushButton_15.setText(QCoreApplication.translate("MainWindow", string("ui", "upArrow"), None))
    self.label_18.setText("")
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_1), QCoreApplication.translate("MainWindow", string("ui", "launchTab"), None))
    self.label_7.setText(QCoreApplication.translate("MainWindow", string("ui", "versionList"), None))
    self.checkBox.setText(QCoreApplication.translate("MainWindow", string("ui", "bmclapiMirror"), None))
    self.checkBox_2.setText(QCoreApplication.translate("MainWindow", string("ui", "showSnapshotVersions"), None))
    self.checkBox_3.setText(QCoreApplication.translate("MainWindow", string("ui", "showAncientVersions"), None))
    self.checkBox_4.setText(QCoreApplication.translate("MainWindow", string("ui", "showReleaseVersions"), None))
    self.label_8.setText(QCoreApplication.translate("MainWindow", string("ui", "versionName"), None))
    self.pushButton_3.setText(QCoreApplication.translate("MainWindow", string("ui", "download"), None))
    self.label_9.setText(QCoreApplication.translate("MainWindow", string("ui", "modLoader"), None))
    self.comboBox.setItemText(0, QCoreApplication.translate("MainWindow", string("ui", "none"), None))
    self.comboBox.setItemText(1, QCoreApplication.translate("MainWindow", string("ui", "forge"), None))
    self.comboBox.setItemText(2, QCoreApplication.translate("MainWindow", string("ui", "fabric"), None))
    self.comboBox.setItemText(3, QCoreApplication.translate("MainWindow", string("ui", "neoforge"), None))

    self.checkBox_5.setText(QCoreApplication.translate("MainWindow", string("ui", "autoDownloadFabricAPI"), None))
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", string("ui", "downloadTab"), None))
    self.label_12.setText(QCoreApplication.translate("MainWindow", string("ui", "minecraftVersion"), None))
    self.pushButton_4.setText(QCoreApplication.translate("MainWindow", string("ui", "delete"), None))
    self.pushButton_9.setText(QCoreApplication.translate("MainWindow", string("ui", "rename"), None))
    self.lineEdit_5.setPlaceholderText(QCoreApplication.translate("MainWindow", string("ui", "newName"), None))
    self.pushButton_14.setText(QCoreApplication.translate("MainWindow", string("ui", "open"), None))
    self.label_15.setText(QCoreApplication.translate("MainWindow", string("ui", "mod"), None))
    self.label_13.setText(QCoreApplication.translate("MainWindow", string("ui", "versionSaves"), None))
    self.pushButton_8.setText(QCoreApplication.translate("MainWindow", string("ui", "deleteShaders"), None))
    self.pushButton_5.setText(QCoreApplication.translate("MainWindow", string("ui", "deleteSaves"), None))
    self.label_14.setText(QCoreApplication.translate("MainWindow", string("ui", "resourcePacks"), None))
    self.pushButton_6.setText(QCoreApplication.translate("MainWindow", string("ui", "deleteResourcePacks"), None))
    self.pushButton_7.setText(QCoreApplication.translate("MainWindow", string("ui", "deleteMods"), None))
    self.label_16.setText(QCoreApplication.translate("MainWindow", string("ui", "shaderPacks"), None))
    self.label_21.setText(QCoreApplication.translate("MainWindow", string("ui", "versionFiles"), None))
    self.pushButton_16.setText(QCoreApplication.translate("MainWindow", string("ui", "ellipsis"), None))
    self.pushButton_17.setText(QCoreApplication.translate("MainWindow", string("ui", "saveVersionSettings"), None))
    self.checkBox_6.setText(QCoreApplication.translate("MainWindow", string("ui", "forceJava"), None))
    self.label_23.setText(QCoreApplication.translate("MainWindow", string("ui", "versionSettings"), None))
    self.pushButton_20.setText(QCoreApplication.translate("MainWindow", string("ui", "refresh"), None))
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", string("ui", "versionManagementTab"), None))
    self.pushButton_12.setText(QCoreApplication.translate("MainWindow", string("ui", "downloadJ21"), None))
    self.pushButton_13.setText(QCoreApplication.translate("MainWindow", string("ui", "ellipsis"), None))
    self.lineEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", string("ui", "path"), None))
    self.label.setText(QCoreApplication.translate("MainWindow", string("ui", "minecraftFolder"), None))
    self.pushButton_11.setText(QCoreApplication.translate("MainWindow", string("ui", "downloadJ17"), None))
    self.pushButton_10.setText(QCoreApplication.translate("MainWindow", string("ui", "downloadJ8"), None))
    self.label_22.setText(QCoreApplication.translate("MainWindow", string("ui", "basicSettings"), None))
    self.label_24.setText(QCoreApplication.translate("MainWindow", string("ui", "personalization"), None))
    self.lineEdit_10.setPlaceholderText(QCoreApplication.translate("MainWindow", string("ui", "displayInBottomLeft"), None))
    self.label_5.setText(QCoreApplication.translate("MainWindow", string("ui", "launcherInfo"), None))
    self.label_20.setText(QCoreApplication.translate("MainWindow", string("ui", "jvmArguments"), None))
    self.lineEdit_11.setText("")
    self.lineEdit_11.setPlaceholderText(QCoreApplication.translate("MainWindow", string("ui", "useDefaultIfEmpty"), None))
    self.label_25.setText(QCoreApplication.translate("MainWindow", string("ui", "advancedSettings"), None))
    self.lineEdit_12.setPlaceholderText(QCoreApplication.translate("MainWindow", string("ui", "appendToLaunchArgs"), None))
    self.label_26.setText(QCoreApplication.translate("MainWindow", string("ui", "gameArguments"), None))
    self.pushButton.setText(QCoreApplication.translate("MainWindow", string("ui", "saveSettings"), None))
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", string("ui", "settingsTab"), None))
    self.label_17.setText(QCoreApplication.translate("MainWindow", string("ui", "aboutText"), None))
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_6), QCoreApplication.translate("MainWindow", string("ui", "aboutTab"), None))
    self.label_27.setText(QCoreApplication.translate("MainWindow", string("ui", "searchMod"), None))
    self.label_28.setText(QCoreApplication.translate("MainWindow", string("ui", "name"), None))
    self.label_29.setText(QCoreApplication.translate("MainWindow", string("ui", "minecraftVersion"), None))
    self.comboBox_3.setItemText(0, QCoreApplication.translate("MainWindow", string("ui", "fabric"), None))
    self.comboBox_3.setItemText(1, QCoreApplication.translate("MainWindow", string("ui", "forge"), None))
    self.comboBox_3.setItemText(2, QCoreApplication.translate("MainWindow", string("ui", "neoforge"), None))
    self.comboBox_3.setItemText(3, QCoreApplication.translate("MainWindow", string("ui", "quilt"), None))
    self.comboBox_3.setItemText(4, QCoreApplication.translate("MainWindow", string("ui", "liteloader"), None))

    self.pushButton_18.setText(QCoreApplication.translate("MainWindow", string("ui", "search"), None))
    self.pushButton_19.setText(QCoreApplication.translate("MainWindow", string("ui", "installThisMod"), None))
    self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.tab_7), QCoreApplication.translate("MainWindow", string("ui", "modrinthTab"), None))
    self.label_6.setText("")
# retranslateUi