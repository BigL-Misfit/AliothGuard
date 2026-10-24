// SPDX-License-Identifier: MIT
package io.github.biglmisfit.aliothguard.test;

import android.app.Instrumentation;
import android.app.Activity;
import android.os.Bundle;
import org.json.JSONObject;

public final class SmokeTest extends Instrumentation {
    @Override public void onCreate(Bundle args) { super.onCreate(args); start(); }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            JSONObject report = MainActivity.report();
            if (report.getInt("sdk") != 35 || !MainActivity.nativeSelfTest()
                    || MainActivity.nativeProbeObserved()
                    || !"NOT_REQUESTED".equals(report.getJSONObject("play_integrity").getString("state"))) {
                throw new IllegalStateException("Unexpected unrooted-emulator result: " + report);
            }
            result.putString("stream", "AGX_APP_SMOKE_PASS\n" + report.toString() + "\n");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable error) {
            result.putString("stream", "AGX_APP_SMOKE_FAIL: " + error + "\n");
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
