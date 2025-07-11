import { useEffect } from 'react';
import { useAppDispatch } from './useAppDispatch';
import { useAppSelector } from './useAppSelector';
import { 
  fetchParentDashboard, 
  fetchConnectedChildren, 
  fetchChildProfile,
  setSelectedChild 
} from '../store/slices/parentSlice';

export const useParentDashboard = () => {
  const dispatch = useAppDispatch();
  const { 
    dashboard, 
    connectedChildren, 
    selectedChildId, 
    selectedChildProfile,
    isLoading,
    error 
  } = useAppSelector((state) => state.parent);
  const { user } = useAppSelector((state) => state.auth);

  // Load dashboard data on mount
  useEffect(() => {
    if (user?.role === 'parent') {
      dispatch(fetchParentDashboard());
    }
  }, [dispatch, user]);

  // Load child profile when selected child changes
  useEffect(() => {
    if (selectedChildId) {
      dispatch(fetchChildProfile(selectedChildId));
    }
  }, [dispatch, selectedChildId]);

  const selectChild = (childId: string) => {
    dispatch(setSelectedChild(childId));
  };

  const refreshDashboard = () => {
    dispatch(fetchParentDashboard());
  };

  const refreshChildren = () => {
    dispatch(fetchConnectedChildren());
  };

  return {
    dashboard,
    connectedChildren,
    selectedChildId,
    selectedChildProfile,
    selectedChild: connectedChildren.find(c => c.childId === selectedChildId),
    isLoading,
    error,
    selectChild,
    refreshDashboard,
    refreshChildren,
  };
};