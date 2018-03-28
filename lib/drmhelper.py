import os
import re
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

# dummy request first for this infolabel, sometimes returns 'Busy'
xbmc.getInfoLabel('System.OSVersionInfo')
xbmc.sleep(100)

version_info = xbmc.getInfoLabel('System.OSVersionInfo')

if xbmc.getCondVisibility('system.platform.android'):
    system_ = 'Android'

try:
    machine = platform.machine()
    if machine[:3] == 'arm':
        machine = machine[:5]
    arch = drmconfig.ARCH_DICT.get(machine, 'NS')
except:
    arch = 'NS'

if system_ == 'Windows':
    try:
        arch = drmconfig.WINDOWS_BITNESS[platform.architecture()[0]]
    except:
        arch = 'Xbox One'

plat = '{0}-{1}'.format(system_, arch)

if plat in drmconfig.SUPPORTED_PLATFORMS:
    supported = True
    if system_ != 'Android':
        ssd_filename = drmconfig.SSD_WV_DICT[system_]
        widevinecdm_filename = drmconfig.WIDEVINECDM_DICT[system_]
else:
    supported = False


def log(message):
    """
    Log message to kodi.log
    """
    ver = xbmcaddon.Addon('script.module.drmhelper').getAddonInfo('version')
    xbmc.log('[DRMHELPER {0}] - {1}'.format(ver, message), xbmc.LOGNOTICE)


def is_libreelec():
    if 'LibreELEC' in version_info:
        return True
    return False


def get_kodi_version():
    """
    Return plain version number as string
    """
    fullver = xbmc.getInfoLabel("System.BuildVersion").split(' ')[0]
    ver = fullver[:fullver.find('-')]
    return ver


def get_kodi_name():
    """
    Returns Kodi codename
    """
    return drmconfig.KODI_NAME[get_kodi_version()[:2]]


def get_kodi_build():
    """
    Return Kodi build date
    """
    try:
        build_string = xbmc.getInfoLabel("System.BuildVersion").split(' ')[1]
    except IndexError:
        return None
    m = re.search('\d{8}', build_string)
    if m:
        return m.group(0)
    else:
        return m


def get_latest_ia_ver():
    """
    Return dict containing info for latest compiled inputstream.adaptive
    addon in the binary repo
    """
    kodi = get_kodi_name()
    return drmconfig.CURRENT_IA_VERSION[kodi]


def is_ia_current(addon, latest=False):
    """
    Check if inputstream.adaptive addon meets the minimum version requirements.
    latest -- checks if addon is equal to the latest available compiled version
    """
    if not addon:
        return False
    ia_ver = addon.getAddonInfo('version')
    if latest:
        ver = get_latest_ia_ver()['ver']
    else:
        ver = drmconfig.MIN_IA_VERSION[get_kodi_name()]
    return LooseVersion(ia_ver) >= LooseVersion(ver)


def get_addon(drm=True):
    """
    Check if inputstream.adaptive is installed, attempt to install if not.
    Enable inpustream.adaptive addon.
    """
    def manual_install(update=False):
        if get_ia_direct(update, drm):
            try:
                addon = xbmcaddon.Addon('inputstream.adaptive')
                return addon
            except RuntimeError:
                return None

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
        log('inputstream.adaptive not currently installed')
        try:  # see if there's an installed repo that has it
            xbmc.executebuiltin('InstallAddon(inputstream.adaptive)', True)
            addon = xbmcaddon.Addon('inputstream.adaptive')
            log('inputstream.adaptive installed from repo')
        except RuntimeError:
            if xbmcgui.Dialog().yesno('inputstream.adaptive not in repo',
                                      'inputstream.adaptive not found in '
                                      'any installed repositories. Would '
                                      'you like to download the zip for '
                                      'your system from a direct link '
                                      'and install?'):
                addon = manual_install()
            if not addon:
                log('Manual install failed/user selected no')
                return False

    else:  # installed but not enabled. let's enable it.
        if result['result']['addon'].get('enabled') is False:
            log('inputstream.adaptive not enabled, enabling...')
            json_string = ('{"jsonrpc":"2.0","id":1,"method":'
                           '"Addons.SetAddonEnabled","params":'
                           '{"addonid":"inputstream.adaptive",'
                           '"enabled":true}}')
            try:
                xbmc.executeJSONRPC(json_string)
            except RuntimeError:
                log('Failure in enabling inputstream.adaptive')
                return False
        addon = xbmcaddon.Addon('inputstream.adaptive')

    if not is_ia_current(addon):
        if xbmcgui.Dialog().yesno('inputstream.adaptive version lower than '
                                  'required', 'inputstream.adaptive version '
                                  'does not meet requirements. Would '
                                  'you like to download the zip for '
                                  'the required version from a direct link '
                                  'and reinstall?'):
            addon = manual_install(update=True)
        else:
            log('inputstream.adaptive version lower than required, aborting..')
            return False
    return addon


