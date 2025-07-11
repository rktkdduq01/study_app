import React from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../components/layout';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Box,
  Container,
  Typography,
  Button,
  Card,
  CardContent,
  CardMedia,
  Stack,
  Chip,
  Avatar,
} from '@mui/material';
import {
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
  Psychology as BrainIcon,
  Group as GroupIcon,
  AutoAwesome,
  RocketLaunch,
  CheckCircle,
  TrendingUp,
} from '@mui/icons-material';
import { useAppSelector } from '../hooks/useAppSelector';

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);

  const features = [
    {
      icon: <SchoolIcon sx={{ fontSize: 40 }} />,
      title: '게임화된 학습',
      description: '지식이 힘이 되는 흥미진진한 RPG 모험으로 교육을 변화시켜요!',
      color: '#6366f1',
    },
    {
      icon: <TrophyIcon sx={{ fontSize: 40 }} />,
      title: '성취와 보상',
      description: '배지를 획득하고, 새로운 레벨을 해금하며, 보상을 모아보세요.',
      color: '#ec4899',
    },
    {
      icon: <BrainIcon sx={{ fontSize: 40 }} />,
      title: 'AI 튜터링',
      description: '당신의 학습 스타일에 맞춰 개인화된 도움을 제공합니다.',
      color: '#10b981',
    },
    {
      icon: <GroupIcon sx={{ fontSize: 40 }} />,
      title: '부모-자녀 연결',
      description: '학습 진도를 추적하고 맞춤형 퀘스트를 만들 수 있어요.',
      color: '#f59e0b',
    },
  ];

  const stats = [
    { value: '10,000+', label: '활동 중인 학생' },
    { value: '500+', label: '퀘스트 완료' },
    { value: '98%', label: '만족도' },
    { value: '4.9', label: '평균 평점' },
  ];

  return (
    <Box sx={{ overflow: 'hidden' }}>
      {/* Hero Section */}
      <Box
        sx={{
          position: 'relative',
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)',
          color: 'white',
          py: { xs: 8, md: 12 },
          mb: 8,
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Cpath d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
            opacity: 0.1,
          },
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, alignItems: 'center', gap: 4 }}>
            <Box sx={{ flex: { xs: '1', md: '0 0 60%' } }}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <Chip
                  icon={<AutoAwesome />}
                  label="🎮 게임처럼 재미있는 학습"
                  sx={{
                    mb: 2,
                    bgcolor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: 600,
                    backdropFilter: 'blur(10px)',
                  }}
                />
                <Typography
                  variant="h1"
                  component="h1"
                  gutterBottom
                  sx={{
                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                    fontWeight: 800,
                    lineHeight: 1.2,
                    mb: 3,
                  }}
                >
                  학습이 모험이 되는
                  <br />
                  <Box component="span" sx={{ color: '#fbbf24' }}>
                    에듀RPG
                  </Box>
                  에 오신 것을 환영합니다!
                </Typography>
                <Typography
                  variant="h6"
                  sx={{
                    mb: 4,
                    opacity: 0.9,
                    fontWeight: 400,
                    lineHeight: 1.6,
                  }}
                >
                  퀘스트를 완료하고, 레벨을 올리며, 친구들과 함께 성장하세요.
                  AI 튜터가 당신만의 학습 여정을 도와드립니다.
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 4 }}>
                  {isAuthenticated ? (
                    <Button
                      variant="contained"
                      size="large"
                      color="secondary"
                      startIcon={<RocketLaunch />}
                      onClick={() => navigate(user?.role === 'student' ? '/student/dashboard' : '/parent/dashboard')}
                      sx={{
                        py: 1.5,
                        px: 4,
                        fontSize: '1.1rem',
                        bgcolor: 'white',
                        color: 'primary.main',
                        '&:hover': {
                          bgcolor: 'rgba(255,255,255,0.9)',
                        },
                      }}
                    >
                      대시보드로 이동
                    </Button>
                  ) : (
                    <>
                      <Button
                        variant="contained"
                        size="large"
                        startIcon={<RocketLaunch />}
                        onClick={() => navigate('/register')}
                        sx={{
                          py: 1.5,
                          px: 4,
                          fontSize: '1.1rem',
                          bgcolor: 'white',
                          color: 'primary.main',
                          '&:hover': {
                            bgcolor: 'rgba(255,255,255,0.9)',
                          },
                        }}
                      >
                        무료로 시작하기
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        onClick={() => navigate('/login')}
                        sx={{
                          py: 1.5,
                          px: 4,
                          fontSize: '1.1rem',
                          color: 'white',
                          borderColor: 'rgba(255,255,255,0.5)',
                          backdropFilter: 'blur(10px)',
                          '&:hover': {
                            borderColor: 'white',
                            bgcolor: 'rgba(255,255,255,0.1)',
                          },
                        }}
                      >
                        로그인
                      </Button>
                    </>
                  )}
                </Stack>
                <Stack direction="row" spacing={3} sx={{ opacity: 0.8 }}>
                  {[
                    { icon: <CheckCircle sx={{ fontSize: 20 }} />, text: '무료 시작' },
                    { icon: <CheckCircle sx={{ fontSize: 20 }} />, text: '카드 불필요' },
                    { icon: <CheckCircle sx={{ fontSize: 20 }} />, text: '언제든 취소 가능' },
                  ].map((item, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {item.icon}
                      <Typography variant="body2">{item.text}</Typography>
                    </Box>
                  ))}
                </Stack>
              </motion.div>
            </Box>
            <Box sx={{ flex: { xs: '1', md: '0 0 40%' }, display: { xs: 'none', md: 'block' } }}>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Box
                  sx={{
                    position: 'relative',
                    '&::before': {
                      content: '""',
                      position: 'absolute',
                      top: -20,
                      right: -20,
                      width: 100,
                      height: 100,
                      bgcolor: 'rgba(251, 191, 36, 0.3)',
                      borderRadius: '50%',
                      filter: 'blur(40px)',
                    },
                  }}
                >
                  <img
                    src="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?ixlib=rb-4.0.3"
                    alt="Students learning"
                    style={{
                      width: '100%',
                      maxWidth: 500,
                      height: 'auto',
                      borderRadius: 16,
                      boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
                    }}
                  />
                </Box>
              </motion.div>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="lg" sx={{ mb: 10, mt: -6 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <Card
            sx={{
              p: 4,
              background: 'white',
              boxShadow: '0 20px 40px rgba(0,0,0,0.08)',
              borderRadius: 3,
            }}
          >
            <GridContainer columns={{ xs: 2, md: 4 }} spacing={3}>
              {stats.map((stat, index) => (
                <Box key={index} sx={{ textAlign: 'center' }}>
                  <Typography
                    variant="h3"
                    sx={{
                      fontWeight: 800,
                      background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      display: 'inline-block',
                      mb: 1,
                    }}
                  >
                    {stat.value}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {stat.label}
                  </Typography>
                </Box>
              ))}
            </GridContainer>
          </Card>
        </motion.div>
      </Container>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 12 }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
        >
          <Box textAlign="center" sx={{ mb: 6 }}>
            <Chip
              icon={<TrendingUp />}
              label="핵심 기능"
              sx={{
                mb: 2,
                bgcolor: 'primary.light',
                color: 'white',
                fontWeight: 600,
              }}
            />
            <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 700 }}>
              왜 에듀RPG인가요?
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto' }}>
              학습을 재미있고, 몰입감 있으며, 보람차게 만들어드립니다
            </Typography>
          </Box>
          <GridContainer columns={{ xs: 1, sm: 2, lg: 4 }} spacing={4}>
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                  <Card
                    sx={{
                      height: '100%',
                      textAlign: 'center',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer',
                      border: '1px solid transparent',
                      position: 'relative',
                      overflow: 'hidden',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
                        borderColor: feature.color,
                        '& .feature-icon': {
                          transform: 'scale(1.1) rotate(5deg)',
                        },
                      },
                      '&::before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: 4,
                        background: feature.color,
                        transform: 'scaleX(0)',
                        transformOrigin: 'left',
                        transition: 'transform 0.3s ease',
                      },
                      '&:hover::before': {
                        transform: 'scaleX(1)',
                      },
                    }}
                  >
                    <CardContent sx={{ p: 4 }}>
                      <Avatar
                        className="feature-icon"
                        sx={{
                          width: 80,
                          height: 80,
                          bgcolor: `${feature.color}20`,
                          color: feature.color,
                          mx: 'auto',
                          mb: 3,
                          transition: 'all 0.3s ease',
                        }}
                      >
                        {feature.icon}
                      </Avatar>
                      <Typography
                        gutterBottom
                        variant="h6"
                        component="h3"
                        sx={{ fontWeight: 700, mb: 2 }}
                      >
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </motion.div>
            ))}
          </GridContainer>
        </motion.div>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%)',
          py: 10,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <Container maxWidth="md">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <Box
              sx={{
                textAlign: 'center',
                position: 'relative',
                zIndex: 1,
              }}
            >
              <motion.div
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  repeatType: 'reverse',
                }}
              >
                <RocketLaunch
                  sx={{
                    fontSize: 60,
                    color: 'primary.main',
                    mb: 3,
                  }}
                />
              </motion.div>
              <Typography
                variant="h3"
                component="h2"
                gutterBottom
                sx={{
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  display: 'inline-block',
                  mb: 3,
                }}
              >
                학습 모험을 시작할 준비가 되셨나요?
              </Typography>
              <Typography
                variant="h6"
                color="text.secondary"
                paragraph
                sx={{ maxWidth: 600, mx: 'auto', mb: 4 }}
              >
                오늘 에듀RPG에 가입하고 학습 방식을 완전히 바꿔보세요.
                무료로 시작할 수 있습니다!
              </Typography>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={2}
                justifyContent="center"
                sx={{ mb: 4 }}
              >
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<RocketLaunch />}
                  onClick={() => navigate('/register')}
                  sx={{
                    py: 2,
                    px: 5,
                    fontSize: '1.2rem',
                    fontWeight: 700,
                    background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                    boxShadow: '0 10px 30px rgba(99, 102, 241, 0.3)',
                    '&:hover': {
                      boxShadow: '0 15px 40px rgba(99, 102, 241, 0.4)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  무료 계정 만들기
                </Button>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => navigate('/login')}
                  sx={{
                    py: 2,
                    px: 5,
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    borderWidth: 2,
                  }}
                >
                  데모 체험하기
                </Button>
              </Stack>
              <Typography variant="body2" color="text.secondary">
                신용카드 없이 • 언제든지 취소 가능 • 5분 안에 시작
              </Typography>
            </Box>
          </motion.div>
        </Container>
        {/* Background decoration */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '10%',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)',
            opacity: 0.1,
            filter: 'blur(60px)',
            transform: 'translate(-50%, -50%)',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: '20%',
            right: '5%',
            width: 300,
            height: 300,
            borderRadius: '50%',
            background: 'radial-gradient(circle, #ec4899 0%, transparent 70%)',
            opacity: 0.1,
            filter: 'blur(80px)',
          }}
        />
      </Box>
    </Box>
  );
};

export default HomePage;
