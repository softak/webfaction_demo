from sorl.thumbnail import default

def thumbnail(file_, geometry, **kwargs):
    thumbnail = default.backend.get_thumbnail(file_, geometry, **kwargs)
    return thumbnail
