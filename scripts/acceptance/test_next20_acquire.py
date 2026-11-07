import io
import urllib.error
import unittest
from unittest.mock import Mock

from next20_acquire import download_source


class SourceDownloadTests(unittest.TestCase):
    def test_retries_gateway_timeout_once_and_records_both_attempts(self):
        response=Mock()
        response.__enter__=Mock(return_value=response)
        response.__exit__=Mock(return_value=False)
        response.read.return_value=b'pinned-source'
        response.getcode.return_value=200
        opener=Mock(side_effect=[urllib.error.HTTPError('https://example.invalid',504,
            'Gateway Timeout',{},io.BytesIO()),response])
        pauses=[]
        data,attempts=download_source('https://example.invalid',opener=opener,pause=pauses.append)
        self.assertEqual(data,b'pinned-source')
        self.assertEqual(pauses,[1])
        self.assertEqual([row['outcome'] for row in attempts],['transient_error','downloaded'])
        self.assertEqual([row['http_status'] for row in attempts],[504,200])

    def test_does_not_retry_permanent_http_failure(self):
        opener=Mock(side_effect=urllib.error.HTTPError('https://example.invalid',404,
            'Not Found',{},io.BytesIO()))
        with self.assertRaises(RuntimeError) as caught:
            download_source('https://example.invalid',opener=opener,pause=lambda _:None)
        self.assertEqual(len(caught.exception.attempts),1)
        self.assertEqual(caught.exception.attempts[0]['outcome'],'error')

    def test_stops_after_three_transient_failures(self):
        opener=Mock(side_effect=urllib.error.HTTPError('https://example.invalid',504,
            'Gateway Timeout',{},io.BytesIO()))
        pauses=[]
        with self.assertRaises(RuntimeError) as caught:
            download_source('https://example.invalid',opener=opener,pause=pauses.append)
        self.assertEqual(len(caught.exception.attempts),3)
        self.assertEqual(pauses,[1,2])


if __name__=='__main__':
    unittest.main()
