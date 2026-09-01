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
  }
};

export default config;
