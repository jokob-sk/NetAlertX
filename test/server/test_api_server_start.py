from types import SimpleNamespace

from server.api_server import api_server_start as api_mod


def _make_fake_thread(recorder):
    class FakeThread:
        def __init__(self, target=None):
            self._target = target

        def start(self):
            # call target synchronously for test
            if self._target:
                self._target()

    return FakeThread


def test_start_server_passes_debug_true(monkeypatch):
    # Arrange
    # Use the settings helper to provide the value
    monkeypatch.setattr(api_mod, 'get_setting_value', lambda k: True if k == 'FLASK_DEBUG' else None)

    called = {}

    def fake_run(*args, **kwargs):
        called['args'] = args
        called['kwargs'] = kwargs

    monkeypatch.setattr(api_mod, 'app', api_mod.app)
    monkeypatch.setattr(api_mod.app, 'run', fake_run)

    # Replace threading.Thread with a fake that executes target immediately
    FakeThread = _make_fake_thread(called)
    monkeypatch.setattr(api_mod.threading, 'Thread', FakeThread)

    # Prevent updateState side effects
    monkeypatch.setattr(api_mod, 'updateState', lambda *a, **k: None)

    app_state = SimpleNamespace(graphQLServerStarted=0)

    # Act
    api_mod.start_server(12345, app_state)

    # Assert
    assert 'kwargs' in called
    assert called['kwargs']['debug'] is True
    assert called['kwargs']['host'] == '0.0.0.0'
    assert called['kwargs']['port'] == 12345


def test_start_server_passes_debug_false(monkeypatch):
    # Arrange
    monkeypatch.setattr(api_mod, 'get_setting_value', lambda k: False if k == 'FLASK_DEBUG' else None)

    called = {}

    def fake_run(*args, **kwargs):
        called['args'] = args
        called['kwargs'] = kwargs

    monkeypatch.setattr(api_mod, 'app', api_mod.app)
    monkeypatch.setattr(api_mod.app, 'run', fake_run)

    FakeThread = _make_fake_thread(called)
    monkeypatch.setattr(api_mod.threading, 'Thread', FakeThread)

    monkeypatch.setattr(api_mod, 'updateState', lambda *a, **k: None)

    app_state = SimpleNamespace(graphQLServerStarted=0)

    # Act
    api_mod.start_server(22222, app_state)

    # Assert
    assert 'kwargs' in called
    assert called['kwargs']['debug'] is False
    assert called['kwargs']['host'] == '0.0.0.0'
    assert called['kwargs']['port'] == 22222


def test_env_var_overrides_setting(monkeypatch):
    # Arrange
    # Ensure env override is present
    monkeypatch.setenv('FLASK_DEBUG', '1')
    # And the stored setting is False to ensure env takes precedence
    monkeypatch.setattr(api_mod, 'get_setting_value', lambda k: False if k == 'FLASK_DEBUG' else None)

    called = {}

    def fake_run(*args, **kwargs):
        called['args'] = args
        called['kwargs'] = kwargs

    monkeypatch.setattr(api_mod, 'app', api_mod.app)
    monkeypatch.setattr(api_mod.app, 'run', fake_run)

    FakeThread = _make_fake_thread(called)
    monkeypatch.setattr(api_mod.threading, 'Thread', FakeThread)

    monkeypatch.setattr(api_mod, 'updateState', lambda *a, **k: None)

    app_state = SimpleNamespace(graphQLServerStarted=0)

    # Act
    api_mod.start_server(33333, app_state)

    # Assert
    assert 'kwargs' in called
    assert called['kwargs']['debug'] is True
    assert called['kwargs']['host'] == '0.0.0.0'
    assert called['kwargs']['port'] == 33333
