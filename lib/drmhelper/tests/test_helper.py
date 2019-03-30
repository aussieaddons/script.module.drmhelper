from drmhelper import config
from drmhelper import helper

import fakes

import mock

import testtools


def get_xbmc_cond_visibility(cond):
    global HACK_PLATFORMS
    if cond in HACK_PLATFORMS:
        return True


class DRMHelperTests(testtools.TestCase):

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

    @mock.patch('xbmc.translatePath')
    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_uwp_kodi17(self, mock_get_system, mock_trans_path):
        for system in fakes.SYSTEMS:
            if system['system'] == 'Windows':
                mock_get_system.return_value = 'UWP'  # Kodi <18
                mock_trans_path.return_value = 'foo bar 4n2hpmxwrvr6p key'
                h = helper.DRMHelper()
                self.assertTrue(h._is_uwp())

    @mock.patch.object(helper.DRMHelper, '_get_system')
    def test_is_uwp_kodi18(self, mock_get_system):
        for system in fakes.SYSTEMS:
            if system['system'] == 'Windows':
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

    def test_get_kodi_arch(self):
        arch = helper.DRMHelper._get_kodi_arch()
        fake_arch = ('64bit', 'test')
        with mock.patch('platform.architecture', return_value=fake_arch):
            self.assertEqual(arch, fake_arch[0])

    def test_get_kodi_platform(self):
        fake_system = 'Windows'
        fake_arch = 'x64'
        with mock.patch.object(helper.DRMHelper, '_get_system',
                               return_value=fake_system):
            with mock.patch.object(helper.DRMHelper, '_get_arch',
                                   return_value=fake_arch):
                h = helper.DRMHelper()
                plat = h._get_platform()
                expected_plat = (fake_system, fake_arch)
                self.assertEqual(plat, expected_plat)

    def test_is_wv_drm_supported(self):
        with mock.patch.object(helper.DRMHelper, '_get_platform',
                               return_value=('Linux', 'x86_64')):
            h = helper.DRMHelper()
            is_supported = h._is_wv_drm_supported()
            self.assertTrue(is_supported)

    def test_is_wv_drm_not_supported(self):
        with mock.patch.object(helper.DRMHelper, '_get_platform',
                               return_value=('PowerPC', 'sparc')):
            h = helper.DRMHelper()
            is_supported = h._is_wv_drm_supported()
            self.assertFalse(is_supported)

    def test_get_ssd_filename(self):
        fake_system = 'Windows'
        with mock.patch.object(helper.DRMHelper, '_get_system',
                               return_value=fake_system):
            ssd_filename = config.SSD_WV_DICT[fake_system]
            h = helper.DRMHelper()
            result = h._get_ssd_filename()
            self.assertEqual(result, ssd_filename)

    def test_get_wvcdm_filename(self):
        fake_system = 'Linux'
        with mock.patch.object(helper.DRMHelper, '_get_system',
                               return_value=fake_system):
            wvcdm_filename = config.WIDEVINE_CDM_DICT[fake_system]
            h = helper.DRMHelper()
            result = h._get_wvcdm_filename()
            self.assertEqual(result, wvcdm_filename)

    @mock.patch('drmhelper.utils.get_kodi_major_version')
    def test_get_latest_ia_version(self, mock_kodi_maj_ver):
        test_kodi_ver = 18
        mock_kodi_maj_ver.return_value = test_kodi_ver
        h = helper.DRMHelper()
        result = h._get_latest_ia_version()
        expected = config.LATEST_IA_VERSION[test_kodi_ver]['ver']
        self.assertEqual(result, expected)

    @mock.patch('drmhelper.utils.get_kodi_major_version')
    def test_get_minimum_ia_version(self, mock_kodi_maj_ver):
        test_kodi_ver = 18
        mock_kodi_maj_ver.return_value = test_kodi_ver
        h = helper.DRMHelper()
        result = h._get_minimum_ia_version()
        expected = config.MIN_IA_VERSION[test_kodi_ver]
        self.assertEqual(result, expected)

    def test_is_ia_current(self):
        with mock.patch.object(helper.DRMHelper, '_get_minimum_ia_version',
                               return_value='0.0.1'):
            fake_addon = fakes.FakeAddon()
            h = helper.DRMHelper()
            result = h._is_ia_current(fake_addon)
            self.assertTrue(result)

    def test_is_ia_current_negative(self):
        with mock.patch.object(helper.DRMHelper, '_get_minimum_ia_version',
                               return_value='0.0.2'):
            fake_addon = fakes.FakeAddon()
            h = helper.DRMHelper()
            result = h._is_ia_current(fake_addon)
            self.assertFalse(result)

    def test_is_ia_current_latest(self):
        with mock.patch.object(helper.DRMHelper, '_get_latest_ia_version',
                               return_value={'ver': '0.0.1'}):
            fake_addon = fakes.FakeAddon()
            h = helper.DRMHelper()
            result = h._is_ia_current(fake_addon, latest=True)
            self.assertTrue(result)

    def test_is_ia_current_latest_negative(self):
        with mock.patch.object(helper.DRMHelper, '_get_latest_ia_version',
                               return_value={'ver': '0.0.2'}):
            fake_addon = fakes.FakeAddon()
            h = helper.DRMHelper()
            result = h._is_ia_current(fake_addon, latest=True)
            self.assertFalse(result)

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

    def test_get_addon_install_ok(self):
        rpc_success = {"result": {"addon": {"enabled": True}}}
        fake_addon = fakes.FakeAddon()
        with mock.patch.object(helper.DRMHelper, '_execute_json_rpc',
                               return_value=rpc_success):
            with mock.patch.object(helper.DRMHelper, '_install_addon',
                                   return_value=fake_addon):
                with mock.patch.object(helper.DRMHelper, '_is_ia_current',
                                       return_value=True):
                    h = helper.DRMHelper()
                    result = h.get_addon()
                    #self.assertEqual(result, fake_addon)
