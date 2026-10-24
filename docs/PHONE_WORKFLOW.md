# Chrome-only repository and CI workflow

Repository editing and CI control work in Chrome. Android's existing file
manager extracts downloaded containers; no PC, OTG, Termux or paid tools are
required. Use Chrome → three-dot menu → **Desktop site** if controls are hidden.

## Put source on GitHub and review it

1. Sign in and open `BigL-Misfit/AliothGuard`. Select the branch menu, type a
   name such as `phase1-diagnostics`, and choose **Create branch**.
2. Open a file → pencil icon → edit → **Commit changes** to your branch.
   Use **Add file → Create new file** for new paths, including subdirectories
   such as `.github/workflows/ci.yml`. **Upload files** accepts files available
   on your phone; keep their directory structure. Uploading a source ZIP does
   not extract it into a project. `github.dev` offers a multi-file editor but
   can be awkward on a small screen; landscape mode helps.
3. If files were prepared in a coding workspace, use its supported commit/push
   or pull-request controls first. Local files are not on GitHub until pushed.
   Do not upload `dist/`, `reports/`, caches, credentials or phone logs.
4. Open **Pull requests → New pull request**, choose your branch, review the
   changes and checks, and create the PR. Check for unexpected binaries, boot
   scripts, destructive commands or secrets. Merge only after review. CI never
   deploys to your phone.

## Run Actions

1. Open **Actions**. If a fork has Actions disabled, review the workflow and
   enable it using GitHub's displayed prompt.
2. Select **Validate and build AliothGuard**. Pushes/PRs run automatically.
   The manual **Run workflow** control requires the workflow to be present on
   the default branch; push/PR checks can run before it is merged there.
3. Tap **Run workflow**, choose the branch and leave **emulator** unchecked for
   the normal build. Select it only for the optional Android 15 shell smoke
   test, then tap the final **Run workflow** button.
4. Open the run and confirm its branch and commit SHA. Review `validate-build`
   steps for lint, tests, archive validation and checksum. A red/cancelled run
   is not approval to use an older artifact. A skipped emulator job is unrun.
5. Review test reports before assessing installation. Even all-green checks
   leave Magisk lifecycle, Mi 11X hardware, OrangeFox and device safety untested.

## Download results

1. On the completed run's summary, scroll to **Artifacts** while signed in.
   Download `AliothGuard-test-reports` first. Extract it using Android's file
   manager and open `tests.txt`, `tests.json` and `validation.txt`. Read failures,
   skips and limitations. JUnit XML is included for machine-readable results.
2. From the **same run/commit**, download `AliothGuard-v0.1.0`. GitHub gives you
   an outer container ZIP. Extract it once to obtain the actual
   `AliothGuard-v0.1.0.zip` and `SHA256SUMS.txt`.
3. Keep the inner module ZIP intact. The outer container and **Code → Download
   ZIP** source archive are not module installers. Chrome may add `(1)` to a
   duplicate download; verify the inner filename.
4. Compare `SHA256SUMS.txt` with that run's build log. If your file manager can
   calculate SHA-256, also hash the **inner** module ZIP. Comparing two text
   hashes does not verify the downloaded bytes. Do not upload files to an
   online hashing site. CI verifies its generated archive, not your phone copy.

Artifacts expire after 14 days (emulator reports after 7); rerun the reviewed
commit when needed. Public repositories use free standard hosted runners and
may expose logs/artifacts publicly. Private repositories have account-specific
quotas: keep spending limits at zero and avoid paid/larger runners. No secret
or payment is required by this workflow. It does not publish a GitHub Release.

**Stop at review for this phase. No request to install the build is part of
the development workflow.** Read the recovery limitations before any later
device-safety decision.
