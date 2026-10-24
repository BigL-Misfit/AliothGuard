// SPDX-License-Identifier: MIT
package io.github.biglmisfit.aliothguard.test;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.widget.TextView;
import java.io.File;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    static { System.loadLibrary("ag_test_reader"); }
    public static native boolean nativeSelfTest();
    public static native boolean nativeProbeObserved();

    public static JSONObject report() throws Exception {
        JSONObject root = new JSONObject();
        root.put("state", "OBSERVATIONS_ONLY");
        root.put("build_test_keys", Build.TAGS != null && Build.TAGS.contains("test-keys"));
        root.put("system_su_path_visible", new File("/system/bin/su").exists() || new File("/system/xbin/su").exists());
        root.put("limits", "Visibility can be restricted or spoofed. No su execution, package enumeration or root verdict.");
        JSONObject integrity = new JSONObject();
        integrity.put("state", "NOT_REQUESTED");
        integrity.put("basic", JSONObject.NULL);
        integrity.put("device", JSONObject.NULL);
        integrity.put("strong", JSONObject.NULL);
        JSONObject result = new JSONObject();
        result.put("native_policy_self_test", nativeSelfTest() ? "PASS" : "FAIL");
        result.put("zygisk_probe", nativeProbeObserved() ? "OBSERVED_IN_THIS_PROCESS" : "NOT_OBSERVED");
        result.put("probe_limits", "A process marker is diagnostic, not authenticated attestation or proof of hiding.");
        result.put("root_detection", root);
        result.put("play_integrity", integrity);
        result.put("sdk", Build.VERSION.SDK_INT);
        return result;
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView text = new TextView(this);
        text.setPadding(24, 40, 24, 24);
        text.setTextIsSelectable(true);
        try { text.setText("AliothGuard Lab — v0.2.0\n\n" + report().toString(2)); }
        catch (Exception error) { text.setText("Diagnostic failed: " + error); }
        setContentView(text);
    }
}
