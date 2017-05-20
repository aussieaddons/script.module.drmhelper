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
import hashlib
import uuid
import xml.etree.ElementTree as ET
import random
import zipfile

system_ = platform.system()
arch = platform.machine()
if arch[:3] == 'arm':
    arch = arch[:5]

if system_+arch in drmconfig.SUPPORTED_PLATFORMS:
    supported = True
    ssd_filename = drmconfig.SSD_WV_DICT[system_]
    widevinecdm_filename = drmconfig.WIDEVINECDM_DICT[system_]
else:
    supported = False


def get_addon():
    """
    Check if inputstream.adaptive is installed, attempt to install if not.
    Enable inpustream.adaptive addon.
    """
    try:
        addon = None
        enabled_json = ('{"jsonrpc":"2.0","id":1,"method":'
                        '"Addons.GetAddonDetails","params":'
                        '{"addonid":"inputstream.adaptive", '
                        '"properties": ["enabled"]}}')
        result = json.loads(xbmc.executeJSONRPC(enabled_json))
        if 'error' in result:
            try:
                xbmc.executebuiltin('InstallAddon(inputstream.adaptive)')
                addon = xbmcaddon.Addon('inputstream.adaptive')
            except RuntimeError:
                return False
        else:
            if result['result']['addon'].get('enabled') is False:
                json_string = ('{"jsonrpc":"2.0","id":1,"method":'
                               '"Addons.SetAddonEnabled","params":'
                               '{"addonid":"inputstream.adaptive",'
                               '"enabled":true}}')
                xbmc.executeJSONRPC(json_string)
            addon = xbmcaddon.Addon('inputstream.adaptive')
    except RuntimeError:
        return False
    return addon


def check_inputstream():
    """
    Make sure all components required are available for DRM playback.
    Inform of missing components
    """
    addon = get_addon()
    if not addon:
        xbmcgui.Dialog().ok('Missing inputstream.adaptive add-on',
                            ('inputstream.adaptive VideoPlayer InputStream'
                             'add-on not found or not enabled. This add-on '
                             'is required to view DRM protected content.'))
        return False

    if not supported:
        xbmcgui.Dialog().ok('OS/Arch not supported',
                            '{0} {1} not supported for DRM playblack'.format(
                                system_, arch))
        xbmc.log('{0} {1} not supported for DRM playback'.format(
            system_, arch), xbmc.LOGNOTICE)
        return False

    if xbmc.getCondVisibility('system.platform.android'):
        xbmcgui.Dialog().ok('Android not supported',
                            'Android not supported for DRM playblack')
        xbmc.log('Android not supported for DRM playback', xbmc.LOGNOTICE)
        return False

    cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))

    if not os.path.isfile(os.path.join(cdm_path, widevinecdm_filename)):
        msg1 = 'Missing widevinecdm module required for DRM content'
        msg2 = '{0} not found in {1}'.format(
            drmconfig.WIDEVINECDM_DICT[system_],
            xbmc.translatePath(addon.getSetting('DECRYPTERPATH')))
        msg3 = ('Do you want to attempt downloading the missing widevinecdm '
                'module for your system?')
        print type(msg1)
        print type(msg2)
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


def get_crx_url():
    """
    Send Chrome extension update request to google, take first url from
    returned xml data
    """
    if system_ == 'Windows':
        os_ = 'win'
        arch_ = 'x86'
    if system_ == 'Darwin':
        os_ = 'mac'
        arch_ = 'x64'
    xml_data = drmconfig.XML_TEMPLATE.format(uuid.uuid4(), os_, arch_)
    nonce = str(random.randint(0, 4294967296))
    headers = {'content-type': 'application/xml',
               'user-agent': ('Mozilla/5.0 (Windows NT 10.0; WOW64) '
                              'AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/55.0.2883.87 Safari/537.36'),
               'accept-encoding': 'gzip, deflate, br'}
    url = drmconfig.CRX_UPDATE_URL.format(nonce,
                                       hashlib.sha256(xml_data).hexdigest())
    req = requests.post(url, headers=headers, data=xml_data, verify=False)
    root = ET.fromstring(req.text)
    child = root.find('app')
    subchild = child.find('updatecheck')
    sschild = subchild.find('urls')
    elem = sschild.find('url')
    return elem.get('codebase')


def unzip_blob(file, cdm_path):
    """
    extract windows 32bit widevinecdm.dll from crx in path 'file'
    """
    with zipfile.ZipFile(file) as zf:
        print file[:file.find(file.split('/')[-1])]
        with open(posixpath.join(cdm_path, widevinecdm_filename), 'wb') as f:
            if system_ == 'Windows':
                data = zf.read('_platform_specific/win_x86/widevinecdm.dll')
            if system_ == 'Mac':
                data = zf.read(('_platform_specific/mac_x64/'
                                'libwidevinecdm.dylib'))
            f.write(data)
    os.remove(file)


def get_widevinecdm(cdm_path=None):
    """
    Win/Mac: download Chrome extension blob ~2MB and extract widevinecdm.dll
    Linux: download Chrome package ~50MB and extract libwidevinecdm.so
    Linux arm: download widevine package ~2MB from 3rd party host
    """
    if not cdm_path:
        addon = get_addon()
        cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))
    if system_ == 'Windows' or system_ == 'Darwin':
        url = get_crx_url()
        filename = 'wv_blob.zip'
    else:
        url = drmconfig.WIDEVINECDM_URL[system_+arch]
        filename = url.split('/')[-1]
        xbmc.log(filename, level=xbmc.LOGNOTICE)
    if not os.path.isdir(cdm_path):
        os.makedirs(cdm_path)
    if os.path.isfile(os.path.join(cdm_path, widevinecdm_filename)):
        os.remove(os.path.join(cdm_path, widevinecdm_filename))
    download_path = os.path.join(cdm_path, filename)
    if not progress_download(url, download_path, widevinecdm_filename):
        return
    if system_ == 'Windows':  # remove crx header
        with open(download_path, 'rb+') as f:
            data = f.read()
            start_index = data.find(b'\x50\x4b\x03\x04')
            f.seek(0)
            f.write(data[start_index:])
            f.truncate()
    dp = xbmcgui.DialogProgress()
    dp.create('Extracting {0}'.format(widevinecdm_filename),
              'Extracting {0} from {1}'.format(widevinecdm_filename, filename))
    dp.update(0)
    if system_ == 'Windows':
        unzip_blob(download_path, cdm_path)
    else:
        command = drmconfig.UNARCHIVE_COMMAND[system_+arch].format(
            filename, cdm_path, drmconfig.WIDEVINECDM_DICT[system_])
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
        cdm_path = xbmc.translatePath(addon.getSetting('DECRYPTERPATH'))
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


def progress_download(url, download_path, filename):
    """
    Download file in with Kodi progress bar
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
    dp.create("Downloading {0}".format(filename),
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
