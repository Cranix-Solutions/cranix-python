# -*- coding: utf-8 -*-

import pytest

from cranix import functions


def test_read_birthday_dashed():
    assert functions.read_birthday("2000-01-02") == "2000-01-02"


def test_read_birthday_dotted():
    assert functions.read_birthday("02.01.2000") == "2000-01-02"


def test_read_birthday_compact():
    assert functions.read_birthday("20000102") == "2000-01-02"


def test_read_birthday_invalid():
    with pytest.raises(SyntaxError):
        functions.read_birthday("not-a-date")


def test_check_uid_too_short():
    assert "2 characters" in functions.check_uid("a")


def test_check_uid_too_long():
    assert "32 characters" in functions.check_uid("a" * 33)


def test_check_uid_invalid_character():
    assert "invalid" in functions.check_uid("bad!")


def test_check_uid_free():
    assert functions.check_uid("zzzznotexistinguser") == ""


def test_create_secure_pw_length():
    password = functions.create_secure_pw(10)
    assert len(password) == 10


def test_print_helpers():
    assert "red" in functions.print_error("boom")
    assert "Title" in functions.print_msg("Title", "value")