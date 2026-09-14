import type { CapacitorConfig } from '@capacitor/cli';

// Change appId to your own reverse-DNS identifier before your first
// build — it's baked into the native project on `npx cap add` and is
// painful to rename later. appName is the label under the home-screen icon.
const config: CapacitorConfig = {
  appId: 'com.essentialsoftware.notebuilder',
  appName: 'Builder',
  webDir: 'www',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    // serverClientId must be the OAuth *Web application* client ID (same
    // value as NB_GOOGLE_WEB_CLIENT_ID in the app and GOOGLE_CLIENT_IDS
    // on the note-publish worker) — not this app's own Android client ID.
    // That's what makes the idToken the plugin returns audienced to the
    // client the worker actually verifies against. Also add this build's
    // own Android OAuth client (SHA-1 + package name registered in
    // Google Cloud Console) or native sign-in will fail with
    // DEVELOPER_ERROR/10, even though it never appears in this config.
    GoogleAuth: {
      scopes: ['email', 'profile'],
      serverClientId: '41762787149-mkbeh1mus5e5v2gbkvnfh1fgblmkkfvj.apps.googleusercontent.com',
      forceCodeForRefreshToken: false
    }
  }
};

export default config;
