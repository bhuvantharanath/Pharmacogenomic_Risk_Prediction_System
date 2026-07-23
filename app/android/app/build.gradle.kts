import java.util.Properties
import java.io.FileInputStream

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// ---------------------------------------------------------------------------
// Release signing.
//
// Credentials live in android/key.properties, which is GITIGNORED and must
// NEVER be committed — along with the .jks keystore it points at. Losing that
// keystore means you can never ship an update to an already-installed app, so
// back it up somewhere private and durable (not this repo).
//
// See infra/DEPLOY_NOTES.md for keystore generation.
//
// When key.properties is absent — a fresh clone, or CI without secrets — the
// release build falls back to the debug signing key. The APK still installs and
// runs, which keeps `flutter build apk --release` working for everyone; it is
// simply not distributable as a real release. The build prints which path it
// took so this is never a silent surprise.
// ---------------------------------------------------------------------------
val keystorePropertiesFile = rootProject.file("key.properties")
val keystoreProperties = Properties()
val hasReleaseKeystore = keystorePropertiesFile.exists()
if (hasReleaseKeystore) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    // MUST match the package of MainActivity.kt, because AndroidManifest.xml
    // declares the launcher as the relative `.MainActivity` — which resolves
    // against this namespace. They disagreed once (namespace was
    // `com.pharmaguard.app`, the class was `com.pharmaguard.pharmaguard`),
    // producing an APK whose launcher target did not exist in its own dex: it
    // installed and then died with ClassNotFoundException on launch.
    // `tests/test_android_identity.py` now fails the build if they drift again.
    namespace = "com.pharmaguard.pharmaguard"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        // Reverse-DNS, stable for the life of the app: changing it after
        // release makes an update look like a different app.
        //
        // Deliberately equal to iOS's PRODUCT_BUNDLE_IDENTIFIER
        // (app/ios/Runner.xcodeproj/project.pbxproj), so the two platforms
        // present the same identity.
        applicationId = "com.pharmaguard.pharmaguard"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            if (hasReleaseKeystore) {
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
                storeFile = keystoreProperties["storeFile"]?.let { file(it) }
                storePassword = keystoreProperties["storePassword"] as String
            }
        }
    }

    buildTypes {
        release {
            signingConfig = if (hasReleaseKeystore) {
                signingConfigs.getByName("release")
            } else {
                logger.lifecycle(
                    "PharmaGuard: android/key.properties not found — signing the " +
                        "release build with the DEBUG key. The APK installs and " +
                        "runs, but is not distributable as a real release. " +
                        "See infra/DEPLOY_NOTES.md."
                )
                signingConfigs.getByName("debug")
            }

            // Shrinking is off deliberately. This app is a thin HTTP client
            // with no large dependency graph, so R8 buys very little, and a
            // misconfigured shrink that strips a JSON model class fails at
            // runtime on a user's phone rather than in CI. Not worth the risk
            // for an academic demo.
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

flutter {
    source = "../.."
}
