import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import characterService from '../../services/characterService';
import { Character, CharacterCreate, CharacterUpdate, ExperienceGain, CurrencyUpdate } from '../../types/character';

interface CharacterState {
  character: Character | null;
  rankings: Character[];
  isLoading: boolean;
  error: string | null;
}

const initialState: CharacterState = {
  character: null,
  rankings: [],
  isLoading: false,
  error: null,
};

// Async thunks
export const createCharacter = createAsyncThunk(
  'character/create',
  async (data: CharacterCreate) => {
    return await characterService.createCharacter(data);
  }
);

export const fetchMyCharacter = createAsyncThunk(
  'character/fetchMy',
  async () => {
    return await characterService.getMyCharacter();
  }
);

export const updateCharacter = createAsyncThunk(
  'character/update',
  async ({ id, data }: { id: number; data: CharacterUpdate }) => {
    return await characterService.updateCharacter(id, data);
  }
);

export const addExperience = createAsyncThunk(
  'character/addExperience',
  async ({ characterId, data }: { characterId: number; data: ExperienceGain }) => {
    await characterService.addExperience(characterId, data);
    // Refetch character to get updated data
    return await characterService.getCharacter(characterId);
  }
);

export const updateCurrency = createAsyncThunk(
  'character/updateCurrency',
  async ({ characterId, data }: { characterId: number; data: CurrencyUpdate }) => {
    return await characterService.updateCurrency(characterId, data);
  }
);

export const updateStreak = createAsyncThunk(
  'character/updateStreak',
  async (characterId: number) => {
    return await characterService.updateStreak(characterId);
  }
);

export const fetchRankings = createAsyncThunk(
  'character/fetchRankings',
  async ({ limit = 100, offset = 0 }: { limit?: number; offset?: number }) => {
    return await characterService.getRankings(limit, offset);
  }
);

// Slice
const characterSlice = createSlice({
  name: 'character',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    resetCharacter: (state) => {
      state.character = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Create character
    builder
      .addCase(createCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.character = action.payload;
      })
      .addCase(createCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create character';
      });

    // Fetch my character
    builder
      .addCase(fetchMyCharacter.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMyCharacter.fulfilled, (state, action) => {
        state.isLoading = false;
        state.character = action.payload;
      })
      .addCase(fetchMyCharacter.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch character';
      });

    // Update character
    builder
      .addCase(updateCharacter.fulfilled, (state, action) => {
        state.character = action.payload;
      });

    // Add experience
    builder
      .addCase(addExperience.fulfilled, (state, action) => {
        state.character = action.payload;
      });

    // Update currency
    builder
      .addCase(updateCurrency.fulfilled, (state, action) => {
        state.character = action.payload;
      });

    // Update streak
    builder
      .addCase(updateStreak.fulfilled, (state, action) => {
        state.character = action.payload;
      });

    // Fetch rankings
    builder
      .addCase(fetchRankings.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchRankings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.rankings = action.payload;
      })
      .addCase(fetchRankings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch rankings';
      });
  },
});

export const { clearError, resetCharacter } = characterSlice.actions;
export default characterSlice.reducer;