package fr.recomposition.suivi;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
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
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/** WebView réservé aux assets locaux ; les pages distantes s'ouvrent hors de l'app. */
public class MainActivity extends Activity {

    private static final String PAGE = "file:///android_asset/www/index.html";
    private static final String ASSET_PREFIX = "file:///android_asset/www/";

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

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(false);
        settings.setAllowFileAccess(true); // nécessaire aux assets embarqués
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setBlockNetworkLoads(true); // mode local : aucun fetch/iframe vers Internet
        settings.setLoadWithOverviewMode(false);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);
        settings.setLayoutAlgorithm(WebSettings.LayoutAlgorithm.NORMAL);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        if (Build.VERSION.SDK_INT >= 26) {
            settings.setSafeBrowsingEnabled(true);
        }
        CookieManager.getInstance().setAcceptCookie(false);
        if (Build.VERSION.SDK_INT >= 21) {
            CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);
        }

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return gererNavigation(request == null ? null : request.getUrl().toString());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return gererNavigation(url);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideSplash();
            }
        });

        webView.setWebChromeClient(new WebChromeClient());
        webView.setBackgroundColor(Color.parseColor("#0B0F17"));
        pont = new NativeBridge(this);
        webView.addJavascriptInterface(pont, "Native");
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        if (savedInstanceState == null) {
            webView.loadUrl(PAGE);
        }

        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                hideSplash();
            }
        }, 5000);
    }

    private boolean gererNavigation(String url) {
        if (url == null) return true;
        if (url.startsWith(ASSET_PREFIX)) return false;

        // Aucune page distante ne s'exécute dans le WebView qui porte le pont natif.
        Uri uri = Uri.parse(url);
        if ("https".equalsIgnoreCase(uri.getScheme()) && uri.getHost() != null) {
            if (pont != null) pont.openExternal(uri.toString());
        }
        // HTTP, javascript:, intent:, file: externe et autres schémas sont bloqués.
        return true;
    }

    private void hideSplash() {
        if (splash == null || splash.getVisibility() != View.VISIBLE) return;
        AlphaAnimation fade = new AlphaAnimation(1f, 0f);
        fade.setDuration(280);
        splash.startAnimation(fade);
        splash.setVisibility(View.GONE);
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
