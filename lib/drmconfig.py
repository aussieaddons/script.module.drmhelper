# flake8: noqa

SSD_WV_REPO = "https://github.com/glennguy/decryptmodules/raw/master/"

WIDEVINECDM_URL = {'Linuxx86_64': 'https://dl.google.com/widevine-cdm/903-linux-x64.zip',
                   'Linuxarmv7': 'http://odroidxu.leeharris.me.uk/xu3/chromium-widevine-1.4.8.823-2-armv7h.pkg.tar.xz',
                   'Linuxarmv8': 'http://odroidxu.leeharris.me.uk/xu3/chromium-widevine-1.4.8.823-2-armv7h.pkg.tar.xz',
                   'WindowsAMD64': 'https://dl.google.com/widevine-cdm/903-win-x64.zip',
                   'Windowsx86': 'https://dl.google.com/widevine-cdm/903-win-ia32.zip',
                   'Darwinx86_64': 'https://dl.google.com/widevine-cdm/903-mac-x64.zip'}

UNARCHIVE_COMMAND = {'Linuxx86_64': "(cd {1} && unzip {0} {2} -d {1} && chmod 755 {1}/{2} && rm -f {0})",
                     'Linuxarmv7': "(cd {1} && tar xJfO {0} usr/lib/chromium/libwidevinecdm.so >{1}/{2} && chmod 755 {1}/{2} && rm -f {0})",
                     'Linuxarmv8': "(cd {1} && tar xJfO {0} usr/lib/chromium/libwidevinecdm.so >{1}/{2} && chmod 755 {1}/{2} && rm -f {0})",
                     'Darwinx86_64': '(cd {1} && unzip {0} {2} -d {1} && chmod 755 {1}/{2} && rm -f {0})'}

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

ADAPTIVE_URL = {'WindowsAMD64': 'https://github.com/vdrtuxnet/binary-repo/raw/master/WIN_32/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Windowsx86': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/win_32/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Darwinx86_64': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/osx_64/inputstream.adaptive/inputstream.adaptive-1.0.7.zip',
                        'Linuxx86_64': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/linux_x68_64/inputstream.adaptive/inputstream.adaptive-1.0.8.1.zip',
                        'Linuxarmv7': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/armv7/inputstream.adaptive/inputstream.adaptive-1.0.8.zip',
                        'Linuxarmv8': 'https://github.com/glennguy/binary-repo-test/raw/master/kodi-17/armv7/inputstream.adaptive/inputstream.adaptive-1.0.8.zip'}

MIN_IA_VERSION = '1.0.7'