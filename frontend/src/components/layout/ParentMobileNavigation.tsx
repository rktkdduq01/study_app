import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Box,
  Typography,
  Avatar,
  Chip,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Person as PersonIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  ExpandLess,
  ExpandMore,
  School as SchoolIcon,
  EmojiEvents as AchievementIcon,
  Timeline as TimelineIcon,
  Assessment,
  Close as CloseIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { ChildConnection } from '../../types/parent';

interface ParentMobileNavigationProps {
  open: boolean;
  onClose: () => void;
  children?: ChildConnection[];
  selectedChildId?: string;
  onChildSelect?: (childId: string) => void;
}

const ParentMobileNavigation: React.FC<ParentMobileNavigationProps> = ({
  open,
  onClose,
  children = [],
  selectedChildId,
  onChildSelect,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [childrenOpen, setChildrenOpen] = useState(false);
  const [reportsOpen, setReportsOpen] = useState(false);

  const selectedChild = children.find(child => child.childId === selectedChildId);

  const handleNavigate = (path: string) => {
    navigate(path);
    onClose();
  };

  const handleChildSelect = (childId: string) => {
    if (onChildSelect) {
      onChildSelect(childId);
    }
    handleNavigate(`/parent/children/${childId}`);
  };

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: 280,
          backgroundColor: 'background.paper',
        },
      }}
    >
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" color="primary">
          Parent Portal
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>
      
      <Divider />

      <List>
        {/* Children Section */}
        {children.length > 0 && (
          <>
            <ListItem disablePadding>
              <ListItemButton onClick={() => setChildrenOpen(!childrenOpen)}>
                <ListItemIcon>
                  <SchoolIcon />
                </ListItemIcon>
                <ListItemText
                  primary="Children"
                  secondary={selectedChild ? selectedChild.childName : 'Select a child'}
                />
                {childrenOpen ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
            </ListItem>
            <Collapse in={childrenOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                {children.map((child) => (
                  <ListItem
                    key={child.childId}
                    disablePadding
                    sx={{ pl: 2 }}
                  >
                    <ListItemButton
                      onClick={() => handleChildSelect(child.childId)}
                      selected={child.childId === selectedChildId}
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
                    </ListItemButton>
                  </ListItem>
                ))}
                <ListItem disablePadding sx={{ pl: 2 }}>
                  <ListItemButton onClick={() => handleNavigate('/parent/children/add')}>
                    <ListItemIcon>
                      <AddIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Add Child"
                      primaryTypographyProps={{ color: 'primary' }}
                    />
                  </ListItemButton>
                </ListItem>
              </List>
            </Collapse>
            <Divider sx={{ my: 1 }} />
          </>
        )}

        {/* Dashboard */}
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => handleNavigate('/parent/dashboard')}
            selected={isActive('/parent/dashboard')}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItemButton>
        </ListItem>

        {/* Reports Section */}
        <ListItem disablePadding>
          <ListItemButton onClick={() => setReportsOpen(!reportsOpen)}>
            <ListItemIcon>
              <ReportsIcon />
            </ListItemIcon>
            <ListItemText primary="Reports" />
            {reportsOpen ? <ExpandLess /> : <ExpandMore />}
          </ListItemButton>
        </ListItem>
        <Collapse in={reportsOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>
            <ListItem disablePadding sx={{ pl: 4 }}>
              <ListItemButton
                onClick={() => handleNavigate('/parent/reports/progress')}
                selected={isActive('/parent/reports/progress')}
              >
                <ListItemIcon>
                  <TimelineIcon />
                </ListItemIcon>
                <ListItemText primary="Progress Overview" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding sx={{ pl: 4 }}>
              <ListItemButton
                onClick={() => handleNavigate('/parent/reports/achievements')}
                selected={isActive('/parent/reports/achievements')}
              >
                <ListItemIcon>
                  <AchievementIcon />
                </ListItemIcon>
                <ListItemText primary="Achievements" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding sx={{ pl: 4 }}>
              <ListItemButton
                onClick={() => handleNavigate('/parent/reports/analytics')}
                selected={isActive('/parent/reports/analytics')}
              >
                <ListItemIcon>
                  <Assessment />
                </ListItemIcon>
                <ListItemText primary="Learning Analytics" />
              </ListItemButton>
            </ListItem>
          </List>
        </Collapse>

        {/* Settings */}
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => handleNavigate('/parent/settings')}
            selected={isActive('/parent/settings')}
          >
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>

        {/* Help & Support */}
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => handleNavigate('/parent/help')}
            selected={isActive('/parent/help')}
          >
            <ListItemIcon>
              <HelpIcon />
            </ListItemIcon>
            <ListItemText primary="Help & Support" />
          </ListItemButton>
        </ListItem>
      </List>
    </Drawer>
  );
};

export default ParentMobileNavigation;