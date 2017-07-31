# flake8: noqa

SSD_WV_REPO = "https://github.com/glennguy/decryptmodules/raw/master/"

WIDEVINECDM_URL = {'Linuxx86_64': 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb',
                   'Linuxarmv7': 'http://odroidxu.leeharris.me.uk/xu3/chromium-widevine-1.4.8.823-2-armv7h.pkg.tar.xz',
                   'Linuxarmv7': 'http://odroidxu.leeharris.me.uk/xu3/chromium-widevine-1.4.8.823-2-armv7h.pkg.tar.xz'}

UNARCHIVE_COMMAND = {'Linuxx86_64': "(cd {1} && ar x {0} data.tar.xz && tar xJfO data.tar.xz ./opt/google/chrome/libwidevinecdm.so >{1}/{2} && chmod 755 {1}/{2} && rm -f data.tar.xz {0})",
                     'Linuxarmv7': "(cd {1} && tar xJfO {0} usr/lib/chromium/libwidevinecdm.so >{1}/{2} && chmod 755 {1}/{2} && rm -f {0})",
                     'Linuxarmv8': "(cd {1} && tar xJfO {0} usr/lib/chromium/libwidevinecdm.so >{1}/{2} && chmod 755 {1}/{2} && rm -f {0})"}

SSD_WV_DICT = {'Windows': 'ssd_wv.dll',
               'Linux': 'libssd_wv.so',
               'Darwin': 'libssd_wv.dylib'}

WIDEVINECDM_DICT = {'Windows': 'widevinecdm.dll',
                    'Linux': 'libwidevinecdm.so',
                    'Darwin': 'libwidevinecdm.dylib'}

SUPPORTED_PLATFORMS = ['WindowsAMD64',
                       'Windowsx86',
                       'Darwinx86_64',
                       'Linuxx86_64',
                       'Linuxarmv7',
                       'Linuxarmv8']
                       
WINDOWS_BITNESS = {'x32': 'x86',
                   'x64': 'AMD64'}

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?><request protocol="3.0" 
version="chrome-55.0.2883.87" prodversion="55.0.2883.87" requestid="{{{0}}}" 
lang="en-US" updaterchannel="" prodchannel="" os="{1}" arch="{2}" 
nacl_arch="x86-64" wow64="1"><hw physmemory="12"/><os platform="Windows" 
arch="x86_64" version="10.0.0"/><app appid="oimompecagnajdejgnnjijobebaeigek" 
version="0.0.0.0" installsource="ondemand"><updatecheck/><ping rd="-2" 
ping_freshness=""/></app></request>"""

CRX_UPDATE_URL = "https://clients2.google.com/service/update2?cup2key=6:{0}&cup2hreq={1}"

ADAPTIVE_URL = {'WindowsAMD64': 'https://github.com/vdrtuxnet/binary-repo/raw/master/WIN_32/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Windowsx86': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/win_32/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Darwinx86_64': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/osx_64/inputstream.adaptive/inputstream.adaptive-1.0.7.zip',
                        'Linuxx86_64': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/linux_x68_64/inputstream.adaptive/inputstream.adaptive-1.0.8.1.zip',
                        'Linuxarmv7': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/armv7/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Linuxarmv8': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/armv7/inputstream.adaptive/inputstream.adaptive-1.0.8.zip'}