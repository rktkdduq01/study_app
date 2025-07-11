import React, { useState, useEffect } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  Link,
  InputAdornment,
  IconButton,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Person as PersonIcon,
  Email as EmailIcon,
  Lock as LockIcon,
  Badge as BadgeIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { register, clearError, login } from '../../store/slices/authSlice';
import { UserRole } from '../../types/user';

const steps = ['계정 유형', '개인 정보', '계정 정보'];

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isLoading, error } = useAppSelector((state) => state.auth);

  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState({
    role: UserRole.STUDENT,
    full_name: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    dispatch(clearError());
  }, [dispatch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | { target: { name?: string; value: unknown }}) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name as string]: value,
    });
    // Clear validation error for this field
    setValidationErrors({
      ...validationErrors,
      [name as string]: '',
    });
  };

  const validateStep = (step: number): boolean => {
    const errors: Record<string, string> = {};

    switch (step) {
      case 0:
        // Account type is always valid
        break;
      case 1:
        if (!formData.full_name.trim()) {
          errors.full_name = '이름을 입력해주세요';
        }
        if (!formData.email.trim()) {
          errors.email = '이메일을 입력해주세요';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
          errors.email = '올바른 이메일 형식이 아닙니다';
        }
        break;
      case 2:
        if (!formData.username.trim()) {
          errors.username = '사용자명을 입력해주세요';
        } else if (formData.username.length < 3) {
          errors.username = '사용자명은 최소 3자 이상이어야 합니다';
        }
        if (!formData.password) {
          errors.password = '비밀번호를 입력해주세요';
        } else if (formData.password.length < 8) {
          errors.password = '비밀번호는 최소 8자 이상이어야 합니다';
        }
        if (formData.password !== formData.confirmPassword) {
          errors.confirmPassword = '비밀번호가 일치하지 않습니다';
        }
        break;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateStep(activeStep)) {
      return;
    }

    const { confirmPassword, ...registerData } = formData;
    
    const result = await dispatch(register(registerData));
    if (register.fulfilled.match(result)) {
      // Registration successful, now log them in
      const loginResult = await dispatch(login({
        username: formData.username,
        password: formData.password,
      }));
      
      if (login.fulfilled.match(loginResult)) {
        // Navigate based on role
        if (formData.role === UserRole.STUDENT) {
          navigate('/character/create');
        } else if (formData.role === UserRole.PARENT) {
          navigate('/parent/dashboard');
        } else {
          navigate('/');
        }
      }
    }
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              계정 유형을 선택하세요
            </Typography>
            <FormControl fullWidth margin="normal">
              <InputLabel id="role-label">계정 유형</InputLabel>
              <Select
                labelId="role-label"
                id="role"
                name="role"
                value={formData.role}
                label="계정 유형"
                onChange={handleChange as any}
              >
                <MenuItem value={UserRole.STUDENT}>
                  <Box>
                    <Typography variant="body1">학생</Typography>
                    <Typography variant="caption" color="text.secondary">
                      학습하고 플레이하고 싶은 어린이용
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value={UserRole.PARENT}>
                  <Box>
                    <Typography variant="body1">학부모</Typography>
                    <Typography variant="caption" color="text.secondary">
                      진도를 모니터링하고 싶은 부모님용
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        );
      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              개인 정보
            </Typography>
            <TextField
              margin="normal"
              required
              fullWidth
              id="full_name"
              label="이름"
              name="full_name"
              autoComplete="name"
              value={formData.full_name}
              onChange={handleChange}
              error={!!validationErrors.full_name}
              helperText={validationErrors.full_name}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BadgeIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="이메일 주소"
              name="email"
              autoComplete="email"
              value={formData.email}
              onChange={handleChange}
              error={!!validationErrors.email}
              helperText={validationErrors.email}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              계정 정보 생성
            </Typography>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="사용자명"
              name="username"
              autoComplete="username"
              value={formData.username}
              onChange={handleChange}
              error={!!validationErrors.username}
              helperText={validationErrors.username}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <PersonIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="비밀번호"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              error={!!validationErrors.password}
              helperText={validationErrors.password}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="비밀번호 확인"
              type={showConfirmPassword ? 'text' : 'password'}
              id="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              error={!!validationErrors.confirmPassword}
              helperText={validationErrors.confirmPassword}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LockIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container component="main" maxWidth="sm">
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
            에듀RPG 가입하기
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
            오늘부터 학습 모험을 시작하세요!
          </Typography>

          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            {getStepContent(activeStep)}

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
              >
                이전
              </Button>
              {activeStep === steps.length - 1 ? (
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isLoading}
                >
                  {isLoading ? <CircularProgress size={24} /> : '가입하기'}
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleNext}
                >
                  다음
                </Button>
              )}
            </Box>
          </Box>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2">
              이미 계정이 있으신가요?{' '}
              <Link component={RouterLink} to="/login" variant="body2">
                로그인하기
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default RegisterPage;