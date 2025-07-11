import api from './api';
import {
  ShopItem,
  ShopCategory,
  ShopItemRarity,
  CurrencyType,
  ShopType,
  ShopPurchase,
  UserInventory,
  UserCurrencies,
  ShopFilters,
  DailyShop,
  ShopBundle,
  RewardShopItem,
  SpecialOffers,
  ShopSection,
  ShopStats,
  ItemEffect
} from '../types/shop';

class ShopService {
  // Basic Shop Methods
  async getShopItems(filters?: ShopFilters): Promise<ShopItem[]> {
    const response = await api.get('/shop/items', { params: filters });
    return response.data;
  }

  async getShopSections(): Promise<ShopSection[]> {
    const response = await api.get('/shop/sections');
    return response.data;
  }

  async getFeaturedItems(): Promise<ShopItem[]> {
    const response = await api.get('/shop/featured');
    return response.data;
  }

  async getDailyShop(): Promise<DailyShop> {
    const response = await api.get('/shop/daily');
    return response.data;
  }

  async getShopBundles(): Promise<ShopBundle[]> {
    const response = await api.get('/shop/bundles');
    return response.data;
  }

  // Reward Shop Methods
  async getRewardShopItems(): Promise<RewardShopItem[]> {
    const response = await api.get('/shop/rewards');
    return response.data;
  }

  async getSpecialOffers(): Promise<SpecialOffers> {
    const response = await api.get('/shop/special-offers');
    return response.data;
  }

  // Purchase Methods
  async purchaseItem(itemId: string, quantity: number = 1): Promise<ShopPurchase> {
    const response = await api.post('/shop/purchase', {
      item_id: itemId,
      quantity
    });
    return response.data;
  }

  async purchaseBundle(bundleId: string): Promise<ShopPurchase> {
    const response = await api.post('/shop/purchase-bundle', {
      bundle_id: bundleId
    });
    return response.data;
  }

  async purchaseRewardItem(itemId: string): Promise<ShopPurchase> {
    const response = await api.post('/shop/rewards/purchase', {
      item_id: itemId
    });
    return response.data;
  }

  // User Data Methods
  async getUserCurrencies(): Promise<UserCurrencies> {
    const response = await api.get('/user/currencies');
    return response.data;
  }

  async getUserInventory(): Promise<UserInventory[]> {
    const response = await api.get('/user/inventory');
    return response.data;
  }

  async getShopStats(): Promise<ShopStats> {
    const response = await api.get('/shop/stats');
    return response.data;
  }

