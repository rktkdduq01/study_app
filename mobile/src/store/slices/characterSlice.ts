import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { characterService } from '../../services/characterService';
import { Character, CharacterStats } from '../../types/Character';

interface CharacterState {
  character: Character | null;
  stats: CharacterStats | null;
  isLoading: boolean;
  error: string | null;
  levelUpAnimation: boolean;
  lastLevelUp: number | null;
  achievements: any[];
  inventory: any[];
  equipment: any[];
}

const initialState: CharacterState = {
  character: null,
  stats: null,
  isLoading: false,
  error: null,
  levelUpAnimation: false,
  lastLevelUp: null,
  achievements: [],
  inventory: [],
  equipment: [],
};

// Async thunks
export const fetchCharacter = createAsyncThunk(
  'character/fetchCharacter',
  async (_, { rejectWithValue }) => {
    try {
      const response = await characterService.getCharacter();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch character');
    }
  }
);

export const createCharacter = createAsyncThunk(
  'character/createCharacter',
  async (characterData: {
    character_class: string;
    appearance: any;
    name?: string;
  }, { rejectWithValue }) => {
    try {
      const response = await characterService.createCharacter(characterData);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to create character');
    }
  }
);

export const updateCharacterStats = createAsyncThunk(
  'character/updateStats',
  async (stats: Partial<CharacterStats>, { rejectWithValue }) => {
    try {
      const response = await characterService.updateStats(stats);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update character stats');
    }
  }
);

export const gainExperience = createAsyncThunk(
  'character/gainExperience',
  async (experienceData: {
    amount: number;
    source: string;
    subject?: string;
  }, { rejectWithValue }) => {
    try {
      const response = await characterService.gainExperience(experienceData);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to gain experience');
    }
  }
);

export const levelUp = createAsyncThunk(
  'character/levelUp',
  async (_, { rejectWithValue }) => {
    try {
      const response = await characterService.levelUp();
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to level up');
    }
  }
);

export const equipItem = createAsyncThunk(
  'character/equipItem',
  async (itemId: number, { rejectWithValue }) => {
    try {
      const response = await characterService.equipItem(itemId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to equip item');
    }
  }
);

export const unequipItem = createAsyncThunk(
  'character/unequipItem',
  async (itemId: number, { rejectWithValue }) => {
    try {
      const response = await characterService.unequipItem(itemId);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to unequip item');
    }
  }
);

export const updateAppearance = createAsyncThunk(
  'character/updateAppearance',
  async (appearance: any, { rejectWithValue }) => {
    try {
      const response = await characterService.updateAppearance(appearance);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update appearance');
    }
  }
);

const characterSlice = createSlice({
  name: 'character',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setLevelUpAnimation: (state, action: PayloadAction<boolean>) => {
      state.levelUpAnimation = action.payload;
    },
    updateLocalStats: (state, action: PayloadAction<Partial<CharacterStats>>) => {
      if (state.stats) {
        state.stats = { ...state.stats, ...action.payload };
      }
    },
    addToInventory: (state, action: PayloadAction<any>) => {
      state.inventory.push(action.payload);
    },
    removeFromInventory: (state, action: PayloadAction<number>) => {
      state.inventory = state.inventory.filter(item => item.id !== action.payload);
    },
    updateInventoryItem: (state, action: PayloadAction<{ id: number; updates: any }>) => {
      const { id, updates } = action.payload;
      const itemIndex = state.inventory.findIndex(item => item.id === id);
      if (itemIndex !== -1) {
        state.inventory[itemIndex] = { ...state.inventory[itemIndex], ...updates };
      }
    },
    addAchievement: (state, action: PayloadAction<any>) => {
      state.achievements.push(action.payload);
    },
    resetCharacter: (state) => {
      state.character = null;
      state.stats = null;
      state.achievements = [];
      state.inventory = [];
      state.equipment = [];
      state.levelUpAnimation = false;
      state.lastLevelUp = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch character
      .addCase(fetchCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.character = action.payload.character;
        state.stats = action.payload.stats;
        state.achievements = action.payload.achievements || [];
        state.inventory = action.payload.inventory || [];
        state.equipment = action.payload.equipment || [];
      })
      .addCase(fetchCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Create character
      .addCase(createCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.character = action.payload.character;
        state.stats = action.payload.stats;
        state.inventory = action.payload.inventory || [];
        state.equipment = action.payload.equipment || [];
      })
      .addCase(createCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Update stats
      .addCase(updateCharacterStats.fulfilled, (state, action) => {
        state.stats = action.payload.stats;
      })
      
      // Gain experience
      .addCase(gainExperience.fulfilled, (state, action) => {
        if (state.character) {
          state.character.experience = action.payload.experience;
          state.character.level = action.payload.level;
          
          // Check if level up occurred
          if (action.payload.levelUp) {
            state.levelUpAnimation = true;
            state.lastLevelUp = Date.now();
          }
        }
        
        if (state.stats) {
          state.stats = { ...state.stats, ...action.payload.stats };
        }
      })
      
      // Level up
      .addCase(levelUp.fulfilled, (state, action) => {
        if (state.character) {
          state.character.level = action.payload.level;
          state.character.available_stat_points = action.payload.available_stat_points;
        }
        
        if (state.stats) {
          state.stats = { ...state.stats, ...action.payload.stats };
        }
        
        state.levelUpAnimation = true;
        state.lastLevelUp = Date.now();
      })
      
      // Equip item
      .addCase(equipItem.fulfilled, (state, action) => {
        state.equipment = action.payload.equipment;
        state.inventory = action.payload.inventory;
        
        if (state.stats) {
          state.stats = { ...state.stats, ...action.payload.stats };
        }
      })
      
      // Unequip item
      .addCase(unequipItem.fulfilled, (state, action) => {
        state.equipment = action.payload.equipment;
        state.inventory = action.payload.inventory;
        
        if (state.stats) {
          state.stats = { ...state.stats, ...action.payload.stats };
        }
      })
      
      // Update appearance
      .addCase(updateAppearance.fulfilled, (state, action) => {
        if (state.character) {
          state.character.appearance = action.payload.appearance;
        }
      });
  },
});

export const {
  clearError,
  setLevelUpAnimation,
  updateLocalStats,
  addToInventory,
  removeFromInventory,
  updateInventoryItem,
  addAchievement,
  resetCharacter,
} = characterSlice.actions;

export default characterSlice.reducer;