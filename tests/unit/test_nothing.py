from tests.testsuite import TestCase


class TestSomethingOrNothing(TestCase):
    def test_nothing_but_make_pytest_in_the_pipeline_happy_while_there_are_no_tests_written(self):
        self.assertTrue(True)