  // Mock Methods for Development
  async mockGetShopItems(): Promise<ShopItem[]> {
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return [
      // Equipment Items
      {
        id: 'crown-wisdom',
        name: 'Crown of Wisdom',
        description: 'A magnificent crown that enhances your learning abilities and grants bonus XP',
        category: ShopCategory.EQUIPMENT,
        rarity: ShopItemRarity.LEGENDARY,
        shop_type: ShopType.BASIC,
        price: 1000,
        currency: CurrencyType.COINS,
        icon_url: '/shop/crown-wisdom.png',
        is_available: true,
        is_limited_time: false,
        is_featured: true,
        is_new: false,
        is_on_sale: false,
        required_level: 15,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'xp_boost',
            value: 25,
            description: '+25% XP from all activities'
          }
        ],
        stats_bonus: {
          intelligence: 15,
          wisdom: 20
        }
      },
      {
        id: 'magic-quill',
        name: 'Enchanted Quill',
        description: 'A magical writing instrument that speeds up problem solving',
        category: ShopCategory.EQUIPMENT,
        rarity: ShopItemRarity.EPIC,
        shop_type: ShopType.BASIC,
        price: 500,
        currency: CurrencyType.COINS,
        icon_url: '/shop/magic-quill.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: true,
        is_on_sale: false,
        required_level: 8,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'time_extension',
            value: 30,
            description: '+30 seconds for timed challenges'
          }
        ]
      },
      // Customization Items
      {
        id: 'rainbow-hair',
        name: 'Rainbow Hair Dye',
        description: 'Transform your avatar with spectacular rainbow colors',
        category: ShopCategory.CUSTOMIZATION,
        rarity: ShopItemRarity.RARE,
        shop_type: ShopType.PREMIUM,
        price: 50,
        currency: CurrencyType.GEMS,
        icon_url: '/shop/rainbow-hair.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: true,
        original_price: 75,
        discount_percentage: 33,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'cosmetic',
            value: 0,
            description: 'Unlocks rainbow hair customization'
          }
        ]
      },
      {
        id: 'royal-outfit',
        name: 'Royal Scholar Outfit',
        description: 'Dress like royalty with this elegant scholar ensemble',
        category: ShopCategory.CUSTOMIZATION,
        rarity: ShopItemRarity.EPIC,
        shop_type: ShopType.BASIC,
        price: 300,
        currency: CurrencyType.COINS,
        icon_url: '/shop/royal-outfit.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: false,
        required_achievements: ['complete_10_quests'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'cosmetic',
            value: 0,
            description: 'Unlocks royal outfit customization'
          }
        ]
      },
      // Consumables
      {
        id: 'xp-potion',
        name: 'Experience Potion',
        description: 'Double your XP gains for the next 2 hours',
        category: ShopCategory.CONSUMABLES,
        rarity: ShopItemRarity.COMMON,
        shop_type: ShopType.BASIC,
        price: 100,
        currency: CurrencyType.COINS,
        icon_url: '/shop/xp-potion.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        duration: 2,
        effects: [
          {
            type: 'xp_boost',
            value: 100,
            description: 'Double XP for 2 hours',
            duration: 2
          }
        ]
      },
      {
        id: 'hint-crystal',
        name: 'Hint Crystal',
        description: 'Provides 3 extra hints for challenging problems',
        category: ShopCategory.CONSUMABLES,
        rarity: ShopItemRarity.RARE,
        shop_type: ShopType.BASIC,
        price: 150,
        currency: CurrencyType.COINS,
        icon_url: '/shop/hint-crystal.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'hint_unlock',
            value: 3,
            description: '+3 hints available'
          }
        ]
      },
      // Special/Limited Items
      {
        id: 'winter-companion',
        name: 'Frost Wolf Companion',
        description: 'A mystical winter companion that provides study guidance',
        category: ShopCategory.SPECIAL,
        rarity: ShopItemRarity.MYTHIC,
        shop_type: ShopType.SEASONAL,
        price: 100,
        currency: CurrencyType.GEMS,
        icon_url: '/shop/frost-wolf.png',
        is_available: true,
        is_limited_time: true,
        is_featured: true,
        is_new: true,
        is_on_sale: false,
        available_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        stock_quantity: 100,
        max_purchases: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'double_rewards',
            value: 10,
            description: 'Double rewards for winter quests'
          }
        ]
      }
    ];
  }

  async mockGetRewardShopItems(): Promise<RewardShopItem[]> {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    return [
      {
        id: 'legendary-staff',
        name: 'Staff of Ancient Knowledge',
        description: 'A legendary staff wielded by the greatest scholars of old',
        category: ShopCategory.EQUIPMENT,
        rarity: ShopItemRarity.MYTHIC,
        shop_type: ShopType.REWARDS,
        reward_currency: 'achievement_points',
        reward_price: 500,
        icon_url: '/shop/legendary-staff.png',
        is_available: true,
        is_limited_time: false,
        is_featured: true,
        is_new: false,
        is_on_sale: false,
        achievement_requirement: 'unlock_all_subjects',
        prestige_level_required: 5,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'xp_boost',
            value: 50,
            description: '+50% XP from all sources'
          },
          {
            type: 'streak_protection',
            value: 1,
            description: 'Protects streak from breaking once per week'
          }
        ],
        stats_bonus: {
          intelligence: 25,
          wisdom: 30,
          focus: 20
        }
      },
      {
        id: 'master-title',
        name: 'Title: The Enlightened',
        description: 'An exclusive title for those who have mastered all subjects',
        category: ShopCategory.SPECIAL,
        rarity: ShopItemRarity.LEGENDARY,
        shop_type: ShopType.REWARDS,
        reward_currency: 'achievement_points',
        reward_price: 300,
        icon_url: '/shop/enlightened-title.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: false,
        achievement_requirement: 'master_all_subjects',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'cosmetic',
            value: 0,
            description: 'Unlocks "The Enlightened" title'
          }
        ]
      },
      {
        id: 'quest-master-badge',
        name: 'Quest Master Badge',
        description: 'A prestigious badge for completing 100 quests',
        category: ShopCategory.CUSTOMIZATION,
        rarity: ShopItemRarity.EPIC,
        shop_type: ShopType.REWARDS,
        reward_currency: 'quest_tokens',
        reward_price: 100,
        icon_url: '/shop/quest-badge.png',
        is_available: true,
        is_limited_time: false,
        is_featured: false,
        is_new: false,
        is_on_sale: false,
        quest_requirement: 'complete_100_quests',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'cosmetic',
            value: 0,
            description: 'Unlocks Quest Master badge'
          }
        ]
      },
      {
        id: 'time-lord-skin',
        name: 'Time Lord Character Skin',
        description: 'Transform into a master of time and space',
        category: ShopCategory.CUSTOMIZATION,
        rarity: ShopItemRarity.MYTHIC,
        shop_type: ShopType.REWARDS,
        reward_currency: 'daily_tokens',
        reward_price: 200,
        icon_url: '/shop/time-lord-skin.png',
        is_available: true,
        is_limited_time: true,
        is_featured: true,
        is_new: true,
        is_on_sale: false,
        available_until: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        effects: [
          {
            type: 'time_extension',
            value: 60,
            description: '+1 minute for all timed challenges'
          },
          {
            type: 'cosmetic',
            value: 0,
            description: 'Unlocks Time Lord appearance'
          }
        ]
      }
    ];
  }

  async mockGetUserCurrencies(): Promise<UserCurrencies> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return {
      coins: 2450,
      gems: 87,
      tokens: 45, // Quest tokens
      points: 230, // Achievement points
      crystals: 12, // Premium currency
      last_updated: new Date().toISOString()
    };
  }

  async mockGetDailyShop(): Promise<DailyShop> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const items = await this.mockGetShopItems();
    
    return {
      id: 'daily-' + new Date().toISOString().split('T')[0],
      date: new Date().toISOString().split('T')[0],
      featured_item: items[0], // Crown of Wisdom
      daily_deals: items.slice(1, 4),
      flash_sales: items.filter(item => item.is_on_sale),
      refresh_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
    };
  }

  async mockGetShopBundles(): Promise<ShopBundle[]> {
    await new Promise(resolve => setTimeout(resolve, 400));
    
    const items = await this.mockGetShopItems();
    
    return [
      {
        id: 'starter-bundle',
        name: 'Scholar Starter Pack',
        description: 'Everything a new scholar needs to begin their journey',
        items: items.slice(0, 3),
        bundle_price: 800,
        currency: CurrencyType.COINS,
        individual_price: 1150,
        savings_amount: 350,
        savings_percentage: 30,
        is_limited_time: false,
        icon_url: '/shop/bundles/starter-pack.png',
        banner_image: '/shop/banners/starter-bundle.jpg'
      },
      {
        id: 'premium-bundle',
        name: 'Master Scholar Collection',
        description: 'Premium items for serious learners',
        items: items.filter(item => item.rarity === ShopItemRarity.LEGENDARY || item.rarity === ShopItemRarity.EPIC),
        bundle_price: 150,
        currency: CurrencyType.GEMS,
        individual_price: 200,
        savings_amount: 50,
        savings_percentage: 25,
        is_limited_time: true,
        expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        icon_url: '/shop/bundles/premium-pack.png',
        banner_image: '/shop/banners/premium-bundle.jpg'
      }
    ];
  }

  async mockPurchaseItem(itemId: string, quantity: number = 1): Promise<ShopPurchase> {
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return {
      id: 'purchase-' + Date.now(),
      user_id: 'user-1',
      item_id: itemId,
      quantity,
      total_price: 100 * quantity,
      currency_used: CurrencyType.COINS,
      purchase_date: new Date().toISOString(),
      transaction_status: 'completed'
    };
  }

  async mockGetShopStats(): Promise<ShopStats> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return {
      total_purchases: 24,
      total_spent: {
        coins: 5420,
        gems: 156,
        tokens: 89,
        points: 0,
        crystals: 25
      },
      favorite_category: ShopCategory.EQUIPMENT,
      rare_items_owned: 7,
      recent_purchases: []
    };
  }
}

const shopService = new ShopService();
export default shopService;