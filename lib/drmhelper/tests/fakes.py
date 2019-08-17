class FakeAddon(object):
    def __init__(self, id='test.addon'):
        self.id = id
        self.name = 'Test Add-on'
        self.version = '0.0.1'

    def getSetting(self, id):
        return ''

    def setSetting(self, id, value):
        pass

    def openSettings(self):
        pass

    def getAddonInfo(self, key):
        return getattr(self, key)


class FakeMd5(object):
    def __init__(self, *args, **kwagrs):
        self.digest_value = None
        pass

    def hexdigest(self):
        return self.digest_value


# Some systems we support
SYSTEMS = [
    # Linux
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Linux'],
        'machine': 'x86_64',
        'expected_system': 'Linux',
        'expected_arch': 'x86_64',
        'drm_supported': True
    },
    # Generic Windows
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows'],
        'machine': 'AMD64',
        'arch': '32bit',
        'expected_system': 'Windows',
        'expected_arch': 'x86',
        'drm_supported': True
    },
    # Generic Mac OS X
    {
        'system': 'Darwin',
        'platforms': ['System.Platform.OSX'],
        'machine': 'x86_64',
        'expected_system': 'Darwin',
        'expected_arch': 'x86_64',
        'drm_supported': True
    },
    # Raspberry Pi
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Linux.RaspberryPi',
                      'System.Platform.Linux'],
        'machine': 'armv7l',
        'expected_system': 'Linux',
        'expected_arch': 'armv7',
        'drm_supported': True
    },
    # MiBox
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Android',
                      'System.Platform.Linux'],
        'machine': 'aarch64',
        'expected_system': 'Android',
        'expected_arch': 'aarch64',
        'drm_supported': True
    },
    # Nexus Player
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Android',
                      'System.Platform.Linux'],
        'machine': 'AMD64',
        'expected_system': 'Android',
        'expected_arch': 'x86_64',
        'drm_supported': True
    },
    # HTC One M8
    {
        'system': 'Linux',
        'platforms': ['System.Platform.Android',
                      'System.Platform.Linux'],
        'machine': 'armv7l',
        'expected_system': 'Android',
        'expected_arch': 'armv7',
        'drm_supported': True
    },
    # Windows (UWP)
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows',
                      'System.Platform.UWP'],
        'machine': 'AMD64',
        'arch': '64bit',
        'expected_system': 'UWP',
        'expected_arch': 'x86_64',
        'drm_supported': False
    },
    # Xbox One
    {
        'system': 'Windows',
        'platforms': ['System.Platform.Windows',
                      'System.Platform.UWP'],
        'machine': 'AMD64',
        'arch': '64bit',
        'expected_system': 'UWP',
        'expected_arch': 'x86_64',
        'drm_supported': False
    },
]


ARCHES = [
    ('aarch64', 'aarch64'),
    ('aarch64_be', 'aarch64'),
    ('arm64', 'aarch64'),
    ('arm', 'arm'),
    ('armv7l', 'arm'),
    ('armv8', 'aarch64'),
    ('AMD64', 'x64'),
    ('x86_64', 'x64'),
    ('x86', 'x86'),
    ('i386', 'x86'),
    ('i686', 'x86'),
]

KODI_BUILDS = [
    {
        'build': '13.2 Git:Unknown',
        'version': '13.2',
        'major_version': 13,
        'build_name': 'Gotham',
        'build_date': None,
    },
    {
        'build': '17.6 Git:20180213-nogitfound',
        'version': '17.6',
        'major_version': 17,
        'build_name': 'Krypton',
        'build_date': '20180213',
    },
    {
        'build': '17.6 Git:20171119-ced5097',
        'version': '17.6',
        'major_version': 17,
        'build_name': 'Krypton',
        'build_date': '20171119',
    },
    {
        'build': '18.0-ALPHA1 Git:20180225-02cb21ec7d',
        'version': '18.0',
        'major_version': 18,
        'build_name': 'Leia',
        'build_date': '20180225',
    },
]


# Expected output from calling Addons.GetAddonDetails for IA if not installed
IA_NOT_AVAILABLE = {
    'id': 1,
    'jsonrpc': '2.0',
    'error': {
        'message': 'Invalid params.',
        'code': -32602
    }
}

IA_ENABLED = {
    'id': 1,
    'jsonrpc': u'2.0',
    'result': {
        'addon': {
            'addonid': 'inputstream.adaptive',
            'enabled': True,
            'type': 'kodi.inputstream'
        }
    }
}

TRANS_PATH_ARGS = [
    "addon.getSetting('DECRYPTERPATH')",
    'special://xbmcbinaddons/inputstream.adaptive',
    'special://home/'
]

TRANSLATED_PATHS = {
    'Linux': ['/storage/.kodi/addons/inputstream.adaptive',
              '/storage/.kodi/cdm'],
    'Windows': ['C:/Program Files (x86)/Kodi/addons/inputstream.adaptive',
                'C:/Users/user/AppData/Roaming/Kodi/cdm'],
    'Darwin': ['/Users/User/Library/Application Support/Kodi/cdm/']
}
