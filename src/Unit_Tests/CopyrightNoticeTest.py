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

COPYRIGHT = re.compile(r'Copyright \(C\) (\d{4})(?:-(\d{4}))? ' + re.escape(HOLDER) + '$')


def copyrightLine(years):
    "'Copyright (C) <years> Stefano Franchi': years is '2026' or '2006-2026'"
    return 'Copyright (C) %s %s' % (years, HOLDER)


def noticeLines(years, marker):
    "The notice as comment lines with marker, for a file of the given years"
    return [(marker + ' ' + line) if line else marker
            for line in [copyrightLine(years), ''] + NOTICE.split('\n')]


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
    first = lines[i][len(marker) + 1:] if i < len(lines) and lines[i].startswith(marker + ' ') else ''
    m = COPYRIGHT.match(first)
    if not m:
        return 'no copyright line at line %d' % (i + 1)
    if m.group(2) and not int(m.group(1)) < int(m.group(2)):
        return 'the years %s are not a range' % first.split()[2]
    expected = noticeLines(m.group(0).split()[2], marker)
    if lines[i:i + len(expected)] != expected:
        return 'the notice after line %d is not the licence text' % (i + 1)
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
    #VRML_SIM line or a #SBATCH block; a missing, altered or misdated one.'''

    def check(self, name, text):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(text)
            return missingNotice(name, root=tmp)

    def notice(self, years='2013-2026', marker='#'):
        return '\n'.join(noticeLines(years, marker)) + '\n'

    def testPlacements(self):
        self.assertIsNone(self.check('a.py', self.notice() + '\nimport os\n'))
        self.assertIsNone(self.check('a.py', '#!/usr/bin/env python3\n' + self.notice('2026')))
        self.assertIsNone(self.check('w.wbt', '#VRML_SIM R2025a utf8\n' + self.notice()))
        self.assertIsNone(self.check('j.slurm', '#!/bin/bash\n#SBATCH --array=1-2\n#\n' + self.notice()))
        self.assertIsNone(self.check('f.tex', self.notice(marker='%')))

    def testWhatIsWrong(self):
        self.assertIn('no copyright', self.check('a.py', 'import os\n' + self.notice()))
        self.assertIn('not a range', self.check('a.py', self.notice('2026-2013')))
        altered = self.notice().replace('version 3', 'version 2')
        self.assertIn('not the licence text', self.check('a.py', altered))

    def testCodeLines(self):
        self.assertEqual(codeLines(['# c', '', 'x = 1', '   # d', 'y'], '#'), 2)


if __name__ == "__main__":
    unittest.main()
