
# import logging
# import os
# import shutil
# from threading import Lock
# import unittest

# import app_config

# import app_constants
# from model.exeptions import StateError
# from model.local_model.server_module_manager import ServerModuleManager
# from services.server_modules.server_module_service import ServerModuleService
# from jodisutils.files import path_builder
# from jodisutils.model_managing.subject_session import SubjectSession

# TEST_MODULE_PATH = "tests/rt/"
# ASSETS_PATH = "tests/assets/"


# def _copy_modules_dir(modules_dir_template: str):
#     if os.path.exists(TEST_MODULE_PATH):
#         shutil.rmtree(TEST_MODULE_PATH)

#     if modules_dir_template is not None:
#         shutil.copytree(ASSETS_PATH + modules_dir_template,
#                         TEST_MODULE_PATH)


# def _initialize(modules_dir_template: str = None):
#     logging.getLogger().disabled = True

#     _copy_modules_dir(modules_dir_template)

#     app_config.initialize({
#         'modules': {
#             'path': TEST_MODULE_PATH
#         }
#     }, False)

#     path_builder.initialize('')
#     path_builder.add_domain(app_constants.MODULE_DOMAIN, TEST_MODULE_PATH)


# class ServerModuleVersionManagerTest(unittest.TestCase):

#     def test_load_from_dir(self):
#         _initialize("create_version_from_dir")

#         versions = set()
#         s = SubjectSession(versions, Lock())

#         created_sessions = set()

#         module_path = os.path.join(TEST_MODULE_PATH, "test_module")

#         # assert invalid module path raises FileNotFoundError
#         self.assertRaises(FileNotFoundError,
#                           lambda: ServerModuleVersionManager.load_from_dir(
#                               s, "invalid_module", "0.2.4"))

#         # assert invalid version path raises FileNotFoundError
#         self.assertRaises(FileNotFoundError,
#                           lambda: ServerModuleVersionManager.load_from_dir(
#                               s, module_path, "1.0.0"))

#         # assert missing config file succeeds with error value
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "0.2.4")
#         self.assertIsNotNone(version.error)
#         self.assertEqual(version.error.code, ModuleError.Type.PATH_NOT_FOUND)
#         self.assertEqual(version.version, "0.2.4")
#         created_sessions.add(version)

#         # assert invalid json in config file succeeds with error value
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "1.2.3")

#         self.assertIsNotNone(version.error)
#         self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
#         self.assertEqual(version.error.name, "ConfigParseError")
#         self.assertEqual(version.version, "1.2.3")
#         created_sessions.add(version)

#         # assert config file with missing mandatory fields succeeds with error
#         # value
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "1.2.4")

#         self.assertIsNotNone(version.error)
#         self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
#         self.assertEqual(version.error.name, "MissingConfigKeyError")
#         self.assertEqual(version.version, "1.2.4")
#         created_sessions.add(version)

#         # assert config file with unmatching config version succeeds with
#         # error value
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "1.2.5")

#         self.assertIsNotNone(version.error)
#         self.assertEqual(version.error.code, ModuleError.Type.CFG_INVALID)
#         self.assertEqual(version.error.name, "ConfigVersionMismatch")
#         created_sessions.add(version)

#         # assert valid config file succeeds without error value and default
#         # values
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "2.1.4")
#         self.assertIsNone(version.error)
#         self.assertEqual(version.version, "2.1.4")
#         self.assertEqual(version.api_version, "1.0.0")
#         self.assertEqual(version.src_dir, "src")
#         self.assertEqual(version.working_dir, "rt")
#         created_sessions.add(version)

#         # assert complete config file loads all values correctly
#         version = ServerModuleVersionManager.load_from_dir(
#             s, module_path, "2.2.1")
#         self.assertIsNone(version.error)
#         self.assertEqual(version.version, "2.2.1")
#         self.assertEqual(version.api_version, "1.0.1")
#         self.assertEqual(version.src_dir, "src_dir")
#         self.assertEqual(version.working_dir, "working_dir")
#         self.assertEqual(version.base_path,
#                          os.path.join(module_path, version.version))

#         self.assertFalse(version.running)
#         self.assertFalse(version.initialized)
#         self.assertFalse(version.last_validation_succeeded)
#         self.assertIsNone(version.last_src_hash)
#         created_sessions.add(version)

#         # assert all versions are stored in session
#         self.assertEqual(versions, created_sessions)

#     def test_get_versions_by_ids(self):
#         _initialize()

#         versions = set()
#         s = SubjectSession(versions, Lock())
#         v1 = ServerModuleVersion(version="0.1.0", base_path="path1")
#         v2 = ServerModuleVersion(version="1.1.0", base_path="path2")
#         v3 = ServerModuleVersion(version="0.1.1", base_path="path3")
#         s.add(v1)
#         s.add(v2)
#         s.add(v3)

#         ids = {v.id for v in versions}

#         # assert unique ids are assigned
#         self.assertEqual(len(ids), 3)

