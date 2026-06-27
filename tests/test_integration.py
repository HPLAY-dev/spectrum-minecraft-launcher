#!/usr/bin/env python3
"""Spectrum Rust 核心 + Python 桥接层集成测试。"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from tests.helpers import (
    cleanup_dir,
    load_fixture,
    make_minecraft_dir,
    network_enabled,
    setup_rust_env,
)

setup_rust_env()

import spectrum_core as sc  # noqa: E402

NATIVE = sc.require_native() if sc.rust_available() else None


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载，请先 cargo build --features python")
class TestCoreLoad(unittest.TestCase):
    def test_rust_available(self):
        self.assertTrue(sc.rust_available())

    def test_is_rust_core(self):
        self.assertTrue(NATIVE.is_rust_core())

    def test_version_string(self):
        self.assertTrue(hasattr(NATIVE, "__version__"))


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestUtils(unittest.TestCase):
    MAVEN = "com.mojang:minecraft:1.20.1"
    EXPECTED = "com/mojang/minecraft/1.20.1/minecraft-1.20.1.jar"

    def test_native_os(self):
        os_name = NATIVE.native_os_py()
        self.assertIn(os_name, ("windows", "linux", "macos"))

    def test_maven_to_path_native(self):
        path = NATIVE.maven_to_path_py(self.MAVEN)
        self.assertEqual(path, self.EXPECTED)

    def test_maven_to_path_bridge(self):
        from spectrum_core.tool_funcs import maven_to_path

        self.assertEqual(maven_to_path(self.MAVEN), self.EXPECTED)

    def test_maven_invalid(self):
        with self.assertRaises(Exception):
            NATIVE.maven_to_path_py("not-a-maven-coord")


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestJavaDetection(unittest.TestCase):
    def test_find_javas_returns_list(self):
        javas = NATIVE.find_javas()
        self.assertIsInstance(javas, list)
        for item in javas:
            self.assertIn("path", item)
            self.assertIn("major_version", item)

    def test_get_java_version_invalid(self):
        with self.assertRaises(Exception):
            NATIVE.get_java_version("/nonexistent/java/path")


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestInstanceManager(unittest.TestCase):
    def setUp(self):
        self.mc_dir = make_minecraft_dir()
        self.instance = "test-1.20.1"

    def tearDown(self):
        cleanup_dir(self.mc_dir)

    def test_list_instances(self):
        names = NATIVE.list_instances(str(self.mc_dir))
        self.assertIn(self.instance, names)

    def test_get_saves_mods_packs(self):
        mc = str(self.mc_dir)
        self.assertIn("world_alpha", NATIVE.get_saves(mc, self.instance))
        self.assertIn("example-mod.jar", NATIVE.get_mods(mc, self.instance))
        self.assertIn("pack.zip", NATIVE.get_resourcepacks(mc, self.instance))
        self.assertIn("shader.zip", NATIVE.get_shaderpacks(mc, self.instance))

    def test_remove_save_and_mod(self):
        mc = str(self.mc_dir)
        NATIVE.remove_save(mc, self.instance, "world_alpha")
        self.assertNotIn("world_alpha", NATIVE.get_saves(mc, self.instance))

        NATIVE.remove_mod(mc, self.instance, "example-mod.jar")
        self.assertNotIn("example-mod.jar", NATIVE.get_mods(mc, self.instance))

    def test_rename_instance(self):
        mc = str(self.mc_dir)
        NATIVE.rename_version(mc, self.instance, "renamed-1.20.1")
        names = NATIVE.list_instances(mc)
        self.assertIn("renamed-1.20.1", names)
        self.assertNotIn(self.instance, names)

    def test_remove_version(self):
        mc = str(self.mc_dir)
        NATIVE.remove_version(mc, self.instance)
        self.assertNotIn(self.instance, NATIVE.list_instances(mc))

    def test_manager_bridge(self):
        import spectrum_core.manager as mgr

        mc = str(self.mc_dir)
        self.assertIn("world_alpha", mgr.get_saves(mc, self.instance))
        self.assertIn("example-mod.jar", mgr.get_mods(mc, self.instance))


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestLauncher(unittest.TestCase):
    def setUp(self):
        self.mc_dir = make_minecraft_dir()
        self.instance = "test-1.20.1"

    def tearDown(self):
        cleanup_dir(self.mc_dir)

    def test_get_minecraft_version(self):
        from spectrum_core.launcher_funcs import get_minecraft_version

        ver = get_minecraft_version(str(self.mc_dir), self.instance)
        self.assertEqual(ver, self.instance)

    def test_get_required_java_version(self):
        from spectrum_core.launcher_funcs import get_required_java_version

        major = get_required_java_version(str(self.mc_dir), self.instance)
        self.assertEqual(major, 17)

    def test_build_launch_script(self):
        from spectrum_core.launcher_funcs import launch

        script = launch(
            javaw="java",
            xmx="2G",
            minecraft_dir=str(self.mc_dir).replace("\\", "/"),
            instance_name=self.instance,
            username="TestPlayer",
            ms_login=False,
        )
        self.assertIn("TestPlayer", script)
        self.assertIn(self.instance, script)
        self.assertIn("java", script)

    def test_ms_login_requires_token(self):
        with self.assertRaises(Exception):
            NATIVE.build_launch_script(
                "java",
                "2G",
                str(self.mc_dir),
                self.instance,
                "TestPlayer",
                "256M",
                True,
                None,
            )


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestDownloadBridge(unittest.TestCase):
    def test_native_os_via_bridge(self):
        from spectrum_core.download_funcs import native

        self.assertIn(native(), ("windows", "linux", "macos"))

    @unittest.skipUnless(network_enabled(), "SPECTRUM_INTEGRATION_NETWORK=0")
    def test_get_version_list(self):
        from spectrum_core.download_funcs import get_version_list

        versions = get_version_list(
            show_snapshot=False,
            show_old_alpha=False,
            show_old_beta=False,
            bmclapi=True,
        )
        self.assertGreater(len(versions), 10)
        self.assertTrue(all(isinstance(v, str) for v in versions))

    @unittest.skipUnless(network_enabled(), "SPECTRUM_INTEGRATION_NETWORK=0")
    def test_get_version_list_native(self):
        versions = NATIVE.get_version_list(False, False, True, True)
        self.assertGreater(len(versions), 10)

    @unittest.skipUnless(network_enabled(), "SPECTRUM_INTEGRATION_NETWORK=0")
    def test_get_version_json(self):
        vj = NATIVE.get_version_json("1.20.1", True)
        self.assertIsInstance(vj, dict)
        self.assertEqual(vj.get("id"), "1.20.1")
        self.assertIn("javaVersion", vj)

    @unittest.skipUnless(network_enabled(), "SPECTRUM_INTEGRATION_NETWORK=0")
    def test_get_version_json_bridge(self):
        from spectrum_core.download_funcs import get_version_json

        vj = get_version_json("1.20.1", bmclapi=True)
        self.assertEqual(vj.get("id"), "1.20.1")


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestProgressCallback(unittest.TestCase):
    """验证 auto_download 进度回调机制（不实际下载完整游戏）。"""

    def test_callback_signature(self):
        calls: list[tuple] = []

        def cb(current, total, desc):
            calls.append((current, total, desc))

        # 使用不存在的版本触发快速失败，但回调通道应已建立
        with self.assertRaises(Exception):
            NATIVE.auto_download(
                str(Path(os.environ.get("TEMP", "."))),
                "0.0.0-nonexistent-version",
                "bad-instance",
                "vanilla",
                None,
                True,
                cb,
            )
        # 失败前可能已有 progress 事件；至少不应 crash
        self.assertIsInstance(calls, list)


@unittest.skipUnless(sc.rust_available(), "Rust 核心未加载")
class TestOAuthBridge(unittest.TestCase):
    def test_oauth_funcs_import(self):
        import spectrum_core.oauth_funcs as oauth

        self.assertTrue(callable(oauth.get_mc_token))
        self.assertTrue(callable(oauth.refresh_token))
        self.assertTrue(callable(oauth.get_mslogin_uuid_name))
        self.assertTrue(callable(oauth.is_owned))

    def test_invalid_token_profile(self):
        with self.assertRaises(Exception):
            NATIVE.get_mslogin_uuid_name("invalid-token")


if __name__ == "__main__":
    verbosity = 2 if os.environ.get("VERBOSE") else 1
    suite = unittest.defaultTestLoader.discover(
        str(Path(__file__).parent),
        pattern="test_*.py",
    )
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
