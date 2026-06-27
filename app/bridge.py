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
    javaRuntimesChanged = Signal()

    def __init__(self, backend: "MainWindow", parent=None):
        super().__init__(parent)
        self._backend = backend
        self._current_page = 0
        self._nav_to_backend = {0: 0, 1: 3, 2: 7, 3: 5}
        self._selected_instance = ""
        self._selected_download_version = ""
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
            m = self._backend.listView.model()
            if m and m.rowCount() > 0:
                return list(m.stringList())
            self._backend.update_version_list()
            m = self._backend.listView.model()
            return list(m.stringList()) if m else []
        except Exception:
            return []

    @Slot()
    def refreshVersionList(self):
        saved = self._selected_download_version
        self._backend.update_version_list()
        if saved:
            self._restore_download_selection(saved)
        self.versionsChanged.emit()

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
        self._backend.update_installed_versions()
        self.instancesChanged.emit()

    @Slot(result=str)
    def getMinecraftDir(self) -> str:
        return self._backend.get_minecraft_dir()

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
        if self._selected_download_version:
            self._backend.update_ml_version_list(None)

    @Slot(result=str)
    def getSelectedDownloadVersion(self) -> str:
        return self._selected_download_version or ""

    @Slot()
    def launch(self):
        if self._selected_instance:
            self._backend.launch_version = self._selected_instance
        err = self._backend.launch()
        if err == 1:
            pass  # 已在 MainWindow 内弹窗

    @Slot(bool)
    def setIgnoreJavaWarnings(self, ignore: bool):
        self._backend.ignore_java_warnings = bool(ignore)
        self._backend.save_config()

    @Slot(result=bool)
    def getIgnoreJavaWarnings(self) -> bool:
        return bool(self._backend.ignore_java_warnings)

    @Slot(str)
    def selectLaunchJava(self, path: str):
        self._backend._launch_java_path = path or None
        idx = self._backend.comboBox_7.findData(path)
        if idx >= 0:
            self._backend.comboBox_7.setCurrentIndex(idx)

    @Slot(str, result=str)
    def getJavaOptionsForInstance(self, instance: str) -> str:
        try:
            import spectrum_core.java_policy as java_policy

            mc = self._backend.get_minecraft_dir()
            if not instance or not mc:
                return json.dumps([])
            ctx = java_policy.build_instance_context(mc, instance)
            runtimes = self._backend.collect_java_runtimes()
            return json.dumps(
                java_policy.java_options_payload(ctx, runtimes),
                ensure_ascii=False,
            )
        except Exception:
            return json.dumps([], ensure_ascii=False)

    @Slot(str, result=str)
    def addJavaPath(self, path: str) -> str:
        path = path.strip()
        if not path:
            self.toast.emit("路径为空", "warn")
            return json.dumps({"ok": False, "error": "路径为空"}, ensure_ascii=False)
        ok, msg = self._backend.register_java_path(path)
        if ok:
            self.javaRuntimesChanged.emit()
            self.toast.emit(msg, "ok")
        else:
            self.toast.emit(msg, "error")
        return json.dumps({"ok": ok, "message": msg}, ensure_ascii=False)

    @Slot(result=str)
    def browseJavaExecutable(self) -> str:
        return self._backend.browse_java_executable()

    @Slot("QVariantList", result=str)
    def addJavaFromDropUrls(self, urls) -> str:
        from PySide6.QtCore import QUrl

        added = 0
        last_msg = ""
        last_ok = False
        for raw in urls or []:
            path = QUrl(str(raw)).toLocalFile()
            if not path:
                continue
            ok, msg = self._backend.register_java_path(path)
            last_msg = msg
            last_ok = ok
            if ok:
                added += 1
        if added:
            self.javaRuntimesChanged.emit()
            self.toast.emit(last_msg, "ok")
        elif last_msg:
            self.toast.emit(last_msg, "error" if not last_ok else "warn")
        return json.dumps({"added": added, "message": last_msg}, ensure_ascii=False)

    @Slot(str)
    def removeJava(self, path: str):
        if self._backend.remove_java_path(path):
            self.javaRuntimesChanged.emit()
            self.toast.emit("已移除 Java", "ok")
        else:
            self.toast.emit("未找到该 Java 路径", "warn")

    @Slot()
    def download(self):
        mcversion = self._selected_download_version
        if not mcversion:
            sel = self._backend.listView.selectionModel().selectedIndexes()
            if sel:
                mcversion = sel[0].data() or ""
        if not mcversion:
            self.toast.emit("请先在版本列表中选择要下载的版本", "warn")
            return
        self._backend.download(mcversion=mcversion)

    def _restore_download_selection(self, version: str) -> None:
        m = self._backend.listView.model()
        if not m:
            return
        for i, ver in enumerate(m.stringList()):
            if ver == version:
                self.selectDownloadVersion(i)
                return
        self._selected_download_version = ""

    @Slot(int)
    def selectDownloadVersion(self, row: int):
        from PySide6.QtCore import QItemSelection, QItemSelectionModel

        m = self._backend.listView.model()
        if m and 0 <= row < m.rowCount():
            ver = m.stringList()[row]
            self._selected_download_version = ver
            ix = m.index(row, 0)
            s = QItemSelection(ix, ix)
            self._backend.listView.selectionModel().select(
                s, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )
            self._backend.update_ml_version_list(None)

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
        self.javaRuntimesChanged.emit()
        self.toast.emit("Java 扫描完成", "ok")

    @Slot()
    def downloadJava(self):
        self._backend.prompt_download_java()

    @Slot(result=str)
    def browseMinecraftDir(self) -> str:
        path = self._backend.open_folder()
        if path:
            self._backend.lineEdit.setText(path)
            self._backend.update_installed_versions()
            self.instancesChanged.emit()
            return path
        return self._backend.get_minecraft_dir()

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
        saved = self._selected_download_version
        self._backend.update_version_list()
        if saved:
            self._restore_download_selection(saved)
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
        saved = self._selected_download_version
        self._backend.update_version_list()
        if saved:
            self._restore_download_selection(saved)
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
        min_java = 8
        mc_version = ""
        java8_only = False
        try:
            mc = self._backend.get_minecraft_dir()
            if inst and mc:
                from spectrum_core import manager
                import spectrum_core.java_policy as java_policy

                mod_count = len(list(manager.get_mods(mc, inst)))
                ctx = java_policy.build_instance_context(mc, inst)
                mc_version = ctx.mc_version
                min_java = 8 if ctx.java8_only else java_policy.get_min_java(mc_version)
                java8_only = ctx.java8_only
        except Exception:
            pass
        return json.dumps(
            {
                "instance": inst or "未选择",
                "memory": self._backend.comboBox_4.currentText(),
                "javaCount": len(self._backend.javas),
                "modCount": mod_count,
                "mcVersion": mc_version,
                "minJava": min_java,
                "java8Only": java8_only,
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
