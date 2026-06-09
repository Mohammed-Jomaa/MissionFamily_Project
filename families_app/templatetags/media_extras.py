from django import template

register = template.Library()

VIDEO_EXTENSIONS = ('.mp4', '.webm', '.ogg', '.mov', '.mkv', '.avi', '.m4v')
AUDIO_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.aac', '.oga', '.opus', '.weba')


@register.filter
def is_video(file_url):
    """يرجع True إذا كان الملف فيديو."""
    if not file_url:
        return False
    return str(file_url).lower().endswith(VIDEO_EXTENSIONS)


@register.filter
def is_audio(file_url):
    """يرجع True إذا كان الملف صوتي."""
    if not file_url:
        return False
    return str(file_url).lower().endswith(AUDIO_EXTENSIONS)
