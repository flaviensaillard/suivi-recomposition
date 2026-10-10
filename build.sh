#!/usr/bin/env bash
# Construction autonome de l'APK Équilibre (Suivi & Recomposition) — sans Gradle.
#
# Utilise les outils natifs du SDK Android :
# aapt2, javac, d8, zipalign et apksigner.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/.cache/android-sdk}}"

# Recherche automatique de build-tools et platforms
BT=""
for cand in "$SDK/build-tools/34.0.0" "$SDK/build-tools/35.0.0" "$SDK/build-tools/"*; do
    if [ -x "$cand/aapt2" ]; then
        BT="$cand"
        break
    fi
done

PLAT=""
for cand in "$SDK/platforms/android-35" "$SDK/platforms/android-34" "$SDK/platforms/"*; do
    if [ -f "$cand/android.jar" ]; then
        PLAT="$cand"
        break
    fi
done

if [ -z "$BT" ] || [ -z "$PLAT" ]; then
    echo "SDK Android introuvable dans $SDK" >&2
    exit 1
fi

AAPT2="$BT/aapt2"
D8="$BT/d8"
ZIPALIGN="$BT/zipalign"
APKSIGNER="$BT/apksigner"
ANDROID_JAR="$PLAT/android.jar"

# Vérification de l'intégrité des modules Web
WWW="$ROOT/app/src/main/assets/www"
for f in js/util.js js/models.js js/store.js js/net.js js/ui.js js/views.js js/app.js; do
    if [ ! -f "$WWW/$f" ]; then
        echo "Module JavaScript manquant : $WWW/$f" >&2
        exit 1
    fi
    if ! grep -q "$f" "$WWW/index.html"; then
        echo "$f existe mais n'est pas chargé dans index.html" >&2
        exit 1
    fi
done

for onglet in bord pesee seances menus apps; do
    if ! grep -q "data-onglet=\"$onglet\"" "$WWW/index.html"; then
        echo "Onglet $onglet absent de la navigation basse" >&2
        exit 1
    fi
done

APP="$ROOT/app/src/main"
BUILD="$ROOT/build"
OUT="$ROOT/dist"

VERSION_NAME="${VERSION_NAME:-1.0.13}"
VERSION_CODE="${VERSION_CODE:-14}"
KEYSTORE="${KEYSTORE:-${KEYSTORE_PATH:-}}"
KEY_PASS="${KEY_PASS:-}"
KEY_ALIAS="${KEY_ALIAS:-equilibre}"
TEMP_KEY_DIR=""

# Une compilation locale/CI sans clé de release utilise une clé éphémère,
# aléatoire et hors du dépôt. Une clé persistante doit être fournie explicitement
# avec KEYSTORE + KEY_PASS (ou rangée dans keystore/equilibre.jks avec le secret).
if [ -z "$KEYSTORE" ] && [ -f "$ROOT/keystore/equilibre.jks" ] && [ -n "$KEY_PASS" ]; then
    KEYSTORE="$ROOT/keystore/equilibre.jks"
fi
if [ -z "$KEYSTORE" ]; then
    TEMP_KEY_DIR="$(mktemp -d "${TMPDIR:-/tmp}/equilibre-build.XXXXXX")"
    KEYSTORE="$TEMP_KEY_DIR/equilibre.jks"
    KEY_PASS="$(od -An -N24 -tx1 /dev/urandom | tr -d '[:space:]')"
    KEY_ALIAS="equilibre"
    trap 'rm -rf "$TEMP_KEY_DIR"' EXIT
fi
if [ -z "$KEY_PASS" ]; then
    echo "Mot de passe de signature manquant : fournir KEY_PASS pour le keystore configuré." >&2
    exit 1
fi

