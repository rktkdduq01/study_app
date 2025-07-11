import React, { useState, useEffect } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import { LoadingErrorWrapper } from '../../components/common/LoadingErrorWrapper';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip,
  Badge,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  Zoom,
  Fade,
  Slide,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Skeleton,
} from '@mui/material';
import {
  Person,
  School,
  EmojiEvents,
  Star,
  LocalFireDepartment,
  Edit,
  Palette,
  ShoppingBag,
  Security,
  TrendingUp,
  Psychology,
  AutoAwesome,
  Favorite,
  Speed,
  Groups,
  Diamond,
  EmojiEvents as Crown,
  Visibility,
  VisibilityOff,
  SwapHoriz,
  Add,
  ExpandMore,
  CheckCircle,
  Lock,
  Verified,
  WorkspacePremium,
  MilitaryTech,
  DiamondOutlined,
  Celebration,
  Animation,
  PhotoCamera,
  Save,
  Cancel,
  Refresh,
  Shield,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { 
  CharacterProfile,
  CharacterClass,
  CharacterTitle,
  EquipmentItem,
  CustomizationOption,
  EquipmentSlot,
  EquipmentRarity,
  CharacterStats
} from '../../types/character';
import characterService from '../../services/characterService';
import { format } from 'date-fns';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const CharacterPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { character } = useAppSelector((state) => state.character);
  
  const [profile, setProfile] = useState<CharacterProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedEquipment, setSelectedEquipment] = useState<EquipmentItem | null>(null);
  const [selectedCustomization, setSelectedCustomization] = useState<CustomizationOption | null>(null);
  const [showTitleSelector, setShowTitleSelector] = useState(false);
  const [showEquipment, setShowEquipment] = useState(false);
  const [showCustomization, setShowCustomization] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await characterService.mockGetCharacterProfile();
      setProfile(data);
      setNewName(data.character.name);
    } catch (error) {
      console.error('Failed to load character profile:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity: EquipmentRarity) => {
    switch (rarity) {
      case EquipmentRarity.COMMON:
        return '#9e9e9e';
      case EquipmentRarity.RARE:
        return '#2196f3';
      case EquipmentRarity.EPIC:
        return '#9c27b0';
      case EquipmentRarity.LEGENDARY:
        return '#ff9800';
      case EquipmentRarity.MYTHIC:
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const getRarityIcon = (rarity: EquipmentRarity) => {
    switch (rarity) {
      case EquipmentRarity.COMMON:
        return <Star />;
      case EquipmentRarity.RARE:
        return <WorkspacePremium />;
      case EquipmentRarity.EPIC:
        return <DiamondOutlined />;
      case EquipmentRarity.LEGENDARY:
        return <MilitaryTech />;
      case EquipmentRarity.MYTHIC:
        return <Crown />;
      default:
        return <Star />;
    }
  };

  const getClassIcon = (characterClass: CharacterClass) => {
    switch (characterClass) {
      case CharacterClass.SCHOLAR:
        return <School />;
      case CharacterClass.EXPLORER:
        return <TrendingUp />;
      case CharacterClass.WARRIOR:
        return <Security />;
      case CharacterClass.SAGE:
        return <Psychology />;
      case CharacterClass.APPRENTICE:
        return <AutoAwesome />;
      default:
        return <Person />;
    }
  };

  const handleEquipItem = async (item: EquipmentItem) => {
    try {
      if (item.owned) {
        await characterService.mockEquipItem(item.id);
        loadProfile();
        setSelectedEquipment(null);
      }
    } catch (error) {
      console.error('Failed to equip item:', error);
    }
  };

  const handlePurchaseCustomization = async (option: CustomizationOption) => {
    try {
      const result = await characterService.mockPurchaseCustomization(option.id);
      if (result.success) {
        loadProfile();
        setSelectedCustomization(null);
      }
    } catch (error) {
      console.error('Failed to purchase customization:', error);
    }
  };

  const handleNameChange = async () => {
    if (newName.trim() && newName !== profile?.character.name) {
      // Would call API to update name
      setEditingName(false);
    } else {
      setEditingName(false);
      setNewName(profile?.character.name || '');
    }
  };

  const renderCharacterOverview = () => (
    <GridContainer spacing={3}>
      {/* Character Display */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 5' } }}>
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Paper
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              position: 'relative',
              overflow: 'hidden',
              minHeight: 400,
            }}
          >
            {/* Background pattern */}
            <Box
              sx={{
                position: 'absolute',
                top: -50,
                right: -50,
                width: 200,
                height: 200,
                background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
                borderRadius: '50%',
              }}
            />

            {/* Character Avatar */}
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <Badge
                badgeContent={profile?.character.prestige_level}
                color="secondary"
                sx={{
                  '& .MuiBadge-badge': {
                    backgroundColor: '#FFD700',
                    color: 'black',
                    fontWeight: 'bold',
                  },
                }}
              >
                <Avatar
                  src={profile?.character.avatar_url}
                  sx={{
                    width: 120,
                    height: 120,
                    border: '4px solid rgba(255,255,255,0.3)',
                    mb: 2,
                    mx: 'auto',
                  }}
                >
                  <Person sx={{ fontSize: 60 }} />
                </Avatar>
              </Badge>
              
              {/* Character Name */}
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                {editingName ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <input
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      style={{
                        background: 'rgba(255,255,255,0.2)',
                        border: 'none',
                        borderRadius: 4,
                        padding: '8px 12px',
                        color: 'white',
                        fontSize: '1.5rem',
                        textAlign: 'center',
                      }}
                      onKeyPress={(e) => e.key === 'Enter' && handleNameChange()}
                    />
                    <IconButton onClick={handleNameChange} size="small">
                      <Save sx={{ color: 'white' }} />
                    </IconButton>
                    <IconButton onClick={() => setEditingName(false)} size="small">
                      <Cancel sx={{ color: 'white' }} />
                    </IconButton>
                  </Box>
                ) : (
                  <>
                    <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                      {profile?.character.name}
                    </Typography>
                    <IconButton onClick={() => setEditingName(true)} size="small">
                      <Edit sx={{ color: 'white' }} />
                    </IconButton>
                  </>
                )}
              </Box>

              {/* Title */}
              {profile?.character.title && (
                <Chip
                  label={profile.character.title.name}
                  icon={<span>{profile.character.title.icon}</span>}
                  sx={{
                    backgroundColor: profile.character.title.color,
                    color: 'white',
                    fontWeight: 'bold',
                    mt: 1,
                  }}
                  onClick={() => setShowTitleSelector(true)}
                />
              )}

              {/* Class & Level */}
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Chip
                  icon={getClassIcon(profile?.class_info.current || CharacterClass.APPRENTICE)}
                  label={profile?.class_info.current || 'Apprentice'}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
                <Chip
                  icon={<Star />}
                  label={`Level ${profile?.character.total_level}`}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
                />
              </Box>

              {/* Rank */}
              <Typography variant="h6" sx={{ mt: 1, color: '#FFD700' }}>
                {profile?.character.rank} Rank
              </Typography>
            </Box>

            {/* Quick Stats */}
            <GridContainer spacing={2} sx={{ mt: 2 }}>
              <Box sx={{ gridColumn: 'span 4' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6">{profile?.character.coins}</Typography>
                  <Typography variant="caption">Coins</Typography>
                </Box>
              </Box>
              <Box sx={{ gridColumn: 'span 4' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h6">{profile?.character.gems}</Typography>
                  <Typography variant="caption">Gems</Typography>
                </Box>
              </Box>
              <Box sx={{ gridColumn: 'span 4' }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5 }}>
                    <LocalFireDepartment sx={{ color: '#FF6B35' }} />
                    <Typography variant="h6">{profile?.character.streak_days}</Typography>
                  </Box>
                  <Typography variant="caption">Streak</Typography>
                </Box>
              </Box>
            </GridContainer>
          </Paper>
        </motion.div>
      </Box>

      {/* Character Stats */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 7' } }}>
        <Paper sx={{ p: 3, height: '100%' }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp color="primary" />
            Character Stats
          </Typography>

          {profile?.character.stats && (
            <GridContainer spacing={2}>
              {Object.entries(profile.character.stats).map(([statName, value]) => {
                const displayName = statName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                const isPercentage = statName.includes('multiplier') || statName.includes('bonus') || statName.includes('protection');
                const displayValue = isPercentage ? `${(value * 100).toFixed(1)}%` : Math.round(value);
                const maxValue = isPercentage ? 1 : 100;
                const normalizedValue = isPercentage ? value * 100 : value;

                return (
                  <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6' } }} key={statName}>
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {displayName}
                        </Typography>
                        <Typography variant="body2" color="primary">
                          {displayValue}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(normalizedValue, 100)}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 4,
                            backgroundColor: normalizedValue > 80 ? '#4CAF50' : normalizedValue > 60 ? '#FF9800' : '#2196F3',
                          },
                        }}
                      />
                    </Box>
                  </Box>
                );
              })}
            </GridContainer>
          )}

          {/* Experience Progress */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Experience Progress
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">
                {profile?.character.total_experience} / {((Math.floor((profile?.character.total_level || 1) / 5) + 1) * 1000)} XP
              </Typography>
              <Typography variant="body2" color="primary">
                Next Level: {(profile?.character.total_level || 0) + 1}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={((profile?.character.total_experience || 0) % 1000) / 10}
              sx={{ height: 10, borderRadius: 5 }}
            />
          </Box>
        </Paper>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ gridColumn: 'span 12' }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Stack direction="row" spacing={2} flexWrap="wrap">
            <Button
              variant="contained"
              startIcon={<ShoppingBag />}
              onClick={() => setShowEquipment(true)}
              sx={{
                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
              }}
            >
              Equipment
            </Button>
            <Button
              variant="contained"
              startIcon={<Palette />}
              onClick={() => setShowCustomization(true)}
              sx={{
                background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              }}
            >
              Customize
            </Button>
            <Button
              variant="contained"
              startIcon={<EmojiEvents />}
              onClick={() => setShowTitleSelector(true)}
              sx={{
                background: 'linear-gradient(45deg, #FF9800 30%, #FFD54F 90%)',
              }}
            >
              Change Title
            </Button>
            <Button
              variant="outlined"
              startIcon={<PhotoCamera />}
              onClick={() => {/* Avatar change logic */}}
            >
              Change Avatar
            </Button>
          </Stack>
        </Paper>
      </Box>
    </GridContainer>
  );

  const renderEquipmentTab = () => (
    <GridContainer spacing={3}>
      {/* Currently Equipped */}
      <Box sx={{ gridColumn: 'span 12' }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Security color="primary" />
          Currently Equipped
        </Typography>
        <GridContainer spacing={2}>
          {Object.entries(EquipmentSlot).map(([key, slot]) => {
            const equippedItem = profile?.character.equipment[slot as keyof typeof profile.character.equipment];
            
            return (
              <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 4' } }} key={slot}>
                <Card
                  sx={{
                    minHeight: 120,
                    display: 'flex',
                    flexDirection: 'column',
                    border: equippedItem ? `2px solid ${getRarityColor(equippedItem.rarity)}` : '2px dashed #ccc',
                    cursor: 'pointer',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => setShowEquipment(true)}
                >
                  <CardContent sx={{ flex: 1, textAlign: 'center' }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      {slot.charAt(0).toUpperCase() + slot.slice(1)}
                    </Typography>
                    {equippedItem ? (
                      <>
                        <Avatar
                          src={equippedItem.icon_url}
                          sx={{
                            width: 48,
                            height: 48,
                            mx: 'auto',
                            mb: 1,
                            backgroundColor: getRarityColor(equippedItem.rarity),
                          }}
                        >
                          {getRarityIcon(equippedItem.rarity)}
                        </Avatar>
                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                          {equippedItem.name}
                        </Typography>
                        <Chip
                          label={equippedItem.rarity}
                          size="small"
                          sx={{
                            mt: 0.5,
                            backgroundColor: getRarityColor(equippedItem.rarity),
                            color: 'white',
                          }}
                        />
                      </>
                    ) : (
                      <Box>
                        <Add sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                        <Typography variant="body2" color="text.disabled">
                          No equipment
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Box>
            );
          })}
        </GridContainer>
      </Box>

      {/* Equipment Inventory */}
      <Box sx={{ gridColumn: 'span 12' }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ShoppingBag color="primary" />
          Equipment Inventory
        </Typography>
        <GridContainer spacing={2}>
          {profile?.equipment_inventory.map((item) => (
            <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 4' } }} key={item.id}>
              <Card
                sx={{
                  border: `2px solid ${getRarityColor(item.rarity)}`,
                  cursor: 'pointer',
                  opacity: item.owned ? 1 : 0.6,
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => setSelectedEquipment(item)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Avatar
                      src={item.icon_url}
                      sx={{
                        width: 48,
                        height: 48,
                        backgroundColor: getRarityColor(item.rarity),
                      }}
                    >
                      {getRarityIcon(item.rarity)}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                        {item.name}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={item.rarity}
                          size="small"
                          sx={{
                            backgroundColor: getRarityColor(item.rarity),
                            color: 'white',
                          }}
                        />
                        {item.equipped && (
                          <Chip label="Equipped" size="small" color="success" />
                        )}
                        {!item.owned && (
                          <Chip
                            label={`${item.cost} coins`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {item.description}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          ))}
        </GridContainer>
      </Box>
    </GridContainer>
  );

  const renderCustomizationTab = () => (
    <GridContainer spacing={3}>
      {/* Current Appearance */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 4' } }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Current Appearance
          </Typography>
          <Avatar
            src={profile?.character.avatar_url}
            sx={{
              width: 150,
              height: 150,
              mx: 'auto',
              mb: 2,
              border: '4px solid',
              borderColor: 'primary.main',
            }}
          >
            <Person sx={{ fontSize: 80 }} />
          </Avatar>
          <Typography variant="body2" color="text.secondary">
            Click on customization options to preview changes
          </Typography>
        </Paper>
      </Box>

      {/* Customization Options */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 8' } }}>
        <Typography variant="h6" gutterBottom>
          Customization Options
        </Typography>
        
        {/* Group by category */}
        {Object.entries(
          profile?.customization_options.reduce((acc, option) => {
            if (!acc[option.category]) acc[option.category] = [];
            acc[option.category].push(option);
            return acc;
          }, {} as Record<string, CustomizationOption[]>) || {}
        ).map(([category, options]) => (
          <Accordion key={category} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="subtitle1">
                {category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <GridContainer spacing={2}>
                {options.map((option) => (
                  <Box sx={{ gridColumn: { xs: 'span 6', sm: 'span 4', md: 'span 3' } }} key={option.id}>
                    <Card
                      sx={{
                        cursor: option.unlocked ? 'pointer' : 'not-allowed',
                        opacity: option.unlocked ? 1 : 0.5,
                        border: option.unlocked ? '2px solid transparent' : '2px solid #ccc',
                        '&:hover': option.unlocked ? {
                          borderColor: 'primary.main',
                          transform: 'translateY(-2px)',
                        } : {},
                      }}
                      onClick={() => option.unlocked && setSelectedCustomization(option)}
                    >
                      <CardContent sx={{ textAlign: 'center', p: 1 }}>
                        <Box
                          sx={{
                            width: 60,
                            height: 60,
                            mx: 'auto',
                            mb: 1,
                            borderRadius: 1,
                            backgroundColor: 'grey.200',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            position: 'relative',
                          }}
                        >
                          {!option.unlocked && (
                            <Lock sx={{ color: 'text.disabled' }} />
                          )}
                        </Box>
                        <Typography variant="caption" display="block">
                          {option.name}
                        </Typography>
                        {option.cost && (
                          <Chip
                            label={`${option.cost} ${option.currency}`}
                            size="small"
                            variant="outlined"
                            sx={{ mt: 0.5 }}
                          />
                        )}
                        {option.requirement && !option.unlocked && (
                          <Typography variant="caption" color="text.disabled" display="block">
                            {option.requirement}
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  </Box>
                ))}
              </GridContainer>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </GridContainer>
  );

  const renderProgressTab = () => (
    <GridContainer spacing={3}>
      {/* Subject Levels */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Subject Mastery
          </Typography>
          {profile?.character.subject_levels.map((subject) => (
            <Box key={subject.id} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                  {subject.subject.charAt(0).toUpperCase() + subject.subject.slice(1)}
                </Typography>
                <Typography variant="body2" color="primary">
                  Level {subject.level}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(subject.experience / subject.exp_to_next_level) * 100}
                sx={{ height: 8, borderRadius: 4, mb: 1 }}
              />
              <Typography variant="caption" color="text.secondary">
                {subject.experience} / {subject.exp_to_next_level} XP
              </Typography>
            </Box>
          ))}
        </Paper>
      </Box>

      {/* Achievements Progress */}
      <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Achievement Progress
          </Typography>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <CircularProgress
              variant="determinate"
              value={(profile?.achievements_progress.completed || 0) / (profile?.achievements_progress.total || 1) * 100}
              size={120}
              thickness={6}
              sx={{ mb: 2 }}
            />
            <Typography variant="h4">
              {profile?.achievements_progress.completed}/{profile?.achievements_progress.total}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Achievements Unlocked
            </Typography>
          </Box>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<EmojiEvents />}
            onClick={() => navigate('/student/achievements')}
          >
            View All Achievements
          </Button>
        </Paper>
      </Box>

      {/* Social Stats */}
      <Box sx={{ gridColumn: 'span 12' }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Social & Community
          </Typography>
          <GridContainer spacing={3}>
            <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
              <Box sx={{ textAlign: 'center' }}>
                <Groups sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                <Typography variant="h5">{profile?.social_stats.friends_count}</Typography>
                <Typography variant="body2" color="text.secondary">Friends</Typography>
              </Box>
            </Box>
            <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
              <Box sx={{ textAlign: 'center' }}>
                <Shield sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h6">{profile?.social_stats.guild || 'None'}</Typography>
                <Typography variant="body2" color="text.secondary">Guild</Typography>
              </Box>
            </Box>
            <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
              <Box sx={{ textAlign: 'center' }}>
                <Psychology sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
                <Typography variant="h6">{profile?.social_stats.mentor || 'None'}</Typography>
                <Typography variant="body2" color="text.secondary">Mentor</Typography>
              </Box>
            </Box>
          </GridContainer>
        </Paper>
      </Box>
    </GridContainer>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Person color="primary" />
          Character Profile
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Customize your character, manage equipment, and track your progress
        </Typography>
      </Box>

      {/* Main Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)}>
          <Tab label="Overview" icon={<Person />} iconPosition="start" />
          <Tab label="Equipment" icon={<Security />} iconPosition="start" />
          <Tab label="Customization" icon={<Palette />} iconPosition="start" />
          <Tab label="Progress" icon={<TrendingUp />} iconPosition="start" />
        </Tabs>
      </Box>

      <LoadingErrorWrapper
        loading={loading}
        error={error}
        onRetry={loadProfile}
        loadingComponent={
          <GridContainer spacing={3}>
            {[...Array(6)].map((_, i) => (
              <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6', md: 'span 4' } }} key={i}>
                <Skeleton variant="rectangular" height={200} />
              </Box>
            ))}
          </GridContainer>
        }
      >
        <TabPanel value={tabValue} index={0}>
          {renderCharacterOverview()}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          {renderEquipmentTab()}
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          {renderCustomizationTab()}
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          {renderProgressTab()}
        </TabPanel>
      </LoadingErrorWrapper>

      {/* Equipment Detail Dialog */}
      <Dialog
        open={!!selectedEquipment}
        onClose={() => setSelectedEquipment(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedEquipment && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar
                  src={selectedEquipment.icon_url}
                  sx={{
                    width: 48,
                    height: 48,
                    backgroundColor: getRarityColor(selectedEquipment.rarity),
                  }}
                >
                  {getRarityIcon(selectedEquipment.rarity)}
                </Avatar>
                <Box>
                  <Typography variant="h6">{selectedEquipment.name}</Typography>
                  <Chip
                    label={selectedEquipment.rarity}
                    size="small"
                    sx={{
                      backgroundColor: getRarityColor(selectedEquipment.rarity),
                      color: 'white',
                    }}
                  />
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedEquipment.description}
              </Typography>
              
              {/* Stats Bonus */}
              <Typography variant="subtitle2" gutterBottom>
                Stats Bonus:
              </Typography>
              <List dense>
                {Object.entries(selectedEquipment.stats_bonus).map(([stat, value]) => (
                  <ListItem key={stat}>
                    <ListItemText
                      primary={`${stat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: +${value}`}
                    />
                  </ListItem>
                ))}
              </List>

              {/* Special Effects */}
              {selectedEquipment.special_effects && selectedEquipment.special_effects.length > 0 && (
                <>
                  <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                    Special Effects:
                  </Typography>
                  <List dense>
                    {selectedEquipment.special_effects.map((effect, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <AutoAwesome color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={effect} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedEquipment(null)}>
                Close
              </Button>
              {selectedEquipment.owned && !selectedEquipment.equipped && (
                <Button
                  variant="contained"
                  onClick={() => handleEquipItem(selectedEquipment)}
                >
                  Equip
                </Button>
              )}
              {!selectedEquipment.owned && (
                <Button
                  variant="contained"
                  disabled={selectedEquipment.cost ? selectedEquipment.cost > (profile?.character.coins || 0) : false}
                >
                  Purchase ({selectedEquipment.cost} coins)
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Title Selector Dialog */}
      <Dialog
        open={showTitleSelector}
        onClose={() => setShowTitleSelector(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Select Title</DialogTitle>
        <DialogContent>
          <GridContainer spacing={2}>
            {profile?.available_titles.map((title) => (
              <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 6' } }} key={title.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    border: profile.character.title?.id === title.id ? '2px solid' : '1px solid',
                    borderColor: profile.character.title?.id === title.id ? 'primary.main' : 'divider',
                    '&:hover': {
                      borderColor: 'primary.main',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <span style={{ fontSize: '1.5rem' }}>{title.icon}</span>
                      <Typography variant="h6" sx={{ color: title.color }}>
                        {title.name}
                      </Typography>
                      {profile.character.title?.id === title.id && (
                        <CheckCircle color="primary" />
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {title.description}
                    </Typography>
                    <Typography variant="caption" color="text.disabled">
                      Earned: {format(new Date(title.earned_at), 'MMM d, yyyy')}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </GridContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTitleSelector(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CharacterPage;
