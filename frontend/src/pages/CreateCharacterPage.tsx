import React, { useState } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../components/layout';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  
  Avatar,
  Alert,
  CircularProgress,
  Card,
  CardActionArea,
  CardContent,
} from '@mui/material';
import {
  Person as PersonIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { createCharacter } from '../store/slices/characterSlice';

const avatarOptions = [
  { id: 1, url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=Felix', name: '모험가' },
  { id: 2, url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Felix', name: '현대적' },
  { id: 3, url: 'https://api.dicebear.com/7.x/big-ears/svg?seed=Felix', name: '친근함' },
  { id: 4, url: 'https://api.dicebear.com/7.x/lorelei/svg?seed=Felix', name: '우아함' },
  { id: 5, url: 'https://api.dicebear.com/7.x/micah/svg?seed=Felix', name: '예술적' },
  { id: 6, url: 'https://api.dicebear.com/7.x/personas/svg?seed=Felix', name: '전문가' },
];

const CreateCharacterPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();

  const [characterName, setCharacterName] = useState('');
  const [selectedAvatar, setSelectedAvatar] = useState(avatarOptions[0].url);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const result = await dispatch(createCharacter({
        name: characterName,
        avatar_url: selectedAvatar,
      }));

      if (createCharacter.fulfilled.match(result)) {
        navigate('/student/dashboard');
      } else {
        setError('캐릭터 생성에 실패했습니다. 다시 시도해주세요.');
      }
    } catch (err: any) {
      setError(err.message || '오류가 발생했습니다');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          marginTop: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            캐릭터 만들기
          </Typography>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ mb: 4 }}>
            아바타와 이름을 선택하여 학습 모험을 시작하세요!
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <GridContainer columns={{ xs: 12, sm: 12, md: 12 }} spacing={3}>
              {/* Character Name */}
              <Box>
                <TextField
                  fullWidth
                  label="캐릭터 이름"
                  value={characterName}
                  onChange={(e) => setCharacterName(e.target.value)}
                  required
                  placeholder="영웅의 이름을 입력하세요"
                  inputProps={{ maxLength: 50 }}
                  helperText={`${characterName.length}/50 글자`}
                />
              </Box>

              {/* Avatar Selection */}
              <Box>
                <Typography variant="h6" gutterBottom>
                  아바타 선택
                </Typography>
                <GridContainer columns={{ xs: 2, sm: 3, md: 4 }} spacing={2}>
                  {avatarOptions.map((avatar) => (
                    <Box key={avatar.id}>
                      <Card
                        sx={{
                          border: selectedAvatar === avatar.url ? 3 : 1,
                          borderColor: selectedAvatar === avatar.url ? 'primary.main' : 'divider',
                          transition: 'all 0.2s',
                        }}
                      >
                        <CardActionArea onClick={() => setSelectedAvatar(avatar.url)}>
                          <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <Avatar
                              src={avatar.url.replace('Felix', characterName || 'Hero')}
                              sx={{ width: 80, height: 80, mb: 1 }}
                            >
                              <PersonIcon />
                            </Avatar>
                            <Typography variant="caption">{avatar.name}</Typography>
                          </Box>
                        </CardActionArea>
                      </Card>
                    </Box>
                  ))}
                </GridContainer>
              </Box>

              {/* Preview */}
              <Box>
                <Box sx={{ textAlign: 'center', mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    내 캐릭터
                  </Typography>
                  <Avatar
                    src={selectedAvatar.replace('Felix', characterName || 'Hero')}
                    sx={{ width: 120, height: 120, mx: 'auto', mb: 1 }}
                  >
                    <PersonIcon sx={{ fontSize: 60 }} />
                  </Avatar>
                  <Typography variant="h5">
                    {characterName || '영웅 이름'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    레벨 1 모험가
                  </Typography>
                </Box>
              </Box>

              {/* Submit Button */}
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    endIcon={<ArrowForwardIcon />}
                    disabled={!characterName.trim() || isLoading}
                  >
                    {isLoading ? <CircularProgress size={24} /> : '모험 시작하기'}
                  </Button>
                </Box>
              </Box>
            </GridContainer>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default CreateCharacterPage;