# Recherche du JDK si JAVA_HOME n'est pas défini
if [ -z "${JAVA_HOME:-}" ]; then
    for cand in /usr/lib/jvm/java-17-openjdk* /usr/lib/jvm/temurin-17* /usr/lib/jvm/jdk-17* /usr/lib/jvm/default-java; do
        if [ -x "$cand/bin/javac" ]; then
            JAVA_HOME="$cand"
            break
        fi
    done
fi
if [ -n "${JAVA_HOME:-}" ]; then
    export PATH="$JAVA_HOME/bin:$PATH"
fi

for tool in "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER" "$ANDROID_JAR"; do
    [ -e "$tool" ] || { echo "Outil requis manquant : $tool" >&2; exit 1; }
done

echo "› 1. Nettoyage et préparation des dossiers"
rm -rf "$BUILD"
mkdir -p "$BUILD/obj" "$BUILD/dex" "$BUILD/gen" "$OUT"

echo "› 2. Compilation des ressources Android (aapt2 compile)"
"$AAPT2" compile --dir "$APP/res" -o "$BUILD/res.zip"

echo "› 3. Édition de liens (aapt2 link)"
"$AAPT2" link \
    -I "$ANDROID_JAR" \
    --manifest "$APP/AndroidManifest.xml" \
    -A "$APP/assets" \
    -o "$BUILD/app.unaligned.apk" \
    --java "$BUILD/gen" \
    -R "$BUILD/res.zip" \
    --auto-add-overlay \
    --min-sdk-version 24 \
    --target-sdk-version 34 \
    --version-code "$VERSION_CODE" \
    --version-name "$VERSION_NAME"

echo "› 4. Compilation Java"
find "$APP/java" "$BUILD/gen" -name '*.java' > "$BUILD/sources.txt"
javac -nowarn -encoding UTF-8 -classpath "$ANDROID_JAR" -d "$BUILD/obj" @"$BUILD/sources.txt"

echo "› 5. Transformation Dex (d8)"
find "$BUILD/obj" -name '*.class' > "$BUILD/classes.txt"
"$D8" --lib "$ANDROID_JAR" --min-api 24 --output "$BUILD/dex" @"$BUILD/classes.txt" >/dev/null

echo "› 6. Assemblage du package APK"
cp "$BUILD/app.unaligned.apk" "$BUILD/app.withdex.apk"
( cd "$BUILD/dex" && zip -q -X -j "$BUILD/app.withdex.apk" classes.dex )

echo "› 7. Alignement 4-octets (zipalign)"
"$ZIPALIGN" -p -f 4 "$BUILD/app.withdex.apk" "$BUILD/app.aligned.apk"

if [ ! -f "$KEYSTORE" ]; then
    if [ -z "$TEMP_KEY_DIR" ]; then
        echo "Keystore configuré introuvable : $KEYSTORE" >&2
        exit 1
    fi
    echo "› 8. Génération d'une clé éphémère pour cette compilation seulement"
    keytool -genkeypair -v -keystore "$KEYSTORE" -alias "$KEY_ALIAS" \
        -keyalg RSA -keysize 2048 -validity 10950 \
        -storepass "$KEY_PASS" -keypass "$KEY_PASS" \
        -dname "CN=Equilibre, OU=Mobile, O=Recomposition, L=Paris, C=FR" >/dev/null
fi

echo "› 9. Signature APK (v1 + v2 + v3)"
"$APKSIGNER" sign --ks "$KEYSTORE" --ks-pass "pass:$KEY_PASS" --key-pass "pass:$KEY_PASS" \
    --ks-key-alias "$KEY_ALIAS" --out "$OUT/Equilibre.apk" "$BUILD/app.aligned.apk"

cp "$OUT/Equilibre.apk" "$OUT/suivi-recomposition.apk"

echo "› 10. Vérification de la signature"
"$APKSIGNER" verify --print-certs "$OUT/Equilibre.apk" | head -10
ls -lh "$OUT/Equilibre.apk"
echo "✔ APK prête avec succès : $OUT/Equilibre.apk"
