import api from './api';
import { 
  Character, 
  CharacterCreate, 
  CharacterUpdate, 
  ExperienceGain, 
  CurrencyUpdate,
  CharacterProfile,
  CharacterClass,
  CharacterTitle,
  EquipmentItem,
  CustomizationOption,
  CharacterAppearance,
  EquipmentSlot,
  EquipmentRarity,
  CharacterStats
} from '../types/character';

class CharacterService {
  async createCharacter(data: CharacterCreate): Promise<Character> {
    const response = await api.post<Character>('/characters/', data);
    return response.data;
  }

  async getMyCharacter(): Promise<Character> {
    const response = await api.get<Character>('/characters/me');
    return response.data;
  }

  async getCharacter(id: number): Promise<Character> {
    const response = await api.get<Character>(`/characters/${id}`);
    return response.data;
  }

  async updateCharacter(id: number, data: CharacterUpdate): Promise<Character> {
    const response = await api.put<Character>(`/characters/${id}`, data);
    return response.data;
  }

  async addExperience(characterId: number, data: ExperienceGain): Promise<void> {
    await api.post(`/characters/${characterId}/experience`, data);
  }

  async updateCurrency(characterId: number, data: CurrencyUpdate): Promise<Character> {
    const response = await api.post<Character>(`/characters/${characterId}/currency`, data);
    return response.data;
  }

  async updateStreak(characterId: number): Promise<Character> {
    const response = await api.post<Character>(`/characters/${characterId}/streak`);
    return response.data;
  }

  async getRankings(limit: number = 100, offset: number = 0): Promise<Character[]> {
    const response = await api.get<Character[]>('/characters/rankings', {
      params: { limit, offset }
    });
    return response.data;
  }

  // Enhanced RPG Character Methods
  async getCharacterProfile(): Promise<CharacterProfile> {
    const response = await api.get('/character/profile');
    return response.data;
  }

  async equipItem(itemId: number): Promise<Character> {
    const response = await api.post(`/character/equip/${itemId}`);
    return response.data;
  }

  async unequipItem(slot: EquipmentSlot): Promise<Character> {
    const response = await api.delete(`/character/equip/${slot}`);
    return response.data;
  }

  async purchaseCustomization(optionId: string): Promise<{
    success: boolean;
    new_balance: { coins: number; gems: number };
  }> {
    const response = await api.post(`/character/customize/${optionId}`);
    return response.data;
  }

  async changeTitle(titleId: number): Promise<Character> {
    const response = await api.put('/character/title', { title_id: titleId });
    return response.data;
  }

  async changeClass(characterClass: CharacterClass): Promise<Character> {
    const response = await api.put('/character/class', { class: characterClass });
    return response.data;
  }

