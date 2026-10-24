#!/usr/bin/env python3
"""Mocked, host-side checks. Never changes a real Magisk installation."""
import os, pathlib, subprocess, tempfile, unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"experimental/tools/denylist-control.sh"
MOCK='''#!/bin/sh
case "$*" in
  "-v") echo "30.7:MAGISK:R";;
  "--sqlite SELECT key,value FROM settings WHERE key IN ('zygisk','denylist');") echo "key=zygisk|value=1"; echo "key=denylist|value=1";;
  "--sqlite SELECT value FROM settings WHERE key='zygisk';") echo "value=1";;
  "--denylist ls") echo "com.example.app|com.example.app";;
  "--denylist add "*|"--denylist rm "*) printf '%s\\n' "$*" >> "$AG_TEST_LOG";;
  *) echo "unexpected magisk args: $*" >&2; exit 90;;
esac
'''
class Controls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        p=pathlib.Path(self.temp.name)
        (p/"magisk").write_text(MOCK); (p/"magisk").chmod(0o755)
        (p/"pm").write_text('#!/bin/sh\n[ "$1" = path ] && [ "$2" = com.example.app ]\n')
        (p/"pm").chmod(0o755)
        (p/"id").write_text('#!/bin/sh\\nif [ "$1" = -u ]; then printf "%s\\n" "${AG_TEST_UID:-0}"; else /usr/bin/id "$@"; fi\\n'.replace('\\\\n','\\n'))
        (p/"id").chmod(0o755)
        self.log=p/"log"
        self.env={**os.environ,"PATH":str(p)+":"+os.environ["PATH"],"AG_TEST_LOG":str(self.log)}
    def call(self,*args):
        return subprocess.run(["sh",str(SCRIPT),*args],capture_output=True,text=True,env=self.env)
    def test_status_does_not_write(self):
        r=self.call("status")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertFalse(self.log.exists())
    def test_list_does_not_write(self):
        r=self.call("list")
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("com.example.app",r.stdout)
        self.assertFalse(self.log.exists())
    def test_protected_target_refused(self):
        r=self.call("add","com.google.android.gms")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.log.exists())
    def test_process_mismatch_refused(self):
        r=self.call("add","com.example.app","com.other.process")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.log.exists())
    def test_noninstalled_target_refused(self):
        r=self.call("add","com.example.missing")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.log.exists())
    def test_invalid_target_refused(self):
        r=self.call("add","bad;command")
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(self.log.exists())
    def test_explicit_add_and_remove(self):
        a=self.call("add","com.example.app")
        self.assertEqual(a.returncode,0,a.stderr)
        b=self.call("remove","com.example.app")
        self.assertEqual(b.returncode,0,b.stderr)
        self.assertEqual(self.log.read_text().splitlines(),[
            "--denylist add com.example.app com.example.app",
            "--denylist rm com.example.app com.example.app"])
    def test_nonroot_refused(self):
        self.env["AG_TEST_UID"]="2000"
        result=self.call("add","com.example.app")
        self.assertNotEqual(result.returncode,0)
        self.assertIn("Root required",result.stderr)
        self.assertFalse(self.log.exists())
if __name__=="__main__": unittest.main()
