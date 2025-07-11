import React, { useState, useEffect } from 'react';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
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
  CircularProgress,
  LinearProgress,
  Zoom,
  Fade,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Skeleton,
  Collapse,
} from '@mui/material';
import {
  ShoppingCart,
  ShoppingBag,
  Diamond,
  MonetizationOn,
  Star,
  Timer,
  LocalFireDepartment,
  EmojiEvents,
  AutoAwesome,
  Palette,
  Security,
  Psychology,
  Add,
  Remove,
  Favorite,
  FavoriteBorder,
  FilterList,
  Sort,
  Search,
  Refresh,
  NewReleases,
  LocalOffer,
  WorkspacePremium,
  MilitaryTech,
  DiamondOutlined,
  EmojiEvents as Crown,
  CheckCircle,
  Lock,
  ExpandMore,
  TrendingUp,
  Schedule,
  Celebration,
  CardGiftcard,
  Inventory,
  AttachMoney,
  TokenOutlined,
  EmojiEventsOutlined,
  Diamond as CrystallineOutlined,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  ShopItem,
  ShopCategory,
  ShopItemRarity,
  CurrencyType,
  ShopType,
  UserCurrencies,
  DailyShop,
  ShopBundle,
  RewardShopItem,
  ShopFilters
} from '../../types/shop';
import shopService from '../../services/shopService';
import { format } from 'date-fns';
import confetti from 'canvas-confetti';
import { 
  flexBox, 
  gridLayout, 
  containerStyles, 
  componentStyles, 
  touchStyles,
  responsiveValues 
} from '../../utils/responsive';
import { FlexContainer, FlexRow, GridContainer } from '../../components/layout';
import { LoadingErrorWrapper } from '../../components/common/LoadingErrorWrapper';

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

const ShopPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { character } = useAppSelector((state) => state.character);

  const [tabValue, setTabValue] = useState(0);
  const [shopItems, setShopItems] = useState<ShopItem[]>([]);
  const [rewardItems, setRewardItems] = useState<RewardShopItem[]>([]);
  const [currencies, setCurrencies] = useState<UserCurrencies | null>(null);
  const [dailyShop, setDailyShop] = useState<DailyShop | null>(null);
  const [bundles, setBundles] = useState<ShopBundle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [selectedItem, setSelectedItem] = useState<ShopItem | RewardShopItem | null>(null);
  const [showPurchaseDialog, setShowPurchaseDialog] = useState(false);
  const [purchaseQuantity, setPurchaseQuantity] = useState(1);
  const [filters, setFilters] = useState<ShopFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [cartItems, setCartItems] = useState<string[]>([]);

  useEffect(() => {
    loadShopData();
  }, []);

  const loadShopData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [itemsData, rewardsData, currenciesData, dailyData, bundlesData] = await Promise.all([
        shopService.mockGetShopItems(),
        shopService.mockGetRewardShopItems(),
        shopService.mockGetUserCurrencies(),
        shopService.mockGetDailyShop(),
        shopService.mockGetShopBundles()
      ]);
      
      setShopItems(itemsData);
      setRewardItems(rewardsData);
      setCurrencies(currenciesData);
      setDailyShop(dailyData);
      setBundles(bundlesData);
    } catch (error) {
      console.error('Failed to load shop data:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const getRarityColor = (rarity: ShopItemRarity) => {
    switch (rarity) {
      case ShopItemRarity.COMMON:
        return '#9e9e9e';
      case ShopItemRarity.RARE:
        return '#2196f3';
      case ShopItemRarity.EPIC:
        return '#9c27b0';
      case ShopItemRarity.LEGENDARY:
        return '#ff9800';
      case ShopItemRarity.MYTHIC:
        return '#f44336';
      default:
        return '#9e9e9e';
    }
  };

  const getRarityIcon = (rarity: ShopItemRarity) => {
    switch (rarity) {
      case ShopItemRarity.COMMON:
        return <Star />;
      case ShopItemRarity.RARE:
        return <WorkspacePremium />;
      case ShopItemRarity.EPIC:
        return <DiamondOutlined />;
      case ShopItemRarity.LEGENDARY:
        return <MilitaryTech />;
      case ShopItemRarity.MYTHIC:
        return <Crown />;
      default:
        return <Star />;
    }
  };

  const getCurrencyIcon = (currency: CurrencyType | string) => {
    switch (currency) {
      case CurrencyType.COINS:
      case 'coins':
        return <MonetizationOn />;
      case CurrencyType.GEMS:
      case 'gems':
        return <Diamond />;
      case CurrencyType.TOKENS:
      case 'tokens':
      case 'quest_tokens':
        return <TokenOutlined />;
      case CurrencyType.POINTS:
      case 'points':
      case 'achievement_points':
        return <EmojiEventsOutlined />;
      case CurrencyType.CRYSTALS:
      case 'crystals':
        return <CrystallineOutlined />;
      case 'daily_tokens':
        return <Schedule />;
      default:
        return <MonetizationOn />;
    }
  };

  const getCategoryIcon = (category: ShopCategory) => {
    switch (category) {
      case ShopCategory.EQUIPMENT:
        return <Security />;
      case ShopCategory.CUSTOMIZATION:
        return <Palette />;
      case ShopCategory.CONSUMABLES:
        return <Psychology />;
      case ShopCategory.BOOSTS:
        return <TrendingUp />;
      case ShopCategory.SPECIAL:
        return <AutoAwesome />;
      case ShopCategory.BUNDLES:
        return <CardGiftcard />;
      default:
        return <ShoppingBag />;
    }
  };

  const canAfford = (item: ShopItem | RewardShopItem): boolean => {
    if (!currencies) return false;
    
    if ('currency' in item) {
      // Regular shop item
      const userAmount = currencies[item.currency];
      return typeof userAmount === 'number' && userAmount >= item.price;
    } else {
      // Reward shop item
      const currencyMap: Record<string, keyof UserCurrencies> = {
        'quest_tokens': 'tokens',
        'achievement_points': 'points',
        'daily_tokens': 'tokens',
        'event_currency': 'crystals'
      };
      
      const currencyKey = currencyMap[item.reward_currency];
      if (!currencyKey) return false;
      
      const userAmount = currencies[currencyKey];
      return typeof userAmount === 'number' && userAmount >= item.reward_price;
    }
  };

  const handlePurchase = async (item: ShopItem | RewardShopItem) => {
    try {
      if ('currency' in item) {
        await shopService.mockPurchaseItem(item.id, purchaseQuantity);
      } else {
        await shopService.mockPurchaseItem(item.id, 1);
      }
      
      // Trigger celebration
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 }
      });
      
      // Refresh currencies and close dialog
      const newCurrencies = await shopService.mockGetUserCurrencies();
      setCurrencies(newCurrencies);
      setShowPurchaseDialog(false);
      setSelectedItem(null);
      setPurchaseQuantity(1);
    } catch (error) {
      console.error('Purchase failed:', error);
    }
  };

  const renderCurrencyBar = () => (
    <Paper sx={{ 
      p: { xs: 2, sm: 3 }, 
      mb: 3, 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
      color: 'white',
      borderRadius: 2
    }}>
      <Box sx={{ 
        ...flexBox.spaceBetween, 
        flexDirection: { xs: 'column', sm: 'row' },
        gap: 2
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            ...flexBox.center, 
            gap: 1,
            fontSize: { xs: '1.125rem', sm: '1.25rem' }
          }}
        >
          <ShoppingBag />
          My Wallet
        </Typography>
        
        <FlexRow
          spacing={1.5}
          wrap
          sx={{
            width: { xs: '100%', sm: 'auto' },
            justifyContent: { xs: 'space-around', sm: 'flex-end' }
          }}>
          {currencies && Object.entries(currencies).map(([key, value]) => {
            if (key === 'last_updated') return null;
            return (
              <Box 
                key={key}
                sx={{ 
                  textAlign: 'center',
                  minWidth: { xs: 'auto', sm: 80 }
                }}
              >
                <Box sx={{ ...flexBox.center, gap: 0.5, mb: 0.5 }}>
                  {getCurrencyIcon(key as CurrencyType)}
                  <Typography 
                    variant="body2" 
                    sx={{ 
                      fontWeight: 'bold',
                      fontSize: { xs: '0.75rem', sm: '0.875rem' }
                    }}
                  >
                    {typeof value === 'number' ? value.toLocaleString() : value}
                  </Typography>
                </Box>
                <Typography 
                  variant="caption" 
                  sx={{ 
                    fontSize: { xs: '0.65rem', sm: '0.75rem' },
                    opacity: 0.9
                  }}
                >
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                </Typography>
              </Box>
            );
          })}
        </FlexRow>
      </Box>
    </Paper>
  );

  const renderItemCard = (item: ShopItem | RewardShopItem, isRewardItem: boolean = false) => {
    const affordable = canAfford(item);
    const price = isRewardItem ? (item as RewardShopItem).reward_price : (item as ShopItem).price;
    const currency = isRewardItem ? (item as RewardShopItem).reward_currency : (item as ShopItem).currency;
    
    return (
      <motion.div
        key={item.id}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <Card
          sx={{
            cursor: 'pointer',
            border: `2px solid ${getRarityColor(item.rarity)}`,
            opacity: affordable ? 1 : 0.7,
            position: 'relative',
            borderRadius: 2,
            ...componentStyles.card,
            height: { xs: 'auto', md: '100%' },
            minHeight: { xs: 280, sm: 320, md: 380 },
            '&:hover': {
              boxShadow: 6,
              transform: 'translateY(-4px)',
            },
            '&:active': {
              transform: 'scale(0.98)',
            }
          }}
          onClick={() => {
            setSelectedItem(item);
            setShowPurchaseDialog(true);
          }}
        >
          {/* Item badges */}
          <Box sx={{ 
            position: 'absolute', 
            top: { xs: 6, sm: 8 }, 
            left: { xs: 6, sm: 8 }, 
            zIndex: 1,
            display: 'flex',
            flexDirection: { xs: 'column', sm: 'row' },
            gap: 0.5
          }}>
            {item.is_new && (
              <Chip 
                label="NEW" 
                size="small" 
                sx={{ 
                  bgcolor: '#4CAF50', 
                  color: 'white',
                  fontSize: { xs: '0.6rem', sm: '0.75rem' },
                  height: { xs: 20, sm: 24 }
                }} 
              />
            )}
            {item.is_on_sale && (
              <Chip 
                label="SALE" 
                size="small" 
                sx={{ 
                  bgcolor: '#FF5722', 
                  color: 'white',
                  fontSize: { xs: '0.6rem', sm: '0.75rem' },
                  height: { xs: 20, sm: 24 }
                }} 
              />
            )}
            {item.is_limited_time && (
              <Chip 
                label="LIMITED" 
                size="small" 
                sx={{ 
                  bgcolor: '#FF9800', 
                  color: 'white',
                  fontSize: { xs: '0.6rem', sm: '0.75rem' },
                  height: { xs: 20, sm: 24 }
                }} 
              />
            )}
          </Box>

          {/* Rarity indicator */}
          <Box sx={{ 
            position: 'absolute', 
            top: { xs: 6, sm: 8 }, 
            right: { xs: 6, sm: 8 }, 
            zIndex: 1 
          }}>
            <Tooltip title={item.rarity}>
              <Avatar
                sx={{
                  width: { xs: 28, sm: 32 },
                  height: { xs: 28, sm: 32 },
                  bgcolor: getRarityColor(item.rarity),
                  '& .MuiSvgIcon-root': {
                    fontSize: { xs: '1rem', sm: '1.25rem' }
                  }
                }}
              >
                {getRarityIcon(item.rarity)}
              </Avatar>
            </Tooltip>
          </Box>

          <CardContent sx={{ 
            pt: { xs: 5, sm: 6 }, 
            p: { xs: 1.5, sm: 2 },
            pb: { xs: 1, sm: 2 },
            ...flexBox.column,
            height: '100%'
          }}>
            {/* Item icon */}
            <Box sx={{ textAlign: 'center', mb: { xs: 1.5, sm: 2 } }}>
              <Avatar
                src={item.icon_url}
                sx={{
                  width: { xs: 60, sm: 70, md: 80 },
                  height: { xs: 60, sm: 70, md: 80 },
                  mx: 'auto',
                  border: `3px solid ${getRarityColor(item.rarity)}`,
                  '& .MuiSvgIcon-root': {
                    fontSize: { xs: '2rem', sm: '2.5rem' }
                  }
                }}
              >
                {getCategoryIcon(item.category)}
              </Avatar>
            </Box>

            {/* Item info */}
            <Typography 
              variant="h6" 
              gutterBottom 
              sx={{ 
                textAlign: 'center', 
                fontWeight: 'bold',
                fontSize: { xs: '1rem', sm: '1.125rem' },
                lineHeight: 1.2,
                mb: 1
              }}
            >
              {item.name}
            </Typography>
            
            <Typography 
              variant="body2" 
              color="text.secondary" 
              sx={{ 
                mb: 2, 
                minHeight: { xs: 32, sm: 40 },
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                lineHeight: 1.4,
                textAlign: 'center',
                flex: 1
              }}
            >
              {item.description}
            </Typography>

            {/* Price */}
            <Box sx={{ 
              ...flexBox.center, 
              gap: 1, 
              mb: 2,
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              {item.is_on_sale && 'original_price' in item && (
                <Typography 
                  variant="body2" 
                  sx={{ 
                    textDecoration: 'line-through', 
                    color: 'text.disabled',
                    fontSize: { xs: '0.75rem', sm: '0.875rem' }
                  }}
                >
                  {item.original_price}
                </Typography>
              )}
              <Box sx={{ ...flexBox.center, gap: 0.5 }}>
                {getCurrencyIcon(currency)}
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontWeight: 'bold', 
                    color: affordable ? 'text.primary' : 'error.main',
                    fontSize: { xs: '1rem', sm: '1.125rem' }
                  }}
                >
                  {price.toLocaleString()}
                </Typography>
              </Box>
            </Box>

            {/* Effects preview - Mobile optimized */}
            {item.effects && item.effects.length > 0 && (
              <Box sx={{ mb: 2, display: { xs: 'none', sm: 'block' } }}>
                <Typography 
                  variant="caption" 
                  color="text.secondary" 
                  gutterBottom
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                >
                  Effects:
                </Typography>
                {item.effects.slice(0, 2).map((effect, index) => (
                  <Typography 
                    key={index} 
                    variant="caption" 
                    display="block" 
                    sx={{ 
                      color: 'primary.main',
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      lineHeight: 1.3
                    }}
                  >
                    • {effect.description}
                  </Typography>
                ))}
              </Box>
            )}

            {/* Requirements - Mobile simplified */}
            {(item.required_level || item.required_achievements) && (
              <Alert 
                severity="info" 
                sx={{ 
                  mt: 1,
                  fontSize: { xs: '0.7rem', sm: '0.75rem' },
                  py: { xs: 0.5, sm: 1 }
                }}
              >
                <Typography 
                  variant="caption"
                  sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                >
                  {item.required_level && `Lv.${item.required_level}`}
                  {item.required_achievements && item.required_level && ' • '}
                  {item.required_achievements && `${item.required_achievements.length} achievements`}
                </Typography>
              </Alert>
            )}
          </CardContent>

          <CardActions sx={{ 
            justifyContent: 'center', 
            pb: { xs: 1.5, sm: 2 },
            pt: 0
          }}>
            <Button
              variant="contained"
              disabled={!affordable}
              startIcon={<ShoppingCart />}
              fullWidth
              sx={{
                background: affordable ? 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)' : undefined,
                fontSize: { xs: '0.75rem', sm: '0.875rem' },
                py: { xs: 1, sm: 1.25 },
                mx: { xs: 1, sm: 2 },
                ...touchStyles.touchTarget
              }}
            >
              {affordable ? 'Purchase' : 'Cannot Afford'}
            </Button>
          </CardActions>
        </Card>
      </motion.div>
    );
  };

  const renderDailyShop = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Schedule color="primary" />
        Daily Shop
        <Chip
          label={`Refreshes in ${Math.floor((new Date(dailyShop?.refresh_time || '').getTime() - Date.now()) / 1000 / 60 / 60)}h`}
          size="small"
          color="warning"
        />
      </Typography>

      {dailyShop && (
        <FlexContainer direction="column" spacing={3}>
          {/* Featured Item */}
          <Box sx={{ width: '100%' }}>
            <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)', color: 'white' }}>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Star />
                Featured Item of the Day
              </Typography>
              <FlexRow spacing={2} alignItems="center" wrap sx={{ flexDirection: { xs: 'column', md: 'row' } }}>
                <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 66%' } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar
                      src={dailyShop.featured_item.icon_url}
                      sx={{ width: 80, height: 80, border: '3px solid white' }}
                    />
                    <Box>
                      <Typography variant="h6">{dailyShop.featured_item.name}</Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        {dailyShop.featured_item.description}
                      </Typography>
                    </Box>
                  </Box>
                </Box>
                <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 33%' }, textAlign: 'center' }}>
                  <Button
                    variant="contained"
                    size="large"
                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' } }}
                    onClick={() => {
                      setSelectedItem(dailyShop.featured_item);
                      setShowPurchaseDialog(true);
                    }}
                  >
                    View Details
                  </Button>
                </Box>
              </FlexRow>
            </Paper>
          </Box>

          {/* Daily Deals */}
          <Box sx={{ width: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Daily Deals
            </Typography>
            <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={2.5}>
              {dailyShop.daily_deals.map((item) => (
                <Box key={item.id}>
                  {renderItemCard(item)}
                </Box>
              ))}
            </GridContainer>
          </Box>

          {/* Flash Sales */}
          {dailyShop.flash_sales.length > 0 && (
            <Box sx={{ width: '100%' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LocalFireDepartment color="error" />
                Flash Sales
              </Typography>
              <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={2.5}>
                {dailyShop.flash_sales.map((item) => (
                  <Box key={item.id}>
                    {renderItemCard(item)}
                  </Box>
                ))}
              </GridContainer>
            </Box>
          )}
        </FlexContainer>
      )}
    </Box>
  );

  const renderRegularShop = () => {
    const filteredItems = shopItems.filter(item => {
      if (searchQuery && !item.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (filters.category && item.category !== filters.category) {
        return false;
      }
      if (filters.rarity && item.rarity !== filters.rarity) {
        return false;
      }
      if (filters.only_affordable && !canAfford(item)) {
        return false;
      }
      return true;
    });

    const groupedItems = filteredItems.reduce((acc, item) => {
      if (!acc[item.category]) acc[item.category] = [];
      acc[item.category].push(item);
      return acc;
    }, {} as Record<ShopCategory, ShopItem[]>);

    return (
      <Box>
        {/* Search and Filters */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search items..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="small"
            InputProps={{
              startAdornment: <Search sx={{ color: 'text.secondary', mr: 1 }} />
            }}
            sx={{ minWidth: 200 }}
          />
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadShopData}
          >
            Refresh
          </Button>
        </Box>

        {/* Filter Panel */}
        <Collapse in={showFilters}>
          <Paper sx={{ p: 2, mb: 3 }}>
            <FlexRow spacing={2} wrap>
              <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 50%', md: '1 1 25%' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={filters.category || ''}
                    onChange={(e) => setFilters({ ...filters, category: e.target.value as ShopCategory })}
                  >
                    <MenuItem value="">All Categories</MenuItem>
                    {Object.values(ShopCategory).map(category => (
                      <MenuItem key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 50%', md: '1 1 25%' } }}>
                <FormControl fullWidth size="small">
                  <InputLabel>Rarity</InputLabel>
                  <Select
                    value={filters.rarity || ''}
                    onChange={(e) => setFilters({ ...filters, rarity: e.target.value as ShopItemRarity })}
                  >
                    <MenuItem value="">All Rarities</MenuItem>
                    {Object.values(ShopItemRarity).map(rarity => (
                      <MenuItem key={rarity} value={rarity}>
                        {rarity.charAt(0).toUpperCase() + rarity.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 50%', md: '1 1 25%' } }}>
                <ToggleButton
                  value="affordable"
                  selected={filters.only_affordable || false}
                  onChange={() => setFilters({ ...filters, only_affordable: !filters.only_affordable })}
                  size="small"
                >
                  Only Affordable
                </ToggleButton>
              </Box>
            </FlexRow>
          </Paper>
        </Collapse>

        {/* Items by Category */}
        {Object.entries(groupedItems).map(([category, items]) => (
          <Accordion key={category} defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getCategoryIcon(category as ShopCategory)}
                {category.charAt(0).toUpperCase() + category.slice(1)} ({items.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={2.5}>
                {items.map((item) => (
                  <Box key={item.id}>
                    {renderItemCard(item)}
                  </Box>
                ))}
              </GridContainer>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    );
  };

  const renderRewardShop = () => (
    <Box>
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          🏆 Special items available for quest tokens, achievement points, and other rewards!
        </Typography>
      </Alert>

      <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={2.5}>
        {rewardItems.map((item) => (
          <Box key={item.id}>
            {renderItemCard(item, true)}
          </Box>
        ))}
      </GridContainer>
    </Box>
  );

  const renderBundles = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Special Bundles
      </Typography>
      <GridContainer columns={{ xs: 1, md: 2 }} spacing={2.5}>
        {bundles.map((bundle) => (
          <Box key={bundle.id}>
            <Card sx={{ height: '100%' }}>
              {bundle.banner_image && (
                <Box
                  sx={{
                    height: 200,
                    backgroundImage: `url(${bundle.banner_image})`,
                    backgroundSize: 'cover',
                    backgroundPosition: 'center',
                  }}
                />
              )}
              <CardContent>
                <Typography variant="h5" gutterBottom>
                  {bundle.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {bundle.description}
                </Typography>

                {/* Bundle savings */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Box>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      {getCurrencyIcon(bundle.currency)}
                      {bundle.bundle_price.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.disabled" sx={{ textDecoration: 'line-through' }}>
                      {bundle.individual_price.toLocaleString()}
                    </Typography>
                  </Box>
                  <Chip
                    label={`Save ${bundle.savings_percentage}%`}
                    color="success"
                    variant="outlined"
                  />
                </Box>

                {/* Items included */}
                <Typography variant="subtitle2" gutterBottom>
                  Includes {bundle.items.length} items:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {bundle.items.slice(0, 4).map((item) => (
                    <Tooltip key={item.id} title={item.name}>
                      <Avatar
                        src={item.icon_url}
                        sx={{
                          width: 32,
                          height: 32,
                          border: `2px solid ${getRarityColor(item.rarity)}`,
                        }}
                      />
                    </Tooltip>
                  ))}
                  {bundle.items.length > 4 && (
                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'grey.300' }}>
                      +{bundle.items.length - 4}
                    </Avatar>
                  )}
                </Box>

                {bundle.is_limited_time && bundle.expires_at && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="caption">
                      Limited time! Expires {format(new Date(bundle.expires_at), 'MMM d, yyyy')}
                    </Typography>
                  </Alert>
                )}
              </CardContent>
              <CardActions>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<CardGiftcard />}
                  sx={{
                    background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                  }}
                >
                  Purchase Bundle
                </Button>
              </CardActions>
            </Card>
          </Box>
        ))}
      </GridContainer>
    </Box>
  );

  return (
    <Container 
      maxWidth="lg" 
      sx={{ 
        ...containerStyles.responsivePadding,
        mt: { xs: 2, sm: 3, md: 4 }, 
        mb: { xs: 2, sm: 3, md: 4 }
      }}
    >
      <LoadingErrorWrapper
        loading={loading}
        error={error}
        onRetry={loadShopData}
        loadingComponent={
          <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4 }} spacing={3}>
            {[...Array(8)].map((_, i) => (
              <Box key={i}>
                <Skeleton variant="rectangular" height={300} />
              </Box>
            ))}
          </GridContainer>
        }
      >
        {/* Header */}
        <Box sx={{ 
        mb: { xs: 2, sm: 3 },
        textAlign: { xs: 'center', sm: 'left' }
      }}>
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            ...flexBox.center, 
            gap: 1,
            justifyContent: { xs: 'center', sm: 'flex-start' },
            fontSize: { xs: '1.5rem', sm: '2rem' }
          }}
        >
          <ShoppingBag color="primary" />
          Shop
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
        >
          Upgrade your learning experience with powerful items and customizations
        </Typography>
      </Box>

      {/* Currency Bar */}
      {renderCurrencyBar()}

      {/* Main Tabs */}
      <Box sx={{ 
        borderBottom: 1, 
        borderColor: 'divider', 
        mb: { xs: 2, sm: 3 }
      }}>
        <Tabs 
          value={tabValue} 
          onChange={(_, value) => setTabValue(value)}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              ...touchStyles.touchTarget,
              minWidth: { xs: 80, sm: 120 }
            }
          }}
        >
          <Tab 
            label="Daily" 
            icon={<Schedule />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<Schedule />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Regular Shop" 
            icon={<ShoppingBag />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<ShoppingBag />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Rewards" 
            icon={<EmojiEvents />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<EmojiEvents />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Bundles" 
            icon={<CardGiftcard />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<CardGiftcard />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {renderDailyShop()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderRegularShop()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderRewardShop()}
      </TabPanel>
      <TabPanel value={tabValue} index={3}>
        {renderBundles()}
      </TabPanel>

      {/* Purchase Dialog */}
      <Dialog
        open={showPurchaseDialog}
        onClose={() => setShowPurchaseDialog(false)}
        maxWidth="sm"
        fullWidth
        fullScreen={false}
        sx={{
          '& .MuiDialog-paper': {
            mx: { xs: 1, sm: 3 },
            my: { xs: 1, sm: 3 },
            width: { xs: 'calc(100% - 16px)', sm: 'auto' },
            maxHeight: { xs: 'calc(100% - 16px)', sm: 'calc(100% - 64px)' },
            borderRadius: { xs: 2, sm: 3 }
          }
        }}
      >
        {selectedItem && (
          <>
            <DialogTitle sx={{ pb: { xs: 1, sm: 2 } }}>
              <Box sx={{ 
                ...flexBox.center, 
                gap: { xs: 1.5, sm: 2 },
                flexDirection: { xs: 'column', sm: 'row' },
                textAlign: { xs: 'center', sm: 'left' }
              }}>
                <Avatar
                  src={selectedItem.icon_url}
                  sx={{
                    width: { xs: 56, sm: 48 },
                    height: { xs: 56, sm: 48 },
                    border: `2px solid ${getRarityColor(selectedItem.rarity)}`,
                  }}
                >
                  {getRarityIcon(selectedItem.rarity)}
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography 
                    variant="h6"
                    sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}
                  >
                    {selectedItem.name}
                  </Typography>
                  <Chip
                    label={selectedItem.rarity}
                    size="small"
                    sx={{
                      backgroundColor: getRarityColor(selectedItem.rarity),
                      color: 'white',
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      mt: 0.5
                    }}
                  />
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent sx={{ px: { xs: 2, sm: 3 }, py: { xs: 1, sm: 2 } }}>
              <Typography 
                variant="body1" 
                paragraph
                sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
              >
                {selectedItem.description}
              </Typography>

              {/* Effects */}
              {selectedItem.effects && selectedItem.effects.length > 0 && (
                <>
                  <Typography 
                    variant="subtitle2" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                  >
                    Effects:
                  </Typography>
                  <List dense sx={{ py: 0 }}>
                    {selectedItem.effects.map((effect, index) => (
                      <ListItem 
                        key={index}
                        sx={{ px: 0, py: { xs: 0.5, sm: 1 } }}
                      >
                        <ListItemIcon sx={{ minWidth: { xs: 32, sm: 40 } }}>
                          <AutoAwesome color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={effect.description}
                          primaryTypographyProps={{
                            fontSize: { xs: '0.875rem', sm: '1rem' }
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {/* Stats bonus */}
              {selectedItem.stats_bonus && Object.keys(selectedItem.stats_bonus).length > 0 && (
                <>
                  <Typography 
                    variant="subtitle2" 
                    gutterBottom 
                    sx={{ 
                      mt: 2,
                      fontSize: { xs: '0.875rem', sm: '1rem' }
                    }}
                  >
                    Stat Bonuses:
                  </Typography>
                  <List dense sx={{ py: 0 }}>
                    {Object.entries(selectedItem.stats_bonus).map(([stat, value]) => (
                      <ListItem 
                        key={stat}
                        sx={{ px: 0, py: { xs: 0.5, sm: 1 } }}
                      >
                        <ListItemText
                          primary={`${stat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: +${value}`}
                          primaryTypographyProps={{
                            fontSize: { xs: '0.875rem', sm: '1rem' },
                            fontWeight: 500
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {/* Quantity selector for consumables */}
              {'currency' in selectedItem && selectedItem.category === ShopCategory.CONSUMABLES && (
                <Box sx={{ 
                  mt: 3, 
                  ...flexBox.center, 
                  gap: { xs: 1, sm: 2 },
                  p: { xs: 1, sm: 2 },
                  bgcolor: 'grey.50',
                  borderRadius: 1
                }}>
                  <Typography 
                    variant="body2"
                    sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                  >
                    Quantity:
                  </Typography>
                  <IconButton 
                    onClick={() => setPurchaseQuantity(Math.max(1, purchaseQuantity - 1))}
                    sx={{ ...touchStyles.touchTarget }}
                  >
                    <Remove />
                  </IconButton>
                  <Typography 
                    variant="h6"
                    sx={{ 
                      minWidth: 40, 
                      textAlign: 'center',
                      fontSize: { xs: '1.125rem', sm: '1.25rem' }
                    }}
                  >
                    {purchaseQuantity}
                  </Typography>
                  <IconButton 
                    onClick={() => setPurchaseQuantity(purchaseQuantity + 1)}
                    sx={{ ...touchStyles.touchTarget }}
                  >
                    <Add />
                  </IconButton>
                </Box>
              )}

              {/* Total cost */}
              <Box sx={{ 
                mt: 3, 
                p: { xs: 2, sm: 3 }, 
                bgcolor: 'primary.50', 
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'primary.100'
              }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    ...flexBox.center, 
                    gap: 1,
                    fontSize: { xs: '1.125rem', sm: '1.25rem' },
                    fontWeight: 'bold'
                  }}
                >
                  Total Cost:
                  {'currency' in selectedItem ? (
                    <>
                      {getCurrencyIcon(selectedItem.currency)}
                      {(selectedItem.price * purchaseQuantity).toLocaleString()}
                    </>
                  ) : (
                    <>
                      {getCurrencyIcon((selectedItem as RewardShopItem).reward_currency)}
                      {(selectedItem as RewardShopItem).reward_price.toLocaleString()}
                    </>
                  )}
                </Typography>
              </Box>
            </DialogContent>
            <DialogActions sx={{ 
              p: { xs: 2, sm: 3 },
              gap: { xs: 1, sm: 2 },
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              <Button 
                onClick={() => setShowPurchaseDialog(false)}
                fullWidth={true}
                sx={{ 
                  order: { xs: 2, sm: 1 },
                  ...touchStyles.touchTarget
                }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                disabled={!canAfford(selectedItem)}
                onClick={() => handlePurchase(selectedItem)}
                startIcon={<ShoppingCart />}
                fullWidth={true}
                sx={{
                  order: { xs: 1, sm: 2 },
                  background: canAfford(selectedItem) 
                    ? 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)' 
                    : undefined,
                  ...touchStyles.touchTarget
                }}
              >
                Purchase
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
      </LoadingErrorWrapper>
    </Container>
  );
};

export default ShopPage;