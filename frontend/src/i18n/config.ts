import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';
import { store } from '../store/store';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    debug: import.meta.env.DEV,
    
    interpolation: {
      escapeValue: false, // React already escapes values
    },

    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage', 'cookie'],
    },

    backend: {
      loadPath: `${API_URL}/api/i18n/translate/batch`,
      
      // Custom request options
      requestOptions: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include' as RequestCredentials,
      },

      // Custom request function to handle our API format
      request: async (options: any, url: string, payload: any, callback: any) => {
        try {
          const token = localStorage.getItem('token');
          const language = url.split('language=')[1].split('&')[0];
          
          // Get all translation keys that need to be loaded
          const namespace = payload.split('&ns=')[1] || 'translation';
          const keys = getNamespaceKeys(namespace);
          
          const response = await fetch(`${API_URL}/api/i18n/translate/batch?language=${language}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token && { 'Authorization': `Bearer ${token}` }),
            },
            body: JSON.stringify({
              keys: keys,
            }),
          });

          if (response.ok) {
            const data = await response.json();
            callback(null, { status: 200, data: data.translations });
          } else {
            callback(new Error(`Failed to load translations: ${response.status}`), null);
          }
        } catch (error) {
          callback(error, null);
        }
      },
    },

    react: {
      useSuspense: false, // Disable suspense for better error handling
    },

    ns: ['common', 'auth', 'student', 'parent', 'admin', 'errors', 'game'],
    defaultNS: 'common',
  });

// Function to get translation keys for a namespace
function getNamespaceKeys(namespace: string): string[] {
  // This would normally be loaded from a key registry
  // For now, we'll return common keys based on namespace
  const keyMap: Record<string, string[]> = {
    common: [
      'app.title',
      'app.loading',
      'button.submit',
      'button.cancel',
      'button.save',
      'button.delete',
      'button.edit',
      'button.back',
      'button.next',
      'button.previous',
      'button.close',
      'button.confirm',
      'nav.home',
      'nav.dashboard',
      'nav.profile',
      'nav.settings',
      'nav.logout',
      'nav.login',
      'nav.register',
      'message.success',
      'message.error',
      'message.warning',
      'message.info',
    ],
    auth: [
      'auth.login.title',
      'auth.login.subtitle',
      'auth.login.email',
      'auth.login.password',
      'auth.login.remember',
      'auth.login.forgot',
      'auth.login.submit',
      'auth.login.register',
      'auth.register.title',
      'auth.register.subtitle',
      'auth.register.email',
      'auth.register.password',
      'auth.register.confirmPassword',
      'auth.register.username',
      'auth.register.submit',
      'auth.register.login',
      'auth.error.invalidCredentials',
      'auth.error.userExists',
      'auth.error.weakPassword',
      'auth.error.passwordMismatch',
    ],
    student: [
      'student.dashboard.title',
      'student.dashboard.welcome',
      'student.dashboard.stats.level',
      'student.dashboard.stats.exp',
      'student.dashboard.stats.health',
      'student.dashboard.stats.mana',
      'student.dashboard.stats.gold',
      'student.dashboard.recentQuests',
      'student.dashboard.achievements',
      'student.character.title',
      'student.character.stats',
      'student.character.equipment',
      'student.character.skills',
      'student.quests.title',
      'student.quests.available',
      'student.quests.inProgress',
      'student.quests.completed',
      'student.quests.difficulty',
      'student.quests.reward',
      'student.achievements.title',
      'student.achievements.unlocked',
      'student.achievements.locked',
      'student.achievements.progress',
    ],
    game: [
      'game.level',
      'game.experience',
      'game.health',
      'game.mana',
      'game.gold',
      'game.attack',
      'game.defense',
      'game.intelligence',
      'game.agility',
      'game.quest',
      'game.achievement',
      'game.reward',
      'game.item',
      'game.skill',
      'game.character',
      'game.inventory',
      'game.shop',
      'game.battle',
      'game.victory',
      'game.defeat',
    ],
  };

  return keyMap[namespace] || [];
}

// Helper function to change language
export const changeLanguage = async (languageCode: string) => {
  try {
    await i18n.changeLanguage(languageCode);
    
    // Update user preference if authenticated
    const state = store.getState();
    if (state.auth.isAuthenticated && state.auth.user) {
      const token = localStorage.getItem('token');
      await fetch(`${API_URL}/api/i18n/user/language`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ language_code: languageCode }),
      });
    }
  } catch (error) {
    console.error('Failed to change language:', error);
  }
};

export default i18n;