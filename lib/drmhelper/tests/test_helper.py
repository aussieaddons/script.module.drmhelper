import io
import json
import os

try:
    import mock
except ImportError:
    import unittest.mock as mock

import responses

import testtools

from drmhelper import config
from drmhelper import helper
from drmhelper.tests import fakes


def get_xbmc_cond_visibility(cond):
    global HACK_PLATFORMS
    if cond in HACK_PLATFORMS:
        return True


def get_trans_path(path, system):
    if path.startswith('special://'):
        if path == 'special://home/':
            return fakes.HOME_PATHS.get(system)
        else:
            return fakes.TRANSLATED_SPECIAL_PATHS.get(system)
    else:
        return path


class DRMHelperTests(testtools.TestCase):

    @classmethod
    def setUpClass(self):
        cwd = os.path.join(os.getcwd(), 'lib/drmhelper/tests')
        with open(os.path.join(cwd, 'modules.v2.json'), 'rb') as f:
            self.MODULE_JSON = io.BytesIO(f.read()).read()

    @mock.patch('xbmc.getCondVisibility')
    def test_get_system(self, mock_cond_vis):
        for system in fakes.SYSTEMS:
            with mock.patch('platform.system', return_value=system['system']):
                global HACK_PLATFORMS
                HACK_PLATFORMS = system['platforms']
                mock_cond_vis.side_effect = get_xbmc_cond_visibility
                h = helper.DRMHelper()
                sys = h._get_system()
                self.assertEqual(sys, system['expected_system'])

    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_windows(self, mock_get_system):
        for system in fakes.SYSTEMS:
            if system['expected_system'] == 'Windows':
                mock_get_system.return_value = 'Windows'
                h = helper.DRMHelper()
                self.assertTrue(h._is_windows())

    @mock.patch('xbmc.getCondVisibility')
    @mock.patch('xbmc.translatePath')
    def test_is_uwp_kodi17(self, mock_trans_path, mock_cond_vis):
        for system in fakes.SYSTEMS:
            if system['system'] == 'Windows':
                global HACK_PLATFORMS
                HACK_PLATFORMS = system['platforms']
                mock_cond_vis.side_effect = get_xbmc_cond_visibility
                mock_trans_path.return_value = 'foo bar 4n2hpmxwrvr6p key'
                h = helper.DRMHelper()
                self.assertTrue(h._is_uwp())

    @mock.patch('xbmc.getCondVisibility')
    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_uwp_kodi18(self, mock_get_system, mock_cond_vis):
        for system in fakes.SYSTEMS:
            if system['system'] == 'Windows':
                global HACK_PLATFORMS
                HACK_PLATFORMS = system['platforms']
                mock_cond_vis.side_effect = get_xbmc_cond_visibility
                mock_get_system.return_value = 'UWP'
                h = helper.DRMHelper()
                self.assertTrue(h._is_uwp())

    @mock.patch('drmhelper.utils.get_info_label')
    def test_is_libreelec(self, mock_get_info_label):
        mock_get_info_label.return_value = 'blah blah LibreElec blah blah'
        h = helper.DRMHelper()
        self.assertTrue(h._is_libreelec())

    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_mac(self, mock_get_system):
        for system in fakes.SYSTEMS:
            mock_get_system.return_value = system['expected_system']
            if system['expected_system'] == 'Darwin':
                h = helper.DRMHelper()
                self.assertTrue(h._is_mac())

    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_android(self, mock_get_system):
        for system in fakes.SYSTEMS:
            mock_get_system.return_value = system['expected_system']
            if system['expected_system'] == 'Android':
                h = helper.DRMHelper()
                sys = h._get_system()
                is_android = h._is_android()
                if sys == system['expected_system']:
                    self.assertTrue(is_android)

    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_linux(self, mock_get_system):
        for system in fakes.SYSTEMS:
            mock_get_system.return_value = system['expected_system']
            if system['expected_system'] == 'Linux':
                h = helper.DRMHelper()
                sys = h._get_system()
                is_linux = h._is_linux()
                if sys == system['expected_system']:
                    self.assertTrue(is_linux)

    @mock.patch('platform.architecture')
    def test_get_kodi_arch(self, mock_arch):
        mock_arch.return_value = ['x86_64']
        arch = helper.DRMHelper._get_kodi_arch()
        fake_arch = ('x86_64', 'test')
        with mock.patch('platform.architecture', return_value=fake_arch):
            self.assertEqual(arch, fake_arch[0])

    @mock.patch('xbmc.getCondVisibility')
    @mock.patch('xbmc.translatePath')
    @mock.patch('platform.machine')
    @mock.patch('platform.system')
    def test_get_kodi_platform(self, mock_system, mock_machine,
                               mock_trans_path, mock_cond_vis):
        for system in fakes.SYSTEMS:
            h = helper.DRMHelper()
            global HACK_PLATFORMS
            HACK_PLATFORMS = system['platforms']
            mock_cond_vis.side_effect = get_xbmc_cond_visibility
            expected_system = system.get('expected_system')
            if expected_system == 'UWP':
                mock_trans_path.return_value = 'foo bar 4n2hpmxwrvr6p key'
            expected_machine = system.get('machine')
            expected_arch = system.get('expected_arch')
            mock_system.return_value = expected_system
            mock_machine.return_value = expected_machine
            observed = h._get_platform()
            expected = (expected_system, expected_arch)
            self.assertEqual(expected, observed)

    @mock.patch('xbmc.getCondVisibility')
    @mock.patch('xbmc.translatePath')
    @mock.patch('platform.machine')
    @mock.patch('platform.system')
    def test_is_wv_drm_supported(self, mock_system, mock_machine,
                                 mock_trans_path, mock_cond_vis):
        for s in fakes.SYSTEMS:
            h = helper.DRMHelper()
            global HACK_PLATFORMS
            HACK_PLATFORMS = s['platforms']
            mock_cond_vis.side_effect = get_xbmc_cond_visibility
            expected_system = s.get('expected_system')
            if expected_system == 'UWP':
                mock_trans_path.return_value = 'foo bar 4n2hpmxwrvr6p key'
            expected_machine = s.get('machine')
            mock_system.return_value = expected_system
            mock_machine.return_value = expected_machine
            observed = h._is_wv_drm_supported()
            expected = s.get('drm_supported')
            self.assertEqual(expected, observed)

    def test_is_wv_drm_not_supported(self):
        with mock.patch.object(helper.DRMHelper, '_get_platform',
                               return_value=('PowerPC', 'sparc')):
            h = helper.DRMHelper()
            is_supported = h._is_wv_drm_supported()
            self.assertFalse(is_supported)

    def test_get_wvcdm_filename(self):
        fake_system = 'Linux'
        with mock.patch.object(helper.DRMHelper, '_get_system',
                               return_value=fake_system):
            wvcdm_filename = config.WIDEVINE_CDM_DICT[fake_system]
            h = helper.DRMHelper()
            result = h._get_wvcdm_filename()
            self.assertEqual(result, wvcdm_filename)

    @mock.patch.object(fakes.FakeAddon, 'getSetting')
    @mock.patch('xbmc.translatePath')
    def test_get_wvcdm_paths(self, translate_path, fake_setting):
        for system in fakes.SYSTEMS:
            sys_name = system.get('system')

            def get_trnspath(path):
                return get_trans_path(path, sys_name)

            translate_path.side_effect = get_trnspath
            fake_setting.side_effect = lambda \
                x: fakes.TRANSLATED_SPECIAL_PATHS.get(sys_name)
            fake_addon = fakes.FakeAddon()
            h = helper.DRMHelper()
            observed = h._get_wvcdm_paths(fake_addon)
            self.assertEqual([fakes.TRANSLATED_SPECIAL_PATHS.get(sys_name),
                              fakes.CDM_PATHS.get(sys_name)[1]], observed)

    @responses.activate
    @mock.patch.object(helper.DRMHelper, '_get_arch')
    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_set_wvcdm_current_ver_data(self, mock_system, mock_arch):
        responses.add(responses.GET, config.CDM_CURRENT_VERSION_URL,
                      body=self.MODULE_JSON)
        h = helper.DRMHelper()
        for system in fakes.SYSTEMS:
            expected_system = system.get('expected_system')
            expected_arch = system.get('expected_arch')
            mock_system.return_value = expected_system
            mock_arch.return_value = expected_arch
            if expected_system in ['Android', 'UWP']:
                continue
            h._set_wvcdm_current_ver_data()
            expected = json.loads(self.MODULE_JSON)['widevine'][
                'platforms'].get(h._lookup_mjh_plat())
            observed = h.wvcdm_download_data
            self.assertEqual(expected, observed)

    @responses.activate
    @mock.patch.object(helper.hashlib, 'md5')
    @mock.patch.object(helper.DRMHelper, '_get_platform')
    @mock.patch.object(helper.DRMHelper, '_get_arch')
    @mock.patch.object(helper.DRMHelper, '_get_system')
    @mock.patch.object(helper.DRMHelper, '_get_wvcdm_filename', str)
    @mock.patch('drmhelper.helper.DRMHelper._get_wvcdm_paths')
    @mock.patch('drmhelper.helper.builtins.open')
    @mock.patch('os.path.isfile')
    def test_check_wvcdm_version_current(self, mock_isfile, mock_open,
                                         mock_paths, mock_system, mock_arch,
                                         mock_platform, mock_md5):
        responses.add(responses.GET, config.CDM_CURRENT_VERSION_URL,
                      body=self.MODULE_JSON)
        h = helper.DRMHelper()
        fake_md5 = fakes.FakeMd5()
        mock_md5.return_value = fake_md5
        wvdata = json.loads(self.MODULE_JSON)['widevine'].get('platforms')
        for system in fakes.SYSTEMS:
            expected_system = system.get('expected_system')
            expected_arch = system.get('expected_arch')
            mock_platform.return_value = (expected_system, expected_arch)
            if expected_system == 'Android' or not h._is_wv_drm_supported():
                continue
            mock_system.return_value = expected_system
            mock_arch.return_value = expected_arch
            mock_paths.return_value = fakes.TRANSLATED_SPECIAL_PATHS.get(
                'Linux')
            mock_isfile.return_value = True
            mock_open.return_value = io.BytesIO(b'bar')
            for entry in wvdata.get(h._lookup_mjh_plat()):
                fake_md5.digest_value = entry.get('md5')
                expected = True
                observed = h._check_wv_cdm_version_current()
                self.assertEqual(expected, observed)

    @responses.activate
    @mock.patch.object(helper.hashlib, 'md5')
    @mock.patch.object(helper.DRMHelper, '_get_arch')
    @mock.patch.object(helper.DRMHelper, '_get_system')
    @mock.patch.object(helper.DRMHelper, '_get_wvcdm_filename', str)
    @mock.patch('drmhelper.helper.DRMHelper._get_wvcdm_paths')
    @mock.patch('drmhelper.helper.builtins.open')
    @mock.patch('os.path.isfile')
    def test_check_wvcdm_version_current_fail(self, mock_isfile, mock_open,
                                              mock_paths, mock_system,
                                              mock_arch, mock_md5):
        responses.add(responses.GET, config.CDM_CURRENT_VERSION_URL,
                      body=self.MODULE_JSON)
        h = helper.DRMHelper()
        fake_md5 = fakes.FakeMd5()
        mock_md5.return_value = fake_md5
        fake_md5.digest_value = 'abc123'
        mock_system.return_value = 'Linux'
        mock_arch.return_value = 'x86_64'
        mock_paths.return_value = fakes.TRANSLATED_SPECIAL_PATHS.get('Linux')
        mock_isfile.return_value = True
        mock_open.return_value = io.BytesIO(b'bar')
        expected = False
        observed = h._check_wv_cdm_version_current()
        self.assertEqual(expected, observed)

    @mock.patch('tempfile.TemporaryFile')
    def test_get_wv_cdm_path(self, temp_file):
        for system in fakes.SYSTEMS:
            rv = fakes.TRANSLATED_SPECIAL_PATHS.get(system.get('system'))
            with mock.patch.object(
                    helper.DRMHelper, '_get_wvcdm_paths', return_value=rv):
                fake_addon = fakes.FakeAddon()
                h = helper.DRMHelper()
                cdm_paths = h._get_wvcdm_paths(fake_addon)
                result = h._get_wvcdm_path(fake_addon, cdm_paths)
                temp_file.assert_called()
                self.assertEqual(result, cdm_paths[0])

    @responses.activate
    @mock.patch.object(helper.DRMHelper, '_get_kodi_arch')
    @mock.patch.object(helper.DRMHelper,
                       '_rename_windows_cdm',
                       return_value=True)
    @mock.patch.object(helper.DRMHelper,
                       '_execute_cdm_command',
                       return_value=True)
    @mock.patch.object(helper.DRMHelper,
                       '_progress_download',
                       return_value='True')
    @mock.patch('xbmc.translatePath')
    @mock.patch('tempfile.TemporaryFile')
    @mock.patch('xbmc.executeJSONRPC')
    @mock.patch('xbmcaddon.Addon')
    @mock.patch('xbmcgui.DialogProgress')
    @mock.patch('os.path.isfile')
    @mock.patch('os.path.isdir')
    def test_get_wvcdm(self, is_dir, is_file, dialog, mock_get_addon,
                       mock_json_rpc, temp_file, translate_path,
                       prog_download, cdm_command, rename_win, mock_kodi_arch):
        fake_addon = fakes.FakeAddon()
        for s in fakes.SYSTEMS:
            h = helper.DRMHelper()
            mock_get_addon.return_value = fake_addon
            mock_json_rpc.return_value = json.dumps(fakes.IA_ENABLED)
            responses.add(responses.GET, config.CDM_CURRENT_VERSION_URL,
                          body=self.MODULE_JSON)
            translate_path.return_value = get_trans_path(
                fakes.TRANS_PATH_ARGS[0], s.get('system'))
            with mock.patch.object(
                    helper.DRMHelper, '_get_wvcdm_paths',
                    return_value=fakes.CDM_PATHS.get(s.get('system'))):
                with mock.patch.object(helper.DRMHelper, '_get_system',
                                       return_value=s.get('expected_system')):
                    with mock.patch.object(
                            helper.DRMHelper, '_get_arch',
                            return_value=s.get('expected_arch')):
                        mock_kodi_arch.return_value = s.get('expected_arch')
                        is_dir.return_value = True
                        is_file.return_value = False
                        observed = h._get_wvcdm()
                        if (not h._is_wv_drm_supported() or
                                s.get('expected_system') == 'Android'):
                            expected = None
                        else:
                            expected = True
                            temp_file.assert_called_once()
                            temp_file.reset_mock()
                            dialog.assert_called_once()
                            dialog.reset_mock()
                            prog_download.assert_called_once()
                            prog_download.reset_mock()
                            assert cdm_command.called or rename_win.called
                            cdm_command.reset_mock()
                            rename_win.reset_mock()

                        self.assertEqual(expected, observed)

    @mock.patch('xbmc.executeJSONRPC')
    def test_execute_json_rpc(self, mock_exec_json_rpc):
        mock_exec_json_rpc.return_value = '{"ok": true}'
        method = 'test_method',
        params = {'test_param': True}
        h = helper.DRMHelper()
        h._execute_json_rpc(method, params)
        mock_exec_json_rpc.assert_called_once()

    @mock.patch('xbmcaddon.Addon')
    def test_private_get_addon(self, mock_get_addon):
        fake_addon = fakes.FakeAddon()
        mock_get_addon.return_value = fake_addon
        h = helper.DRMHelper()
        result = h._get_addon()
        mock_get_addon.assert_called_once_with('inputstream.adaptive')
        self.assertEqual(result, fake_addon)

    def test_enable_addon(self):
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value=True):
            h = helper.DRMHelper()
            result = h._enable_addon()
            self.assertTrue(result)

    def test_enable_addon_negative(self):
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value=None):
            h = helper.DRMHelper()
            result = h._enable_addon()
            self.assertFalse(result)

    @mock.patch('xbmc.executebuiltin')
    def test_install_addon(self, mock_executebuiltin):
        fake_addon = fakes.FakeAddon()
        with mock.patch.object(helper.DRMHelper, '_get_addon',
                               return_value=fake_addon):
            h = helper.DRMHelper()
            result = h._install_addon()
            self.assertEqual(result, fake_addon)

    def test_get_addon_enable_error(self):
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value=None):
            h = helper.DRMHelper()
            result = h.get_addon()
            self.assertFalse(result)

    def test_get_addon_install_error(self):
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value={"error": "message"}):
            with mock.patch.object(helper.DRMHelper, '_install_addon',
                                   return_value=None):
                h = helper.DRMHelper()
                result = h.get_addon()
                self.assertFalse(result)

    @mock.patch('xbmcaddon.Addon')
    def test_get_addon_install_ok(self, mock_get_addon):
        rpc_success = {"result": {"addon": {"enabled": True}}}
        fake_addon = fakes.FakeAddon()
        mock_get_addon.return_value = fake_addon
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value=rpc_success):
            with mock.patch.object(helper.DRMHelper, '_install_addon',
                                   return_value=fake_addon):
                h = helper.DRMHelper()
                result = h.get_addon()
                self.assertEqual(result, fake_addon)
