# Copyright 2016 Glenn Guy
# This file is part of 9now Kodi Addon
#
# tenplay is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 9now is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 9now.  If not, see <http://www.gnu.org/licenses/>.

import os
import posixpath
import xbmc
import xbmcgui
import xbmcaddon
import drmconfig
import platform
import requests
import json
import zipfile
import shutil
from pipes import quote
from distutils.version import LooseVersion

system_ = platform.system()
arch = platform.machine()
if arch[:3] == 'arm':
    arch = arch[:5]

if system_ == 'Windows':
    arch = drmconfig.WINDOWS_BITNESS[platform.architecture()[0]]

if system_+arch in drmconfig.SUPPORTED_PLATFORMS:
    supported = True
    ssd_filename = drmconfig.SSD_WV_DICT[system_]
    widevinecdm_filename = drmconfig.WIDEVINECDM_DICT[system_]
else:
    supported = False


def get_kodi_version():
    """
    Return plain version number as string
    """
    fullver = xbmc.getInfoLabel("System.BuildVersion").split(' ')[0]
    ver = fullver[:fullver.find('-')]
    return ver


def get_kodi_date():
    """
    Return Kodi git date from build
    """
    git_string = xbmc.getInfoLabel("System.BuildVersion").split(' ')[1]
    date = git_string[git_string.find(':')+1:git_string.find('-')]
    return date


def get_addon():
    """
    Check if inputstream.adaptive is installed, attempt to install if not.
    Enable inpustream.adaptive addon.
    """
    def manual_install(update=False):
        if get_ia_direct(update):
            try:
                addon = xbmcaddon.Addon('inputstream.adaptive')
                return addon
            except RuntimeError:
                return False

    addon = None
    try:
        enabled_json = ('{"jsonrpc":"2.0","id":1,"method":'
                        '"Addons.GetAddonDetails","params":'
                        '{"addonid":"inputstream.adaptive", '
                        '"properties": ["enabled"]}}')
        # is inputstream.adaptive enabled?
        result = json.loads(xbmc.executeJSONRPC(enabled_json))
    except RuntimeError:
        return False

    if 'error' in result:  # not installed
        try:  # see if there's an installed repo that has it
            xbmc.executebuiltin('InstallAddon(inputstream.adaptive)', True)
            addon = xbmcaddon.Addon('inputstream.adaptive')
        except RuntimeError:
            if xbmcgui.Dialog().yesno('inputstream.adaptive not in repo',
                                      'inputstream.adaptive not found in '
                                      'any installed repositories. Would '
                                      'you like to download the zip for '
                                      'your system from a direct link '
                                      'and install?'):
                addon = manual_install()

    else:  # installed but not enabled. let's enable it.
        if result['result']['addon'].get('enabled') is False:
            json_string = ('{"jsonrpc":"2.0","id":1,"method":'
                           '"Addons.SetAddonEnabled","params":'
                           '{"addonid":"inputstream.adaptive",'
                           '"enabled":true}}')
            try:
                xbmc.executeJSONRPC(json_string)
            except RuntimeError:
                return False
        addon = xbmcaddon.Addon('inputstream.adaptive')

    ia_ver = addon.getAddonInfo('version')
    if LooseVersion(ia_ver) < LooseVersion(
        drmconfig.MIN_IA_VERSION[get_kodi_version()[:2]]):
        if xbmcgui.Dialog().yesno('inputstream.adaptive version lower than '
                                  'required', 'inputstream.adaptive version '
                                  'does not meet requirements. Would '
                                  'you like to download the zip for '
                                  'the required version from a direct link '
                                  'and reinstall?'):
            addon = manual_install(update=True)
    return addon


def is_supported():
    """
    Returns true if we're on a platform that has a cdm module and
    can interface with the decrypter module.
    i.e not armv6 (RPi1)
    """
    # Android now supported
    if xbmc.getCondVisibility('system.platform.android'):
        return True

    if not supported:
        xbmcgui.Dialog().ok('OS/Arch not supported',
                            '{0} {1} not supported for DRM playblack'.format(
                                system_, arch))
        xbmc.log('{0} {1} not supported for DRM playback'.format(
            system_, arch), xbmc.LOGNOTICE)
        return False
    return True


