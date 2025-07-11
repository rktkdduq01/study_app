export enum SubjectType {
  MATH = 'math',
  KOREAN = 'korean',
  ENGLISH = 'english',
  SCIENCE = 'science',
  SOCIAL = 'social',
  HISTORY = 'history'
}

export interface SubjectLevel {
  id: number;
  character_id: number;
  subject: SubjectType;
  level: number;
  experience: number;
  exp_to_next_level: number;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: number;
  user_id: number;
  name: string;
  avatar_url?: string;
  total_level: number;
  total_experience: number;
  coins: number;
  gems: number;
  streak_days: number;
  last_active_date?: string;
  created_at: string;
  updated_at: string;
  subject_levels: SubjectLevel[];
  // RPG-style additions
  title?: CharacterTitle;
  stats: CharacterStats;
  equipment: CharacterEquipment;
  appearance: CharacterAppearance;
  achievements_count?: number;
  rank?: string;
  prestige_level?: number;
}

export interface CharacterCreate {
  name: string;
  avatar_url?: string;
}

export interface CharacterUpdate {
  name?: string;
  avatar_url?: string;
  title_id?: number;
  appearance?: Partial<CharacterAppearance>;
}

export interface ExperienceGain {
  subject: SubjectType;
  experience_gained: number;
  reason?: string;
}

export interface CurrencyUpdate {
  coins?: number;
  gems?: number;
  reason?: string;
}

// RPG Character System Types
export enum CharacterClass {
  SCHOLAR = 'scholar',
  EXPLORER = 'explorer',
  WARRIOR = 'warrior',
  SAGE = 'sage',
  APPRENTICE = 'apprentice'
}

export enum EquipmentSlot {
  HEAD = 'head',
  BODY = 'body',
  ACCESSORY = 'accessory',
  WEAPON = 'weapon',
  COMPANION = 'companion'
}

export enum EquipmentRarity {
  COMMON = 'common',
  RARE = 'rare',
  EPIC = 'epic',
  LEGENDARY = 'legendary',
  MYTHIC = 'mythic'
}

export interface CharacterTitle {
  id: number;
  name: string;
  description: string;
  color: string;
  icon?: string;
  requirements?: string;
  earned_at: string;
}

export interface CharacterStats {
  intelligence: number;
  wisdom: number;
  focus: number;
  creativity: number;
  persistence: number;
  collaboration: number;
  // Derived stats
  learning_speed: number;
  accuracy_bonus: number;
  xp_multiplier: number;
  streak_protection: number;
}

export interface EquipmentItem {
  id: number;
  name: string;
  description: string;
  slot: EquipmentSlot;
  rarity: EquipmentRarity;
  icon_url: string;
  stats_bonus: Partial<CharacterStats>;
  special_effects?: string[];
  required_level?: number;
  cost?: number;
  owned: boolean;
  equipped: boolean;
}

export interface CharacterEquipment {
  head?: EquipmentItem;
  body?: EquipmentItem;
  accessory?: EquipmentItem;
  weapon?: EquipmentItem;
  companion?: EquipmentItem;
}

export interface CharacterAppearance {
  skin_tone: string;
  hair_style: string;
  hair_color: string;
  eye_color: string;
  outfit_style: string;
  outfit_color: string;
  accessories: string[];
  background_theme: string;
  pose: string;
}

export interface CustomizationOption {
  id: string;
  name: string;
  category: keyof CharacterAppearance;
  preview_url: string;
  cost?: number;
  currency?: 'coins' | 'gems';
  unlocked: boolean;
  requirement?: string;
}

export interface CharacterProfile {
  character: Character;
  available_titles: CharacterTitle[];
  equipment_inventory: EquipmentItem[];
  customization_options: CustomizationOption[];
  class_info: {
    current: CharacterClass;
    available: CharacterClass[];
    next_unlock?: {
      class: CharacterClass;
      requirement: string;
    };
  };
  achievements_progress: {
    total: number;
    completed: number;
    recent: any[];
  };
  social_stats: {
    friends_count: number;
    guild?: string;
    mentor?: string;
  };
}