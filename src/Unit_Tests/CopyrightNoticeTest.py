# Copyright (C) 2026 Stefano Franchi
#
# This file is part of Homeo, a simulation of Ashby's homeostat and of
# homeostat-controlled robots.
#
# Homeo is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Homeo is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Homeo.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

'''
Every source file of Homeo with more than 10 lines of code starts with its
copyright and licence notice, the GNU GPL's (version 3 or later), as the FSF
asks: after a #! or coding line, the #VRML_SIM line of a Webots file, or the
#SBATCH block of a SLURM script, and before anything else.

The notice opens with one copyright line per holder, whoever the holder is:
anyone who adds a file to Homeo, or changes one, under the GPL can add their
own.  The test checks that each file states its licence, not who holds it.

The files are the repository's tracked ones, so the test runs in a git
checkout only.
'''
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The comment marker of each kind of source file.
COMMENT = {'.py': '#', '.sh': '#', '.slurm': '#', '.wbt': '#', '.proto': '#', '.tex': '%'}

# Files that are not Homeo's to license, with the licence they carry.
EXEMPT = {
    'src/Webots/protos/HomeoEpuck.proto':
        "Cyberbotics' E-puck.proto, under the Webots Assets licence of its header",
}

# The holder in the notices of the files Homeo is distributed with.
HOLDER = 'Stefano Franchi'

NOTICE = """\
This file is part of Homeo, a simulation of Ashby's homeostat and of
homeostat-controlled robots.

Homeo is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

Homeo is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License
along with Homeo.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-or-later"""

# Years are a year, a range or a list of both: '2026', '2006-2026', '2013, 2015-2026'.
YEARS = r'\d{4}(?:-\d{4})?(?:, \d{4}(?:-\d{4})?)*'
COPYRIGHT = re.compile(r'Copyright \(C\) (' + YEARS + r') (\S.*)$')


def copyrightLine(years, holder=HOLDER):
    "'Copyright (C) <years> <holder>': years is '2026' or '2006-2026'"
    return 'Copyright (C) %s %s' % (years, holder)


def commented(lines, marker):
    return [(marker + ' ' + line) if line else marker for line in lines]


def noticeLines(years, marker, holder=HOLDER):
    "The notice as comment lines with marker, for a file of the given years"
    return commented([copyrightLine(years, holder), ''] + NOTICE.split('\n'), marker)


def yearsInOrder(years):
    "True if each range of years goes forward, and each piece comes after the one before"
    last = 0
    for piece in years.split(', '):
        first, dash, end = piece.partition('-')
        first, end = int(first), int(end or first)
        if first <= last or (dash and end <= first):
            return False
        last = end
    return True


def codeLines(lines, marker):
    "The number of lines that are neither blank nor comments"
    return sum(1 for line in lines if line.strip() and not line.lstrip().startswith(marker))


def headerEnd(lines):
    '''The index of the first line after the lines that must come first:
    a #! line and a coding line, a #VRML_SIM line, a #SBATCH block.'''
    i = 0
    if i < len(lines) and lines[i].startswith('#!'):
        i += 1
    if i < len(lines) and re.match(r'#.*coding[:=]', lines[i]):
        i += 1
    if i < len(lines) and lines[i].startswith('#VRML_SIM'):
        i += 1
    while i < len(lines) and lines[i].startswith('#SBATCH'):
        i += 1
    return i


