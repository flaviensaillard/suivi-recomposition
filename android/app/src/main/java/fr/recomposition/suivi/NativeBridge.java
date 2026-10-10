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
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.widget.Toast;

/**
 * Pont natif minimal pour l'interface locale Équilibre.
 *
 * Aucun transport HTTP n'est exposé au JavaScript : la coque n'accepte pas de
 * clé Supabase et ne prétend pas synchroniser les données. Les liens Web sont
 * ouverts dans le navigateur système, hors du WebView privilégié.
 */
public class NativeBridge {

    private static final String TAG = "EquilibreNative";
    private final Activity activity;

    NativeBridge(Activity activity) {
        this.activity = activity;
    }

    @JavascriptInterface
    public boolean isOnline() {
        try {
            ConnectivityManager cm = (ConnectivityManager)
                    activity.getSystemService(Context.CONNECTIVITY_SERVICE);
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
                String texte = message == null ? "" : message;
                if (texte.length() > 220) texte = texte.substring(0, 220);
                Toast.makeText(activity, texte, Toast.LENGTH_SHORT).show();
            }
        });
    }

    @JavascriptInterface
    public void openExternal(String url) {
        try {
            Uri uri = Uri.parse(url == null ? "" : url);
            if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null) {
                return;
            }
            Intent intent = new Intent(Intent.ACTION_VIEW, uri);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);
        } catch (Exception e) {
            Log.w(TAG, "openExternal: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public void share(String title, String text) {
        try {
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("text/plain");
            intent.putExtra(Intent.EXTRA_SUBJECT, title == null ? "Équilibre" : title);
            intent.putExtra(Intent.EXTRA_TEXT, text == null ? "" : text);
            activity.startActivity(Intent.createChooser(intent, "Partager"));
        } catch (Exception e) {
            Log.w(TAG, "share: " + e.getMessage());
        }
    }

    @JavascriptInterface
    public int versionCode() {
        return 14;
    }

    @JavascriptInterface
    public String versionName() {
        try {
            return activity.getPackageManager()
                    .getPackageInfo(activity.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "1.0.13";
        }
    }
}
