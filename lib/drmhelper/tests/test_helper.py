from drmhelper import config
from drmhelper import helper

import fakes

import mock

import testtools

import logging

logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger()


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

#    def test_get_latest_ia_version(self):
#
#    def test_get_minimum_ia_version(self):
#
#    def test_should_update_ia(self):
