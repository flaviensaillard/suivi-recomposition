package fr.recomposition.suivi;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.util.Base64;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Pont natif Android pour l'application Équilibre.
 *
 * Fournit l'accès réseau direct sans restriction CORS (nécessaire depuis file:///),
 * les retours haptiques tactiles, l'ouverture sécurisée des liens externes et
 * le partage natif.
 */
public class NativeBridge {

    public interface JsRunner {
        void eval(String js);
    }

    private static final String TAG = "EquilibreNative";
    private static final int TIMEOUT_MS = 25000;
    private static final String UA =
            "Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) "
                    + "Chrome/124.0.0.0 Mobile Safari/537.36 EquilibreApp/1.0.12";

    private final Activity activity;
    private final JsRunner js;
    private final ExecutorService pool = Executors.newFixedThreadPool(4);

    NativeBridge(Activity activity, JsRunner js) {
        this.activity = activity;
        this.js = js;
    }

    @JavascriptInterface
    public void httpAsync(final String method, final String url, final String headersJson,
                          final String body, final String callbackId) {
        pool.execute(new Runnable() {
            @Override
            public void run() {
                JSONObject res = executer(method, url, headersJson, body);
                String payload = res.optString("body", "");
                res.remove("body");
                try {
                    res.put("body_b64", Base64.encodeToString(
                            payload.getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP));
                } catch (Exception ignore) {
                    try {
                        res.put("body_b64", "");
                    } catch (Exception ignore2) {
                    }
                }
                final String jsAppel = "window.EQ && EQ.net && EQ.net._fin('" + callbackId + "', " + res.toString() + ")";
                if (js != null) {
                    js.eval(jsAppel);
                }
            }
        });
    }

    @JavascriptInterface
    public String http(String method, String url, String headersJson, String body) {
        return executer(method, url, headersJson, body).toString();
    }

    private JSONObject executer(String method, String url, String headersJson, String body) {
        HttpURLConnection conn = null;
        try {
            URL u = new URL(url);
            conn = (HttpURLConnection) u.openConnection();
            conn.setRequestMethod(method == null ? "GET" : method.toUpperCase(Locale.US));
            conn.setConnectTimeout(TIMEOUT_MS);
            conn.setReadTimeout(TIMEOUT_MS);
            conn.setInstanceFollowRedirects(true);
            conn.setRequestProperty("User-Agent", UA);
            conn.setRequestProperty("Accept", "application/json, text/plain, */*");

            if (headersJson != null && !headersJson.isEmpty() && !headersJson.equals("null")) {
                JSONObject h = new JSONObject(headersJson);
                java.util.Iterator<String> it = h.keys();
                while (it.hasNext()) {
                    String k = it.next();
                    conn.setRequestProperty(k, h.optString(k, ""));
                }
            }

            if (body != null && !body.isEmpty() && !body.equals("null")) {
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json");
                byte[] out = body.getBytes(StandardCharsets.UTF_8);
                conn.setFixedLengthStreamingMode(out.length);
                OutputStream os = conn.getOutputStream();
                os.write(out);
                os.flush();
                os.close();
            }

            int status = conn.getResponseCode();
            InputStream is = status >= 400 ? conn.getErrorStream() : conn.getInputStream();
            String payload = is == null ? "" : readAll(is);
            JSONObject res = new JSONObject();
            res.put("ok", status >= 200 && status < 300);
            res.put("status", status);
            res.put("body", payload);
            return res;
        } catch (Exception e) {
            Log.w(TAG, "HTTP " + method + " " + url + " : " + e.getMessage());
            JSONObject err = new JSONObject();
            try {
                err.put("ok", false);
                err.put("status", -1);
                err.put("error", String.valueOf(e.getMessage()));
                err.put("body", "");
            } catch (Exception ignore) {
            }
            return err;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private static String readAll(InputStream is) throws Exception {
        BufferedReader r = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = r.readLine()) != null) {
            sb.append(line).append('\n');
        }
        r.close();
        return sb.toString();
    }

    @JavascriptInterface
    public boolean isOnline() {
        try {
            ConnectivityManager cm = (ConnectivityManager) activity.getSystemService(Context.CONNECTIVITY_SERVICE);
            if (cm == null) return false;
            NetworkInfo ni = cm.getActiveNetworkInfo();
            return ni != null && ni.isConnected();
        } catch (Exception e) {
            return false;
        }
    }

    @JavascriptInterface
    public void haptic(int ms) {
        try {
            Vibrator v = (Vibrator) activity.getSystemService(Context.VIBRATOR_SERVICE);
            if (v == null) return;
            int d = Math.max(1, Math.min(ms <= 0 ? 12 : ms, 120));
            if (Build.VERSION.SDK_INT >= 26) {
                v.vibrate(VibrationEffect.createOneShot(d, VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                v.vibrate(d);
            }
        } catch (Exception ignored) {
        }
    }

    @JavascriptInterface
    public void toast(final String message) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(activity, message, Toast.LENGTH_SHORT).show();
            }
        });
    }

    @JavascriptInterface
    public void openExternal(String url) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(i);
        } catch (Exception e) {
            Log.w(TAG, "openExternal: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public void share(String title, String text) {
        try {
            Intent i = new Intent(Intent.ACTION_SEND);
            i.setType("text/plain");
            i.putExtra(Intent.EXTRA_SUBJECT, title);
            i.putExtra(Intent.EXTRA_TEXT, text);
            activity.startActivity(Intent.createChooser(i, "Partager"));
        } catch (Exception e) {
            Log.w(TAG, "share: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public int versionCode() {
        return 13;
    }

    @JavascriptInterface
    public String versionName() {
        try {
            return activity.getPackageManager()
                    .getPackageInfo(activity.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "1.0.12";
        }
    }
}
