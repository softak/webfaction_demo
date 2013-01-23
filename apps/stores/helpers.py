def gen_backround(store):
    sd = getattr(store, 'design', None)
    if not sd is None:
        tags = (
            sd.background_color if sd.background_color else '',
            'url(%s)' % sd.background_image.url if sd.background_image else '',
            'repeat' if sd.is_repeated and sd.background_image else ''
        )
        out = ' '.join([tag for tag in tags if tag])
        return 'style="background:%s;"' % out if out else ''
    return ''
