from server.plugins.plugin_helper import Plugin_Object, is_mac, normalize_mac, per_item_timeout, sanitize_plugin_text


def test_is_mac_accepts_wildcard():
    # is_mac checks structure, so it should still return True
    assert is_mac("aa:bb:cc:*") is True
    assert is_mac("AA-BB-CC:*") is True  # mixed case/separator should still be recognized
    assert is_mac("00:11:22:33:44:55") is True
    assert is_mac("00-11-22-33-44-55") is True
    assert is_mac("not-a-mac") is False


def test_normalize_mac_preserves_wildcard():
    # UPDATED: Expected results are now lowercase to match the DB standard
    assert normalize_mac("aa:bb:cc:*") == "aa:bb:cc:*"
    assert normalize_mac("AA-BB-CC-*") == "aa:bb:cc:*"

    # Call once and assert deterministic result
    result = normalize_mac("aabbcc*")
    assert result == "aa:bb:cc:*", f"Expected 'aa:bb:cc:*' but got '{result}'"

    # Ensure full MACs are lowercase too
    assert normalize_mac("AA:BB:CC:DD:EE:FF") == "aa:bb:cc:dd:ee:ff"


def test_normalize_mac_preserves_internet_root():
    # Stays lowercase
    assert normalize_mac("internet") == "internet"
    assert normalize_mac("Internet") == "internet"
    assert normalize_mac("INTERNET") == "internet"


def test_per_item_timeout_unchanged_for_zero_or_one_items():
    # The common case (0 or 1 queued items) must see no behavior change.
    assert per_item_timeout(10, 0) == 10
    assert per_item_timeout(10, 1) == 10


def test_per_item_timeout_divides_budget_across_items():
    assert per_item_timeout(10, 5) == 2
    assert per_item_timeout(9, 2) == 4  # integer division, not rounded


def test_per_item_timeout_never_goes_below_floor():
    # A large queue must not divide the per-item timeout down to 0.
    assert per_item_timeout(10, 100) == 1
    assert per_item_timeout(10, 100, floor=2) == 2


def test_helpval_preserves_real_zero_and_false():
    # A device with a legitimate 0/False value (e.g. VLAN 0, an "inactive"
    # flag) must not have it silently collapsed to "" - only an actually
    # omitted (None) value should fall back to the empty-string default.
    obj = Plugin_Object(helpVal1=0, helpVal2=False, helpVal3="", helpVal4=None)
    assert obj.helpVal1 == 0
    assert obj.helpVal2 is False
    assert obj.helpVal3 == ""
    assert obj.helpVal4 == ""


def test_watched_columns_unaffected_by_helpval_fix():
    # watchedValue1-4 were never coerced and must stay that way.
    obj = Plugin_Object(watched1=0, watched2=False, watched3="", watched4=None)
    assert obj.watched1 == 0
    assert obj.watched2 is False
    assert obj.watched3 == ""
    assert obj.watched4 is None


def test_sanitize_plugin_text_strips_tag_delimiters():
    assert sanitize_plugin_text("<img src=x onerror=alert(1)>") == "img src=x onerror=alert(1)"


def test_sanitize_plugin_text_strips_control_chars_but_keeps_tab_and_newline():
    assert sanitize_plugin_text("a\x00b\x1fc\td\ne\rf") == "abc\td\ne\rf"


def test_sanitize_plugin_text_passes_through_clean_text_unchanged():
    text = "Living Room TV (Samsung) - " + ("x" * 2000)  # no length cap
    assert sanitize_plugin_text(text) == text


def test_sanitize_plugin_text_passes_none_through():
    assert sanitize_plugin_text(None) is None
