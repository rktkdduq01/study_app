import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { UserRole } from '../../types/user';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
  requireCharacter?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  allowedRoles,
  requireCharacter = false 
}) => {
  const location = useLocation();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { character } = useAppSelector((state) => state.character);

  if (!isAuthenticated || !user) {
    // Redirect to login page but save the attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    // User doesn't have the required role
    return <Navigate to="/unauthorized" replace />;
  }

  if (requireCharacter && !character) {
    // User needs to create a character first
    return <Navigate to="/character/create" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;