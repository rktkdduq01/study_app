export enum ShopCategory {
  EQUIPMENT = 'equipment',
  CUSTOMIZATION = 'customization',
  CONSUMABLES = 'consumables',
  BOOSTS = 'boosts',
  SPECIAL = 'special',
  BUNDLES = 'bundles'
}

export enum ShopItemRarity {
  COMMON = 'common',
  RARE = 'rare',
  EPIC = 'epic',
  LEGENDARY = 'legendary',
  MYTHIC = 'mythic'
}

export enum CurrencyType {
  COINS = 'coins',
  GEMS = 'gems',
  TOKENS = 'tokens', // Special reward currency
  POINTS = 'points', // Achievement points
  CRYSTALS = 'crystals' // Premium currency
}

export enum ShopType {
  BASIC = 'basic',
  PREMIUM = 'premium',
  REWARDS = 'rewards',
  SEASONAL = 'seasonal',
  LIMITED = 'limited'
}

export interface ShopItem {
  id: string;
  name: string;
  description: string;
  category: ShopCategory;
  rarity: ShopItemRarity;
  shop_type: ShopType;
  
  // Pricing
  price: number;
  currency: CurrencyType;
  original_price?: number; // For sale items
  discount_percentage?: number;
  
  // Visual
  icon_url: string;
  preview_images?: string[];
  animation_url?: string;
  
  // Availability
  is_available: boolean;
  is_limited_time: boolean;
  is_featured: boolean;
  is_new: boolean;
  is_on_sale: boolean;
  stock_quantity?: number; // For limited stock items
  max_purchases?: number; // Max per user
  
  // Requirements
  required_level?: number;
  required_achievements?: string[];
  required_quests?: string[];
  unlock_condition?: string;
  
  // Timing
  available_from?: string;
  available_until?: string;
  created_at: string;
  updated_at: string;
  
  // Item effects/stats
  effects?: ItemEffect[];
  stats_bonus?: Record<string, number>;
  duration?: number; // For temporary items (in hours)
  
  // Bundle specific
  bundle_items?: string[]; // Item IDs included in bundle
  bundle_savings?: number; // Amount saved vs individual purchases
}

export interface ItemEffect {
  type: 'xp_boost' | 'coin_boost' | 'streak_protection' | 'hint_unlock' | 'time_extension' | 'double_rewards' | 'cosmetic';
  value: number;
  description: string;
  duration?: number; // in hours
}

export interface ShopPurchase {
  id: string;
  user_id: string;
  item_id: string;
  quantity: number;
  total_price: number;
  currency_used: CurrencyType;
  purchase_date: string;
  is_gift?: boolean;
  gift_recipient?: string;
  transaction_status: 'pending' | 'completed' | 'failed' | 'refunded';
}

export interface UserInventory {
  id: string;
  user_id: string;
  item_id: string;
  quantity: number;
  is_equipped?: boolean;
  is_active?: boolean;
  obtained_date: string;
  expires_at?: string; // For temporary items
  purchase_id?: string;
}

export interface ShopSection {
  id: string;
  title: string;
  description?: string;
  icon: string;
  shop_type: ShopType;
  categories: ShopCategory[];
  featured_items: ShopItem[];
  banner_image?: string;
  is_locked: boolean;
  unlock_requirement?: string;
}

export interface UserCurrencies {
  coins: number;
  gems: number;
  tokens: number;
  points: number;
  crystals: number;
  last_updated: string;
}

export interface ShopStats {
  total_purchases: number;
  total_spent: Record<CurrencyType, number>;
  favorite_category: ShopCategory;
  rare_items_owned: number;
  recent_purchases: ShopPurchase[];
}

export interface DailyShop {
  id: string;
  date: string;
  featured_item: ShopItem;
  daily_deals: ShopItem[];
  flash_sales: ShopItem[];
  refresh_time: string;
}

export interface ShopBundle {
  id: string;
  name: string;
  description: string;
  items: ShopItem[];
  bundle_price: number;
  currency: CurrencyType;
  individual_price: number;
  savings_amount: number;
  savings_percentage: number;
  is_limited_time: boolean;
  expires_at?: string;
  icon_url: string;
  banner_image?: string;
}

export interface GiftSystem {
  can_send_gifts: boolean;
  daily_gift_limit: number;
  gifts_sent_today: number;
  gift_history: GiftTransaction[];
}

export interface GiftTransaction {
  id: string;
  sender_id: string;
  recipient_id: string;
  item_id: string;
  message?: string;
  sent_date: string;
  claimed_date?: string;
  status: 'sent' | 'claimed' | 'expired';
}

export interface ShopFilters {
  category?: ShopCategory;
  rarity?: ShopItemRarity;
  currency?: CurrencyType;
  price_range?: {
    min: number;
    max: number;
  };
  only_available?: boolean;
  only_affordable?: boolean;
  sort_by?: 'price_asc' | 'price_desc' | 'newest' | 'popular' | 'rarity';
}

export interface ShopNotification {
  id: string;
  type: 'new_item' | 'sale' | 'restock' | 'gift_received' | 'purchase_complete';
  title: string;
  message: string;
  item_id?: string;
  created_at: string;
  is_read: boolean;
}

// Special Rewards Shop Types
export interface RewardShopItem extends Omit<ShopItem, 'currency' | 'price'> {
  reward_currency: 'quest_tokens' | 'achievement_points' | 'daily_tokens' | 'event_currency';
  reward_price: number;
  quest_requirement?: string;
  achievement_requirement?: string;
  event_requirement?: string;
  prestige_level_required?: number;
}

export interface QuestReward {
  type: 'currency' | 'item' | 'experience';
  currency_type?: CurrencyType;
  amount?: number;
  item_id?: string;
  item_quantity?: number;
}

export interface SpecialOffers {
  welcome_bundle?: ShopBundle;
  level_up_rewards: Record<number, ShopItem[]>; // Level -> Items
  streak_bonuses: Record<number, QuestReward[]>; // Days -> Rewards
  achievement_unlocks: Record<string, ShopItem[]>; // Achievement ID -> Items
}