import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Badge,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  LocalMall as BagIcon,
  Speed as BoostIcon,
  Palette as CosmeticIcon,
  Restaurant as ConsumableIcon,
  Shield as EquipmentIcon,
  Star as SpecialIcon,
  Info as InfoIcon,
  PlayArrow as UseIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { gamificationService, InventoryItem } from '../../services/gamificationService';

interface InventoryPanelProps {
  onItemUse?: (item: InventoryItem) => void;
}

const InventoryPanel: React.FC<InventoryPanelProps> = ({ onItemUse }) => {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [usingItem, setUsingItem] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const typeIcons = {
    boost: <BoostIcon />,
    cosmetic: <CosmeticIcon />,
    consumable: <ConsumableIcon />,
    equipment: <EquipmentIcon />,
    special: <SpecialIcon />,
  };

  const rarityColors = {
    common: '#9E9E9E',
    uncommon: '#4CAF50',
    rare: '#2196F3',
    epic: '#9C27B0',
    legendary: '#FF9800',
  };

  useEffect(() => {
    loadInventory();
  }, [selectedType]);

  const loadInventory = async () => {
    try {
      setLoading(true);
      const itemType = selectedType === 'all' ? undefined : selectedType;
      const data = await gamificationService.getInventory(itemType);
      setItems(data.items);
    } catch (error) {
      console.error('Failed to load inventory:', error);
      setError('Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const handleUseItem = async (item: InventoryItem) => {
    if (item.type !== 'boost' && item.type !== 'consumable') {
      setError('This item cannot be used directly');
      return;
    }

    try {
      setUsingItem(item.id);
      const result = await gamificationService.useItem(item.id);
      
      setSuccessMessage(`Used ${item.name}! ${Object.entries(result.effects).map(([key, value]) => `${key}: +${value}`).join(', ')}`);
      
      // Reload inventory
      await loadInventory();
      
      if (onItemUse) {
        onItemUse(item);
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to use item');
    } finally {
      setUsingItem(null);
    }
  };

  const filteredItems = selectedType === 'all' 
    ? items 
    : items.filter(item => item.type === selectedType);

  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
  const uniqueItems = items.length;

  return (
    <>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                <InventoryIcon />
              </Avatar>
              <Box>
                <Typography variant="h5">Inventory</Typography>
                <Typography variant="body2" color="text.secondary">
                  {totalItems} items ({uniqueItems} unique)
                </Typography>
              </Box>
            </Box>
            <Chip
              icon={<BagIcon />}
              label={`${totalItems} / 100`}
              color={totalItems > 80 ? 'warning' : 'default'}
            />
          </Box>
        </Box>

        {/* Type Tabs */}
        <Tabs
          value={selectedType}
          onChange={(e, value) => setSelectedType(value)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ mb: 3 }}
        >
          <Tab label="All" value="all" icon={<BagIcon />} iconPosition="start" />
          {Object.entries(typeIcons).map(([type, icon]) => (
            <Tab
              key={type}
              label={type.charAt(0).toUpperCase() + type.slice(1)}
              value={type}
              icon={icon}
              iconPosition="start"
            />
          ))}
        </Tabs>

        {/* Success/Error Messages */}
        {successMessage && (
          <Alert severity="success" onClose={() => setSuccessMessage(null)} sx={{ mb: 2 }}>
            {successMessage}
          </Alert>
        )}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Items Grid */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : filteredItems.length === 0 ? (
          <Alert severity="info">
            No items in this category
          </Alert>
        ) : (
          <Grid container spacing={2}>
            {filteredItems.map((item) => (
              <Grid size={{ xs: 6, sm: 4, md: 3 }} key={item.id}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Card
                    sx={{
                      height: '100%',
                      border: 2,
                      borderColor: rarityColors[item.rarity as keyof typeof rarityColors],
                      background: `linear-gradient(135deg, ${rarityColors[item.rarity as keyof typeof rarityColors]}11 0%, transparent 100%)`,
                    }}
                  >
                    <CardContent sx={{ textAlign: 'center', pb: 1 }}>
                      <Badge
                        badgeContent={item.quantity > 1 ? item.quantity : null}
                        color="primary"
                      >
                        <Avatar
                          src={item.icon_url}
                          sx={{
                            width: 64,
                            height: 64,
                            mx: 'auto',
                            mb: 1,
                            bgcolor: rarityColors[item.rarity as keyof typeof rarityColors],
                          }}
                        >
                          {typeIcons[item.type as keyof typeof typeIcons]}
                        </Avatar>
                      </Badge>
                      
                      <Typography variant="subtitle2" noWrap>
                        {item.name}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center', mt: 1 }}>
                        <Chip
                          label={item.type}
                          size="small"
                          icon={typeIcons[item.type as keyof typeof typeIcons]}
                        />
                        <Chip
                          label={item.rarity}
                          size="small"
                          sx={{
                            color: 'white',
                            bgcolor: rarityColors[item.rarity as keyof typeof rarityColors],
                          }}
                        />
                      </Box>
                      
                      {item.equipped && (
                        <Chip
                          label="Equipped"
                          size="small"
                          color="success"
                          sx={{ mt: 1 }}
                        />
                      )}
                    </CardContent>
                    
                    <CardActions sx={{ justifyContent: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => setSelectedItem(item)}
                      >
                        <InfoIcon />
                      </IconButton>
                      
                      {(item.type === 'boost' || item.type === 'consumable') && (
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleUseItem(item)}
                          disabled={usingItem === item.id}
                        >
                          {usingItem === item.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <UseIcon />
                          )}
                        </IconButton>
                      )}
                    </CardActions>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Item Detail Dialog */}
      <Dialog
        open={!!selectedItem}
        onClose={() => setSelectedItem(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedItem && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar
                  src={selectedItem.icon_url}
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: rarityColors[selectedItem.rarity as keyof typeof rarityColors],
                  }}
                >
                  {typeIcons[selectedItem.type as keyof typeof typeIcons]}
                </Avatar>
                <Box>
                  <Typography variant="h6">{selectedItem.name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Chip
                      label={selectedItem.type}
                      size="small"
                      icon={typeIcons[selectedItem.type as keyof typeof typeIcons]}
                    />
                    <Chip
                      label={selectedItem.rarity}
                      size="small"
                      sx={{
                        color: 'white',
                        bgcolor: rarityColors[selectedItem.rarity as keyof typeof rarityColors],
                      }}
                    />
                  </Box>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedItem.description}
              </Typography>
              
              {selectedItem.effects && Object.keys(selectedItem.effects).length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Effects:
                  </Typography>
                  {Object.entries(selectedItem.effects).map(([effect, value]) => (
                    <Chip
                      key={effect}
                      label={`${effect}: +${value}`}
                      size="small"
                      color="primary"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              )}
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Quantity: {selectedItem.quantity}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Acquired: {new Date(selectedItem.acquired_at).toLocaleDateString()}
                </Typography>
              </Box>
            </DialogContent>
            <DialogActions>
              {(selectedItem.type === 'boost' || selectedItem.type === 'consumable') && (
                <Button
                  onClick={() => {
                    handleUseItem(selectedItem);
                    setSelectedItem(null);
                  }}
                  variant="contained"
                  startIcon={<UseIcon />}
                  disabled={usingItem === selectedItem.id}
                >
                  Use Item
                </Button>
              )}
              <Button onClick={() => setSelectedItem(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </>
  );
};

export default InventoryPanel;