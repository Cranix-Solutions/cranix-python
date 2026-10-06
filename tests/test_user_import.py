# -*- coding: utf-8 -*-

import os
from types import SimpleNamespace

from cranix.user_import import Importer, build_parser


def make_args(tmp_path, **overrides):
    values = dict(
        input=str(tmp_path / "users.csv"),
        role="students",
        password="",
        lang="DE",
        identifier="uid",
        full=False,
        test=True,
        debug=False,
        mustChange=False,
        resetPassword=False,
        allClasses=False,
        cleanClassDirs=False,
        appendBirthdayToPassword=False,
        appendClassToPassword=False,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def make_importer(tmp_path, **overrides):
    importer = Importer(make_args(tmp_path, **overrides))
    importer.import_dir = str(tmp_path / "import")
    os.makedirs(importer.import_dir + "/tmp", exist_ok=True)
    importer.identifier = overrides.get("identifier", "uid")
    return importer


def test_read_csv_by_uid(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "system", lambda *args, **kwargs: 0)
    (tmp_path / "users.csv").write_text(
        "uid;surName;givenName;birthDay\n"
        "jdoe;Doe;John;2000-01-02\n",
        encoding="utf-8")
    importer = make_importer(tmp_path)
    importer.read_csv()
    assert "jdoe" in importer.import_list
    assert importer.import_list["jdoe"]["surName"] == "Doe"
    assert importer.import_list["jdoe"]["birthDay"] == "2000-01-02"


def test_read_csv_german_header(tmp_path, monkeypatch):
    monkeypatch.setattr(os, "system", lambda *args, **kwargs: 0)
    (tmp_path / "users.csv").write_text(
        "BENUTZERKÜRZEL;NACHNAME;VORNAME;GEBURTSTAG\n"
        "jdoe;Doe;John;02.01.2000\n",
        encoding="utf-8")
    importer = make_importer(tmp_path)
    importer.read_csv()
    assert importer.import_list["jdoe"]["givenName"] == "John"
    assert importer.import_list["jdoe"]["birthDay"] == "2000-01-02"


def test_check_attributes_missing_givenname(tmp_path):
    importer = make_importer(tmp_path)
    assert not importer.check_attributes({"surName": "Doe"}, 1)


def test_build_parser_defaults():
    parser = build_parser(["students", "teachers"])
    args = parser.parse_args(["--role", "teachers"])
    assert args.role == "teachers"
    assert args.identifier == "sn-gn-bd"
    assert args.test is False