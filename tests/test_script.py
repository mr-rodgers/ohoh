from codecs import open
from ohoh import build_parser, DEFAULT_HOST, DEFAULT_PORT
from os import path
import os
import pytest
import sys
import time

@pytest.fixture
def parser():
    return build_parser()

@pytest.fixture
def modfile(request, tmpdir):
    def uninstall():
        sys.path.remove(tmpdir.strpath)

    sys.path.insert(0, tmpdir.strpath)

    name = "rand_mod_name" + str(hash(time.time()))
    pyfile = path.join(tmpdir.strpath, name + ".py")
    with open(pyfile, "w", encoding="utf-8") as modfile:
        modfile.write("#-*- coding: utf-8 -*-\n")
        modfile.write("app = lambda: None\n")

    request.addfinalizer(uninstall)
    return pyfile

@pytest.fixture
def modname(modfile):
    modname = path.splitext(path.basename(modfile))[0]
    sys.modules.pop(modname, None)
    return modname

@pytest.mark.parametrize("address,expected", [
    (None, (DEFAULT_HOST, DEFAULT_PORT)),
    ("localhost", ("localhost", DEFAULT_PORT)),
    ("localhost:80", ("localhost", 80)),
    ("google.com", ("google.com", DEFAULT_PORT)),
    ("google.com:80", ("google.com", 80)),
    (":5868", (DEFAULT_HOST, 5868)),
])
def test_address_parse(address, expected, modname, parser):
    args = ["-s", address, modname] if address else [modname]
    parsed = parser.parse_args(args)
    assert parsed.address == expected

def test_app_spec_parse_nomod(parser):
    with pytest.raises(ImportError):
        parser = parser.parse_args(["sys.RANDOM_FOO.MODULE_I.PRAY.DOESNT_EXIST"])

def test_app_spec_parse_mod(parser, modname):
    parsed = parser.parse_args([modname])
    assert parsed.app() is None

def test_app_spec_parse_noobj(parser, modname):
    with pytest.raises(AttributeError):
        parser.parse_args(["{0}:obj_doesnt_exist".format(modname)])

def test_app_spec_parse_obj_not_callable(parser, modname, modfile):
    with open(modfile, "a", encoding="utf-8") as f:
        f.write("appx = None")

    with pytest.raises(SystemExit):
        parser.parse_args(["{0}:appx".format(modname)])

def test_app_spec_parse_obj(parser, modname, modfile):
    with open(modfile, "a", encoding="utf-8") as f:
        f.write("appx = lambda: None")

    parsed = parser.parse_args(["{0}:appx".format(modname)])
    assert parsed.app() is None

def test_app_spec_parse_filename(parser, modfile):
    sys.path.remove(path.dirname(modfile))

    parsed = parser.parse_args([modfile])
    assert parsed.app() is None
    assert path.dirname(modfile) in sys.path

def test_path_parse(parser, tmpdir):
    created = path.join(tmpdir.strpath, "created")
    uncreated = path.join(tmpdir.strpath, "uncreated")

    os.mkdir(created)

    with pytest.raises(SystemExit):
        parsed = parser.parse_args(["-p", created])
    assert created in sys.path

    with pytest.raises(SystemExit):
        parsed = parser.parse_args(["-p", uncreated])
    assert uncreated not in sys.path

def test_app_spec_parse_obj_factory(parser, modname, modfile):
    with open(modfile, "a", encoding="utf-8") as f:
        f.write("""
class App(object):
    def __init__(self, name=None, **kwargs):
        self.name = name
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])

    def __call__(self):
        pass
""")

    parsed = parser.parse_args(["{0}:App()".format(modname)])
    assert parsed.app.name is None
    assert getattr(parsed.app, 'age', None) is None

    parsed = parser.parse_args(['{0}:App("Te-je")'.format(modname)])
    assert parsed.app.name == "Te-je"
    assert getattr(parsed.app, 'age', None) is None

    parsed = parser.parse_args(['{0}:App(name="Jimmy", age=59)'.format(modname)])
    assert parsed.app.name == "Jimmy"
    assert parsed.app.age == 59
