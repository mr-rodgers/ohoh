from codecs import open
from os import path


here = path.dirname(__file__)
with open(path.join(here, "VERSION.txt"), encoding="ascii") as f:
    __version__ = f.read().strip()


def main():
    pass


if __name__ == '__main__':
    main()