def trackedSources(root=ROOT):
    "The tracked files with a comment marker, relative to root"
    out = subprocess.run(['git', '-C', root, 'ls-files'], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return [path for path in out.stdout.splitlines()
            if os.path.splitext(path)[1] in COMMENT]


def needsNotice(path, root=ROOT):
    marker = COMMENT[os.path.splitext(path)[1]]
    with open(os.path.join(root, path), encoding='utf-8') as f:
        lines = f.read().split('\n')
    return codeLines(lines, marker) > 10


def missingNotice(path, root=ROOT):
    '''None if path starts with the notice, else what is wrong.'''
    marker = COMMENT[os.path.splitext(path)[1]]
    with open(os.path.join(root, path), encoding='utf-8') as f:
        lines = f.read().split('\n')
    i = headerEnd(lines)
    if i < len(lines) and lines[i] == marker:      # the separator after a #SBATCH block
        i += 1
    start = i
    while i < len(lines) and lines[i].startswith(marker + ' '):
        m = COPYRIGHT.match(lines[i][len(marker) + 1:])
        if not m:
            break
        if not yearsInOrder(m.group(1)):
            return 'the years %s at line %d are not in order' % (m.group(1), i + 1)
        i += 1
    if i == start:
        return 'no copyright line at line %d' % (i + 1)
    expected = commented([''] + NOTICE.split('\n'), marker)
    if lines[i:i + len(expected)] != expected:
        return 'the notice after line %d is not the licence text' % i
    return None


class CopyrightNoticeTest(unittest.TestCase):

    def setUp(self):
        self.sources = trackedSources()
        if self.sources is None:
            self.skipTest('not a git checkout')

    def testEverySourceFileHasTheNotice(self):
        problems = ['%s: %s' % (path, missingNotice(path))
                    for path in self.sources
                    if path not in EXEMPT and needsNotice(path) and missingNotice(path)]
        self.assertEqual(problems, [])

    def testTheExemptFilesAreTrackedAndCarryTheirOwnLicence(self):
        for path in EXEMPT:
            self.assertIn(path, self.sources)
            with open(os.path.join(ROOT, path), encoding='utf-8') as f:
                head = f.read(2000)
            self.assertIn('license:', head)
            self.assertNotIn('General Public License', head)


class NoticeFunctionsTest(unittest.TestCase):
    '''missingNotice on made-up files: a notice after a #! line, a
    #VRML_SIM line or a #SBATCH block; any holders; a missing, altered or
    misdated one.'''

    def check(self, name, text):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(text)
            return missingNotice(name, root=tmp)

    def notice(self, years='2013-2026', marker='#', holder=HOLDER):
        return '\n'.join(noticeLines(years, marker, holder)) + '\n'

    def testPlacements(self):
        self.assertIsNone(self.check('a.py', self.notice() + '\nimport os\n'))
        self.assertIsNone(self.check('a.py', '#!/usr/bin/env python3\n' + self.notice('2026')))
        self.assertIsNone(self.check('w.wbt', '#VRML_SIM R2025a utf8\n' + self.notice()))
        self.assertIsNone(self.check('j.slurm', '#!/bin/bash\n#SBATCH --array=1-2\n#\n' + self.notice()))
        self.assertIsNone(self.check('f.tex', self.notice(marker='%')))

    def testAnyHolders(self):
        self.assertIsNone(self.check('a.py', self.notice('2027', holder='Jane Doe')))
        second = '# ' + copyrightLine('2027, 2029-2030', 'Jane Doe') + '\n'
        first, rest = self.notice('2006-2026').split('\n', 1)
        self.assertIsNone(self.check('a.py', first + '\n' + second + rest))

    def testYearsInOrder(self):
        for years in ['2026', '2006-2026', '2013, 2015-2026', '2006-2010, 2013']:
            self.assertTrue(yearsInOrder(years), years)
        for years in ['2026-2013', '2026-2026', '2015, 2013', '2006-2015, 2013']:
            self.assertFalse(yearsInOrder(years), years)

    def testWhatIsWrong(self):
        self.assertIn('no copyright', self.check('a.py', 'import os\n' + self.notice()))
        self.assertIn('no copyright', self.check('a.py', self.notice(holder='').replace('2026 \n', '2026\n')))
        self.assertIn('not in order', self.check('a.py', self.notice('2026-2013')))
        altered = self.notice().replace('version 3', 'version 2')
        self.assertIn('not the licence text', self.check('a.py', altered))

    def testCodeLines(self):
        self.assertEqual(codeLines(['# c', '', 'x = 1', '   # d', 'y'], '#'), 2)


if __name__ == "__main__":
    unittest.main()