def check_inputstream():
    """
    Main function call to check all components required are available for
    DRM playback before setting the resolved URL in Kodi.
    """
    try:
        ver = get_kodi_version()
        if ver < 17.0:
            xbmcgui.Dialog().ok('Kodi 17+ Required',
                                ('The minimum version of Kodi required for DRM'
                                 'protected content is 17.0 - please upgrade '
                                 'in order to use this feature.'))
            return False
    except ValueError:  # custom builds of Kodi may not follow same convention
        pass

    if not is_supported():
        return False

    addon = get_addon()
    if not addon:
        xbmcgui.Dialog().ok('Missing inputstream.adaptive add-on',
                            ('inputstream.adaptive VideoPlayer InputStream '
                             'add-on not found or not enabled. This add-on '
                             'is required to view DRM protected content.'))
        return False

    if xbmc.getCondVisibility('system.platform.android'):
        return True

    cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

    if not os.path.isfile(os.path.join(cdm_path, widevinecdm_filename)):
        msg1 = 'Missing widevinecdm module required for DRM content'
        msg2 = '{0} not found in {1}'.format(
            drmconfig.WIDEVINECDM_DICT[system_],
            xbmc.translatePath(addon.getSetting('DECRYPTERPATH')))
        msg3 = ('Do you want to attempt downloading the missing widevinecdm '
                'module for your system?')
        if xbmcgui.Dialog().yesno(msg1, msg2, msg3):
            get_widevinecdm(cdm_path)
        else:
            return False

    if not os.path.isfile(os.path.join(cdm_path, ssd_filename)):
        msg1 = 'Missing ssd_wv module required for DRM content'
        msg2 = '{0} not found in {1}'.format(
            drmconfig.SSD_WV_DICT[system_],
            xbmc.translatePath(addon.getSetting('DECRYPTERPATH')))
        msg2 = ('Do you want to attempt downloading the missing ssd_wv '
                'module for your system?')
        if xbmcgui.Dialog().yesno(msg1, msg2):
            get_ssd_wv(cdm_path)
        else:
            return False
    return True


def unzip_cdm(zpath, cdm_path):
    """
    extract windows 32bit widevinecdm.dll from downloaded zip
    """
    with zipfile.ZipFile(zpath) as zf:
        with open(posixpath.join(cdm_path, widevinecdm_filename), 'wb') as f:
            data = zf.read('widevinecdm.dll')
            f.write(data)
    os.remove(zpath)


def get_widevinecdm(cdm_path=None):
    """
    Win/Mac: download Chrome extension blob ~2MB and extract widevinecdm.dll
    Linux: download Chrome package ~50MB and extract libwidevinecdm.so
    Linux arm: download widevine package ~2MB from 3rd party host
    """
    if not cdm_path:
        addon = get_addon()
        if not addon:
            xbmcgui.Dialog().ok('inputstream.adaptive not found',
                                'inputstream.adaptive add-on must be installed'
                                ' before installing widevide_cdm module')
            return
        cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

    if xbmc.getCondVisibility('system.platform.android'):
        xbmcgui.Dialog().ok('Not required for Android',
                            'This module is not required for Android')
        return

    url = drmconfig.WIDEVINECDM_URL[system_+arch]
    filename = url.split('/')[-1]

    if not os.path.isdir(cdm_path):
        os.makedirs(cdm_path)
    if os.path.isfile(os.path.join(cdm_path, widevinecdm_filename)):
        os.remove(os.path.join(cdm_path, widevinecdm_filename))

    download_path = os.path.join(cdm_path, filename)
    if not progress_download(url, download_path, widevinecdm_filename):
        return

    dp = xbmcgui.DialogProgress()
    dp.create('Extracting {0}'.format(widevinecdm_filename),
              'Extracting {0} from {1}'.format(widevinecdm_filename, filename))
    dp.update(0)

    if system_ == 'Windows':
        unzip_cdm(download_path, cdm_path)
    else:
        command = drmconfig.UNARCHIVE_COMMAND[system_+arch].format(
            quote(filename),
            quote(cdm_path),
            drmconfig.WIDEVINECDM_DICT[system_])
        os.system(command)
    dp.close()
    xbmcgui.Dialog().ok('Success', '{0} successfully installed at {1}'.format(
        widevinecdm_filename, os.path.join(cdm_path, widevinecdm_filename)))


