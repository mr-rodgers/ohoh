from types import TracebackType
import cPickle as pickle
import copy
import inspect
import json
import tblib


class ShadowMixin(object):
    extras = {}
    deep_extras = []

    def __init__(self, obj):
        super(ShadowMixin, self.__class__).__init__(self, obj)

        for extra, factory in self.extras.items():
            if hasattr(obj, extra):
                attr = getattr(obj, extra)
                attr = factory(attr) if attr and factory else attr
                setattr(self, extra, attr)

        for extra in self.deep_extras:
            if hasattr(obj, extra):
                attr = getattr(obj, extra)
                attr = self._walk(attr, can_dump) if attr else attr
                setattr(self, extra, attr)

    def _walk(self, obj, p):
        if isinstance(obj, dict):
            return dict(
                (key, value) for key, value in obj.items() if p(value)
            )
        elif isinstance(obj, list):
            return [value for value in obj if p(value)]
        else:
            cp = copy.copy(obj)
            for member in inspect.getmembers(cp):
                if not(p(getattr(cp, member))):
                    delattr(cp, member)
            return cp


class Code(ShadowMixin, tblib.Code):
    extras = {'co_lnotab': None}


class Frame(ShadowMixin, tblib.Frame):
    extras = {'f_code': Code, 'f_lineno': None}
    deep_extras = ['f_locals', 'f_globals']

    def __init__(self, f):
        ShadowMixin.__init__(self, f)


class Traceback(ShadowMixin, tblib.Traceback):
    extras = {'tb_lasti': None, 'tb_frame': Frame}

    def __init__(self, tb):
        self.extras['tb_next'] = Traceback
        ShadowMixin.__init__(self, tb)


def can_dump(obj, dump=pickle.dumps):
    if isinstance(obj, TracebackType):
        return True

    try:
        dump(obj)
    except:
        return False
    else:
        return True


def can_dump_json(obj):
    return can_dump(obj, json.dumps)
