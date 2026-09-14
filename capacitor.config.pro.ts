import type { CapacitorConfig } from '@capacitor/cli';

// Change appId to your own reverse-DNS identifier before your first
// build — it's baked into the native project on `npx cap add` and is
// painful to rename later. appName is the label under the home-screen icon.
const config: CapacitorConfig = {
  appId: 'com.essentialsoftware.notebuilderpro',
  appName: 'Builder Pro',
  webDir: 'www',
  server: {
    androidScheme: 'https'
  },
  plugins: {
    // See capacitor.config.free.ts for what serverClientId needs to be
    // and why — same value here, plus this build's own Android OAuth
    // client registered separately in Google Cloud Console (different
    // package name/SHA-1 than the free app).
    GoogleAuth: {
      scopes: ['email', 'profile'],
      serverClientId: '41762787149-mkbeh1mus5e5v2gbkvnfh1fgblmkkfvj.apps.googleusercontent.com',
      forceCodeForRefreshToken: false
    }
  }
};

export default config;
