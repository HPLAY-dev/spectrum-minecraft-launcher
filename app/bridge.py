"""QML / Vue UI 桥接层 — 连接 MainWindow 后端与新界面。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot

if TYPE_CHECKING:
    from main import MainWindow


class AppBridge(QObject):
    """暴露启动器能力给 QML。"""

    accountsChanged = Signal()
    instancesChanged = Signal()
    versionsChanged = Signal()
    labymodVersionsChanged = Signal()
    downloadProgress = Signal(int, int, str)
    downloadFinished = Signal(bool, str)
    toast = Signal(str, str)
    consoleLog = Signal(str)
    currentPageChanged = Signal()
    managerDataChanged = Signal()

    def __init__(self, backend: "MainWindow", parent=None):
        super().__init__(parent)
        self._backend = backend
        self._current_page = 0
        self._nav_to_backend = {0: 0, 1: 3, 2: 7, 3: 5}
        self._selected_instance = ""
        self._download_pct_main = 0
        self._download_pct_assets = 0

        backend.download_progress.connect(self._on_download_progress)
        backend.download_finished.connect(self._on_download_finished)

        import main as main_module

        main_module.set_log_listener(self.consoleLog.emit)

    @Property(int, notify=currentPageChanged)
    def currentPage(self):
        return self._current_page

    @Slot(int)
    def setCurrentPage(self, index: int):
        if self._current_page != index:
            self._current_page = index
            self._switch_backend(self._nav_to_backend.get(index, 0))
            self.currentPageChanged.emit()

    @Slot(int)
    def setBackendTab(self, backend_index: int):
        self._switch_backend(backend_index)

    def _switch_backend(self, backend_index: int):
        idx = min(backend_index, self._backend.mainTabWidget.count() - 1)
        self._backend.mainTabWidget.setCurrentIndex(idx)
        self._backend.page_process(idx)

    @Slot(result=list)
    def getAccounts(self) -> list:
        items = []
        for i, acc in enumerate(self._backend.accounts):
            kind = "Microsoft" if acc.get("type") == "microsoft" else "Offline"
            items.append({"index": i, "name": acc.get("name", ""), "type": kind})
        return items

    @Slot(result=list)
    def getInstances(self) -> list:
        try:
            mc = self._backend.get_minecraft_dir()
            from spectrum_core import manager

            return manager.list_instances(mc)
        except Exception:
            return []

    @Slot(result=list)
    def getVersionList(self) -> list:
        try:
            self._backend.update_version_list()
            m = self._backend.listView.model()
            return list(m.stringList()) if m else []
        except Exception:
            return []

    @Slot(result=list)
    def getLabymodVersions(self) -> list:
        try:
            m = self._backend.listView_5.model()
            return list(m.stringList()) if m else []
        except Exception:
            return []

    @Slot(str)
    def selectInstance(self, name: str):
        self._selected_instance = name
        self._backend.launch_version = name or None

    @Slot(int)
    def selectAccount(self, index: int):
        if 0 <= index < self._backend.comboBox_8.count():
            self._backend.comboBox_8.setCurrentIndex(index)

    @Slot(str)
    def setMinecraftDir(self, path: str):
        self._backend.lineEdit.setText(path)

    @Slot(result=str)
    def getMinecraftDir(self) -> str:
        return self._backend.lineEdit.text()

    @Slot(str)
    def setInstanceName(self, name: str):
        self._backend.lineEdit_7.setText(name)

    @Slot(str)
    def setLabymodInstanceName(self, name: str):
        self._backend.lineEdit_14.setText(name)

    @Slot(str)
    def setModloader(self, name: str):
        idx = self._backend.comboBox.findText(name)
        if idx >= 0:
            self._backend.comboBox.setCurrentIndex(idx)

    @Slot()
    def launch(self):
        if self._selected_instance:
            self._backend.launch_version = self._selected_instance
        self._backend.launch()

    @Slot()
    def download(self):
        idx = -1
        versions = self.getVersionList()
        # QML ListView 选中通过 setCurrentIndex 同步到 listView
        sel = self._backend.listView.selectionModel().selectedIndexes()
        if sel:
            self._backend.download()
        elif versions:
            from PySide6.QtCore import QItemSelection, QItemSelectionModel

            self._backend.listView.model().index(0, 0)
            ix = self._backend.listView.model().index(0, 0)
            s = QItemSelection(ix, ix)
            self._backend.listView.selectionModel().select(
                s, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )
            self._backend.download()

    @Slot(int)
    def selectDownloadVersion(self, row: int):
        from PySide6.QtCore import QItemSelection, QItemSelectionModel

        m = self._backend.listView.model()
        if m and 0 <= row < m.rowCount():
            ix = m.index(row, 0)
            s = QItemSelection(ix, ix)
            self._backend.listView.selectionModel().select(
                s, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )

    @Slot(int)
    def selectLabymodVersion(self, row: int):
        from PySide6.QtCore import QItemSelection, QItemSelectionModel

        m = self._backend.listView_5.model()
        if m and 0 <= row < m.rowCount():
            ix = m.index(row, 0)
            s = QItemSelection(ix, ix)
            self._backend.listView_5.selectionModel().select(
                s, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )

    @Slot()
    def downloadLabymod(self):
        self._backend.download_labymod()

    @Slot()
    def saveSettings(self):
        self._backend.save_config()

    @Slot()
    def scanJava(self):
        self._backend.scan_system_javas()

    @Slot()
    def downloadJava(self):
        self._backend.prompt_download_java()

    @Slot(result=str)
    def browseMinecraftDir(self) -> str:
        path = self._backend.open_folder()
        if path:
            self._backend.lineEdit.setText(path)
            return path
        return self._backend.lineEdit.text()

    @Slot()
    def oauthLogin(self):
        try:
            self._backend.oauth()
            self._backend.save_accounts()
            self.accountsChanged.emit()
            self.toast.emit("Microsoft 登录成功", "ok")
        except Exception as exc:
            self.toast.emit(str(exc), "error")

    @Slot()
    def refreshVersions(self):
        self._backend.update_version_list()
        self.versionsChanged.emit()

    @Slot()
    def refreshInstances(self):
        self._backend.update_installed_versions()
        self.instancesChanged.emit()

    def _sync_manager_instance(self, name: str) -> None:
        idx = self._backend.comboBox_5.findText(name)
        if idx >= 0:
            self._backend.comboBox_5.setCurrentIndex(idx)

    @Slot(str, result=str)
    def getManagerDetail(self, instance: str) -> str:
        try:
            mc = self._backend.get_minecraft_dir()
            if not instance or not mc:
                raise ValueError("no instance")
            from spectrum_core import manager

            return json.dumps(
                {
                    "saves": list(manager.get_saves(mc, instance)),
                    "mods": list(manager.get_mods(mc, instance)),
                    "resourcepacks": list(manager.get_resourcepacks(mc, instance)),
                    "shaderpacks": list(manager.get_shaderpacks(mc, instance)),
                },
                ensure_ascii=False,
            )
        except Exception:
            return json.dumps(
                {"saves": [], "mods": [], "resourcepacks": [], "shaderpacks": []},
                ensure_ascii=False,
            )

    @Slot(str, str)
    def renameInstance(self, old_name: str, new_name: str):
        if not new_name.strip():
            self.toast.emit("请输入新名称", "warn")
            return
        self._sync_manager_instance(old_name)
        self._backend.lineEdit_5.setText(new_name.strip())
        self._backend.rename_version()
        self.refreshInstances()
        self.managerDataChanged.emit()
        self.toast.emit(f"已重命名为 {new_name.strip()}", "ok")

    @Slot(str)
    def deleteInstance(self, name: str):
        self._sync_manager_instance(name)
        self._backend.remove_version()
        self.refreshInstances()
        self.managerDataChanged.emit()
        self.toast.emit(f"已删除实例 {name}", "ok")

    @Slot(str)
    def openInstanceFolder(self, name: str):
        self._sync_manager_instance(name)
        self._backend.open_version_folder()

    @Slot(str, str, str)
    def deleteManagerItem(self, kind: str, instance: str, item: str):
        try:
            mc = self._backend.get_minecraft_dir()
            from spectrum_core import manager

            if kind == "save":
                manager.remove_save(mc, instance, item)
            elif kind == "mod":
                manager.remove_mod(mc, instance, item)
            elif kind == "respack":
                manager.remove_resourcepack(mc, instance, item)
            elif kind == "shader":
                manager.remove_shaderpack(mc, instance, item)
            self.managerDataChanged.emit()
            self.toast.emit(f"已删除 {item}", "ok")
        except Exception as exc:
            self.toast.emit(str(exc), "error")

    @Slot(str)
    def addOfflineAccount(self, name: str):
        name = name.strip()
        if not name:
            self.toast.emit("请输入玩家名", "warn")
            return
        self._backend.lineEdit_2.setText(name)
        self._backend.comboBox_9.setCurrentIndex(0)
        self._backend.add_account(microsoft=False)
        self._backend.save_accounts()
        self.accountsChanged.emit()
        self.toast.emit(f"已添加离线账户 {name}", "ok")

    @Slot(int)
    def removeAccount(self, index: int):
        from PySide6.QtCore import QItemSelection, QItemSelectionModel

        m = self._backend.listView_4.model()
        if not m or not (0 <= index < m.rowCount()):
            return
        ix = m.index(index, 0)
        sel = QItemSelection(ix, ix)
        self._backend.listView_4.selectionModel().select(
            sel, QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        self._backend.remove_account()
        self._backend.save_accounts()
        self.accountsChanged.emit()
        self.toast.emit("账户已删除", "ok")

    @Slot(result=str)
    def getMemory(self) -> str:
        return self._backend.comboBox_4.currentText()

    @Slot(str)
    def setMemory(self, mem: str):
        idx = self._backend.comboBox_4.findText(mem)
        if idx >= 0:
            self._backend.comboBox_4.setCurrentIndex(idx)
        else:
            self._backend.comboBox_4.setCurrentText(mem)

    @Slot(result=str)
    def getJvmArgs(self) -> str:
        return self._backend.lineEdit_11.text()

    @Slot(str)
    def setJvmArgs(self, args: str):
        self._backend.lineEdit_11.setText(args)

    @Slot(result=list)
    def getJavaRuntimes(self) -> list:
        self._backend.refresh_java_combo()
        items = []
        for i in range(self._backend.comboBox_7.count()):
            items.append(
                {
                    "label": self._backend.comboBox_7.itemText(i),
                    "path": self._backend.comboBox_7.itemData(i) or "",
                }
            )
        return items

    @Slot(str)
    def selectJava(self, path: str):
        idx = self._backend.comboBox_7.findData(path)
        if idx >= 0:
            self._backend.comboBox_7.setCurrentIndex(idx)

    @Slot(bool, bool, bool, bool)
    def setVersionFilters(self, bmclapi, snapshot, old_alpha, old_beta):
        self._backend.checkBox.setChecked(bmclapi)
        self._backend.checkBox_4.setChecked(snapshot)
        self._backend.checkBox_3.setChecked(old_alpha)
        self._backend.checkBox_2.setChecked(old_beta)
        self._backend.update_version_list()
        self.versionsChanged.emit()

    @Slot(result=str)
    def modrinthWebUrl(self) -> str:
        from pathlib import Path

        web = Path(__file__).resolve().parent.parent / "web" / "index.html"
        return QUrl.fromLocalFile(str(web)).toString()

    @Slot(result=str)
    def getLaunchStatus(self) -> str:
        inst = self._selected_instance
        mod_count = 0
        try:
            mc = self._backend.get_minecraft_dir()
            if inst and mc:
                from spectrum_core import manager

                mod_count = len(list(manager.get_mods(mc, inst)))
        except Exception:
            pass
        return json.dumps(
            {
                "instance": inst or "未选择",
                "memory": self._backend.comboBox_4.currentText(),
                "javaCount": len(self._backend.javas),
                "modCount": mod_count,
            },
            ensure_ascii=False,
        )

    def _on_download_progress(self, current, total, description):
        if total <= 0:
            return
        pct = int(current / total * 100)
        self.downloadProgress.emit(pct, total, description)
        if description:
            self.consoleLog.emit(str(description))

    def _on_download_finished(self, result, instance_name, minecraft_dir):
        ok = not (isinstance(result, dict) and result.get("status") == "error")
        self.downloadFinished.emit(ok, instance_name or "")
        self.instancesChanged.emit()


class WebBridge(QObject):
    """QWebChannel — Vue Modrinth 面板。"""

    def __init__(self, backend: "MainWindow", parent=None):
        super().__init__(parent)
        self._backend = backend

    def _target_mc_version(self) -> str | None:
        try:
            mc_dir = self._backend.get_minecraft_dir().replace("\\", "/").rstrip("/")
            instance = self._backend.comboBox_6.currentText()
            if not mc_dir or not instance:
                return None
            import spectrum_core.launcher_funcs as launcher

            return launcher.get_minecraft_version(mc_dir, instance)
        except Exception:
            return None

    @Slot(str, str, result=str)
    def searchModrinth(self, query: str, loader: str) -> str:
        from spectrum_core import modrinth_api

        try:
            hits = modrinth_api.search(
                query,
                loader=loader,
                game_version=self._target_mc_version(),
            )
            self._backend.mods = [h.get("project_id", h.get("slug", "")) for h in hits]
            return json.dumps(
                [
                    {
                        "index": i,
                        "id": h.get("project_id", ""),
                        "slug": h.get("slug", ""),
                        "title": h.get("title", ""),
                        "description": h.get("description", ""),
                        "icon_url": h.get("icon_url", ""),
                        "downloads": h.get("downloads", 0),
                    }
                    for i, h in enumerate(hits)
                ],
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    @Slot(int, result=bool)
    def installMod(self, index: int) -> bool:
        try:
            mods = getattr(self._backend, "mods", [])
            if not (0 <= index < len(mods)):
                return False

            project_id = mods[index]
            loader = self._backend.comboBox_3.currentText()
            game_version = self._target_mc_version()
            if not game_version:
                return False

            mc_dir = self._backend.get_minecraft_dir().replace("\\", "/").rstrip("/")
            instance = self._backend.comboBox_6.currentText()
            mods_dir = f"{mc_dir}/versions/{instance}/mods"

            from spectrum_core import modrinth_api

            modrinth_api.install_mod(
                project_id,
                loader=loader,
                game_version=game_version,
                mods_dir=mods_dir,
            )
            return True
        except Exception:
            return False

    @Slot(result=list)
    def getInstances(self) -> list:
        try:
            from spectrum_core import manager

            return manager.list_instances(self._backend.get_minecraft_dir())
        except Exception:
            return []

    @Slot(str)
    def setTargetInstance(self, name: str):
        idx = self._backend.comboBox_6.findText(name)
        if idx >= 0:
            self._backend.comboBox_6.setCurrentIndex(idx)