#         # assert empty id list returns empty set
#         self.assertListEqual(
#             ServerModuleVersionManager.get_versions_by_ids(s, []), [])

#         # assert single id returns single version
#         self.assertListEqual(
#             ServerModuleVersionManager.get_versions_by_ids(s, [v1.id]),
#             [v1])

#         # assert multiple ids return all versions
#         self.assertListEqual(
#             ServerModuleVersionManager.get_versions_by_ids(s, [v1.id, v2.id]),
#             [v1, v2])

#         # assert non-exising id raises
#         self.assertRaises(
#             IndexError,
#             lambda: ServerModuleVersionManager.get_versions_by_ids(
#                 s, [v1.id, 123]))

#         # assert order is preserved
#         self.assertListEqual(
#             ServerModuleVersionManager.get_versions_by_ids(
#                 s, [v3.id, v1.id, v2.id]),
#             [v3, v1, v2])

#     def test_initialize(self):
#         _initialize("initialize")

#         module_path = os.path.join(TEST_MODULE_PATH, "module1")

#         versions = set()
#         s = SubjectSession(versions, Lock())
#         v1 = ServerModuleVersionManager.load_from_dir(s, module_path, "1.0.0")
#         v2 = ServerModuleVersionManager.load_from_dir(s, module_path, "1.0.1")

#         # --- v1 - src missing ---
#         version_base_path \
#             = os.path.join(module_path, "1.0.0")

#         # assert version is not initialized
#         vm = ServerModuleVersionManager(s, v1.id)
#         self.assertFalse(vm.has_error())
#         self.assertFalse(vm.is_initialized())
#         self.assertEqual(vm.get_working_path(),
#                          os.path.join(version_base_path, "rt"))
#         self.assertFalse(os.path.exists(vm.get_working_path()))

#         # assert initialization succeeds
#         self.assertIsNone(vm.model().last_src_hash)
#         self.assertTrue(vm.validate_file_structure())
#         self.assertTrue(vm.is_initialized())
#         self.assertTrue(os.path.exists(vm.get_working_path()))

#         # assert validation failed (src dir missing)
#         self.assertFalse(os.path.exists(vm.get_src_path()))
#         self.assertFalse(vm.is_src_validated())
#         self.assertIsNotNone(vm.model().last_src_hash)

#         # --- v2 - src present ---
#         version_base_path \
#             = os.path.join(module_path, "1.0.1")

#         # assert version is not initialized
#         vm = ServerModuleVersionManager(s, v2.id)
#         self.assertFalse(vm.has_error())
#         self.assertFalse(vm.is_initialized())
#         self.assertEqual(vm.get_working_path(),
#                          os.path.join(version_base_path, "runtime"))
#         self.assertFalse(os.path.exists(vm.get_working_path()))

#         # assert initialization succeeds
#         self.assertIsNone(vm.model().last_src_hash)
#         self.assertTrue(vm.validate_file_structure())
#         self.assertTrue(vm.is_initialized())
#         self.assertTrue(os.path.exists(vm.get_working_path()))

#         # assert succeeded failed
#         self.assertTrue(os.path.exists(vm.get_src_path()))
#         self.assertTrue(vm.is_src_validated())
#         self.assertIsNotNone(vm.model().last_src_hash)


# class ServerModuleManagerTest(unittest.TestCase):

#     def test_load_from_dir(self):
#         _initialize("create_module_from_dir")

#         versions = set()
#         s = SubjectSession(versions, Lock())

#         # assert invalid domain path raises FileNotFoundError
#         path_builder._paths[app_constants.MODULE_DOMAIN] = "wrong_path"
#         self.assertRaises(FileNotFoundError,
#                           lambda: ServerModuleManager.load_from_dir(
#                               s, "missing_config"))
#         self.assertEqual(len(versions), 0)
#         path_builder._paths[app_constants.MODULE_DOMAIN] = TEST_MODULE_PATH

#         # assert invalid module path raises FileNotFoundError
#         self.assertRaises(FileNotFoundError,
#                           lambda: ServerModuleManager.load_from_dir(
#                               s, "missing_module"))
#         self.assertEqual(len(versions), 0)

#         # assert missing config file raises FileNotFoundError
#         self.assertRaises(FileNotFoundError,
#                           lambda: ServerModuleManager.load_from_dir(
#                               s, "missing_config"))
#         self.assertEqual(len(versions), 0)

#         # assert invalid json in config file succeeds with error value
#         module = ServerModuleManager.load_from_dir(s, "invalid_config")
#         self.assertIsNotNone(module.error)
#         self.assertEqual(module.error.code, ModuleError.Type.CFG_INVALID)
#         self.assertEqual(module.error.name, "ConfigParseError")
#         self.assertTrue(module in versions)

#         # assert empty config file loads default values
#         module = ServerModuleManager.load_from_dir(s, "empty_config")
#         self.assertIsNone(module.error)
#         self.assertTrue(module in versions)
#         self.assertEqual(module.name, "empty_config")
#         self.assertEqual(module.version_ids, {})
#         self.assertIsNone(module.active_version)
#         self.assertEqual(module.autostart, False)
#         self.assertEqual(module.enabled, False)
#         self.assertEqual(module.description, "No description provided")

