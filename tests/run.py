#!/usr/bin/env python3
"""Run nonempty tests and emit current-run text, JSON and JUnit results."""
import datetime
import json
import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self.started = {}

    def startTest(self, test):
        self.started[test.id()] = time.monotonic()
        super().startTest(test)

    def record(self, test, status, detail=''):
        self.records.append({'test': test.id(), 'status': status, 'detail': detail,
                             'seconds': round(time.monotonic() - self.started.get(test.id(), time.monotonic()), 4)})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'failed', self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'error', self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'skipped', reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err:
            self.record(subtest, 'failed', self._exc_info_to_string(err, test))


def main():
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
    if suite.countTestCases() == 0:
        raise RuntimeError('Zero tests discovered')
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    summary = {'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'tests_run': result.testsRun, 'failures': len(result.failures),
               'errors': len(result.errors), 'skipped': len(result.skipped),
               'expected_failures': len(result.expectedFailures),
               'unexpected_successes': len(result.unexpectedSuccesses),
               'successful': result.wasSuccessful(), 'tests': result.records,
               'limits': ['Mocked Magisk customization, not a real Magisk installation',
                          'No real device, kernel, boot-safety or attestation validation',
                          'Emulator is a separate optional workflow, not part of these results']}
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    (reports / 'tests.json').write_text(json.dumps(summary, indent=2) + '\n')
    xml = ET.Element('testsuite', name='AliothGuard', tests=str(result.testsRun),
                     failures=str(len(result.failures)), errors=str(len(result.errors)),
                     skipped=str(len(result.skipped)))
    for record in result.records:
        case = ET.SubElement(xml, 'testcase', name=record['test'], time=str(record['seconds']))
        tag = {'failed': 'failure', 'error': 'error', 'skipped': 'skipped'}.get(record['status'])
        if tag:
            ET.SubElement(case, tag).text = record['detail']
    ET.ElementTree(xml).write(reports / 'junit.xml', encoding='utf-8', xml_declaration=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
