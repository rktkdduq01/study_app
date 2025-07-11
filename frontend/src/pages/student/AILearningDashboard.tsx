import React, { useState, useEffect } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Tab,
  Tabs,
  CircularProgress,
  Badge,
} from '@mui/material';
import {
  Psychology,
  TrendingUp,
  EmojiEvents,
  School,
  Timer,
  Lightbulb,
  AutoAwesome,
  Timeline,
  Groups,
  NavigateNext,
  Refresh,
  Info,
  CheckCircle,
  Warning,
  Error,
  Star,
  LocalFireDepartment,
  Insights,
  Science,
  Calculate,
  Language,
  Public,
  Palette,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import {
  LearningAnalysis,
  StudentLearningProfile,
  AdaptiveLearningPath,
  ConceptStrength,
  ConceptWeakness,
  StudyStrategy,
} from '../../types/ai-learning';
import aiLearningService from '../../services/aiLearningService';
import ConceptualQuestionGenerator from '../../components/ai/ConceptualQuestionGenerator';
// Chart imports will be added when chart library is installed

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const AILearningDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { character } = useAppSelector((state) => state.character);
  
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<StudentLearningProfile | null>(null);
  const [analysis, setAnalysis] = useState<LearningAnalysis | null>(null);
  const [learningPath, setLearningPath] = useState<AdaptiveLearningPath | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedSubject, setSelectedSubject] = useState<string>('math');
  const [showConceptGenerator, setShowConceptGenerator] = useState(false);
  const [selectedConcept, setSelectedConcept] = useState<string>('');

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [profileData, analysisData] = await Promise.all([
        aiLearningService.analyzeStudentProfile(user!.id.toString()),
        aiLearningService.analyzeLearningProgress(user!.id.toString()),
      ]);
      
      setProfile(profileData);
      setAnalysis(analysisData);
      
      // Load learning path for selected subject
      const pathData = await aiLearningService.generateLearningPath(
        user!.id.toString(),
        selectedSubject,
        analysisData.recommendations.nextConcepts
      );
      setLearningPath(pathData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSubjectIcon = (subject: string) => {
    switch (subject) {
      case 'math': return <Calculate />;
      case 'science': return <Science />;
      case 'language': return <Language />;
      case 'social': return <Public />;
      case 'art': return <Palette />;
      default: return <School />;
    }
  };

  const renderOverviewTab = () => (
    <GridContainer spacing={3} columns={{ xs: 1, md: 2 }}>
      {/* AI Analysis Summary */}
      <Box sx={{ gridColumn: 'span 2' }}>
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Psychology />
            AI Learning Analysis
          </Typography>
          <Typography variant="body1" paragraph>
            Based on your learning patterns, you're a <strong>{profile?.learningStyle.replace('_', ' ')}</strong> learner
            who excels in <strong>{analysis?.learningPatterns.effectiveStrategies[0]}</strong>.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              icon={<Timer />}
              label={`Optimal study time: ${analysis?.learningPatterns.optimalSessionLength} min`}
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
            <Chip
              icon={<LocalFireDepartment />}
              label={`Best time: ${analysis?.learningPatterns.bestTimeOfDay}`}
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
            <Chip
              icon={<Star />}
              label={`${analysis?.motivationProfile.engagementLevel}/10 Engagement`}
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          </Box>
        </Paper>
      </Box>

      {/* Concept Mastery Overview */}
      <Box>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircle color="success" />
              Strong Concepts
            </Typography>
            <List>
              {analysis?.conceptualUnderstanding.strongConcepts.slice(0, 3).map((concept, index) => (
                <ListItem key={index} sx={{ px: 0 }}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'success.light' }}>
                      <TrendingUp color="success" />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={concept.concept}
                    secondary={`${concept.masteryLevel}% mastery • ${concept.applications.length} applications`}
                  />
                  <Box sx={{ minWidth: 100 }}>
                    <LinearProgress
                      variant="determinate"
                      value={concept.masteryLevel}
                      color="success"
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                </ListItem>
              ))}
            </List>
            <Button
              fullWidth
              variant="outlined"
              color="success"
              onClick={() => setTabValue(1)}
              sx={{ mt: 2 }}
            >
              View All Strong Areas
            </Button>
          </CardContent>
        </Card>
      </Box>

      {/* Areas for Improvement */}
      <Box>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Warning color="warning" />
              Areas to Focus
            </Typography>
            <List>
              {analysis?.conceptualUnderstanding.weakConcepts.slice(0, 3).map((concept, index) => (
                <ListItem 
                  key={index} 
                  sx={{ px: 0, cursor: 'pointer' }}
                  onClick={() => {
                    setSelectedConcept(concept.concept);
                    setShowConceptGenerator(true);
                  }}
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'warning.light' }}>
                      <Lightbulb color="warning" />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={concept.concept}
                    secondary={
                      <Box>
                        <Typography variant="caption">
                          {concept.masteryLevel}% mastery
                        </Typography>
                        <Typography variant="caption" display="block">
                          Common error: {concept.commonErrors[0]}
                        </Typography>
                      </Box>
                    }
                  />
                  <Tooltip title="Practice this concept">
                    <IconButton color="primary">
                      <NavigateNext />
                    </IconButton>
                  </Tooltip>
                </ListItem>
              ))}
            </List>
            <Button
              fullWidth
              variant="contained"
              color="warning"
              onClick={() => setTabValue(2)}
              sx={{ mt: 2 }}
            >
              Start Focused Practice
            </Button>
          </CardContent>
        </Card>
      </Box>

      {/* Learning Stats */}
      <Box sx={{ gridColumn: { xs: 'span 2', md: 'span 1' } }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Learning Progress
            </Typography>
            <Box sx={{ position: 'relative', display: 'inline-flex' }}>
              <CircularProgress
                variant="determinate"
                value={analysis?.motivationProfile.confidenceLevel ? analysis.motivationProfile.confidenceLevel * 10 : 0}
                size={120}
                thickness={4}
              />
              <Box
                sx={{
                  top: 0,
                  left: 0,
                  bottom: 0,
                  right: 0,
                  position: 'absolute',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="h4" component="div" color="text.secondary">
                  {analysis?.motivationProfile.confidenceLevel || 0}/10
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" sx={{ mt: 2 }}>
              Confidence Level
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Recommended Strategies */}
      <Box sx={{ gridColumn: { xs: 'span 2', md: 'span 1' } }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoAwesome color="primary" />
              AI-Recommended Study Strategies
            </Typography>
            <GridContainer spacing={2} columns={{ xs: 1, sm: 2 }}>
              {analysis?.recommendations.studyStrategies.slice(0, 4).map((strategy, index) => (
                <Box key={index}>
                  <Paper sx={{ p: 2, height: '100%', bgcolor: 'grey.50' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      {strategy.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {strategy.description}
                    </Typography>
                    <Typography variant="caption" color="primary">
                      Best for: {strategy.whenToUse}
                    </Typography>
                  </Paper>
                </Box>
              ))}
            </GridContainer>
          </CardContent>
        </Card>
      </Box>
    </GridContainer>
  );

  const renderLearningPathTab = () => (
    <GridContainer spacing={3}>
      {/* Subject Selection */}
      <Box>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Select Subject
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {['math', 'science', 'language', 'social', 'art'].map((subject) => (
              <Chip
                key={subject}
                label={subject.charAt(0).toUpperCase() + subject.slice(1)}
                icon={getSubjectIcon(subject)}
                onClick={() => setSelectedSubject(subject)}
                color={selectedSubject === subject ? 'primary' : 'default'}
                variant={selectedSubject === subject ? 'filled' : 'outlined'}
              />
            ))}
          </Box>
        </Paper>
      </Box>

      {/* Learning Path Visualization */}
      <Box>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Timeline />
            Your Personalized Learning Path
          </Typography>
          
          {learningPath && (
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, overflowX: 'auto', pb: 2 }}>
                {learningPath.recommendedPath.map((nodeId, index) => {
                  const node = learningPath.availableNodes.find(n => n.id === nodeId);
                  if (!node) return null;
                  
                  return (
                    <React.Fragment key={nodeId}>
                      <Card
                        sx={{
                          minWidth: 200,
                          cursor: 'pointer',
                          transition: 'all 0.3s',
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            boxShadow: 4,
                          },
                        }}
                        onClick={() => {
                          setSelectedConcept(node.concept);
                          setShowConceptGenerator(true);
                        }}
                      >
                        <CardContent>
                          <Typography variant="subtitle2" gutterBottom>
                            Step {index + 1}
                          </Typography>
                          <Typography variant="h6">
                            {node.concept}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {node.estimatedTime} min
                          </Typography>
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={node.id === learningPath.currentNode.id ? 50 : 0}
                            />
                          </Box>
                        </CardContent>
                      </Card>
                      {index < learningPath.recommendedPath.length - 1 && (
                        <NavigateNext color="action" />
                      )}
                    </React.Fragment>
                  );
                })}
              </Box>
              
              {/* Alternative Paths */}
              {learningPath.alternativePaths.length > 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="body2">
                    {learningPath.alternativePaths.length} alternative learning paths available based on your preferences
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
        </Paper>
      </Box>

      {/* Next Activities */}
      <Box>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recommended Activities
          </Typography>
          <GridContainer spacing={2} columns={{ xs: 1, sm: 2, md: 3 }}>
            {learningPath?.currentNode.activities.map((activity, index) => (
              <Box key={index}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      {activity.title}
                    </Typography>
                    <Chip
                      label={activity.type}
                      size="small"
                      color={
                        activity.type === 'exploration' ? 'info' :
                        activity.type === 'practice' ? 'primary' :
                        activity.type === 'application' ? 'success' :
                        'secondary'
                      }
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {activity.description}
                    </Typography>
                    <Typography variant="caption">
                      Duration: {activity.duration} min
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </GridContainer>
        </Paper>
      </Box>
    </GridContainer>
  );

  const renderCollaborationTab = () => (
    <GridContainer spacing={3}>
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            AI has identified study partners who complement your learning style and can help with concepts you're working on.
          </Typography>
        </Alert>
      </Box>
      
      {/* Study Partners */}
      <Box>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Groups />
            Recommended Study Partners
          </Typography>
          
          <List>
            {/* Mock study partners - would be real data from API */}
            {[
              { name: 'Alex Kim', strength: 'Algebra', match: 85 },
              { name: 'Sarah Chen', strength: 'Geometry', match: 78 },
              { name: 'Mike Johnson', strength: 'Problem Solving', match: 72 },
            ].map((partner, index) => (
              <ListItem key={index} divider>
                <ListItemAvatar>
                  <Avatar>{partner.name.charAt(0)}</Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={partner.name}
                  secondary={`Strong in: ${partner.strength}`}
                />
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body2" color="primary">
                    {partner.match}% Match
                  </Typography>
                  <Button size="small" variant="outlined" sx={{ mt: 1 }}>
                    Connect
                  </Button>
                </Box>
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </GridContainer>
  );

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (showConceptGenerator) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Button
          startIcon={<NavigateNext sx={{ transform: 'rotate(180deg)' }} />}
          onClick={() => setShowConceptGenerator(false)}
          sx={{ mb: 2 }}
        >
          Back to Dashboard
        </Button>
        <ConceptualQuestionGenerator
          subject={selectedSubject}
          topic={selectedConcept}
          onComplete={(mastery) => {
            setShowConceptGenerator(false);
            loadDashboardData();
          }}
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Psychology color="primary" />
          AI Learning Assistant
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Personalized learning powered by AI analysis
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)}>
          <Tab label="Overview" icon={<Insights />} iconPosition="start" />
          <Tab label="Learning Path" icon={<Timeline />} iconPosition="start" />
          <Tab label="Study Together" icon={<Groups />} iconPosition="start" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        {renderOverviewTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderLearningPathTab()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderCollaborationTab()}
      </TabPanel>
    </Container>
  );
};

export default AILearningDashboard;
