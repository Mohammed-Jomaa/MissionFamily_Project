"""
خدمة ملفات media مع دعم HTTP Range Requests (للفيديو والصوت).
ضرورية فقط في بيئة التطوير (runserver) لأن خادم Django الافتراضي
لا يدعم range requests، فلا تعمل الفيديوهات. في الإنتاج يتولى الخادم ذلك.
"""
import os
import re
import mimetypes
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings


RANGE_RE = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)


def serve_media(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise Http404('الملف غير موجود')

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = RANGE_RE.match(range_header) if range_header else None

    if range_match:
        start = int(range_match.group(1))
        end_group = range_match.group(2)
        end = int(end_group) if end_group else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        f = open(full_path, 'rb')
        f.seek(start)
        resp = HttpResponse(f.read(length), status=206, content_type=content_type)
        f.close()
        resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        resp['Accept-Ranges'] = 'bytes'
        resp['Content-Length'] = str(length)
        return resp

    resp = FileResponse(open(full_path, 'rb'), content_type=content_type)
    resp['Accept-Ranges'] = 'bytes'
    resp['Content-Length'] = str(file_size)
    return resp
