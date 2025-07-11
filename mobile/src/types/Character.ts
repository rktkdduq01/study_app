export interface Character {
  id: number;
  user_id: number;
  name: string;
  character_class: 'warrior' | 'mage' | 'archer' | 'scholar';
  level: number;
  experience: number;
  available_stat_points: number;
  appearance: {
    theme: string;
    customization?: Record<string, any>;
  };
  created_at: string;
  updated_at: string;
}

export interface CharacterStats {
  id: number;
  user_id: number;
  health: number;
  max_health: number;
  mana: number;
  max_mana: number;
  strength: number;
  defense: number;
  intelligence: number;
  wisdom: number;
  agility: number;
  luck: number;
  created_at: string;
  updated_at: string;
}

export interface CharacterInventory {
  id: number;
  user_id: number;
  items: InventoryItem[];
  capacity: number;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  id: number;
  name: string;
  type: 'weapon' | 'armor' | 'accessory' | 'consumable' | 'quest';
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  stats?: Record<string, number>;
  description: string;
  quantity: number;
  equipped: boolean;
  created_at: string;
}

export interface CharacterEquipment {
  id: number;
  user_id: number;
  weapon?: InventoryItem;
  armor?: InventoryItem;
  accessory?: InventoryItem;
  created_at: string;
  updated_at: string;
}