  // Mock methods for development
  async mockGetCharacterProfile(): Promise<CharacterProfile> {
    await new Promise(resolve => setTimeout(resolve, 500));

    const mockStats: CharacterStats = {
      intelligence: 85,
      wisdom: 72,
      focus: 68,
      creativity: 91,
      persistence: 76,
      collaboration: 83,
      learning_speed: 1.2,
      accuracy_bonus: 0.15,
      xp_multiplier: 1.1,
      streak_protection: 0.05
    };

    const mockAppearance: CharacterAppearance = {
      skin_tone: 'medium',
      hair_style: 'long',
      hair_color: 'brown',
      eye_color: 'brown',
      outfit_style: 'scholar',
      outfit_color: 'blue',
      accessories: ['glasses', 'badge'],
      background_theme: 'library',
      pose: 'confident'
    };

    const mockEquipment: EquipmentItem[] = [
      {
        id: 1,
        name: 'Scholar\'s Crown',
        description: 'A mystical crown that enhances learning abilities',
        slot: EquipmentSlot.HEAD,
        rarity: EquipmentRarity.EPIC,
        icon_url: '/equipment/crown.png',
        stats_bonus: { intelligence: 10, wisdom: 5 },
        special_effects: ['Double XP on first quest of the day'],
        required_level: 10,
        owned: true,
        equipped: true
      },
      {
        id: 2,
        name: 'Robe of Concentration',
        description: 'A magical robe that helps maintain focus during study',
        slot: EquipmentSlot.BODY,
        rarity: EquipmentRarity.RARE,
        icon_url: '/equipment/robe.png',
        stats_bonus: { focus: 8, persistence: 6 },
        special_effects: ['Reduces distraction penalties'],
        required_level: 8,
        owned: true,
        equipped: true
      },
      {
        id: 3,
        name: 'Pendant of Wisdom',
        description: 'An ancient pendant that grants deep understanding',
        slot: EquipmentSlot.ACCESSORY,
        rarity: EquipmentRarity.LEGENDARY,
        icon_url: '/equipment/pendant.png',
        stats_bonus: { wisdom: 15, intelligence: 8 },
        special_effects: ['Unlock hidden quest hints', 'Bonus rewards for perfect scores'],
        required_level: 15,
        cost: 500,
        owned: false,
        equipped: false
      },
      {
        id: 4,
        name: 'Quill of Swift Learning',
        description: 'A enchanted quill that speeds up problem solving',
        slot: EquipmentSlot.WEAPON,
        rarity: EquipmentRarity.EPIC,
        icon_url: '/equipment/quill.png',
        stats_bonus: { learning_speed: 0.3, creativity: 12 },
        special_effects: ['Faster question response time bonus'],
        required_level: 12,
        owned: true,
        equipped: false
      },
      {
        id: 5,
        name: 'Owl Companion',
        description: 'A wise owl that provides study guidance',
        slot: EquipmentSlot.COMPANION,
        rarity: EquipmentRarity.MYTHIC,
        icon_url: '/equipment/owl.png',
        stats_bonus: { wisdom: 20, collaboration: 10, xp_multiplier: 0.2 },
        special_effects: ['Daily study tips', 'Weekly progress reports', 'Emergency hint system'],
        required_level: 20,
        cost: 1000,
        owned: false,
        equipped: false
      }
    ];

    const mockTitles: CharacterTitle[] = [
      {
        id: 1,
        name: 'The Dedicated',
        description: 'Awarded for maintaining a 7-day streak',
        color: '#4CAF50',
        icon: '🔥',
        requirements: '7-day learning streak',
        earned_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 2,
        name: 'Math Wizard',
        description: 'Master of mathematical arts',
        color: '#9C27B0',
        icon: '🧙‍♂️',
        requirements: 'Complete 50 math quests with 90%+ accuracy',
        earned_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 3,
        name: 'Knowledge Seeker',
        description: 'Always hungry for new learning',
        color: '#FF9800',
        icon: '📚',
        requirements: 'Try quests from all subjects',
        earned_at: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString()
      }
    ];

    const mockCustomizations: CustomizationOption[] = [
      // Hair Styles
      {
        id: 'hair_short',
        name: 'Short Hair',
        category: 'hair_style',
        preview_url: '/customization/hair_short.png',
        unlocked: true
      },
      {
        id: 'hair_curly',
        name: 'Curly Hair',
        category: 'hair_style',
        preview_url: '/customization/hair_curly.png',
        cost: 100,
        currency: 'coins',
        unlocked: false
      },
      // Hair Colors
      {
        id: 'hair_black',
        name: 'Black Hair',
        category: 'hair_color',
        preview_url: '/customization/hair_black.png',
        unlocked: true
      },
      {
        id: 'hair_rainbow',
        name: 'Rainbow Hair',
        category: 'hair_color',
        preview_url: '/customization/hair_rainbow.png',
        cost: 50,
        currency: 'gems',
        unlocked: false,
        requirement: 'Reach Level 25'
      },
      // Outfits
      {
        id: 'outfit_casual',
        name: 'Casual Wear',
        category: 'outfit_style',
        preview_url: '/customization/outfit_casual.png',
        unlocked: true
      },
      {
        id: 'outfit_royal',
        name: 'Royal Outfit',
        category: 'outfit_style',
        preview_url: '/customization/outfit_royal.png',
        cost: 300,
        currency: 'coins',
        unlocked: false,
        requirement: 'Complete 10 achievements'
      },
      // Backgrounds
      {
        id: 'bg_classroom',
        name: 'Classroom',
        category: 'background_theme',
        preview_url: '/customization/bg_classroom.png',
        unlocked: true
      },
      {
        id: 'bg_space',
        name: 'Space Station',
        category: 'background_theme',
        preview_url: '/customization/bg_space.png',
        cost: 200,
        currency: 'coins',
        unlocked: false
      }
    ];

    return {
      character: {
        id: 1,
        user_id: 1,
        name: 'Emma Scholar',
        avatar_url: '/avatars/emma.png',
        total_level: 18,
        total_experience: 4250,
        coins: 850,
        gems: 45,
        streak_days: 12,
        last_active_date: new Date().toISOString(),
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        subject_levels: [
          {
            id: 1,
            character_id: 1,
            subject: 'math' as any,
            level: 15,
            experience: 2800,
            exp_to_next_level: 3200,
            created_at: '',
            updated_at: ''
          },
          {
            id: 2,
            character_id: 1,
            subject: 'science' as any,
            level: 12,
            experience: 1450,
            exp_to_next_level: 1600,
            created_at: '',
            updated_at: ''
          }
        ],
        title: mockTitles[1], // Math Wizard
        stats: mockStats,
        equipment: {
          head: mockEquipment[0],
          body: mockEquipment[1]
        },
        appearance: mockAppearance,
        achievements_count: 15,
        rank: 'Gold',
        prestige_level: 2
      },
      available_titles: mockTitles,
      equipment_inventory: mockEquipment,
      customization_options: mockCustomizations,
      class_info: {
        current: CharacterClass.SCHOLAR,
        available: [CharacterClass.SCHOLAR, CharacterClass.EXPLORER],
        next_unlock: {
          class: CharacterClass.SAGE,
          requirement: 'Reach Level 25 and complete 20 achievements'
        }
      },
      achievements_progress: {
        total: 50,
        completed: 15,
        recent: []
      },
      social_stats: {
        friends_count: 8,
        guild: 'Study Masters',
        mentor: 'Professor Owl'
      }
    };
  }

  async mockEquipItem(itemId: number): Promise<Character> {
    await new Promise(resolve => setTimeout(resolve, 300));
    // Mock response - would update character with equipped item
    const profile = await this.mockGetCharacterProfile();
    return profile.character;
  }

  async mockPurchaseCustomization(optionId: string): Promise<{
    success: boolean;
    new_balance: { coins: number; gems: number };
  }> {
    await new Promise(resolve => setTimeout(resolve, 400));
    return {
      success: true,
      new_balance: { coins: 750, gems: 40 }
    };
  }
}

export default new CharacterService();