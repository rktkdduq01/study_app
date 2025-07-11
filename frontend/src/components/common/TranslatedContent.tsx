import React, { useEffect, useState } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { useTranslation } from '../../hooks/useTranslation';

interface TranslatedContentProps {
  contentType: string;
  contentId: number;
  fields: string[];
  fallbackContent?: Record<string, string>;
  children: (content: Record<string, string>) => React.ReactNode;
}

const TranslatedContent: React.FC<TranslatedContentProps> = ({
  contentType,
  contentId,
  fields,
  fallbackContent = {},
  children,
}) => {
  const { language } = useTranslation();
  const [content, setContent] = useState<Record<string, string>>(fallbackContent);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTranslatedContent();
  }, [language, contentId]);

  const fetchTranslatedContent = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/i18n/content/${contentType}/${contentId}?language=${language}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Merge translated fields with fallback content
        const mergedContent = { ...fallbackContent };
        fields.forEach((field) => {
          if (data.fields && data.fields[field]) {
            mergedContent[field] = data.fields[field];
          }
        });
        
        setContent(mergedContent);
      }
    } catch (error) {
      console.error('Failed to fetch translated content:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  return <>{children(content)}</>;
};

export default TranslatedContent;