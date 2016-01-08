import os
import logging
import traceback

from base_test_case import BaseTestCase
from pbreports.io.csv_reader import CsvReader

log = logging.getLogger(__name__)


class TestCsvReader(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()

    def setUp(self):
        """
        Before *every* test
        """
        try:
            BaseTestCase.setUp(self)
        except Exception as err:
            log.error(err)
            tb = traceback.format_exc()
            log.error(tb)
            raise
        log.debug("In setUp()")

    def tearDown(self):
        """
        After *every* test
        """
        try:
            BaseTestCase.tearDown(self)
        except Exception as err:
            log.error(err)
            tb = traceback.format_exc()
            log.error(tb)
            raise

    def test_validate_csv(self):
        """
        Incorrect csv should be rejected immediately if strict == True
        """
        b = os.path.join(self.get_output_dir(), 'bogus.csv')
        with open(b, 'w') as f:
            f.write("foo,bar,baz")

        # all of the columns in the csv need to be represented in dict
        # baz is not
        column_dtypes = {"foo": ("|S64", str),
                         "bah": ("|S64", str)}
        r = CsvReader(b,column_dtypes, True)

        def _test_valerror():
            r.load()

        self.assertRaises(ValueError, _test_valerror)
        
        #strict is false, so no exception
        column_dtypes = {"foo": ("|S64", str),
                         "bah": ("|S64", str)}
        r = CsvReader(b,column_dtypes, False)

        #we only want 2 columns        
        column_dtypes = {"foo": ("|S64", str),
                         "bar": ("|S64", str)}
        r = CsvReader(b,column_dtypes, True)
