import { useTranslation as useI18nTranslation } from 'react-i18next';
import { useCallback, useEffect } from 'react';
import { useAppSelector } from './useAppSelector';

export const useTranslation = (namespace?: string | string[]) => {
  const { t, i18n, ready } = useI18nTranslation(namespace);
  const user = useAppSelector((state) => state.auth.user);

  // Sync language with user preference
  useEffect(() => {
    const syncUserLanguage = async () => {
      if (user && ready) {
        try {
          const token = localStorage.getItem('token');
          const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/i18n/user/language`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const data = await response.json();
            if (data.language_code && data.language_code !== i18n.language) {
              await i18n.changeLanguage(data.language_code);
            }
          }
        } catch (error) {
          console.error('Failed to sync user language:', error);
        }
      }
    };

    syncUserLanguage();
  }, [user, i18n, ready]);

  // Enhanced translation function with fallback
  const translate = useCallback((key: string, options?: any) => {
    const translation = t(key, options);
    
    // If translation is the same as key, it means translation is missing
    if (translation === key && import.meta.env.DEV) {
      console.warn(`Missing translation for key: ${key}`);
    }
    
    return translation;
  }, [t]);

  // Helper function to translate with HTML
  const translateHtml = useCallback((key: string, options?: any) => {
    return { __html: t(key, options) };
  }, [t]);

  // Helper function to translate with pluralization
  const translatePlural = useCallback((key: string, count: number, options?: any) => {
    return t(key, { count, ...options });
  }, [t]);

  // Helper function to translate with context
  const translateContext = useCallback((key: string, context: string, options?: any) => {
    return t(`${key}_${context}`, options);
  }, [t]);

  return {
    t: translate,
    tHtml: translateHtml,
    tPlural: translatePlural,
    tContext: translateContext,
    i18n,
    ready,
    language: i18n.language,
    changeLanguage: i18n.changeLanguage,
  };
};