
import logging
import os
import shutil
from threading import Lock
import unittest

import app_constants
from model.local_model.models import ModuleError, ServerModuleVersion
from model.local_model.module_version_manager import ServerModuleVersionManager
from utils import path_builder
from utils.model_managing.subject_session import SubjectSession

TEST_MODULE_PATH = "tests/rt/"
ASSETS_PATH = "tests/assets/"


def _initialize(modules_dir_template: str = None):
    logging.getLogger().disabled = True

    if os.path.exists(TEST_MODULE_PATH):
        shutil.rmtree(TEST_MODULE_PATH)

    if modules_dir_template is not None:
        shutil.copytree(ASSETS_PATH + modules_dir_template,
                        TEST_MODULE_PATH)

    path_builder.initialize('')
    path_builder.add_domain(app_constants.MODULE_DOMAIN, TEST_MODULE_PATH)


class ServerModuleVersionManagerTest(unittest.TestCase):

    def test_load_from_dir(self):
        _initialize("create_version_from_dir")

        versions = set()
        s = SubjectSession(versions, Lock())

        created_sessions = set()

        # assert invalid domain path raises FileNotFoundError
        path_builder._paths[app_constants.MODULE_DOMAIN] = "wrong_path"
        self.assertRaises(FileNotFoundError,
                          lambda: ServerModuleVersionManager.load_from_dir(
                              s, "test_module", "0.2.4"))
        path_builder._paths[app_constants.MODULE_DOMAIN] = TEST_MODULE_PATH

        # assert invalid module path raises FileNotFoundError
        self.assertRaises(FileNotFoundError,
                          lambda: ServerModuleVersionManager.load_from_dir(
                              s, "invalid_module", "0.2.4"))

        # assert invalid version path raises FileNotFoundError
        self.assertRaises(FileNotFoundError,
                          lambda: ServerModuleVersionManager.load_from_dir(
                              s, "test_module", "1.0.0"))

        # assert missing config file succeeds with error value
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "0.2.4")
        self.assertIsNotNone(version.error)
        self.assertEqual(version.error.code, ModuleError.Type.PATH_NOT_FOUND)
        self.assertEqual(version.version, "0.2.4")
        created_sessions.add(version)

        # assert invalid json in config file succeeds with error value
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "1.2.3")

        self.assertIsNotNone(version.error)
        self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
        self.assertEqual(version.error.name, "ConfigParseError")
        self.assertEqual(version.version, "1.2.3")
        created_sessions.add(version)

        # assert config file with missing mandatory fields succeeds with error
        # value
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "1.2.4")

        self.assertIsNotNone(version.error)
        self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
        self.assertEqual(version.error.name, "MissingConfigKeyError")
        self.assertEqual(version.version, "1.2.4")
        created_sessions.add(version)

        # assert config file with unmatching config version succeeds with
        # error value
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "1.2.5")

        self.assertIsNotNone(version.error)
        self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
        self.assertEqual(version.error.name, "ConfigVersionMismatch")
        created_sessions.add(version)

        # assert valid config file succeeds without error value and default
        # values
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "2.1.4")
        self.assertIsNone(version.error)
        self.assertEqual(version.version, "2.1.4")
        self.assertEqual(version.api_version, "1.0.0")
        self.assertEqual(version.src_dir, "src")
        self.assertEqual(version.working_dir, "rt")
        created_sessions.add(version)

        # assert complete config file loads all values correctly
        version = ServerModuleVersionManager.load_from_dir(
            s, "test_module", "2.2.1")
        self.assertIsNone(version.error)
        self.assertEqual(version.version, "2.2.1")
        self.assertEqual(version.api_version, "1.0.1")
        self.assertEqual(version.src_dir, "src_dir")
        self.assertEqual(version.working_dir, "working_dir")
        self.assertEqual(version.base_path,
                         os.path.join(
                             TEST_MODULE_PATH, "test_module", version.version))

        self.assertFalse(version.running)
        self.assertFalse(version.initialized)
        self.assertFalse(version.last_validation_succeeded)
        self.assertIsNone(version.last_src_hash)
        created_sessions.add(version)

        # assert all versions are stored in session
        self.assertEqual(versions, created_sessions)

    def test_get_versions_by_ids(self):
        _initialize()

        versions = set()
        s = SubjectSession(versions, Lock())
        v1 = ServerModuleVersion(version="0.1.0", base_path="path1")
        v2 = ServerModuleVersion(version="1.1.0", base_path="path2")
        v3 = ServerModuleVersion(version="0.1.1", base_path="path3")
        s.add(v1)
        s.add(v2)
        s.add(v3)

        ids = {v.id for v in versions}

        # assert unique ids are assigned
        self.assertEqual(len(ids), 3)

        # assert empty id list returns empty set
        self.assertListEqual(
            ServerModuleVersionManager.get_versions_by_ids(s, []), [])

        # assert single id returns single version
        self.assertListEqual(
            ServerModuleVersionManager.get_versions_by_ids(s, [v1.id]),
            [v1])

        # assert multiple ids return all versions
        self.assertListEqual(
            ServerModuleVersionManager.get_versions_by_ids(s, [v1.id, v2.id]),
            [v1, v2])

        # assert non-exising id raises
        self.assertRaises(
            IndexError,
            lambda: ServerModuleVersionManager.get_versions_by_ids(
                s, [v1.id, 123]))

        # assert order is preserved
        self.assertListEqual(
            ServerModuleVersionManager.get_versions_by_ids(
                s, [v3.id, v1.id, v2.id]),
            [v3, v1, v2])

    def test_initialize(self):
        _initialize("initialize")

        versions = set()
        s = SubjectSession(versions, Lock())
        v1 = ServerModuleVersionManager.load_from_dir(s, "module1", "1.0.0")
        v2 = ServerModuleVersionManager.load_from_dir(s, "module1", "1.0.1")

        # --- v1 - src missing ---
        version_base_path \
            = os.path.join(TEST_MODULE_PATH, "module1", "1.0.0")

        # assert version is not initialized
        vm = ServerModuleVersionManager(s, v1.id)
        self.assertFalse(vm.has_error())
        self.assertFalse(vm.is_initialized())
        self.assertEqual(vm.get_working_path(),
                         os.path.join(version_base_path, "rt"))
        self.assertFalse(os.path.exists(vm.get_working_path()))

        # assert initialization succeeds
        self.assertIsNone(vm.model().last_src_hash)
        self.assertTrue(vm.initialize_and_validate())
        self.assertTrue(vm.is_initialized())
        self.assertTrue(os.path.exists(vm.get_working_path()))

        # assert validation failed (src dir missing)
        self.assertFalse(os.path.exists(vm.get_src_path()))
        self.assertFalse(vm.is_src_validated())
        self.assertIsNotNone(vm.model().last_src_hash)

        # --- v2 - src present ---
        version_base_path \
            = os.path.join(TEST_MODULE_PATH, "module1", "1.0.1")

        # assert version is not initialized
        vm = ServerModuleVersionManager(s, v2.id)
        self.assertFalse(vm.has_error())
        self.assertFalse(vm.is_initialized())
        self.assertEqual(vm.get_working_path(),
                         os.path.join(version_base_path, "runtime"))
        self.assertFalse(os.path.exists(vm.get_working_path()))

        # assert initialization succeeds
        self.assertIsNone(vm.model().last_src_hash)
        self.assertTrue(vm.initialize_and_validate())
        self.assertTrue(vm.is_initialized())
        self.assertTrue(os.path.exists(vm.get_working_path()))

        # assert succeeded failed
        self.assertTrue(os.path.exists(vm.get_src_path()))
        self.assertTrue(vm.is_src_validated())
        self.assertIsNotNone(vm.model().last_src_hash)


class ServerModuleManagerTest(unittest.TestCase):
    pass
