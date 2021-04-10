import logging
import mock

from unittest import TestCase as TestClass


class TestCase(TestClass):
    _multiprocess_can_split_ = True

    def setup_patch(self, to_patch):
        patcher = mock.patch(to_patch)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        super().setUp()
        logging.disable(logging.CRITICAL)
