import os

from django.test import TestCase
from django.conf import settings
from django.http import StreamingHttpResponse, HttpResponse

from djangofloor.views import send_file


class TestSendFile(TestCase):
    def test_plain_send_file(self):
        settings.USE_X_SEND_FILE = False
        settings.X_ACCEL_REDIRECT = []
        filepath = __file__
        size = os.path.getsize(filepath)
        response = send_file(filepath, mimetype="text/python", force_download=True, attachment_filename="test_views.py")
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(str(size), response["Content-Length"])
        self.assertEqual("attachment; filename=\"test_views.py\"", response["Content-Disposition"])
        with open(filepath, "rb") as fd:
            content = fd.read()
        self.assertEqual(content, response.getvalue())

    def test_apache_send_file(self):
        settings.USE_X_SEND_FILE = True
        settings.X_ACCEL_REDIRECT = []
        filepath = __file__
        response = send_file(filepath, mimetype="text/python", force_download=True, attachment_filename="test_views.py")
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(filepath, response["X-SENDFILE"])
        self.assertEqual("attachment; filename=\"test_views.py\"", response["Content-Disposition"])

    def test_nginx_send_file_1(self):
        settings.USE_X_SEND_FILE = False
        settings.X_ACCEL_REDIRECT = [(settings.MEDIA_ROOT, settings.MEDIA_URL)]
        filepath = __file__
        response = send_file(filepath, mimetype="text/python", force_download=True, attachment_filename="test_views.py")
        size = os.path.getsize(filepath)
        self.assertIsInstance(response, StreamingHttpResponse)
        self.assertEqual(str(size), response["Content-Length"])
        self.assertEqual("attachment; filename=\"test_views.py\"", response["Content-Disposition"])
        with open(filepath, "rb") as fd:
            content = fd.read()
        self.assertEqual(content, response.getvalue())

    def test_nginx_send_file_2(self):
        settings.USE_X_SEND_FILE = False
        settings.X_ACCEL_REDIRECT = [(settings.MEDIA_ROOT, settings.MEDIA_URL)]
        filepath = os.path.join(settings.MEDIA_ROOT, "test.md")
        response = send_file(filepath, mimetype="text/markdown", force_download=True, attachment_filename="test.md")
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual("text/markdown", response["Content-Type"])
        self.assertEqual("attachment; filename=\"test.md\"", response["Content-Disposition"])
        self.assertEqual(os.path.join(settings.MEDIA_URL, "test.md"), response["X-Accel-Redirect"])
