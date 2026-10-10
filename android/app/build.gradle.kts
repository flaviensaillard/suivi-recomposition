plugins {
    id("com.android.application")
}

android {
    namespace = "fr.recomposition.suivi"
    compileSdk = 34
    buildToolsVersion = "34.0.0"

    defaultConfig {
        applicationId = "fr.recomposition.suivi"
        minSdk = 24
        targetSdk = 34
        versionCode = 14
        versionName = "1.0.13"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}
