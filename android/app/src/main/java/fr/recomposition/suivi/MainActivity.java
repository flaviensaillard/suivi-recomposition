package fr.recomposition.suivi;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.text.InputType;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Suivi Recomposition — coque Android de l'application Streamlit.
 *
 * Cette application est une "fenêtre" native qui affiche ton application Streamlit hébergée
 * (Streamlit Community Cloud) et mémorise son adresse. Au premier lancement, elle te demande
 * l'adresse de ton application ; ensuite elle s'ouvre directement dessus.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "suivi_recomposition";
    private static final String KEY_URL = "app_url";

    private static final int NAVY  = 0xFF0F2A43;
    private static final int TEAL  = 0xFF0D9488;
    private static final int BG    = 0xFFF4F7FA;
    private static final int INK   = 0xFF1C2530;
    private static final int MUTED = 0xFF5B6B7C;
    private static final int LINE  = 0xFFDFE6EC;

    private SharedPreferences prefs;
    private WebView web;
    private ProgressBar bar;
    private boolean errorShown = false;

    // ------------------------------------------------------------------ cycle de vie
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (Build.VERSION.SDK_INT >= 21) {
            Window w = getWindow();
            w.setStatusBarColor(NAVY);
            w.setNavigationBarColor(NAVY);
        }
        String url = prefs.getString(KEY_URL, "");
        if (url == null || url.trim().length() == 0) {
            showSetup(false);
        } else {
            showApp(url);
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    // ------------------------------------------------------------------ utilitaires
    private int dp(float v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v,
                getResources().getDisplayMetrics());
    }

    private TextView label(String txt, int sizeSp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(txt);
        t.setTextSize(sizeSp);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setLineSpacing(dp(3), 1f);
        return t;
    }

    private TextView action(String txt) {
        TextView t = label(txt, 20, Color.WHITE, false);
        t.setPadding(dp(12), dp(6), dp(12), dp(6));
        t.setGravity(Gravity.CENTER);
        return t;
    }

    // ------------------------------------------------------------------ écran de configuration
    private void showSetup(boolean fromMenu) {
        if (web != null) { web.destroy(); web = null; }
        String saved = prefs.getString(KEY_URL, "");

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(28), dp(24), dp(28));
        scroll.addView(root);

        TextView titre = label("Suivi Recomposition", 26, NAVY, true);
        root.addView(titre);

        TextView sous = label("Perte de gras sans perte de muscle", 15, MUTED, false);
        sous.setPadding(0, dp(2), 0, dp(18));
        root.addView(sous);

        TextView intro = label("Cette application affiche ton suivi hébergé en ligne, avec un vrai "
                + "bouton sur ton téléphone. Renseigne une seule fois l'adresse de ton application "
                + "Streamlit, puis appuie sur Ouvrir : elle sera mémorisée.", 15, INK, false);
        intro.setPadding(0, 0, 0, dp(18));
        root.addView(intro);

        // encadré "où trouver mon adresse"
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(Color.WHITE);
        card.setPadding(dp(16), dp(16), dp(16), dp(16));
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.bottomMargin = dp(18);
        root.addView(card, cardLp);

        card.addView(label("Où trouver mon adresse ?", 16, NAVY, true));
        TextView steps = label(
                "1. Sur share.streamlit.io, ouvre ton application.\n"
                        + "2. L'adresse ressemble à :\n"
                        + "   https://suivi-recomposition.streamlit.app\n"
                        + "3. Copie-la et colle-la dans le champ ci-dessous.",
                15, MUTED, false);
        steps.setPadding(0, dp(8), 0, 0);
        card.addView(steps);

        EditText input = new EditText(this);
        input.setHint("https://mon-app.streamlit.app");
        input.setText(saved);
        input.setInputType(InputType.TYPE_TEXT_VARIATION_URI | InputType.TYPE_CLASS_TEXT);
        input.setTextSize(15);
        input.setPadding(dp(12), dp(12), dp(12), dp(12));
        input.setBackgroundColor(Color.WHITE);
        LinearLayout.LayoutParams inLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        inLp.bottomMargin = dp(14);
        root.addView(input, inLp);

        Button ok = new Button(this);
        ok.setText("Ouvrir mon application");
        ok.setAllCaps(false);
        ok.setTextSize(16);
        ok.setBackgroundColor(TEAL);
        ok.setTextColor(Color.WHITE);
        ok.setPadding(dp(12), dp(14), dp(12), dp(14));
        root.addView(ok, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        ok.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String u = input.getText().toString().trim();
                if (u.length() == 0) {
                    Toast.makeText(MainActivity.this, "Colle d'abord l'adresse de ton application.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                if (!u.startsWith("http://") && !u.startsWith("https://")) u = "https://" + u;
                if (u.endsWith("/")) u = u.substring(0, u.length() - 1);
                prefs.edit().putString(KEY_URL, u).apply();
                showApp(u);
            }
        });

        TextView note = label("Ton adresse reste enregistrée sur ce téléphone. Tu peux la modifier "
                + "à tout moment avec le bouton ⚙ une fois l'application ouverte.", 13, MUTED, false);
        note.setPadding(0, dp(18), 0, 0);
        root.addView(note);

        setContentView(scroll);
    }

    // ------------------------------------------------------------------ écran principal
    private void showApp(String url) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        // --- barre de titre
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setBackgroundColor(NAVY);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(16), dp(8), dp(8), dp(8));

        TextView title = label("Suivi Recomposition", 17, Color.WHITE, true);
        header.addView(title, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView reload = action("⟳");
        reload.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (web != null) web.reload();
            }
        });
        header.addView(reload);

        TextView gear = action("⚙");
        gear.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                menu();
            }
        });
        header.addView(gear);

        root.addView(header, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        // --- barre de chargement
        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        bar.setMax(100);
        bar.setVisibility(View.GONE);
        root.addView(bar, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(3)));

        // --- vue web
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setUserAgentString(s.getUserAgentString() + " SuiviApp/1.0");
        if (Build.VERSION.SDK_INT >= 21) {
            CookieManager.getInstance().setAcceptThirdPartyCookies(web, true);
        }
        CookieManager.getInstance().setAcceptCookie(true);

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int p) {
                if (bar == null) return;
                bar.setProgress(p);
                bar.setVisibility(p < 100 ? View.VISIBLE : View.GONE);
            }
        });

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String u) {
                return handleUrl(u);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                return handleUrl(req.getUrl().toString());
            }

            @Override
            public void onPageFinished(WebView view, String u) {
                errorShown = false;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req != null && req.isForMainFrame()) erreur(err == null ? "" : err.getDescription().toString());
            }

            @Override
            public void onReceivedError(WebView view, int code, String desc, String failingUrl) {
                erreur(desc == null ? "" : desc);
            }
        });

        web.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String u, String agent, String disposition, String mime, long size) {
                Toast.makeText(MainActivity.this,
                        "Le téléchargement de fichiers n'est pas géré ici : fais ton export depuis l'ordinateur.",
                        Toast.LENGTH_LONG).show();
            }
        });

        web.loadUrl(url);

        root.addView(web, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
    }

    /** Ouvre les liens externes (mail, téléphone, autre site) hors de l'application. */
    private boolean handleUrl(String u) {
        if (u == null) return false;
        if (u.startsWith("http://") || u.startsWith("https://")) return false; // on reste dedans
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u)));
        } catch (Exception e) {
            Toast.makeText(this, "Lien impossible à ouvrir.", Toast.LENGTH_SHORT).show();
        }
        return true;
    }

    private void erreur(String detail) {
        if (errorShown) return;
        errorShown = true;
        final String saved = prefs.getString(KEY_URL, "");
        new AlertDialog.Builder(this)
                .setTitle("Impossible de charger l'application")
                .setMessage("Vérifie ta connexion internet, puis réessaie.\n\n"
                        + "Si le message persiste :\n"
                        + "• l'application Streamlit est peut-être en veille — le premier chargement "
                        + "peut prendre 30 secondes, réessaie.\n"
                        + "• l'adresse est peut-être erronée : vérifie-la avec ⚙.\n"
                        + "\nAdresse enregistrée :\n" + saved
                        + (detail.length() > 0 ? "\n\nDétail technique : " + detail : ""))
                .setPositiveButton("Réessayer", new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface d, int w) {
                        errorShown = false;
                        if (web != null) web.reload();
                    }
                })
                .setNegativeButton("Changer d'adresse", new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface d, int w) {
                        showSetup(true);
                    }
                })
                .setNeutralButton("Fermer", null)
                .show();
    }

    // ------------------------------------------------------------------ menu ⚙
    private void menu() {
        final String[] options = new String[]{
                "Modifier l'adresse de l'application",
                "Recharger la page",
                "Ouvrir dans le navigateur",
                "Vider le cache"
        };
        new AlertDialog.Builder(this)
                .setTitle("Options")
                .setItems(options, new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface d, int which) {
                        switch (which) {
                            case 0:
                                showSetup(true);
                                break;
                            case 1:
                                if (web != null) web.reload();
                                break;
                            case 2: {
                                String u = prefs.getString(KEY_URL, "");
                                try {
                                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(u)));
                                } catch (Exception e) {
                                    Toast.makeText(MainActivity.this, "Ouverture impossible.",
                                            Toast.LENGTH_SHORT).show();
                                }
                                break;
                            }
                            case 3:
                                if (web != null) {
                                    web.clearCache(true);
                                    web.clearHistory();
                                }
                                Toast.makeText(MainActivity.this, "Cache vidé.", Toast.LENGTH_SHORT).show();
                                break;
                            default:
                                break;
                        }
                    }
                })
                .show();
    }
}
