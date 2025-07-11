import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { store } from './store/store';
import { useAppSelector } from './hooks/useAppSelector';
import { useAppDispatch } from './hooks/useAppDispatch';
import { useWebSocket } from './hooks/useWebSocket';
import { getCurrentUser } from './store/slices/authSlice';
import { fetchMyCharacter } from './store/slices/characterSlice';
import { UserRole } from './types/user';
import theme from './styles/theme';
import './i18n/config'; // Initialize i18n
import './styles/global.css';
import './styles/rpg-theme.css';

// Error handling components
import ErrorBoundary from './components/ErrorBoundary';
import { ErrorToastProvider } from './components/ErrorToast';

// Layout - 항상 필요하므로 동기 import
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/common/ProtectedRoute';
import Loading from './components/common/Loading';

// Auth Pages - 로그인/회원가입은 자주 사용되므로 동기 import
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Common Pages - 자주 사용되는 페이지는 동기 import
import HomePage from './pages/HomePage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import NotFoundPage from './pages/NotFoundPage';

// Lazy load pages
const StudentDashboard = lazy(() => import('./pages/student/Dashboard'));
const QuestListPage = lazy(() => import('./pages/student/QuestList'));
const QuestDetailPage = lazy(() => import('./pages/student/QuestDetail'));
const AchievementsPage = lazy(() => import('./pages/student/Achievements'));
const CharacterPage = lazy(() => import('./pages/student/Character'));
const LearningPage = lazy(() => import('./pages/student/Learning'));
const AILearningDashboard = lazy(() => import('./pages/student/AILearningDashboard'));
const AITutorPage = lazy(() => import('./pages/student/AITutor'));
const ShopPage = lazy(() => import('./pages/student/Shop'));
const LeaderboardPage = lazy(() => import('./pages/student/Leaderboard'));
const SocialHubPage = lazy(() => import('./pages/student/SocialHub'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const CreateCharacterPage = lazy(() => import('./pages/CreateCharacterPage'));
const ParentDashboard = lazy(() => import('./pages/parent/Dashboard'));
const ChildMonitoring = lazy(() => import('./pages/parent/ChildMonitoring'));
const NotificationContainer = lazy(() => import('./components/notifications/NotificationContainer'));
const MultiplayerInviteHandler = lazy(() => import('./components/multiplayer/MultiplayerInviteHandler'));

const AppContent: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated, user, isLoading } = useAppSelector((state) => state.auth);
  useWebSocket();

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('token');
    if (token && !user) {
      dispatch(getCurrentUser());
    }
  }, [dispatch, user]);

  useEffect(() => {
    // Fetch character data for students
    if (isAuthenticated && user?.role === UserRole.STUDENT) {
      dispatch(fetchMyCharacter());
    }
  }, [dispatch, isAuthenticated, user]);

  if (isLoading) {
    return <Loading message="Initializing..." />;
  }

  return (
    <>
      <Routes>
        <Route path="/" element={<Layout />}>
        {/* Public Routes */}
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
        <Route path="unauthorized" element={<UnauthorizedPage />} />

        {/* Protected Routes - All authenticated users */}
        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <Suspense fallback={<Loading message="Loading profile..." />}>
                <ProfilePage />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* Character Creation */}
        <Route
          path="character/create"
          element={
            <ProtectedRoute allowedRoles={[UserRole.STUDENT]}>
              <Suspense fallback={<Loading message="Loading character creator..." />}>
                <CreateCharacterPage />
              </Suspense>
            </ProtectedRoute>
          }
        />

        {/* Student Routes */}
        <Route path="student">
          <Route
            path="dashboard"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading dashboard..." />}>
                  <StudentDashboard />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="quests"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading quests..." />}>
                  <QuestListPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="quests/:id"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading quest details..." />}>
                  <QuestDetailPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="achievements"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading achievements..." />}>
                  <AchievementsPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="character"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading character..." />}>
                  <CharacterPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="learning/:contentId"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading learning content..." />}>
                  <LearningPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="ai-learning"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading AI learning..." />}>
                  <AILearningDashboard />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="ai-tutor"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading AI tutor..." />}>
                  <AITutorPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="shop"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading shop..." />}>
                  <ShopPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="leaderboard"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading leaderboard..." />}>
                  <LeaderboardPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="social"
            element={
              <ProtectedRoute allowedRoles={[UserRole.STUDENT]} requireCharacter>
                <Suspense fallback={<Loading message="Loading social hub..." />}>
                  <SocialHubPage />
                </Suspense>
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Parent Routes */}
        <Route path="parent">
          <Route
            path="dashboard"
            element={
              <ProtectedRoute allowedRoles={[UserRole.PARENT]}>
                <Suspense fallback={<Loading message="Loading parent dashboard..." />}>
                  <ParentDashboard />
                </Suspense>
              </ProtectedRoute>
            }
          />
          <Route
            path="child/:childId"
            element={
              <ProtectedRoute allowedRoles={[UserRole.PARENT]}>
                <Suspense fallback={<Loading message="Loading child monitoring..." />}>
                  <ChildMonitoring />
                </Suspense>
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Admin Routes - To be implemented */}
        <Route path="admin">
          <Route
            path="dashboard"
            element={
              <ProtectedRoute allowedRoles={[UserRole.ADMIN]}>
                <div>Admin Dashboard - Coming Soon</div>
              </ProtectedRoute>
            }
          />
        </Route>

        {/* 404 Page */}
        <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
      
      {/* Notification System */}
      {isAuthenticated && (
        <>
          <Suspense fallback={null}>
            <NotificationContainer />
          </Suspense>
          <Suspense fallback={null}>
            <MultiplayerInviteHandler />
          </Suspense>
        </>
      )}
    </>
  );
};

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <ErrorToastProvider>
            <Router>
              <AppContent />
            </Router>
          </ErrorToastProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </Provider>
  );
}

export default App;