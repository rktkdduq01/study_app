import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Grid, Card, CardContent, Typography, Box, Tab, Tabs } from '@mui/material';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { RootState } from '../../store';
import { analyticsAPI } from '../../services/analytics';
import DashboardStats from '../../components/analytics/DashboardStats';
import ActivityHeatmap from '../../components/analytics/ActivityHeatmap';
import ProgressChart from '../../components/analytics/ProgressChart';
import LeaderboardWidget from '../../components/analytics/LeaderboardWidget';
import RealtimeMetrics from '../../components/analytics/RealtimeMetrics';
import DateRangePicker from '../../components/common/DateRangePicker';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AnalyticsDashboard: React.FC = () => {
  const user = useSelector((state: RootState) => state.auth.user);
  const [tabValue, setTabValue] = useState(0);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    endDate: new Date()
  });
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, [dateRange]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getDashboardSummary();
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const renderUserDashboard = () => (
    <Grid container spacing={3}>
      {/* Key Stats */}
      <Grid size={12}>
        <DashboardStats data={dashboardData?.analytics} />
      </Grid>

      {/* Progress Chart */}
      <Grid size={{ xs: 12, md: 8 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Learning Progress
            </Typography>
            <ProgressChart 
              data={dashboardData?.analytics?.learning_progress}
              dateRange={dateRange}
            />
          </CardContent>
        </Card>
      </Grid>

      {/* Activity Heatmap */}
      <Grid size={{ xs: 12, md: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Activity Pattern
            </Typography>
            <ActivityHeatmap 
              data={dashboardData?.analytics?.activity_patterns}
            />
          </CardContent>
        </Card>
      </Grid>

      {/* Performance Metrics */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Trends
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line
                data={{
                  labels: dashboardData?.analytics?.performance_metrics?.accuracy?.map((m: any) => 
                    new Date(m.date).toLocaleDateString()
                  ) || [],
                  datasets: [
                    {
                      label: 'Accuracy',
                      data: dashboardData?.analytics?.performance_metrics?.accuracy?.map((m: any) => m.value) || [],
                      borderColor: 'rgb(75, 192, 192)',
                      backgroundColor: 'rgba(75, 192, 192, 0.2)',
                      tension: 0.1
                    },
                    {
                      label: 'Engagement',
                      data: dashboardData?.analytics?.performance_metrics?.engagement?.map((m: any) => m.value) || [],
                      borderColor: 'rgb(255, 99, 132)',
                      backgroundColor: 'rgba(255, 99, 132, 0.2)',
                      tension: 0.1
                    }
                  ]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'top' as const,
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Subject Performance */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Subject Performance
            </Typography>
            <Box sx={{ height: 300 }}>
              <Radar
                data={{
                  labels: Object.keys(dashboardData?.analytics?.learning_progress?.subjects || {}),
                  datasets: [{
                    label: 'Average Score',
                    data: Object.values(dashboardData?.analytics?.learning_progress?.subjects || {})
                      .map((s: any) => s.average_score),
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    pointBackgroundColor: 'rgb(54, 162, 235)',
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    r: {
                      beginAtZero: true,
                      max: 100
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderAdminDashboard = () => (
    <Grid container spacing={3}>
      {/* Real-time Metrics */}
      <Grid size={12}>
        <RealtimeMetrics />
      </Grid>

      {/* Global Stats */}
      <Grid size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Platform Overview
            </Typography>
            <Typography variant="h3">
              {dashboardData?.today?.users?.active || 0}
            </Typography>
            <Typography color="textSecondary">
              Active Users Today
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Total Users: {dashboardData?.today?.users?.total || 0}
            </Typography>
            <Typography variant="body2">
              New Users: {dashboardData?.today?.users?.new || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      {/* Activity Trends */}
      <Grid size={{ xs: 12, md: 9 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Activity Trends
            </Typography>
            <Box sx={{ height: 300 }}>
              <Line
                data={{
                  labels: dashboardData?.month?.activity_trend?.map((a: any) => a.date) || [],
                  datasets: [{
                    label: 'Daily Activities',
                    data: dashboardData?.month?.activity_trend?.map((a: any) => a.count) || [],
                    fill: true,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      display: false
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Content Performance */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Content Engagement
            </Typography>
            <Box sx={{ height: 300 }}>
              <Bar
                data={{
                  labels: ['Total Content', 'Views', 'Completions'],
                  datasets: [{
                    label: 'This Week',
                    data: [
                      dashboardData?.week?.content?.total || 0,
                      dashboardData?.week?.content?.views || 0,
                      dashboardData?.week?.content?.completions || 0
                    ],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1
                  }, {
                    label: 'This Month',
                    data: [
                      dashboardData?.month?.content?.total || 0,
                      dashboardData?.month?.content?.views || 0,
                      dashboardData?.month?.content?.completions || 0
                    ],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    borderWidth: 1
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* User Distribution */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              User Activity Distribution
            </Typography>
            <Box sx={{ height: 300 }}>
              <Doughnut
                data={{
                  labels: ['Very Active', 'Active', 'Moderate', 'Low', 'Inactive'],
                  datasets: [{
                    data: [
                      dashboardData?.user_segments?.very_active || 0,
                      dashboardData?.user_segments?.active || 0,
                      dashboardData?.user_segments?.moderate || 0,
                      dashboardData?.user_segments?.low || 0,
                      dashboardData?.user_segments?.inactive || 0
                    ],
                    backgroundColor: [
                      'rgba(75, 192, 192, 0.2)',
                      'rgba(54, 162, 235, 0.2)',
                      'rgba(255, 206, 86, 0.2)',
                      'rgba(255, 159, 64, 0.2)',
                      'rgba(255, 99, 132, 0.2)'
                    ],
                    borderColor: [
                      'rgb(75, 192, 192)',
                      'rgb(54, 162, 235)',
                      'rgb(255, 206, 86)',
                      'rgb(255, 159, 64)',
                      'rgb(255, 99, 132)'
                    ],
                    borderWidth: 1
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'right' as const
                    }
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Top Content */}
      <Grid size={{ xs: 12, md: 6 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Top Performing Content
            </Typography>
            <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
              {dashboardData?.month?.top_content?.map((content: any, index: number) => (
                <Box key={content.content_id} sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    #{index + 1} Content ID: {content.content_id}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Effectiveness Score: {content.score?.toFixed(2)}
                  </Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Leaderboard */}
      <Grid size={{ xs: 12, md: 6 }}>
        <LeaderboardWidget />
      </Grid>
    </Grid>
  );

  if (loading) {
    return <Typography>Loading analytics...</Typography>;
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Analytics Dashboard</Typography>
        <DateRangePicker
          startDate={dateRange.startDate}
          endDate={dateRange.endDate}
          onChange={setDateRange}
        />
      </Box>

      {user?.role === 'admin' ? (
        <>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Overview" />
              <Tab label="Users" />
              <Tab label="Content" />
              <Tab label="Revenue" />
              <Tab label="Reports" />
            </Tabs>
          </Box>
          <TabPanel value={tabValue} index={0}>
            {renderAdminDashboard()}
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <Typography>User Analytics (Coming Soon)</Typography>
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <Typography>Content Analytics (Coming Soon)</Typography>
          </TabPanel>
          <TabPanel value={tabValue} index={3}>
            <Typography>Revenue Analytics (Coming Soon)</Typography>
          </TabPanel>
          <TabPanel value={tabValue} index={4}>
            <Typography>Reports (Coming Soon)</Typography>
          </TabPanel>
        </>
      ) : (
        renderUserDashboard()
      )}
    </Box>
  );
};

export default AnalyticsDashboard;