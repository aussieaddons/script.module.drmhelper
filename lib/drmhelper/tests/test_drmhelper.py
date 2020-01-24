import testtools

import drmhelper


class DRMHelperTests(testtools.TestCase):

    def test_check_inputstream(self):
        drmhelper.check_inputstream()