#         # assert valid config file loads all values correctly
#         module = ServerModuleManager.load_from_dir(s, "filled_config")
#         self.assertIsNone(module.error)
#         self.assertTrue(module in versions)
#         self.assertEqual(module.name, "filled_config")
#         self.assertEqual(module.version_ids, {})
#         self.assertIsNone(module.active_version)
#         self.assertEqual(module.autostart, True)
#         self.assertEqual(module.enabled, True)
#         self.assertEqual(module.description, "valid config")

#         # assert valid config file loads all values correctly
#         module = ServerModuleManager.load_from_dir(s, "with_versions")
#         self.assertIsNone(module.error)
#         self.assertEqual(module.name, "with_versions")
#         self.assertSetEqual(set(module.version_ids.keys()),
#                             {"1.0.1", "1.0.0"})
#         self.assertIsNone(module.active_version)
#         self.assertEqual(module.autostart, True)
#         self.assertEqual(module.enabled, True)
#         self.assertEqual(module.description, "valid config")

#         vs = ServerModuleVersionManager.get_versions_by_ids(
#             s, module.version_ids.values())
#         self.assertEqual(len(vs), 2)

#         self.assertTrue(vs[0].initialized)
#         self.assertTrue(vs[1].initialized)

#     def test_update_versions(self):
#         _initialize()

#         subjects = set()
#         s = SubjectSession(subjects, Lock())

#         def get_versions() -> set[ServerModuleVersion]:
#             return {v for v in subjects if isinstance(v, ServerModuleVersion)}

#         _copy_modules_dir('update_module_versions/1')
#         module = ServerModuleManager.load_from_dir(s, "mod")
#         smm = ServerModuleManager(s, "mod")
#         self.assertSetEqual(set(module.version_ids.keys()), {'1.0.0'})
#         self.assertEqual(len(get_versions()), 1)

#         self.assertFalse(smm.is_running())

#         # set only version as active
#         self.assertIsNone(smm.get_active_version())
#         module.active_version = '1.0.0'
#         v = smm.get_active_version()
#         self.assertIsNotNone(v)

#         # set version as running
#         v.running = True
#         self.assertTrue(smm.is_running())
#         self.assertRaises(StateError, lambda: smm.load_versions())
#         v.running = False
#         self.assertFalse(smm.is_running())

#         _copy_modules_dir('update_module_versions/2')
#         smm.load_versions()
#         self.assertSetEqual(set(module.version_ids.keys()), {'1.0.0', '1.0.1'})
#         self.assertEqual(len(get_versions()), 2)
#         self.assertEqual(smm.get_active_version().version, '1.0.0')

#         _copy_modules_dir('update_module_versions/3')
#         smm.load_versions()
#         self.assertSetEqual(set(module.version_ids.keys()), {'1.0.3'})
#         self.assertEqual(len(get_versions()), 1)
#         self.assertIsNone(smm.get_active_version())


# class ServerModuleServiceTest(unittest.TestCase):

#     def test_examine_modules(self):
#         _initialize()

#         subjects = set()
#         s = SubjectSession(subjects, Lock())

#         # assert no modules exist
#         self.assertEqual(len(ServerModuleManager.all(s)), 0)

#         # empty dir
#         ServerModuleService.examine_modules(s)
#         self.assertEqual(len(ServerModuleManager.all(s)), 0)

#         # assert no modules exist
#         ServerModuleService.examine_modules(s)
#         self.assertEqual(len(ServerModuleManager.all(s)), 0)

#         # assert valid module is found and invalid module is ignored
#         _copy_modules_dir("examine_modules/1")
#         ServerModuleService.examine_modules(s)
#         self.assertSetEqual(
#             {m.name for m in ServerModuleManager.all(s)}, {"mod 1"})

#         # assert examine raises on running modules
#         _copy_modules_dir("examine_modules/2")
#         smm = ServerModuleManager(s, "mod 1")
#         smm.model().active_version = '1.0.0'
#         smm.get_active_version().running = True
#         self.assertRaises(StateError,
#                           lambda: ServerModuleService.examine_modules(s))
#         smm.get_active_version().running = False
#         self.assertSetEqual(
#             {m.name for m in ServerModuleManager.all(s)}, {"mod 1"})

#         # assert new version is added and existing version is updated
#         ServerModuleService.examine_modules(s)
#         self.assertSetEqual(
#             {m.name for m in ServerModuleManager.all(s)}, {"mod 1", "mod 2"})
#         self.assertIsNone(smm.get_active_version())
#         self.assertTrue('1.0.1' in smm.model().version_ids)

#         # assert abandoned version is removed
#         _copy_modules_dir("examine_modules/3")
#         ServerModuleService.examine_modules(s)
#         self.assertSetEqual(
#             {m.name for m in ServerModuleManager.all(s)}, {"mod 3"})
