from front.plugins.plugin_helper import is_mac, normalize_mac


def test_is_mac_accepts_wildcard():
    assert is_mac("AA:BB:CC:*") is True
    assert is_mac("aa-bb-cc:*") is True  # mixed separator
    assert is_mac("00:11:22:33:44:55") is True
    assert is_mac("00-11-22-33-44-55") is True
    assert is_mac("not-a-mac") is False


def test_normalize_mac_preserves_wildcard():
    assert normalize_mac("aa:bb:cc:*") == "AA:BB:CC:*"
    assert normalize_mac("aa-bb-cc-*") == "AA:BB:CC:*"
    # Call once and assert deterministic result
    result = normalize_mac("aabbcc*")
    assert result == "AA:BB:CC:*", f"Expected 'AA:BB:CC:*' but got '{result}'"
    assert normalize_mac("aa:bb:cc:dd:ee:ff") == "AA:BB:CC:DD:EE:FF"


def test_normalize_mac_preserves_internet_root():
    assert normalize_mac("internet") == "Internet"
    assert normalize_mac("Internet") == "Internet"
    assert normalize_mac("INTERNET") == "Internet"
