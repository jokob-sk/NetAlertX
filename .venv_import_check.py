import sys, importlib
mods = [
    'json', 'simplejson',
    'httplib', 'http.client',
    'urllib2', 'urllib.request',
    'Queue', 'queue',
    'cStringIO', 'StringIO', 'io',
    'md5', 'hashlib',
    'ssl'
]
print('PYTHON_EXE:' + sys.executable)
print('PYTHON_VER:' + sys.version.replace('\n', ' '))
for m in mods:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, '__version__', None)
        if ver is None:
            # try common attributes
            ver = getattr(mod, 'version', None)
        info = (' version=' + str(ver)) if ver is not None else ''
        print('OK %s%s' % (m, info))
    except Exception as e:
        print('MISSING %s %s: %s' % (m, e.__class__.__name__, e))