def get_ssd_wv(cdm_path=None):
    """
    Download compiled ssd_wv from github repository
    """
    if not cdm_path:
        addon = get_addon()
        if not addon:
            xbmcgui.Dialog().ok('inputstream.adaptive not found',
                                'inputstream.adaptive add-on must be installed'
                                ' before installing ssd_wv module')
            return
        cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

    if xbmc.getCondVisibility('system.platform.android'):
        xbmcgui.Dialog().ok('Not required for Android',
                            'This module is not required for Android')
        return

    if not os.path.isdir(cdm_path):
        os.makedirs(cdm_path)
    ssd = os.path.join(cdm_path, ssd_filename)
    if os.path.islink(ssd):
        download_path = os.path.realpath(ssd)
    else:
        download_path = os.path.join(cdm_path, ssd_filename)
    if os.path.isfile(download_path):
        os.remove(download_path)
    url = posixpath.join(drmconfig.SSD_WV_REPO, system_, arch, ssd_filename)
    if not progress_download(url, download_path, ssd_filename):
        return
    os.chmod(download_path, 0755)
    xbmcgui.Dialog().ok('Success', '{0} successfully installed at {1}'.format(
        ssd_filename, download_path))


def progress_download(url, download_path, display_filename=None):
    """
    Download file in Kodi with progress bar
    """
    xbmc.log('Downloading {0}'.format(url), xbmc.LOGNOTICE)
    try:
        res = requests.get(url, stream=True, verify=False)
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        xbmcgui.Dialog().ok('Download failed',
                            'HTTP ' + str(res.status_code) + ' error')
        xbmc.log('Error retrieving {0}'.format(url), level=xbmc.LOGNOTICE)

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
    xbmc.log('Download {0} bytes complete, saved in {1}'.format(
        int(total_length), download_path), xbmc.LOGNOTICE)
    dp.close()
    return True


def get_ia_direct(update=False):
    """
    Download inputstream.adaptive zip file from remote repository and save in
    Kodi's 'home' folder, unzip to addons folder.
    """
    if not is_supported():
        return False

    url = drmconfig.ADAPTIVE_URL[system_+arch]
    filename = url.split('/')[-1]
    location = os.path.join(xbmc.translatePath('special://home'), filename)
    xbmc.log(location, level=xbmc.LOGDEBUG)
    if not progress_download(url, location, filename):
        xbmcgui.Dialog().ok('Download Failed', 'Failed to download {0} from '
                            '{1}'.format(filename, url))
        return False
    else:
        try:
            with zipfile.ZipFile(location, "r") as z:
                ia_path = os.path.join(xbmc.translatePath('special://home'),
                                       'addons')
                if update:
                    shutil.rmtree(
                        os.path.join(ia_path, 'inputstream.adaptive'))
                z.extractall(ia_path)
            xbmc.executebuiltin('UpdateLocalAddons', True)
            #  enable addon, seems to default to disabled
            json_string = ('{"jsonrpc":"2.0","id":1,"method":'
                           '"Addons.SetAddonEnabled","params":'
                           '{"addonid":"inputstream.adaptive",'
                           '"enabled":true}}')
            xbmc.executeJSONRPC(json_string)
            xbmcgui.Dialog().ok('Installation complete',
                                'inputstream.adaptive installed.')
        except Exception as e:
            xbmcgui.Dialog().ok('Unzipping failed',
                                'Unzipping failed error {0}'.format(e))
        os.remove(location)
        return True