def is_supported():
    """
    Reads the value of 'supported' global variable and displays a helpful
    message to the user if on an unsupported platform.
    """
    if not supported:
        xbmcgui.Dialog().ok('Platform not supported',
                            '{0} {1} not supported for DRM playback'.format(
                                system_, arch))
        log('{0} {1} not supported for DRM playback'.format(
            system_, arch))
        return False
    return True


def check_inputstream(drm=True):
    """
    Main function call to check all components required are available for
    DRM playback before setting the resolved URL in Kodi.
    drm -- set to false if you just want to check for inputstream.adaptive
        and not widevine components eg. HLS playback
    """
    try:
        ver = get_kodi_version()
        log('Kodi version: {0}'.format(ver))
        if float(ver) < 17.0:
            xbmcgui.Dialog().ok('Kodi 17+ Required',
                                ('The minimum version of Kodi required for '
                                 'DASH/DRM protected content is 17.0 - please '
                                 'upgrade in order to use this feature.'))
            return False
    except ValueError:  # custom builds of Kodi may not follow same convention
        pass

    date = get_kodi_build()
    if not date:  # can't find build date, assume meets minimum
        log('Could not determine date of build, assuming date meets minimum. '
            'Build string is {0}'
            ''.format(xbmc.getInfoLabel("System.BuildVersion")))
        date = drmconfig.MIN_LEIA_BUILD[0]

    log('Build date: {0}'.format(date))
    log('System: {0}'.format(system_))
    log('Arch: {0}'.format(arch))

    min_date, min_commit = drmconfig.MIN_LEIA_BUILD
    if int(date) < int(min_date) and float(get_kodi_version()) >= 18.0:
        xbmcgui.Dialog().ok('Kodi 18 build is outdated',
                            ('The minimum Kodi 18 build required for DASH/DRM '
                             'support is dated {0} with commit hash {1}. '
                             'Your installation is dated {2}.'
                             'Please update your Kodi installation '
                             'and try again.'.format(
                                min_date, min_commit, date)))
        return False

    if not is_supported() and drm:
        return False

    addon = get_addon()
    if not addon:
        xbmcgui.Dialog().ok('Missing inputstream.adaptive add-on',
                            ('inputstream.adaptive VideoPlayer InputStream '
                             'add-on not found or not enabled. This add-on '
                             'is required to view DRM protected content.'))
        return False

    # widevine built into android - not supported on 17 atm though
    if xbmc.getCondVisibility('system.platform.android'):
        log('Running on Android')
        if get_kodi_version()[:2] == '17' and drm:
            xbmcgui.Dialog().ok('Kodi 17 on Android not supported',
                                ('Kodi 17 is not currently supported for '
                                 'Android with encrypted content. Nightly '
                                 'builds of Kodi 18 are available to download '
                                 'from http://mirrors.kodi.tv/nightlies/androi'
                                 'd/arm/master/'))
            log('Kodi 17 Android DRM - not supported')
            return False
        return True

    # ??? not sure if ios has widevine support, assuming so for now ???
    if xbmc.getCondVisibility('system.platform.ios'):
        log('Running on iOS')
        return True

    # only checking for installation of inputstream.adaptive (eg HLS playback)
    if not drm:
        log('DRM checking not requested')
        return True

    # only 32bit userspace supported for linux aarch64 - no 64bit widevinecdm
    if plat == 'Linux-aarch64':
        if platform.architecture()[0] == '64bit':
            log('Running on Linux aarch64 64bit userspace - not supported')
            xbmcgui.Dialog().ok('64 bit build for aarch64 not supported',
                                ('A build of your OS that supports 32 bit '
                                 'userspace binaries is required for DRM '
                                 'playback. Special builds of LibreELEC '
                                 'for your platform may be available from '
                                 'the LibreELEC forums user Raybuntu '
                                 'for this.'))

    cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

    if not os.path.isfile(os.path.join(cdm_path, widevinecdm_filename)):
        log('Widevine CDM missing')
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
        log('SSD module not found')
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
    extract windows widevinecdm.dll from downloaded zip
    """
    cdm_fn = posixpath.join(cdm_path, widevinecdm_filename)
    log('unzipping widevinecdm.dll from {0} to {1}'.format(zpath, cdm_fn))
    with zipfile.ZipFile(zpath) as zf:
        with open(cdm_fn, 'wb') as f:
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
        log('Widevinecdm update - not possible on Android')
        xbmcgui.Dialog().ok('Not required for Android',
                            'This module cannot be updated on Android')
        return

    url = drmconfig.WIDEVINECDM_URL[plat]
    filename = url.split('/')[-1]

    if not os.path.isdir(cdm_path):
        log('Creating directory: {0}'.format(cdm_path))
        os.makedirs(cdm_path)
    cdm_fn = os.path.join(cdm_path, widevinecdm_filename)
    if os.path.isfile(cdm_fn):
        log('Removing existing widevine_cdm: {0}'.format(cdm_fn))
        os.remove(cdm_fn)
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
        command = drmconfig.UNARCHIVE_COMMAND[plat].format(
            quote(filename),
            quote(cdm_path),
            drmconfig.WIDEVINECDM_DICT[system_])
        log('executing command: {0}'.format(command))
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
        log('ssd_wv update - not possible on Android')
        xbmcgui.Dialog().ok('Not required for Android',
                            'This module cannot be updated on Android')
        return

    if system_ == 'Linux' and not is_libreelec():
        log('ssd_wv update - not possible on linux other than LibreELEC')
        xbmcgui.Dialog().ok('Not Available for this OS',
                            'This method is not available for installation '
                            'on Linux distributions other than LibreELEC. '
                            'Try installing kodi-inputstream-adaptive '
                            'package from your terminal (eg Ubuntu. sudo apt '
                            'install kodi-inputstream-adaptive).')
        return

    if not os.path.isdir(cdm_path):
        log('Creating directory: {0}'.format(cdm_path))
        os.makedirs(cdm_path)
    ssd = os.path.join(cdm_path, ssd_filename)
    # preserve link for addons/inputstream.adaptive/lib
    if os.path.islink(ssd):
        download_path = os.path.realpath(ssd)
        download_dir = os.path.dirname(download_path)
        if not os.path.isdir(download_dir):
            log('Creating directory: {0}'.format(download_dir))
            os.makedirs(download_dir)
    else:
        download_path = os.path.join(cdm_path, ssd_filename)
    if os.path.isfile(download_path):
        log('Removing existing ssd_wv: {0}'.format(download_path))
        os.remove(download_path)

    try:
        kodi = drmconfig.KODI_NAME[get_kodi_version()[:2]]
    # custom builds (SPMC etc.) might have something else here, let's assume
    # Krypton for now
    except KeyError:
        kodi = 'Krypton'
    commit = drmconfig.CURRENT_IA_VERSION[kodi]['commit']
    ssdfn, ssdext = ssd_filename.split('.')[0], ssd_filename.split('.')[1]
    url = '{base}{kodi}/{plat}-{ssdfn}-{commit}.{ssdext}'.format(
        base=drmconfig.REPO_BASE,
        kodi=kodi,
        plat=plat.lower(),
        ssdfn=ssdfn,
        commit=commit,
        ssdext=ssdext)

    if not progress_download(url, download_path, ssd_filename):
        return
    os.chmod(download_path, 0755)
    xbmcgui.Dialog().ok(
        'Success', ('{fn} version {commit} for Kodi {kodi} '
                    'successfully installed at {path}'.format(
                        fn=ssd_filename,
                        commit=commit,
                        kodi=kodi,
                        path=download_path)))


def progress_download(url, download_path, display_filename=None):
    """
    Download file in Kodi with progress bar
    """
    log('Downloading {0}'.format(url))
    try:
        res = requests.get(url, stream=True, verify=False)
        res.raise_for_status()
    except requests.exceptions.HTTPError:
        xbmcgui.Dialog().ok('Download failed',
                            'HTTP ' + str(res.status_code) + ' error')
        log('Error retrieving {0}'.format(url))

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
    log('Download {0} bytes complete, saved in {1}'.format(
        int(total_length), download_path))
    dp.close()
    return True


def get_ia_direct(update=False, drm=True):
    """
    Download inputstream.adaptive zip file from remote repository and save in
    Kodi's 'home' folder, unzip to addons folder.
    """
    if not is_supported():
        return False

    if system_ == 'Linux' and not is_libreelec():
        log('inputstream.adaptive update not possible on this Linux distro')
        xbmcgui.Dialog().ok('Not Available for this OS',
                            'This method is not available for installation '
                            'on Linux distributions other than LibreELEC. '
                            'Try installing/updating kodi-inputstream-adaptive'
                            ' package from your terminal (eg Ubuntu: sudo apt '
                            'install kodi-inputstream-adaptive).')
        return False

    try:
        kodi = drmconfig.KODI_NAME[get_kodi_version()[:2]]
    # custom builds (SPMC etc.) might have something else here, let's assume
    # Krypton for now
    except KeyError:
        kodi = 'Krypton'
    ver = drmconfig.CURRENT_IA_VERSION[kodi]['ver']
    commit = drmconfig.CURRENT_IA_VERSION[kodi]['commit']

    log('Attempting manual install of inputstream.adaptive (update={0}, '
        'drm={1}, kodi={2})'.format(str(update), str(drm), kodi))

    url = '{base}{kodi}/{plat}-inputstream.adaptive-{ver}-{commit}.zip'.format(
        base=drmconfig.REPO_BASE,
        kodi=kodi,
        plat=plat.lower(),
        ver=ver,
        commit=commit)

    filename = url.split('/')[-1]
    location = os.path.join(xbmc.translatePath('special://home'), filename)
    if not progress_download(url, location, filename):
        xbmcgui.Dialog().ok('Download Failed', 'Failed to download {0} from '
                            '{1}'.format(filename, url))
        return False
    else:
        try:
            with zipfile.ZipFile(location, "r") as z:
                addons_path = os.path.join(
                    xbmc.translatePath('special://home'), 'addons')
                if update:
                    ia_path = os.path.join(addons_path, 'inputstream.adaptive')
                    if os.path.isdir(ia_path):
                        shutil.rmtree(ia_path)
                    os.mkdir(ia_path)

                z.extractall(addons_path)
            xbmc.executebuiltin('UpdateLocalAddons', True)
            #  enable addon, seems to default to disabled
            json_string = ('{"jsonrpc":"2.0","id":1,"method":'
                           '"Addons.SetAddonEnabled","params":'
                           '{"addonid":"inputstream.adaptive",'
                           '"enabled":true}}')
            xbmc.executeJSONRPC(json_string)
            xbmcgui.Dialog().ok(
                'Installation complete',
                ('inputstream.adaptive version {ver} commit '
                 '{commit} for Kodi {kodi} installed.'.format(
                     ver=ver,
                     commit=commit,
                     kodi=kodi)))
        except Exception as e:
            xbmcgui.Dialog().ok('Unzipping failed',
                                'Unzipping failed error {0}'.format(e))
        os.remove(location)
        if drm:
            if xbmcgui.Dialog().yesno(
                'Download ssd_wv module?',
                ('Would you like to update the corresponding '
                 'ssd_wv module? (recommended if updating '
                 ' inputstream.adaptive)')):
                get_ssd_wv()
        return True
