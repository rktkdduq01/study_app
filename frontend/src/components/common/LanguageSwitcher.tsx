import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import LanguageIcon from '@mui/icons-material/Language';
import CheckIcon from '@mui/icons-material/Check';
import { useTranslation } from '../../hooks/useTranslation';
import { changeLanguage } from '../../i18n/config';

interface Language {
  code: string;
  name: string;
  nativeName: string;
  flag?: string;
}

const LanguageSwitcher: React.FC = () => {
  const { i18n, language } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(false);
  const [changing, setChanging] = useState(false);

  useEffect(() => {
    fetchAvailableLanguages();
  }, []);

  const fetchAvailableLanguages = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/i18n/languages`);
      
      if (response.ok) {
        const data = await response.json();
        setLanguages(
          data.languages.map((lang: any) => ({
            code: lang.code,
            name: lang.name,
            nativeName: lang.native_name,
            flag: getFlagEmoji(lang.code),
          }))
        );
      }
    } catch (error) {
      console.error('Failed to fetch languages:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFlagEmoji = (languageCode: string): string => {
    // Map language codes to country codes for flag emojis
    const languageToCountry: Record<string, string> = {
      en: '🇺🇸',
      ko: '🇰🇷',
      ja: '🇯🇵',
      'zh-CN': '🇨🇳',
      'zh-TW': '🇹🇼',
      es: '🇪🇸',
      fr: '🇫🇷',
      de: '🇩🇪',
      it: '🇮🇹',
      pt: '🇵🇹',
      ru: '🇷🇺',
      ar: '🇸🇦',
      hi: '🇮🇳',
      th: '🇹🇭',
      vi: '🇻🇳',
    };

    return languageToCountry[languageCode] || '🌐';
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageChange = async (languageCode: string) => {
    if (languageCode === language) {
      handleClose();
      return;
    }

    try {
      setChanging(true);
      await changeLanguage(languageCode);
      handleClose();
    } catch (error) {
      console.error('Failed to change language:', error);
    } finally {
      setChanging(false);
    }
  };

  const getCurrentLanguage = () => {
    return languages.find((lang) => lang.code === language);
  };

  const currentLanguage = getCurrentLanguage();

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleClick}
        disabled={loading || changing}
        sx={{
          position: 'relative',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.1)',
          },
        }}
      >
        {changing ? (
          <CircularProgress size={24} color="inherit" />
        ) : (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <LanguageIcon />
            {currentLanguage && (
              <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
                {currentLanguage.flag}
              </Typography>
            )}
          </Box>
        )}
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: 200,
            maxHeight: 400,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
              borderRadius: 1,
              mx: 0.5,
              my: 0.25,
            },
          },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Select Language
          </Typography>
        </Box>
        <Divider />
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          languages.map((lang) => (
            <MenuItem
              key={lang.code}
              onClick={() => handleLanguageChange(lang.code)}
              selected={lang.code === language}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'primary.alpha10',
                  '&:hover': {
                    backgroundColor: 'primary.alpha20',
                  },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                <Typography>{lang.flag}</Typography>
              </ListItemIcon>
              <ListItemText
                primary={lang.nativeName}
                secondary={lang.name}
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight: lang.code === language ? 600 : 400,
                }}
                secondaryTypographyProps={{
                  fontSize: 12,
                }}
              />
              {lang.code === language && (
                <CheckIcon fontSize="small" color="primary" sx={{ ml: 1 }} />
              )}
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  );
};

export default LanguageSwitcher;