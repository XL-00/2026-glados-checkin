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
        self.assertTrue(result['request_failed'])
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


    def test_auth_failure_response_does_not_expose_cookie_in_logs(self):
        marker = 'synthetic-sensitive-auth-value'
        output = io.StringIO()
        client = mock.Mock()
        client.checkin.return_value = {'code': -2, 'message': 'unauthorized ' + marker}
        with contextlib.redirect_stdout(output):
            _, success = checkin.checkin_with_retry(client)
        self.assertFalse(success)
        self.assertNotIn(marker, output.getvalue())
        client.checkin.assert_called_once()

    @mock.patch('checkin.GLaDOS')
    def test_disabled_exchange_never_redeems_even_with_high_balance(self, client_class):
        client = client_class.return_value
        client.checkin.return_value = {'code': 0, 'message': 'Checkin! Got 12 Points'}
        client.email = 'synthetic@example.test'
        client.points = '10000'
        client.points_change = '+12'
        client.left_days = '100'
        client.exchange_info = ''
        with mock.patch.dict(checkin.os.environ, {
            'GLADOS_COOKIE': 'gld:sess=test; gld:sess.sig=test',
            'EXCHANGE_PLAN': 'off',
            'PUSH_LEVEL': 'fail_only',
        }, clear=True), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(checkin.main(), 0)
        client.checkin.assert_called_once()
        client.exchange.assert_not_called()


if __name__ == '__main__':
    unittest.main()

