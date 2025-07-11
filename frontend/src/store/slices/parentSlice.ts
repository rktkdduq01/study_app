import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { 
  ParentDashboard, 
  ChildConnection, 
  ChildProfile,
  ParentNotification,
  AIInsight,
  RecentActivity,
  ProgressSummary
} from '../../types/parent';
import {
  FamilyResponse,
  FamilyMemberResponse,
  DashboardData,
  ParentNotificationResponse
} from '../../types/family';
import api from '../../services/api';
import { familyService } from '../../services/parentService';

interface ParentState {
  dashboard: ParentDashboard | null;
  familyDashboard: DashboardData | null;
  family: FamilyResponse | null;
  familyMembers: FamilyMemberResponse[];
  connectedChildren: ChildConnection[];
  selectedChildId: string | null;
  selectedChildProfile: ChildProfile | null;
  notifications: ParentNotification[];
  familyNotifications: ParentNotificationResponse[];
  unreadNotificationCount: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: ParentState = {
  dashboard: null,
  familyDashboard: null,
  family: null,
  familyMembers: [],
  connectedChildren: [],
  selectedChildId: null,
  selectedChildProfile: null,
  notifications: [],
  familyNotifications: [],
  unreadNotificationCount: 0,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchParentDashboard = createAsyncThunk(
  'parent/fetchDashboard',
  async () => {
    const response = await api.get('/parent/dashboard');
    return response.data;
  }
);

// New Family API thunks
export const fetchFamilyDashboard = createAsyncThunk(
  'parent/fetchFamilyDashboard',
  async () => {
    return await familyService.getDashboard();
  }
);

export const fetchMyFamily = createAsyncThunk(
  'parent/fetchMyFamily',
  async () => {
    return await familyService.getMyFamily();
  }
);

export const fetchFamilyMembers = createAsyncThunk(
  'parent/fetchFamilyMembers',
  async (familyId: number) => {
    return await familyService.getFamilyMembers(familyId);
  }
);

export const fetchFamilyNotifications = createAsyncThunk(
  'parent/fetchFamilyNotifications',
  async (params?: { unreadOnly?: boolean; skip?: number; limit?: number }) => {
    return await familyService.getNotifications(
      params?.unreadOnly || false,
      params?.skip || 0,
      params?.limit || 20
    );
  }
);

export const fetchConnectedChildren = createAsyncThunk(
  'parent/fetchConnectedChildren',
  async () => {
    const response = await api.get('/parent/children');
    return response.data;
  }
);

export const fetchChildProfile = createAsyncThunk(
  'parent/fetchChildProfile',
  async (childId: string) => {
    const response = await api.get(`/parent/children/${childId}/profile`);
    return response.data;
  }
);

export const fetchParentNotifications = createAsyncThunk(
  'parent/fetchNotifications',
  async () => {
    const response = await api.get('/parent/notifications');
    return response.data;
  }
);

export const markNotificationAsRead = createAsyncThunk(
  'parent/markNotificationAsRead',
  async (notificationId: string) => {
    const response = await api.put(`/parent/notifications/${notificationId}/read`);
    return response.data;
  }
);

export const addChild = createAsyncThunk(
  'parent/addChild',
  async (childData: { username: string; connectionCode: string }) => {
    const response = await api.post('/parent/children/add', childData);
    return response.data;
  }
);

const parentSlice = createSlice({
  name: 'parent',
  initialState,
  reducers: {
    setSelectedChild: (state, action: PayloadAction<string>) => {
      state.selectedChildId = action.payload;
      // Clear profile to trigger fresh fetch
      state.selectedChildProfile = null;
    },
    clearSelectedChild: (state) => {
      state.selectedChildId = null;
      state.selectedChildProfile = null;
    },
    updateNotificationCount: (state, action: PayloadAction<number>) => {
      state.unreadNotificationCount = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch Dashboard
    builder
      .addCase(fetchParentDashboard.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchParentDashboard.fulfilled, (state, action) => {
        state.isLoading = false;
        state.dashboard = action.payload;
        state.connectedChildren = action.payload.connectedChildren;
      })
      .addCase(fetchParentDashboard.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch dashboard';
      });
      
    // Fetch Family Dashboard
    builder
      .addCase(fetchFamilyDashboard.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchFamilyDashboard.fulfilled, (state, action) => {
        state.isLoading = false;
        state.familyDashboard = action.payload;
      })
      .addCase(fetchFamilyDashboard.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch family dashboard';
      });
      
    // Fetch Family
    builder
      .addCase(fetchMyFamily.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMyFamily.fulfilled, (state, action) => {
        state.isLoading = false;
        state.family = action.payload;
      })
      .addCase(fetchMyFamily.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch family';
      });
      
    // Fetch Family Members
    builder
      .addCase(fetchFamilyMembers.fulfilled, (state, action) => {
        state.familyMembers = action.payload;
      });
      
    // Fetch Family Notifications
    builder
      .addCase(fetchFamilyNotifications.fulfilled, (state, action) => {
        state.familyNotifications = action.payload;
        state.unreadNotificationCount = action.payload.filter(n => !n.is_read).length;
      });

    // Fetch Connected Children
    builder
      .addCase(fetchConnectedChildren.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchConnectedChildren.fulfilled, (state, action) => {
        state.isLoading = false;
        state.connectedChildren = action.payload;
        // Auto-select first child if none selected
        if (!state.selectedChildId && action.payload.length > 0) {
          state.selectedChildId = action.payload[0].childId;
        }
      })
      .addCase(fetchConnectedChildren.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch children';
      });

    // Fetch Child Profile
    builder
      .addCase(fetchChildProfile.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchChildProfile.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selectedChildProfile = action.payload;
      })
      .addCase(fetchChildProfile.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch child profile';
      });

    // Fetch Notifications
    builder
      .addCase(fetchParentNotifications.fulfilled, (state, action) => {
        state.notifications = action.payload.notifications;
        state.unreadNotificationCount = action.payload.unreadCount;
      });

    // Mark Notification as Read
    builder
      .addCase(markNotificationAsRead.fulfilled, (state, action) => {
        const notification = state.notifications.find(n => n.id === action.meta.arg);
        if (notification) {
          notification.readAt = new Date();
          state.unreadNotificationCount = Math.max(0, state.unreadNotificationCount - 1);
        }
      });

    // Add Child
    builder
      .addCase(addChild.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(addChild.fulfilled, (state, action) => {
        state.isLoading = false;
        state.connectedChildren.push(action.payload);
        // Select the newly added child
        state.selectedChildId = action.payload.childId;
      })
      .addCase(addChild.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to add child';
      });
  },
});

export const {
  setSelectedChild,
  clearSelectedChild,
  updateNotificationCount,
  clearError,
} = parentSlice.actions;

export default parentSlice.reducer;