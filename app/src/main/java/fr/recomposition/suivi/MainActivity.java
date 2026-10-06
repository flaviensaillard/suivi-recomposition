package fr.recomposition.suivi;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.animation.AlphaAnimation;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/**
 * Coque Android native de l'application Équilibre (Suivi & Menus).
 *
 * Exécute l'application mobile locale fluide et tactile (HTML5/CSS/JS)
 * stockée dans les assets, tout en offrant une passerelle directe vers
 * les services distants et les deux applications Streamlit (Suivi et Menus).
 */
public class MainActivity extends Activity implements NativeBridge.JsRunner {

    private static final String PAGE = "file:///android_asset/www/index.html";

    private WebView webView;
    private NativeBridge pont;
    private View splash;
    private boolean backPressedOnce = false;
    private final Handler handler = new Handler(Looper.getMainLooper());

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Window w = getWindow();
        if (Build.VERSION.SDK_INT >= 28) {
            w.getAttributes().layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }
        if (Build.VERSION.SDK_INT >= 30) {
            w.setDecorFitsSystemWindows(false);
        }
        w.setStatusBarColor(Color.TRANSPARENT);
        w.setNavigationBarColor(Color.TRANSPARENT);

        setContentView(R.layout.activity_main);
        splash = findViewById(R.id.splash);
        webView = findViewById(R.id.webview);

        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setLoadWithOverviewMode(false);
        s.setUseWideViewPort(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setTextZoom(100);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setLayoutAlgorithm(WebSettings.LayoutAlgorithm.NORMAL);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        if (Build.VERSION.SDK_INT >= 26) {
            s.setSafeBrowsingEnabled(false);
        }
        CookieManager.getInstance().setAcceptCookie(true);
        if (Build.VERSION.SDK_INT >= 21) {
            CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url != null && url.startsWith("file:///android_asset/")) {
                    return false;
                }
                if (url != null && (url.startsWith("http://") || url.startsWith("https://"))) {
                    // Les liens web internes sont gérés par l'interface ou le pont
                    return false;
                }
                if (url != null && pont != null) {
                    pont.openExternal(url);
                    return true;
                }
                return false;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideSplash();
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
        webView.setBackgroundColor(Color.parseColor("#0B0F17"));
        pont = new NativeBridge(this, this);
        webView.addJavascriptInterface(pont, "Native");
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        if (savedInstanceState == null) {
            webView.loadUrl(PAGE);
        }

        // Sécurité : masque l'écran de chargement après 5 secondes maximum
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                hideSplash();
            }
        }, 5000);
    }

    private void hideSplash() {
        if (splash == null || splash.getVisibility() != View.VISIBLE) return;
        AlphaAnimation fade = new AlphaAnimation(1f, 0f);
        fade.setDuration(280);
        splash.startAnimation(fade);
        splash.setVisibility(View.GONE);
    }

    @Override
    public void eval(final String js) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (webView != null) {
                    try {
                        webView.evaluateJavascript(js, null);
                    } catch (Exception ignored) {
                    }
                }
            }
        });
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (webView != null) webView.saveState(outState);
    }

    @Override
    protected void onRestoreInstanceState(Bundle savedInstanceState) {
        super.onRestoreInstanceState(savedInstanceState);
        if (webView != null) webView.restoreState(savedInstanceState);
    }

    @Override
    public void onBackPressed() {
        if (webView == null) {
            super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{return (typeof App!=='undefined' && App.onBack) ? String(App.onBack()) : 'false';}catch(e){return 'false';}})()",
                value -> {
                    boolean handled = value != null && value.contains("true");
                    if (handled) {
                        backPressedOnce = false;
                        return;
                    }
                    if (backPressedOnce) {
                        finishAffinity();
                        return;
                    }
                    backPressedOnce = true;
                    Toast.makeText(MainActivity.this, "Appuyez encore pour quitter", Toast.LENGTH_SHORT).show();
                    handler.postDelayed(() -> backPressedOnce = false, 2000);
                });
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            try {
                webView.evaluateJavascript("try{App&&App.onPause&&App.onPause()}catch(e){}", null);
            } catch (Exception ignored) {
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            try {
                webView.evaluateJavascript("try{App&&App.onResume&&App.onResume()}catch(e){}", null);
            } catch (Exception ignored) {
            }
        }
    }
}
