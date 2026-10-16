import contextlib
import io
import unittest
from unittest import mock

import checkin


class LogPrivacyTests(unittest.TestCase):
    def test_request_error_does_not_log_header_values(self):
        marker = 'synthetic-sensitive-header-value'
        output = io.StringIO()
        error = checkin.requests.exceptions.InvalidHeader(marker)
        with mock.patch('checkin.requests.get', side_effect=error):
            with contextlib.redirect_stdout(output):
                result = checkin.GLaDOS('gld:sess=test; gld:sess.sig=test').req(
                    'GET', '/api/user/status'
                )
        self.assertIsNone(result)
        self.assertIn('InvalidHeader', output.getvalue())
        self.assertNotIn(marker, output.getvalue())

    def test_push_error_does_not_log_exception_payload(self):
        marker = 'synthetic-sensitive-push-value'
        output = io.StringIO()
        error = checkin.requests.exceptions.RequestException(marker)
        with mock.patch('checkin.requests.post', side_effect=error):
            with contextlib.redirect_stdout(output):
                checkin.pushplus('test', 'test', 'test')
                checkin.telegram_push('test', 'test', 'test', 'test')
        self.assertNotIn(marker, output.getvalue())


if __name__ == '__main__':
    unittest.main()

