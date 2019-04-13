import json
import os
import platform
import posixpath
import zipfile

from distutils.version import LooseVersion
from pipes import quote

from drmhelper import config
from drmhelper import utils

import requests

import xbmc
import xbmcaddon
import xbmcgui


class DRMHelper(object):
    """DRM Helper"""

    def _get_system(self):
        """Get the system platform information"""

        if xbmc.getCondVisibility('System.Platform.UWP'):
            return 'UWP'

        if '4n2hpmxwrvr6p' in xbmc.translatePath('special://xbmc'):
            # Look for this app key in the path, which is the only reliable
            # way we can tell if it's a special UWP build on Kodi v17
            return 'UWP'

        if xbmc.getCondVisibility('System.Platform.Android'):
            return 'Android'

        if xbmc.getCondVisibility('System.Platform.IOS'):
            return 'IOS'

        return platform.system()

    def _is_windows(self):
        return self._get_system() == 'Windows'

    def _is_uwp(self):
        return self._get_system() == 'UWP'

    def _is_mac(self):
        return self._get_system() == 'Darwin'

    def _is_linux(self):
        return self._get_system() == 'Linux'

    # TODO(andy): Make this more generic to cover other cases where we allow
    # manual install, like Arch
    @classmethod
    def _is_libreelec(cls):
        return True
        version_info = utils.get_info_label('System.OSVersionInfo')
        if version_info:
            return 'LibreELEC' in version_info

    def _is_android(self):
        return self._get_system() == 'Android'

    def _is_ios(self):
        return self._get_system() == 'IOS'

    def _get_arch(self):
        arch = platform.machine()
        if arch.startswith('arm'):
            # strip armv6l down to armv6
            arch = arch[:5]

        # TODO(andy) Should Windows be a special case?
        if platform.system() == 'Windows':
            try:
                kodi_arch = self._get_kodi_arch()
                arch = config.WINDOWS_BITNESS.get(kodi_arch)
            except ImportError:
                # No module named _subprocess on Xbox One, so this call fails
                # so we assume it'll always be x86_64 in this case.
                arch = 'x86_64'

        return arch

    @classmethod
    def _get_kodi_arch(cls):
        try:
            arch = platform.architecture()[0]
        except ImportError:
            # No module named _subprocess on Xbox One, so this call fails
            # so we assume it'll always be x86_64 in this case.
            arch = 'x86_64'
        return arch

    def _get_platform(self):
        """Return a tuple for our system/arch

        For example:
            ('Windows', 'x86')
            ('Darwin', 'x86_64')
            ('Linux', 'x86_64')
            ('Linux', 'arm')
            ('Android', 'aarch64')
        """
        arch = self._get_arch()
        if arch in config.ARCH_DICT:
            arch = config.ARCH_DICT[arch]
        return (self._get_system(), arch)

    def get_platform_name(self):
        """Return a friendlier platform name"""
        system = self._get_system()
        arch = self._get_arch()

        if system == 'Darwin':
            system = 'Mac OS X'

        if system == 'IOS':
            system = 'iOS'

        if system == 'UWP':
            system = 'Windows UWP/Xbox One'

        return '{0} ({1})'.format(system, arch)

    def _is_wv_drm_supported(self):
        plat = self._get_platform()
        if plat in config.SUPPORTED_WV_DRM_PLATFORMS:
            return True
        return False

    def _get_ssd_filename(self):
        return config.SSD_WV_DICT.get(self._get_system())

    def _get_wvcdm_filename(self):
        return config.WIDEVINE_CDM_DICT.get(self._get_system())

    @classmethod
    def _get_latest_ia_version(cls):
        kodi_ver = utils.get_kodi_major_version()
        ver = config.LATEST_IA_VERSION.get(kodi_ver)['ver']
        utils.log('Latest inputstream.adaptive version is {0}'.format(ver))
        return ver

    @classmethod
    def _get_minimum_ia_version(cls):
        kodi_ver = utils.get_kodi_major_version()
        return config.MIN_IA_VERSION.get(kodi_ver)

    def _is_ia_current(self, addon, latest=False):
        """Check if InputStream Adaptive is a current enough version

        Check if inputstream.adaptive addon meets the minimum version
        requirements.
        latest -- checks if addon is equal to the latest available compiled
        version
        """
        if not addon:
            return False

        ia_ver = addon.getAddonInfo('version')
        utils.log('Found inputstream.adaptive version is {0}'.format(ia_ver))

        if latest:
            ver = self._get_latest_ia_version()['ver']
        else:
            ver = self._get_minimum_ia_version()

        utils.log('Candidate inputstream.adaptive version is {0}'.format(ver))

        return LooseVersion(ia_ver) >= LooseVersion(ver)

    @classmethod
    def _execute_json_rpc(cls, method, params):
        """Execute an XBMC JSON RPC call"""
        try:
            json_enable = {
                'id': 1,
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
            }
            rpc_enable = json.dumps(json_enable)
            rpc_call = xbmc.executeJSONRPC(rpc_enable)
            return json.loads(rpc_call)
        except RuntimeError:
            return False

    def _get_addon(self):
        try:
            return xbmcaddon.Addon('inputstream.adaptive')
        except Exception:
            return None

    def _enable_addon(self):
        req = {
            'method': 'Addons.SetAddonEnabled',
            'params': {'addonid': 'inputstream.adaptive',
                       'enabled': True}}
        result = self._execute_json_rpc(**req)

        if not result:
            utils.log('Failure in enabling inputstream.adaptive')
            return False
        return True

    def _install_addon(self):
        try:  # see if there's an installed repo that has it
            xbmc.executebuiltin('InstallAddon(inputstream.adaptive)', True)
            addon = self._get_addon()
            utils.log('inputstream.adaptive installed from repo')
            return addon
        except RuntimeError:
            utils.dialog('inputstream.adaptive not installed',
                         'inputstream.adaptive not installed. This '
                         'addon now comes supplied with newer builds '
                         'of Kodi 18 for Windows/Mac/LibreELEC/OSMC, '
                         'and can be installed from most Linux package '
                         'managers eg. "sudo apt install kodi-'
                         'inputstream-adaptive"')

    def get_addon(self, drm=True):
        """Enable and get the inpustream.adaptive add-on

        Check if inputstream.adaptive is installed, attempt to install if not.
        """
        addon = None

        req = {
            'method': 'Addons.GetAddonDetails',
            'params': {'addonid': 'inputstream.adaptive',
                       'properties': ['enabled']}}
        result = self._execute_json_rpc(**req)

        if not result:
            return False  # error

        if 'error' in result:  # not installed
            utils.log('inputstream.adaptive not currently installed')
            addon = self._install_addon()
            if not addon:
                return False  # error installing
        else:  # installed but not enabled. let's enable it.
            if result['result']['addon'].get('enabled') is False:
                utils.log('inputstream.adaptive not enabled, enabling...')
                self._enable_addon()
            addon = self._get_addon()

        if not self._is_ia_current(addon):
            utils.dialog('inputstream.adaptive version lower than '
                         'required', 'inputstream.adaptive version '
                         'does not meet requirements. Please '
                         'update your Kodi installation to a newer '
                         'v18 build and try again')
            return False
        return addon

    def is_wv_drm_supported(self):
        """Is platform supported"""
        # TODO(andy): Store something in settings to prevent this message
        # appearing more than once?
        if not self._is_wv_drm_supported():
            utils.dialog(
                'Platform not supported',
                '{0} not supported for DRM playback. '
                'For more information, see our DRM FAQ at {1}'
                ''.format(self.get_platform_name(), config.DRM_INFO))
            return False
        return True

    @classmethod
    def _is_kodi_supported_version(cls):
        if utils.get_kodi_major_version() < 18:
            utils.dialog(
                'Kodi 18+ Required',
                'The minimum version of Kodi required for DASH/DRM '
                'protected content is v18. Please upgrade in order to '
                'use this feature.')
            return False
        return True

    @classmethod
    def _is_leia_build_ok(cls):
        date = utils.get_kodi_build_date()
        if not date:  # can't find build date, assume meets minimum
            utils.log('Could not determine date of build, assuming date meets '
                      'minimum. Build string is {0}'.format(
                          utils.get_kodi_build()))
            return True

        leia_min_date = config.MIN_LEIA_BUILD[0]
        min_date, min_commit = config.MIN_LEIA_BUILD

        if int(date) < int(leia_min_date) and \
                utils.get_kodi_major_version() >= 18:
            utils.dialog(
                'Kodi 18 build is too old',
                'The minimum Kodi 18 build required for DASH/DRM support is '
                'dated {0} with commit hash {1}. Your installation is dated '
                '{2}. Please update your Kodi installation and try again.'
                ''.format(min_date, min_commit, date))
            return False
        return True

    def check_inputstream(self, drm=True):
        """Check InputStream Adaptive is installed and ready

        Main function call to check all components required are available for
        DRM playback before setting the resolved URL in Kodi.
        drm -- set to false if you just want to check for inputstream.adaptive
        and not widevine components eg. HLS playback
        """
        # DRM not supported
        if drm and not self.is_wv_drm_supported():
            utils.log('DRM not supported')
            return False

        # Kodi version too old
        if drm and utils.get_kodi_major_version() < 18:
            utils.dialog(
                'Kodi version not supported for DRM',
                'This version of Kodi is not currently supported for viewing '
                'DRM encrypted content. Please upgrade to Kodi v18.')
            return False

        addon = self.get_addon()
        if not addon:
            utils.dialog(
                'Missing inputstream.adaptive add-on',
                'inputstream.adaptive VideoPlayer InputStream add-on not '
                'found or not enabled. This add-on is required to view DRM '
                'protected content.')
            return False

        # checking for installation of inputstream.adaptive (eg HLS playback)
        if not drm:
            utils.log('DRM checking not requested')
            return True

        # only 32bit userspace supported for linux aarch64 no 64bit wvcdm
        if self._get_platform() == ('Linux', 'aarch64'):
            if self._get_kodi_arch() == '64bit':
                utils.dialog(
                    '64 bit build for aarch64 not supported',
                    'A build of your OS that supports 32 bit userspace '
                    'binaries is required for DRM playback. We recommend '
                    'CoreELEC to support this.')

        cdm_paths = [
            xbmc.translatePath(addon.getSetting('DECRYPTERPATH')),
            xbmc.translatePath('special://xbmc/addons/inputstream.adaptive'),
            xbmc.translatePath('special://home/addons/inputstream.adaptive'),
            xbmc.translatePath('special://xbmcbinaddons/inputstream.adaptive')
        ]
        cdm_fn = self._get_wvcdm_filename()

        resolved_paths = [(os.path.join(p, cdm_fn)) for p in cdm_paths]
        utils.log("Resolved CDM paths: {0}".format(resolved_paths))
        if not any(os.path.isfile(p) for p in resolved_paths):
            if utils.dialog_yn(
                'Missing Widevine module',
                '{0} not found in any expected location.'.format(cdm_fn),
                'Do you want to attempt downloading the missing '
                    'Widevine CDM module to your system for DRM support?'):
                self._get_wvcdm(cdm_paths[0])  # Use first path
            else:
                # TODO(andy): Ask to never attempt again
                return False

        # SSD
        ssd_fn = self._get_ssd_filename()
        if not any(os.path.isfile(os.path.join(p, ssd_fn)) for p in cdm_paths):
            utils.dialog(
                'Missing Widevine SSD module',
                '{0} not found in any expected location.'.format(ssd_fn),
                'ssd_wv module is supplied with Windows/Mac/LibreELEC, '
                'and can be installed from most package managers in Linux '
                'eg. "apt install kodi-inputstream-adaptive"')
            return False

        return True

    def _unzip_cdm(self, zpath, cdm_path):
        """Extract windows widevinecdm.dll from downloaded zip"""
        cdm_fn = posixpath.join(cdm_path, self._get_wvcdm_filename())
        utils.log('unzipping widevinecdm.dll from {0} to {1}'
                  ''.format(zpath, cdm_fn))
        with zipfile.ZipFile(zpath) as zf:
            with open(cdm_fn, 'wb') as f:
                data = zf.read('widevinecdm.dll')
                f.write(data)
        os.remove(zpath)

    def _get_wvcdm(self, cdm_path=None):
        """Get the Widevine CDM library

        Win/Mac: download Chrome extension blob ~2MB and extract
        widevinecdm.dll
        Linux: download Chrome package ~50MB and extract libwidevinecdm.so
        Linux arm: download widevine package ~2MB from 3rd party host
        """
        if not cdm_path:
            addon = self.get_addon()
            if not addon:
                utils.dialog(
                    'inputstream.adaptive not found'
                    'inputstream.adaptive add-on must be installed '
                    'before installing widevide_cdm module')
                return

            cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

        if self._is_android():
            utils.dialog('Not available',
                         'This module cannot be updated on Android')
            return

        plat = self._get_platform()
        current_cdm_ver = requests.get(config.CMD_CURRENT_VERSION_URL).text
        url = config.WIDEVINE_CDM_URL[plat].format(current_cdm_ver)
        filename = url.split('/')[-1]
        wv_cdm_fn = self._get_wvcdm_filename()

        if not os.path.isdir(cdm_path):
            utils.log('Creating directory: {0}'.format(cdm_path))
            os.makedirs(cdm_path)
        cdm_fn = os.path.join(cdm_path, wv_cdm_fn)
        if os.path.isfile(cdm_fn):
            utils.log('Removing existing widevine_cdm: {0}'.format(cdm_fn))
            os.remove(cdm_fn)
        download_path = os.path.join(cdm_path, filename)
        if not self._progress_download(url, download_path, wv_cdm_fn):
            return

        dp = xbmcgui.DialogProgress()
        dp.create('Extracting {0}'.format(wv_cdm_fn),
                  'Extracting {0} from {1}'.format(wv_cdm_fn, filename))
        dp.update(0)

        if self._is_windows():
            self._unzip_cdm(download_path, cdm_path)
        else:
            command = config.UNARCHIVE_COMMAND[plat].format(
                quote(filename), quote(cdm_path),
                config.WIDEVINE_CDM_DICT[self._get_system()])
            utils.log('executing command: {0}'.format(command))
            output = os.popen(command).read()
            utils.log('command output: {0}'.format(output))
        dp.close()
        # TODO(andy): Test it was actually successful. Can be cancelled
        utils.dialog(
            'Success',
            '{0} successfully installed at {1}'.format(
                wv_cdm_fn, os.path.join(cdm_path, wv_cdm_fn)))

    def _progress_download(self, url, download_path, display_filename=None):
        """Progress download

        Download file in Kodi with progress bar
        """
        utils.log('Downloading {0}'.format(url))
        try:
            res = requests.get(url, stream=True, verify=False)
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            utils.dialog('Download failed',
                         'HTTP ' + str(res.status_code) + ' error')
            return False
        except Exception as exc:
            utils.dialog('Download failed',
                         'Exception was: {0}'.format(exc))
            return False

        total_length = float(res.headers.get('content-length'))
        dp = xbmcgui.DialogProgress()
        if not display_filename:
            display_filename = download_path.split()[-1]
        dp.create("Downloading {0}".format(display_filename),
                  "Downloading File", url)

        with open(download_path, 'wb') as f:
            chunk_size = 1024
            downloaded = 0
            for chunk in res.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                percent = int(downloaded*100/total_length)
                if dp.iscanceled():
                    dp.close()
                    res.close()
                dp.update(percent)
        utils.log('Download {0} bytes complete, saved in {1}'.format(
            int(total_length), download_path))
        dp.close()
        return True

    def _get_ia_direct(self, update=False, drm=True):
        """Get IA direct

        Download inputstream.adaptive zip file from remote repository and save
        in Kodi's 'home' folder, unzip to addons folder.
        """
        utils.dialog('No longer supported',
                     'This feature is no longer supported. Please upgrade '
                     'your Kodi installation to a newer v18 build, or for '
                     'Linux installations you should be able to obtain '
                     'from your package manager eg. '
                     '"sudo apt update && sudo apt install kodi-inputstream'
                     '-adaptive"')
