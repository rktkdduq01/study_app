import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface Content {
  id: number;
  title: string;
  description: string;
  type: 'lesson' | 'quiz' | 'exercise' | 'video' | 'reading';
  subject: string;
  difficulty: number;
  duration: number;
  content_url?: string;
  created_at: string;
  updated_at: string;
}

interface ContentState {
  contents: Content[];
  currentContent: Content | null;
  favorites: Content[];
  recentlyViewed: Content[];
  isLoading: boolean;
  error: string | null;
}

const initialState: ContentState = {
  contents: [],
  currentContent: null,
  favorites: [],
  recentlyViewed: [],
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchContent = createAsyncThunk(
  'content/fetchContent',
  async (params: { subject?: string; type?: string; difficulty?: number }, { rejectWithValue }) => {
    try {
      // Mock API call
      const queryParams = new URLSearchParams();
      if (params.subject) queryParams.append('subject', params.subject);
      if (params.type) queryParams.append('type', params.type);
      if (params.difficulty) queryParams.append('difficulty', params.difficulty.toString());
      
      const response = await fetch(`/api/content?${queryParams.toString()}`);
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch content');
    }
  }
);

export const fetchContentById = createAsyncThunk(
  'content/fetchContentById',
  async (contentId: number, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch(`/api/content/${contentId}`);
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch content');
    }
  }
);

export const addToFavorites = createAsyncThunk(
  'content/addToFavorites',
  async (contentId: number, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch(`/api/content/${contentId}/favorite`, {
        method: 'POST',
      });
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to add to favorites');
    }
  }
);

export const removeFromFavorites = createAsyncThunk(
  'content/removeFromFavorites',
  async (contentId: number, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch(`/api/content/${contentId}/favorite`, {
        method: 'DELETE',
      });
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to remove from favorites');
    }
  }
);

const contentSlice = createSlice({
  name: 'content',
  initialState,
  reducers: {
    setCurrentContent: (state, action: PayloadAction<Content | null>) => {
      state.currentContent = action.payload;
      
      // Add to recently viewed
      if (action.payload) {
        const existingIndex = state.recentlyViewed.findIndex(
          c => c.id === action.payload!.id
        );
        if (existingIndex !== -1) {
          state.recentlyViewed.splice(existingIndex, 1);
        }
        state.recentlyViewed.unshift(action.payload);
        
        // Keep only last 10 items
        if (state.recentlyViewed.length > 10) {
          state.recentlyViewed = state.recentlyViewed.slice(0, 10);
        }
      }
    },
    clearRecentlyViewed: (state) => {
      state.recentlyViewed = [];
    },
    clearError: (state) => {
      state.error = null;
    },
    resetContentState: (state) => {
      state.contents = [];
      state.currentContent = null;
      state.favorites = [];
      state.recentlyViewed = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch content
      .addCase(fetchContent.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchContent.fulfilled, (state, action) => {
        state.isLoading = false;
        state.contents = action.payload.contents;
      })
      .addCase(fetchContent.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Fetch content by ID
      .addCase(fetchContentById.fulfilled, (state, action) => {
        state.currentContent = action.payload.content;
        
        // Add to recently viewed
        const existingIndex = state.recentlyViewed.findIndex(
          c => c.id === action.payload.content.id
        );
        if (existingIndex !== -1) {
          state.recentlyViewed.splice(existingIndex, 1);
        }
        state.recentlyViewed.unshift(action.payload.content);
        
        // Keep only last 10 items
        if (state.recentlyViewed.length > 10) {
          state.recentlyViewed = state.recentlyViewed.slice(0, 10);
        }
      })
      
      // Add to favorites
      .addCase(addToFavorites.fulfilled, (state, action) => {
        const content = action.payload.content;
        const existingIndex = state.favorites.findIndex(c => c.id === content.id);
        if (existingIndex === -1) {
          state.favorites.push(content);
        }
      })
      
      // Remove from favorites
      .addCase(removeFromFavorites.fulfilled, (state, action) => {
        const contentId = action.payload.contentId;
        state.favorites = state.favorites.filter(c => c.id !== contentId);
      });
  },
});

export const {
  setCurrentContent,
  clearRecentlyViewed,
  clearError,
  resetContentState,
} = contentSlice.actions;

export default contentSlice.reducer;