package fr.recomposition.suivi;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
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
 * Suivi Recomposition — coque Android à DEUX applications.
 *
 * Cette application affiche deux applications Streamlit hébergées :
 *   • l'application « Suivi »  (pesée, séances, protéines…)
 *   • l'application « Menus »  (recettes, menus, liste de courses) — facultative
 * et permet de passer de l'une à l'autre d'un appui (bouton ⇄).
 *
 * Les deux adresses sont mémorisées sur le téléphone : elles ne sont demandées qu'une fois.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "suivi_recomposition";
    private static final String KEY_URL1 = "url_suivi";
    private static final String KEY_URL2 = "url_menus";
    private static final String KEY_CURRENT = "app_courante";
    private static final String LABEL1 = "Suivi";
    private static final String LABEL2 = "Menus";

    private static final int NAVY  = 0xFF0F2A43;
    private static final int TEAL  = 0xFF0D9488;
    private static final int BG    = 0xFFF4F7FA;
    private static final int INK   = 0xFF1C2530;
    private static final int MUTED = 0xFF5B6B7C;

    private SharedPreferences prefs;
    private WebView web;
    private ProgressBar bar;
    private TextView titre;
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
        if (urlActive().length() == 0) {
            showSetup();
        } else {
            showApp();
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

    // ------------------------------------------------------------------ préférences
    private int courante() {
        return prefs.getInt(KEY_CURRENT, 1) == 2 ? 2 : 1;
    }

    private String urlActive() {
        String u = courante() == 2 ? prefs.getString(KEY_URL2, "") : prefs.getString(KEY_URL1, "");
        return u == null ? "" : u.trim();
    }

    private boolean deuxiemeConfiguree() {
        String u = prefs.getString(KEY_URL2, "");
        return u != null && u.trim().length() > 0;
    }

    private String labelActif() {
        return courante() == 2 ? LABEL2 : LABEL1;
    }

    private void basculer() {
        prefs.edit().putInt(KEY_CURRENT, courante() == 1 ? 2 : 1).apply();
        if (urlActive().length() == 0) {
            showSetup();
        } else {
            showApp();
        }
    }

    // ------------------------------------------------------------------ utilitaires UI
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
    private void showSetup() {
        if (web != null) { web.destroy(); web = null; }

        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(24), dp(28), dp(24), dp(28));
        scroll.addView(root);

        root.addView(label("Mes applications", 26, NAVY, true));
        TextView sous = label("Suivi de recomposition  +  Menus et recettes", 15, MUTED, false);
        sous.setPadding(0, dp(2), 0, dp(18));
        root.addView(sous);

        root.addView(label("Renseigne une seule fois l'adresse de chaque application Streamlit. "
                + "Ensuite, le bouton ⇄ en haut de l'écran permet de passer de l'une à l'autre "
                + "sans quitter l'application.", 15, INK, false));

        // --- encadré d'aide
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setBackgroundColor(Color.WHITE);
        card.setPadding(dp(16), dp(16), dp(16), dp(16));
        LinearLayout.LayoutParams cardLp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cardLp.topMargin = dp(16);
        cardLp.bottomMargin = dp(16);
        root.addView(card, cardLp);
        card.addView(label("Où trouver ces adresses ?", 16, NAVY, true));
        TextView steps = label("Sur share.streamlit.io, ouvre une application : son adresse s'affiche "
                + "en haut de la page et ressemble à :\n   https://mon-app.streamlit.app\n\n"
                + "Tu peux aussi la lire dans la barre d'adresse du navigateur quand tu utilises "
                + "l'application.", 15, MUTED, false);
        steps.setPadding(0, dp(8), 0, 0);
        card.addView(steps);

        EditText in1 = new EditText(this);
        in1.setHint("https://suivi-recomposition.streamlit.app");
        in1.setText(prefs.getString(KEY_URL1, ""));
        in1.setInputType(InputType.TYPE_TEXT_VARIATION_URI | InputType.TYPE_CLASS_TEXT);
        in1.setTextSize(15);
        in1.setPadding(dp(12), dp(12), dp(12), dp(12));
        in1.setBackgroundColor(Color.WHITE);

        EditText in2 = new EditText(this);
        in2.setHint("https://gestion-menus.streamlit.app");
        in2.setText(prefs.getString(KEY_URL2, ""));
        in2.setInputType(InputType.TYPE_TEXT_VARIATION_URI | InputType.TYPE_CLASS_TEXT);
        in2.setTextSize(15);
        in2.setPadding(dp(12), dp(12), dp(12), dp(12));
        in2.setBackgroundColor(Color.WHITE);

        root.addView(label("1. Application SUIVI (pesée, séances, protéines)", 15, NAVY, true));
        LinearLayout.LayoutParams lp1 = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp1.topMargin = dp(6);
        lp1.bottomMargin = dp(16);
        root.addView(in1, lp1);

        root.addView(label("2. Application MENUS (facultative — recettes, courses)", 15, NAVY, true));
        LinearLayout.LayoutParams lp2 = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp2.topMargin = dp(6);
        lp2.bottomMargin = dp(18);
        root.addView(in2, lp2);

        Button ok = new Button(this);
        ok.setText("Enregistrer et ouvrir");
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
                String u1 = nettoyer(in1.getText().toString());
                String u2 = nettoyer(in2.getText().toString());
                if (u1.length() == 0) {
                    Toast.makeText(MainActivity.this,
                            "Renseigne au moins l'adresse de l'application Suivi.",
                            Toast.LENGTH_LONG).show();
                    return;
                }
                prefs.edit().putString(KEY_URL1, u1).putString(KEY_URL2, u2)
                        .putInt(KEY_CURRENT, 1).apply();
                showApp();
            }
        });

        TextView note = label("Les adresses restent enregistrées sur ce téléphone. "
                + "Tu peux les modifier à tout moment avec le bouton ⚙.", 13, MUTED, false);
        note.setPadding(0, dp(18), 0, 0);
        root.addView(note);

        setContentView(scroll);
    }

    private String nettoyer(String u) {
        u = u == null ? "" : u.trim();
        if (u.length() == 0) return "";
        if (!u.startsWith("http://") && !u.startsWith("https://")) u = "https://" + u;
        while (u.endsWith("/")) u = u.substring(0, u.length() - 1);
        return u;
    }

    // ------------------------------------------------------------------ écran principal
    private void showApp() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);

        // --- barre de titre
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setBackgroundColor(NAVY);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(16), dp(8), dp(8), dp(8));

        titre = label(labelActif(), 17, Color.WHITE, true);
        header.addView(titre, new LinearLayout.LayoutParams(0,
                ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        if (deuxiemeConfiguree()) {
            TextView swap = action("⇄");
            swap.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    basculer();
                }
            });
            header.addView(swap);
        }

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
        if (web != null) web.destroy();
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
        s.setUserAgentString(s.getUserAgentString() + " SuiviApp/1.1");
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
                        "Export de fichiers : à faire depuis l'ordinateur (page Réglages).",
                        Toast.LENGTH_LONG).show();
            }
        });

        web.loadUrl(urlActive());

        root.addView(web, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));

        setContentView(root);
    }

    private boolean handleUrl(String u) {
        if (u == null) return false;
        if (u.startsWith("http://") || u.startsWith("https://")) return false;
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
        final String saved = urlActive();
        new AlertDialog.Builder(this)
                .setTitle("Impossible de charger l'application")
                .setMessage("Vérifie ta connexion internet, puis réessaie.\n\n"
                        + "• L'application Streamlit était peut-être en veille : le premier chargement "
                        + "peut prendre 30 secondes.\n"
                        + "• L'adresse est peut-être erronée : vérifie-la avec ⚙.\n"
                        + "\nApplication : " + labelActif() + "\nAdresse :\n" + saved
                        + (detail.length() > 0 ? "\n\nDétail technique : " + detail : ""))
                .setPositiveButton("Réessayer", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        errorShown = false;
                        if (web != null) web.reload();
                    }
                })
                .setNegativeButton("Changer d'adresse", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int w) {
                        showSetup();
                    }
                })
                .setNeutralButton("Fermer", null)
                .show();
    }

    // ------------------------------------------------------------------ menu ⚙
    private void menu() {
        boolean deux = deuxiemeConfiguree();
        final String[] options = deux
                ? new String[]{"Passer à " + (courante() == 1 ? LABEL2 : LABEL1), "Modifier les adresses",
                               "Recharger la page", "Ouvrir dans le navigateur", "Vider le cache"}
                : new String[]{"Modifier l'adresse", "Recharger la page",
                               "Ouvrir dans le navigateur", "Vider le cache"};
        new AlertDialog.Builder(this)
                .setTitle("Options — " + labelActif())
                .setItems(options, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface d, int which) {
                        int i = 0;
                        if (deux && which == i++) {
                            basculer();
                            return;
                        }
                        if (which == i++) {                      // adresses
                            showSetup();
                            return;
                        }
                        if (which == i++) {                      // recharger
                            if (web != null) web.reload();
                            return;
                        }
                        if (which == i++) {                      // navigateur
                            try {
                                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(urlActive())));
                            } catch (Exception e) {
                                Toast.makeText(MainActivity.this, "Ouverture impossible.",
                                        Toast.LENGTH_SHORT).show();
                            }
                            return;
                        }
                        if (web != null) {                       // cache
                            web.clearCache(true);
                            web.clearHistory();
                        }
                        Toast.makeText(MainActivity.this, "Cache vidé.", Toast.LENGTH_SHORT).show();
                    }
                })
                .show();
    }
}
