package fr.recomposition.suivi;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.Context;
import android.content.Intent;
import android.content.DialogInterface;
import android.content.pm.PackageManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.CancellationSignal;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.util.Log;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
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
    private WebView webView;

    NativeBridge(Activity activity) {
        this.activity = activity;
    }

    /** Le pont rappelle le JavaScript via ce WebView (résultats asynchrones). */
    void setWebView(WebView webView) {
        this.webView = webView;
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
        return 25;
    }

    @JavascriptInterface
    public String versionName() {
        try {
            return activity.getPackageManager()
                    .getPackageInfo(activity.getPackageName(), 0).versionName;
        } catch (Exception e) {
            return "1.4";
        }
    }

    // ---------------------------------------------------------------------
    // 1.4 : déverrouillage par empreinte à l'ouverture de l'application.
    // BiometricPrompt de la plateforme (API 28+) : aucune dépendance AndroidX.
    // ---------------------------------------------------------------------

    /** Vrai si un capteur biométrique est présent ET l'appareil est sécurisé. */
    @JavascriptInterface
    public boolean biometrieDisponible() {
        if (Build.VERSION.SDK_INT < 28) return false;
        try {
            PackageManager pm = activity.getPackageManager();
            boolean materiel = pm != null && (
                    pm.hasSystemFeature(PackageManager.FEATURE_FINGERPRINT)
                    || pm.hasSystemFeature("android.hardware.biometrics.face"));
            if (!materiel) return false;
            KeyguardManager km = (KeyguardManager)
                    activity.getSystemService(Context.KEYGUARD_SERVICE);
            return km != null && km.isDeviceSecure();
        } catch (Exception e) {
            Log.w(TAG, "biometrieDisponible", e);
            return false;
        }
    }

    /**
     * Ouvre l'invite biométrique. Le résultat revient en JavaScript via
     * NativeSurEmpreinte(callbackId, succes, message).
     */
    @JavascriptInterface
    public void demanderEmpreinte(final String callbackId) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (Build.VERSION.SDK_INT < 28) {
                    rappeler(callbackId, false, "Empreinte indisponible avant Android 9");
                    return;
                }
                try {
                    BiometricPrompt invite = new BiometricPrompt.Builder(activity)
                            .setTitle("Équilibre")
                            .setSubtitle("Identifie-toi pour ouvrir l'application")
                            .setNegativeButton("Annuler", activity.getMainExecutor(),
                                    new DialogInterface.OnClickListener() {
                                        @Override
                                        public void onClick(DialogInterface d, int which) {
                                            rappeler(callbackId, false, "Annulé");
                                        }
                                    })
                            .build();
                    invite.authenticate(new CancellationSignal(), activity.getMainExecutor(),
                            new BiometricPrompt.AuthenticationCallback() {
                                @Override
                                public void onAuthenticationSucceeded(
                                        BiometricPrompt.AuthenticationResult result) {
                                    rappeler(callbackId, true, "");
                                }

                                @Override
                                public void onAuthenticationError(int errorCode,
                                                                  CharSequence errString) {
                                    rappeler(callbackId, false,
                                            errString == null ? "Erreur " + errorCode
                                                              : String.valueOf(errString));
                                }
                            });
                } catch (Exception e) {
                    Log.w(TAG, "demanderEmpreinte", e);
                    rappeler(callbackId, false, e.getMessage());
                }
            }
        });
    }

    private void rappeler(final String callbackId, final boolean succes, final String message) {
        final WebView cible = webView;
        if (cible == null || callbackId == null || callbackId.trim().isEmpty()) return;
        final String js = "try{window.NativeSurEmpreinte&&window.NativeSurEmpreinte("
                + quote(callbackId) + "," + (succes ? "true" : "false") + ","
                + quote(message == null ? "" : message) + ")}catch(e){}";
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                cible.evaluateJavascript(js, null);
            }
        });
    }

    private static String quote(String texte) {
        return "'" + texte.replace("\\", "\\\\")
                .replace("'", "\\'")
                .replace("\n", " ")
                .replace("\r", " ") + "'";
    }
}
