import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Menu,
  MenuItem,
  Divider,
  Avatar,
  Typography,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  KeyboardArrowDown as ArrowDownIcon,
  School as SchoolIcon,
  EmojiEvents as AchievementIcon,
  Timeline as TimelineIcon,
  Assessment,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { ChildConnection } from '../../types/parent';

interface ParentNavigationProps {
  children?: ChildConnection[];
  selectedChildId?: string;
  onChildSelect?: (childId: string) => void;
}

const ParentNavigation: React.FC<ParentNavigationProps> = ({ 
  children = [], 
  selectedChildId,
  onChildSelect 
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAppSelector((state) => state.auth);
  
  const [childMenuAnchor, setChildMenuAnchor] = useState<null | HTMLElement>(null);
  const [reportsMenuAnchor, setReportsMenuAnchor] = useState<null | HTMLElement>(null);
  
  const selectedChild = children.find(child => child.childId === selectedChildId);

  const handleChildMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setChildMenuAnchor(event.currentTarget);
  };

  const handleChildMenuClose = () => {
    setChildMenuAnchor(null);
  };

  const handleReportsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setReportsMenuAnchor(event.currentTarget);
  };

  const handleReportsMenuClose = () => {
    setReportsMenuAnchor(null);
  };

  const handleChildSelect = (childId: string) => {
    if (onChildSelect) {
      onChildSelect(childId);
    }
    handleChildMenuClose();
    // Navigate to child-specific dashboard
    navigate(`/parent/children/${childId}`);
  };

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  const handleReportsItemClick = (path: string) => {
    navigate(path);
    handleReportsMenuClose();
  };

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
      {/* Children Dropdown */}
      {children.length > 0 && (
        <Box>
          <Button
            color="inherit"
            onClick={handleChildMenuOpen}
            startIcon={
              selectedChild ? (
                <Avatar 
                  sx={{ width: 24, height: 24 }}
                  src={selectedChild.avatar}
                >
                  {selectedChild.childName.charAt(0)}
                </Avatar>
              ) : (
                <SchoolIcon />
              )
            }
            endIcon={<ArrowDownIcon />}
            sx={{
              textTransform: 'none',
              mr: 2,
              backgroundColor: childMenuAnchor ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
              },
            }}
          >
            {selectedChild ? selectedChild.childName : 'Select Child'}
          </Button>
          <Menu
            anchorEl={childMenuAnchor}
            open={Boolean(childMenuAnchor)}
            onClose={handleChildMenuClose}
            PaperProps={{
              sx: {
                mt: 1,
                minWidth: 250,
              },
            }}
          >
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="subtitle2" color="text.secondary">
                Your Children
              </Typography>
            </Box>
            <Divider />
            {children.map((child) => (
              <MenuItem
                key={child.childId}
                onClick={() => handleChildSelect(child.childId)}
                selected={child.childId === selectedChildId}
                sx={{
                  py: 1.5,
                }}
              >
                <ListItemIcon>
                  <Avatar 
                    sx={{ width: 32, height: 32 }}
                    src={child.avatar}
                  >
                    {child.childName.charAt(0)}
                  </Avatar>
                </ListItemIcon>
                <ListItemText
                  primary={child.childName}
                  secondary={
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                      <Chip 
                        label={`Grade ${child.grade}`} 
                        size="small" 
                        variant="outlined"
                      />
                      {child.isActive && (
                        <Chip 
                          label="Online" 
                          size="small" 
                          color="success"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  }
                />
              </MenuItem>
            ))}
            <Divider />
            <MenuItem
              onClick={() => {
                handleChildMenuClose();
                navigate('/parent/children/add');
              }}
              sx={{
                color: 'primary.main',
                py: 1.5,
              }}
            >
              <ListItemIcon>
                <PersonIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary="Add Child" />
            </MenuItem>
          </Menu>
        </Box>
      )}

      {/* Navigation Items */}
      <Button
        color="inherit"
        onClick={() => navigate('/parent/dashboard')}
        startIcon={<DashboardIcon />}
        sx={{
          textTransform: 'none',
          backgroundColor: isActive('/parent/dashboard') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
      >
        Dashboard
      </Button>

      {/* Reports Dropdown */}
      <Box>
        <Button
          color="inherit"
          onClick={handleReportsMenuOpen}
          startIcon={<ReportsIcon />}
          endIcon={<ArrowDownIcon />}
          sx={{
            textTransform: 'none',
            backgroundColor: isActive('/parent/reports') || reportsMenuAnchor ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          Reports
        </Button>
        <Menu
          anchorEl={reportsMenuAnchor}
          open={Boolean(reportsMenuAnchor)}
          onClose={handleReportsMenuClose}
          PaperProps={{
            sx: {
              mt: 1,
              minWidth: 200,
            },
          }}
        >
          <MenuItem onClick={() => handleReportsItemClick('/parent/reports/progress')}>
            <ListItemIcon>
              <TimelineIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Progress Overview" />
          </MenuItem>
          <MenuItem onClick={() => handleReportsItemClick('/parent/reports/achievements')}>
            <ListItemIcon>
              <AchievementIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Achievements" />
          </MenuItem>
          <MenuItem onClick={() => handleReportsItemClick('/parent/reports/analytics')}>
            <ListItemIcon>
              <Assessment fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Learning Analytics" />
          </MenuItem>
        </Menu>
      </Box>

      <Button
        color="inherit"
        onClick={() => navigate('/parent/settings')}
        startIcon={<SettingsIcon />}
        sx={{
          textTransform: 'none',
          backgroundColor: isActive('/parent/settings') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
      >
        Settings
      </Button>

      <Button
        color="inherit"
        onClick={() => navigate('/parent/help')}
        startIcon={<HelpIcon />}
        sx={{
          textTransform: 'none',
          backgroundColor: isActive('/parent/help') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.2)',
          },
        }}
      >
        Help & Support
      </Button>
    </Box>
  );
};

export default ParentNavigation;