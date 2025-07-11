import { Character, CharacterStats, CharacterInventory, CharacterEquipment } from '../types/Character';
import { authService } from './authService';
import { isOffline, saveCharacterOffline } from './offlineService';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'http://localhost:8000/api'; // Update this to your backend URL

class CharacterService {
  private async makeRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = authService.getToken();
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response;
  }

  async getCharacter(): Promise<{
    character: Character;
    stats: CharacterStats;
    inventory: any[];
    equipment: any[];
    achievements: any[];
  }> {
    const offline = await isOffline();
    
    if (offline) {
      // Try to get from offline storage
      const characterData = await AsyncStorage.getItem('current_character');
      if (characterData) {
        return JSON.parse(characterData);
      }
      throw new Error('No character data available offline');
    }
    
    const response = await this.makeRequest('/character/me');
    const data = await response.json();
    
    // Cache the character data for offline use
    await AsyncStorage.setItem('current_character', JSON.stringify(data));
    
    return data;
  }

  async createCharacter(characterData: {
    character_class: string;
    name?: string;
    appearance: any;
  }): Promise<{
    character: Character;
    stats: CharacterStats;
    inventory: any[];
    equipment: any[];
  }> {
    const response = await this.makeRequest('/character/create', {
      method: 'POST',
      body: JSON.stringify(characterData),
    });
    return await response.json();
  }

  async updateStats(stats: Partial<CharacterStats>): Promise<{
    stats: CharacterStats;
  }> {
    const offline = await isOffline();
    
    if (offline) {
      // Save to offline storage
      const characterData = await AsyncStorage.getItem('current_character');
      if (characterData) {
        const character = JSON.parse(characterData);
        await saveCharacterOffline(character.id, { stats });
        
        // Return merged stats for immediate UI update
        const currentStats = character.stats || {};
        return { stats: { ...currentStats, ...stats } };
      }
      throw new Error('No character data available offline');
    }
    
    const response = await this.makeRequest('/character/stats', {
      method: 'PUT',
      body: JSON.stringify(stats),
    });
    return await response.json();
  }

  async gainExperience(experienceData: {
    amount: number;
    source: string;
    subject?: string;
  }): Promise<{
    character: Character;
    stats: CharacterStats;
    experience: number;
    level: number;
    levelUp: boolean;
  }> {
    const offline = await isOffline();
    
    if (offline) {
      // Save to offline storage
      const characterData = await AsyncStorage.getItem('current_character');
      if (characterData) {
        const character = JSON.parse(characterData);
        await saveCharacterOffline(character.id, { experience: experienceData });
        
        // Calculate new experience locally for immediate feedback
        const currentExp = character.experience || 0;
        const newExp = currentExp + experienceData.amount;
        const currentLevel = character.level || 1;
        
        // Simple level calculation (adjust based on your game's formula)
        const expForNextLevel = currentLevel * 100;
        const levelUp = newExp >= expForNextLevel;
        const newLevel = levelUp ? currentLevel + 1 : currentLevel;
        
        return {
          character: { ...character, experience: newExp, level: newLevel },
          stats: character.stats,
          experience: newExp,
          level: newLevel,
          levelUp
        };
      }
      throw new Error('No character data available offline');
    }
    
    const response = await this.makeRequest('/character/experience', {
      method: 'POST',
      body: JSON.stringify(experienceData),
    });
    return await response.json();
  }

  async levelUp(): Promise<{
    character: Character;
    stats: CharacterStats;
    level: number;
    available_stat_points: number;
  }> {
    const response = await this.makeRequest('/character/level-up', {
      method: 'POST',
    });
    return await response.json();
  }

  async equipItem(itemId: number): Promise<{
    equipment: any[];
    inventory: any[];
    stats: CharacterStats;
  }> {
    const offline = await isOffline();
    
    if (offline) {
      // Save to offline storage
      const characterData = await AsyncStorage.getItem('current_character');
      if (characterData) {
        const character = JSON.parse(characterData);
        await saveCharacterOffline(character.id, {
          equipment: { equip: [{ itemId, timestamp: Date.now() }] }
        });
        
        // Return current data for UI update
        return {
          equipment: character.equipment || [],
          inventory: character.inventory || [],
          stats: character.stats || {}
        };
      }
      throw new Error('No character data available offline');
    }
    
    const response = await this.makeRequest(`/character/equip/${itemId}`, {
      method: 'POST',
    });
    return await response.json();
  }

  async unequipItem(itemId: number): Promise<{
    equipment: any[];
    inventory: any[];
    stats: CharacterStats;
  }> {
    const offline = await isOffline();
    
    if (offline) {
      // Save to offline storage
      const characterData = await AsyncStorage.getItem('current_character');
      if (characterData) {
        const character = JSON.parse(characterData);
        await saveCharacterOffline(character.id, {
          equipment: { unequip: [{ itemId, timestamp: Date.now() }] }
        });
        
        // Return current data for UI update
        return {
          equipment: character.equipment || [],
          inventory: character.inventory || [],
          stats: character.stats || {}
        };
      }
      throw new Error('No character data available offline');
    }
    
    const response = await this.makeRequest(`/character/unequip/${itemId}`, {
      method: 'POST',
    });
    return await response.json();
  }

  async updateAppearance(appearance: any): Promise<{
    character: Character;
    appearance: any;
  }> {
    const response = await this.makeRequest('/character/appearance', {
      method: 'PUT',
      body: JSON.stringify({ appearance }),
    });
    return await response.json();
  }

  async getInventory(): Promise<{
    inventory: any[];
    capacity: number;
  }> {
    const response = await this.makeRequest('/character/inventory');
    return await response.json();
  }

  async getEquipment(): Promise<{
    equipment: any[];
    stats: CharacterStats;
  }> {
    const response = await this.makeRequest('/character/equipment');
    return await response.json();
  }

  async useItem(itemId: number): Promise<{
    character: Character;
    stats: CharacterStats;
    inventory: any[];
    message: string;
  }> {
    const response = await this.makeRequest(`/character/use-item/${itemId}`, {
      method: 'POST',
    });
    return await response.json();
  }

  async getCharacterStats(): Promise<{
    stats: CharacterStats;
  }> {
    const response = await this.makeRequest('/character/stats');
    return await response.json();
  }
}

export const characterService = new CharacterService();