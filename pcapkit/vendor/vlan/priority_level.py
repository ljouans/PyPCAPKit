# -*- coding: utf-8 -*-

import contextlib
import os
import re
import webbrowser
import tempfile

import bs4
# import requests

###############
# Macros
###############

NAME = 'PriorityLevel'
DOCS = 'priority levels defined in IEEE 802.1p'
FLAG = 'isinstance(value, int) and 0b000 <= value <= 0b111'
LINK = 'https://en.wikipedia.org/wiki/IEEE_P802.1p#Priority_levels'

###############
# Processors
###############

# page = requests.get(LINK)
# soup = bs4.BeautifulSoup(page.text, 'html5lib')
with tempfile.TemporaryDirectory(prefix='{}/'.format(os.path.realpath(os.curdir))) as tempdir:
    index_html = os.path.join(tempdir, 'index.html')

    webbrowser.open(LINK)
    print('Please save the HTML code as {!r}.'.format(index_html))
    input('Press ENTER to continue...')

    with open(index_html) as file:
        text = file.read()
soup = bs4.BeautifulSoup(text, 'html5lib')

table = soup.find_all('table', class_='wikitable')[0]
content = filter(lambda item: isinstance(item, bs4.element.Tag), table.tbody)  # pylint: disable=filter-builtin-not-iterating
header = next(content)

enum = list()
miss = [
    "extend_enum(cls, 'Unassigned [0b%s]' % bin(value)[2:].zfill(3), value)",
    'return cls(value)'
]
for item in content:
    line = item.find_all('td')

    pval = ' '.join(line[0].stripped_strings)
    prio = ' '.join(line[1].stripped_strings)
    abbr = ' '.join(line[2].stripped_strings)
    desc = ' '.join(line[3].stripped_strings)

    match = re.match(r'(\d) *(\(.*\))*', prio)
    group = match.groups()

    code = '0b{}'.format(bin(int(pval))[2:].zfill(3))

    pres = "{}[{!r}] = {}".format(NAME, abbr, code).ljust(76)
    sufs = "# {} - {} {}".format(group[0], desc, group[1] or '')

    enum.append('{}{}'.format(pres, sufs))

###############
# Defaults
###############

temp, FILE = os.path.split(os.path.abspath(__file__))
ROOT, STEM = os.path.split(temp)

ENUM = '\n    '.join(map(lambda s: s.rstrip(), enum))
MISS = '\n        '.join(map(lambda s: s.rstrip(), miss))


LINE = lambda NAME, DOCS, FLAG, ENUM, MISS: '''\
# -*- coding: utf-8 -*-

from aenum import IntEnum, extend_enum


class {}(IntEnum):
    """Enumeration class for {}."""
    _ignore_ = '{} _'
    {} = vars()

    # {}
    {}

    @staticmethod
    def get(key, default=-1):
        """Backport support for original codes."""
        if isinstance(key, int):
            return {}(key)
        if key not in {}._member_map_:
            extend_enum({}, key, default)
        return {}[key]

    @classmethod
    def _missing_(cls, value):
        """Lookup function used when value is not found."""
        if not ({}):
            raise ValueError('%r is not a valid %s' % (value, cls.__name__))
        {}
        super()._missing_(value)
'''.format(NAME, NAME, NAME, NAME, DOCS, ENUM, NAME, NAME, NAME, NAME, FLAG, MISS)


with contextlib.suppress(FileExistsError):
    os.mkdir(os.path.join(ROOT, '../const/{}'.format(STEM)))
with open(os.path.join(ROOT, '../const/{}/{}'.format(STEM, FILE)), 'w') as file:
    file.write(LINE(NAME, DOCS, FLAG, ENUM, MISS))