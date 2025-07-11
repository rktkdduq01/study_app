import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Chip,
  useMediaQuery,
  useTheme,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  ListItemButton,
  Collapse,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Person as PersonIcon,
  EmojiEvents as TrophyIcon,
  Assignment as QuestIcon,
  Dashboard as DashboardIcon,
  ShoppingBag as ShopIcon,
  Leaderboard as LeaderboardIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore,
  School,
  Psychology,
  MonetizationOn,
  Diamond,
  LocalFireDepartment,
  Notifications,
  NotificationsActive,
  Group,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { logout } from '../../store/slices/authSlice';
import { UserRole } from '../../types/user';
import ParentNavigation from './ParentNavigation';
import ParentMobileNavigation from './ParentMobileNavigation';
import { fetchConnectedChildren, setSelectedChild } from '../../store/slices/parentSlice';
import { toggleNotificationPanel } from '../../store/slices/notificationSlice';
import { flexBox, touchStyles } from '../../utils/responsive';
import LanguageSwitcher from '../common/LanguageSwitcher';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const { character } = useAppSelector((state) => state.character);
  const { connectedChildren, selectedChildId } = useAppSelector((state) => state.parent);
  const { unreadCount } = useAppSelector((state) => state.notifications);
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [studentMobileDrawerOpen, setStudentMobileDrawerOpen] = useState(false);

  // Fetch connected children when parent logs in
  useEffect(() => {
    if (user?.role === UserRole.PARENT && isAuthenticated) {
      dispatch(fetchConnectedChildren());
    }
  }, [user, isAuthenticated, dispatch]);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login');
    handleClose();
  };

  const handleProfile = () => {
    navigate('/profile');
    handleClose();
  };

  const navigateToHome = () => {
    if (user?.role === UserRole.STUDENT) {
      navigate('/student/dashboard');
    } else if (user?.role === UserRole.PARENT) {
      navigate('/parent/dashboard');
    } else if (user?.role === UserRole.ADMIN) {
      navigate('/admin/dashboard');
    } else {
      navigate('/');
    }
  };

  // Mobile navigation items for students
  const studentNavItems = [
    { label: 'Dashboard', icon: <DashboardIcon />, path: '/student/dashboard' },
    { label: 'Quests', icon: <QuestIcon />, path: '/student/quests' },
    { label: 'Achievements', icon: <TrophyIcon />, path: '/student/achievements' },
    { label: 'Character', icon: <PersonIcon />, path: '/student/character' },
    { label: 'Shop', icon: <ShopIcon />, path: '/student/shop' },
    { label: 'Leaderboard', icon: <LeaderboardIcon />, path: '/student/leaderboard' },
    { label: 'Social', icon: <Group />, path: '/student/social' },
  ];

  const handleMobileMenuClick = () => {
    if (user?.role === UserRole.STUDENT) {
      setStudentMobileDrawerOpen(true);
    } else if (user?.role === UserRole.PARENT) {
      setMobileMenuOpen(true);
    } else {
      navigateToHome();
    }
  };

  const handleNotificationClick = () => {
    dispatch(toggleNotificationPanel());
  };

  return (
    <>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
          {/* Mobile Menu Button */}
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={handleMobileMenuClick}
            sx={{
              mr: 2,
              display: { xs: 'block', lg: user?.role === UserRole.PARENT ? 'block' : 'none' },
              ...touchStyles.touchTarget
            }}
          >
            <MenuIcon />
          </IconButton>
        
          {/* Logo */}
          <Typography 
            variant="h6" 
            component="div" 
            onClick={navigateToHome}
            sx={{ 
              flexGrow: 1, 
              cursor: 'pointer',
              fontSize: { xs: '1.1rem', sm: '1.25rem' },
              fontWeight: 'bold'
            }}
          >
            EduRPG
          </Typography>

          {isAuthenticated && user && (
            <>
              {/* Desktop Navigation - Students */}
              {user.role === UserRole.STUDENT && (
                <Box sx={{ 
                  display: { xs: 'none', lg: 'flex' }, 
                  gap: { lg: 0.5, xl: 1 }, 
                  mr: 2,
                  overflow: 'hidden'
                }}>
                  {studentNavItems.map((item) => (
                    <Button
                      key={item.path}
                      color="inherit"
                      startIcon={item.icon}
                      onClick={() => navigate(item.path)}
                      sx={{
                        fontSize: { lg: '0.75rem', xl: '0.875rem' },
                        px: { lg: 1, xl: 2 },
                        ...touchStyles.touchTarget,
                        minWidth: 'auto'
                      }}
                    >
                      <Box sx={{ display: { lg: 'none', xl: 'block' } }}>
                        {item.label}
                      </Box>
                    </Button>
                  ))}
                </Box>
              )}

              {/* Desktop Navigation - Parents */}
              {user.role === UserRole.PARENT && (
                <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
                  <ParentNavigation 
                    children={connectedChildren}
                    selectedChildId={selectedChildId || undefined}
                    onChildSelect={(childId) => dispatch(setSelectedChild(childId))}
                  />
                </Box>
              )}

              {/* Character Info - Responsive */}
              {character && (
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: { xs: 0.5, sm: 1 }, 
                  mr: { xs: 1, sm: 2 },
                  flexShrink: 0
                }}>
                  <Badge
                    badgeContent={character.total_level}
                    color="secondary"
                    sx={{
                      '& .MuiBadge-badge': {
                        fontSize: { xs: '0.6rem', sm: '0.75rem' },
                        minWidth: { xs: 16, sm: 20 },
                        height: { xs: 16, sm: 20 }
                      }
                    }}
                  >
                    <LocalFireDepartment sx={{ 
                      color: '#FFD700', 
                      fontSize: { xs: '1rem', sm: '1.25rem' } 
                    }} />
                  </Badge>
                  
                  <Box sx={{ 
                    display: { xs: 'none', sm: 'flex' }, 
                    alignItems: 'center', 
                    gap: 0.5 
                  }}>
                    <Chip 
                      icon={<MonetizationOn sx={{ fontSize: '0.875rem' }} />}
                      label={character.coins.toLocaleString()} 
                      variant="outlined" 
                      size="small" 
                      sx={{ 
                        color: 'white', 
                        borderColor: 'white',
                        '& .MuiChip-icon': { color: '#FFD700' }
                      }}
                    />
                    <Chip 
                      icon={<Diamond sx={{ fontSize: '0.875rem' }} />}
                      label={character.gems.toLocaleString()} 
                      variant="outlined" 
                      size="small" 
                      sx={{ 
                        color: 'white', 
                        borderColor: 'white',
                        '& .MuiChip-icon': { color: '#87CEEB' }
                      }}
                    />
                  </Box>

                  {/* Mobile - Simplified currency display */}
                  <Box sx={{ 
                    display: { xs: 'flex', sm: 'none' }, 
                    alignItems: 'center', 
                    gap: 0.5,
                    fontSize: '0.75rem',
                    color: 'white'
                  }}>
                    <MonetizationOn sx={{ fontSize: '0.875rem', color: '#FFD700' }} />
                    <Typography variant="caption" sx={{ color: 'white' }}>
                      {character.coins}
                    </Typography>
                    <Diamond sx={{ fontSize: '0.875rem', color: '#87CEEB', ml: 0.5 }} />
                    <Typography variant="caption" sx={{ color: 'white' }}>
                      {character.gems}
                    </Typography>
                  </Box>
                </Box>
              )}

              {/* Notification Button */}
              {user?.role === UserRole.STUDENT && (
                <IconButton
                  color="inherit"
                  onClick={handleNotificationClick}
                  sx={{
                    mr: 1,
                    ...touchStyles.touchTarget,
                  }}
                >
                  <Badge badgeContent={unreadCount} color="error" max={99}>
                    {unreadCount > 0 ? <NotificationsActive /> : <Notifications />}
                  </Badge>
                </IconButton>
              )}

              {/* Language Switcher */}
              <LanguageSwitcher />

              {/* Profile Menu */}
              <IconButton
                aria-label="account menu"
                onClick={handleMenu}
                color="inherit"
                sx={{ ...touchStyles.touchTarget }}
              >
                <Avatar sx={{ 
                  width: { xs: 32, sm: 40 }, 
                  height: { xs: 32, sm: 40 } 
                }}>
                  {character?.avatar_url ? (
                    <img 
                      src={character.avatar_url} 
                      alt={character.name} 
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <PersonIcon />
                  )}
                </Avatar>
              </IconButton>

              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                transformOrigin={{ vertical: 'top', horizontal: 'right' }}
                sx={{
                  '& .MuiMenuItem-root': {
                    ...touchStyles.touchListItem
                  }
                }}
              >
                <MenuItem onClick={handleProfile}>
                  <ListItemIcon>
                    <PersonIcon />
                  </ListItemIcon>
                  Profile
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <ListItemIcon>
                    <CloseIcon />
                  </ListItemIcon>
                  Logout
                </MenuItem>
              </Menu>
            </>
          )}

          {/* Auth Buttons */}
          {!isAuthenticated && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                color="inherit" 
                onClick={() => navigate('/login')}
                sx={{ 
                  fontSize: { xs: '0.875rem', sm: '1rem' },
                  ...touchStyles.touchTarget
                }}
              >
                Login
              </Button>
              <Button 
                color="inherit" 
                onClick={() => navigate('/register')}
                sx={{ 
                  fontSize: { xs: '0.875rem', sm: '1rem' },
                  ...touchStyles.touchTarget
                }}
              >
                Register
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Navigation Drawer - Students */}
      {user?.role === UserRole.STUDENT && (
        <Drawer
          anchor="left"
          open={studentMobileDrawerOpen}
          onClose={() => setStudentMobileDrawerOpen(false)}
          sx={{
            '& .MuiDrawer-paper': {
              width: { xs: 280, sm: 320 },
              bgcolor: 'background.paper'
            }
          }}
        >
          <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }} />
          
          {/* Character Info in Drawer */}
          {character && (
            <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
              <Box sx={{ ...flexBox.center, mb: 2 }}>
                <Avatar
                  src={character.avatar_url}
                  sx={{ width: 60, height: 60, mr: 2 }}
                >
                  <PersonIcon />
                </Avatar>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {character.name}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Level {character.total_level}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ ...flexBox.spaceBetween }}>
                <Box sx={{ ...flexBox.center, gap: 0.5 }}>
                  <MonetizationOn sx={{ fontSize: '1rem', color: '#FFD700' }} />
                  <Typography variant="body2">{character.coins.toLocaleString()}</Typography>
                </Box>
                <Box sx={{ ...flexBox.center, gap: 0.5 }}>
                  <Diamond sx={{ fontSize: '1rem', color: '#87CEEB' }} />
                  <Typography variant="body2">{character.gems.toLocaleString()}</Typography>
                </Box>
                <Box sx={{ ...flexBox.center, gap: 0.5 }}>
                  <LocalFireDepartment sx={{ fontSize: '1rem', color: '#FF6B35' }} />
                  <Typography variant="body2">{character.streak_days}</Typography>
                </Box>
              </Box>
            </Box>
          )}

          <List sx={{ pt: 0 }}>
            {studentNavItems.map((item) => (
              <ListItemButton
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  setStudentMobileDrawerOpen(false);
                }}
                sx={{ ...touchStyles.touchListItem }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{
                    fontWeight: 500
                  }}
                />
              </ListItemButton>
            ))}
            
            <Divider sx={{ my: 1 }} />
            
            <ListItemButton
              onClick={() => {
                handleNotificationClick();
                setStudentMobileDrawerOpen(false);
              }}
              sx={{ ...touchStyles.touchListItem }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Badge badgeContent={unreadCount} color="error" max={99}>
                  {unreadCount > 0 ? <NotificationsActive /> : <Notifications />}
                </Badge>
              </ListItemIcon>
              <ListItemText primary="알림" />
            </ListItemButton>
            
            <ListItemButton
              onClick={() => {
                navigate('/profile');
                setStudentMobileDrawerOpen(false);
              }}
              sx={{ ...touchStyles.touchListItem }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <PersonIcon />
              </ListItemIcon>
              <ListItemText primary="Profile" />
            </ListItemButton>
          </List>
        </Drawer>
      )}

      {/* Mobile Navigation for Parents */}
      {user?.role === UserRole.PARENT && (
        <ParentMobileNavigation
          open={mobileMenuOpen}
          onClose={() => setMobileMenuOpen(false)}
          children={connectedChildren}
          selectedChildId={selectedChildId || undefined}
          onChildSelect={(childId) => dispatch(setSelectedChild(childId))}
        />
      )}
    </>
  );
};

export default Navbar;