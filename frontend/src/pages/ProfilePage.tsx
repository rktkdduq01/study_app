import React, { useState } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../components/layout';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  
  Avatar,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Badge as BadgeIcon,
  Lock as LockIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import { useAppSelector } from '../hooks/useAppSelector';
import { useAppDispatch } from '../hooks/useAppDispatch';
import { setUser } from '../store/slices/authSlice';
import authService from '../services/authService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ProfilePage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const [tabValue, setTabValue] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setMessage(null);
  };

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    try {
      const updatedUser = await authService.updateProfile(profileData);
      dispatch(setUser(updatedUser));
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to update profile' });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' });
      setIsLoading(false);
      return;
    }

    try {
      await authService.changePassword(passwordData.current_password, passwordData.new_password);
      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to change password' });
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3}>
        <Box sx={{ p: 3 }}>
          <GridContainer spacing={3} alignItems="center">
            <Box>
              <Avatar sx={{ width: 80, height: 80 }}>
                <PersonIcon sx={{ fontSize: 40 }} />
              </Avatar>
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h4">{user.full_name}</Typography>
              <Typography color="text.secondary">@{user.username}</Typography>
              <Typography variant="body2" color="text.secondary">
                {user.role.charAt(0).toUpperCase() + user.role.slice(1)} Account
              </Typography>
            </Box>
          </GridContainer>
        </Box>

        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Profile Information" />
            <Tab label="Change Password" />
          </Tabs>
        </Box>

        {message && (
          <Box sx={{ p: 2 }}>
            <Alert severity={message.type}>{message.text}</Alert>
          </Box>
        )}

        <TabPanel value={tabValue} index={0}>
          <Box component="form" onSubmit={handleProfileSubmit}>
            <GridContainer spacing={3}>
              <Box>
                <TextField
                  fullWidth
                  label="Username"
                  value={user.username}
                  disabled
                  InputProps={{
                    startAdornment: <PersonIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <TextField
                  fullWidth
                  label="Full Name"
                  name="full_name"
                  value={profileData.full_name}
                  onChange={handleProfileChange}
                  required
                  InputProps={{
                    startAdornment: <BadgeIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={profileData.email}
                  onChange={handleProfileChange}
                  required
                  InputProps={{
                    startAdornment: <EmailIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={isLoading}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Save Changes'}
                </Button>
              </Box>
            </GridContainer>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box component="form" onSubmit={handlePasswordSubmit}>
            <GridContainer spacing={3}>
              <Box>
                <TextField
                  fullWidth
                  label="Current Password"
                  name="current_password"
                  type="password"
                  value={passwordData.current_password}
                  onChange={handlePasswordChange}
                  required
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <TextField
                  fullWidth
                  label="New Password"
                  name="new_password"
                  type="password"
                  value={passwordData.new_password}
                  onChange={handlePasswordChange}
                  required
                  helperText="Password must be at least 8 characters long"
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <TextField
                  fullWidth
                  label="Confirm New Password"
                  name="confirm_password"
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={handlePasswordChange}
                  required
                  InputProps={{
                    startAdornment: <LockIcon sx={{ mr: 1, color: 'action.active' }} />,
                  }}
                />
              </Box>
              <Box>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={isLoading}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Change Password'}
                </Button>
              </Box>
            </GridContainer>
          </Box>
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default ProfilePage;
