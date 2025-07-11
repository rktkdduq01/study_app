import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Avatar,
  Typography,
  Chip,
  Button,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Alert,
  Stack,
  Card,
  CardContent,
  Tabs,
  Tab,
  Badge,
} from '@mui/material';
import {
  Send as SendIcon,
  Psychology as PsychologyIcon,
  Lightbulb as LightbulbIcon,
  QuestionAnswer as QuestionIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { aiTutorServiceNew } from '../../services/aiTutorServiceNew';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useWebSocket } from '../../hooks/useWebSocket';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  metadata?: any;
}

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
      id={`ai-tutor-tabpanel-${index}`}
      aria-labelledby={`ai-tutor-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

const AITutorInterface: React.FC = () => {
  const { user } = useAppSelector((state) => state.auth);
  const { websocketService } = useWebSocket();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [analysis, setAnalysis] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  useEffect(() => {
    // Load initial data
    loadAnalysis();
    loadRecommendations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAnalysis = async () => {
    try {
      const data = await aiTutorServiceNew.analyzePerformance();
      setAnalysis(data);
    } catch (error) {
      console.error('Failed to load analysis:', error);
    }
  };

  const loadRecommendations = async () => {
    try {
      const data = await aiTutorServiceNew.getRecommendations();
      setRecommendations(data);
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await aiTutorServiceNew.getChatResponse(inputMessage, {
        session_id: sessionId,
        user_analysis: analysis,
      });

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.ai_response,
        timestamp: new Date(),
        metadata: {
          suggestions: response.suggestions,
          resources: response.resources,
        },
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Failed to get AI response:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = async (action: string) => {
    switch (action) {
      case 'explain_concept':
        setInputMessage('Can you explain fractions to me?');
        break;
      case 'get_help':
        setInputMessage('I need help with my homework');
        break;
      case 'practice':
        setInputMessage('Can we practice some math problems?');
        break;
      case 'progress':
        setInputMessage('How am I doing in my studies?');
        break;
    }
  };

  const handleStartSession = async (subject: string, topic: string) => {
    try {
      const session = await aiTutorServiceNew.startLearningSession(
        `${subject}_${topic}_${Date.now()}`,
        'interactive',
        subject,
        topic,
        'medium'
      );
      setSessionId(session.session_id);
      
      // Send notification via WebSocket
      if (websocketService) {
        websocketService.emit('learning_session_started', {
          session_id: session.session_id,
          subject,
          topic,
        });
      }
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  const renderAnalysisCard = () => {
    if (!analysis) return null;

    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Your Learning Analysis
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Learning Style
            </Typography>
            <Chip
              label={analysis.learning_style}
              color="primary"
              size="small"
              sx={{ mt: 0.5 }}
            />
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Strengths
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
              {analysis.strengths.map((strength: any, index: number) => (
                <Chip
                  key={index}
                  label={strength.subject}
                  color="success"
                  size="small"
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Areas for Improvement
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 0.5, flexWrap: 'wrap' }}>
              {analysis.weaknesses.map((weakness: any, index: number) => (
                <Chip
                  key={index}
                  label={weakness.subject}
                  color="warning"
                  size="small"
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>

          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Progress Summary
            </Typography>
            <Typography variant="body2">
              Total Learning Time: {Math.floor(analysis.progress_summary.total_learning_time / 3600)} hours
            </Typography>
            <Typography variant="body2">
              Overall Accuracy: {Math.round(analysis.progress_summary.overall_accuracy * 100)}%
            </Typography>
            <Typography variant="body2">
              Current Streak: {analysis.progress_summary.streak_days} days
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderRecommendations = () => {
    return (
      <List>
        {recommendations.map((rec, index) => (
          <ListItem
            key={index}
            sx={{
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              mb: 1,
            }}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: 'primary.light' }}>
                <SchoolIcon />
              </Avatar>
            </ListItemAvatar>
            <ListItemText
              primary={`${rec.subject} - ${rec.topic}`}
              secondary={
                <>
                  <Typography variant="body2" color="text.secondary">
                    {rec.reason}
                  </Typography>
                  <Box sx={{ mt: 1 }}>
                    <Chip
                      label={rec.difficulty}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Chip
                      label={`Relevance: ${Math.round(rec.relevance_score * 100)}%`}
                      size="small"
                      color="secondary"
                    />
                  </Box>
                </>
              }
            />
            <Button
              variant="outlined"
              size="small"
              onClick={() => handleStartSession(rec.subject, rec.topic)}
            >
              Start
            </Button>
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, borderRadius: 0 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
              <PsychologyIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">AI Tutor</Typography>
              <Typography variant="caption" color="text.secondary">
                Your personalized learning assistant
              </Typography>
            </Box>
          </Box>
          <Badge badgeContent={3} color="secondary">
            <IconButton>
              <LightbulbIcon />
            </IconButton>
          </Badge>
        </Box>
      </Paper>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab label="Chat" icon={<QuestionIcon />} iconPosition="start" />
          <Tab label="Analysis" icon={<AssessmentIcon />} iconPosition="start" />
          <Tab label="Recommendations" icon={<AutoAwesomeIcon />} iconPosition="start" />
        </Tabs>
      </Box>

      {/* Content Area */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <TabPanel value={activeTab} index={0}>
          {/* Quick Actions */}
          <Box sx={{ mb: 2 }}>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              <Chip
                label="Explain a concept"
                onClick={() => handleQuickAction('explain_concept')}
                clickable
              />
              <Chip
                label="Get help"
                onClick={() => handleQuickAction('get_help')}
                clickable
              />
              <Chip
                label="Practice problems"
                onClick={() => handleQuickAction('practice')}
                clickable
              />
              <Chip
                label="Check progress"
                onClick={() => handleQuickAction('progress')}
                clickable
              />
            </Stack>
          </Box>

          {/* Messages */}
          <Box sx={{ flex: 1, mb: 2 }}>
            {messages.length === 0 ? (
              <Alert severity="info">
                Hi! I'm your AI tutor. Ask me anything about your studies, and I'll help you learn!
              </Alert>
            ) : (
              messages.map((message) => (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                    mb: 2,
                  }}
                >
                  <Box
                    sx={{
                      maxWidth: '70%',
                      p: 2,
                      borderRadius: 2,
                      bgcolor: message.type === 'user' ? 'primary.light' : 'grey.100',
                      color: message.type === 'user' ? 'primary.contrastText' : 'text.primary',
                    }}
                  >
                    <Typography variant="body1">{message.content}</Typography>
                    {message.metadata?.suggestions && (
                      <Box sx={{ mt: 1 }}>
                        {message.metadata.suggestions.map((suggestion: string, idx: number) => (
                          <Chip
                            key={idx}
                            label={suggestion}
                            size="small"
                            onClick={() => setInputMessage(suggestion)}
                            sx={{ mr: 0.5, mt: 0.5 }}
                          />
                        ))}
                      </Box>
                    )}
                  </Box>
                </Box>
              ))
            )}
            {isLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                <Box sx={{ p: 2 }}>
                  <CircularProgress size={20} />
                </Box>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {renderAnalysisCard()}
          
          {analysis?.recommendations && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrophyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Personalized Recommendations
                </Typography>
                <List>
                  {analysis.recommendations.map((rec: any, index: number) => (
                    <ListItem key={index}>
                      <ListItemText
                        primary={rec.action}
                        secondary={`Priority: ${rec.priority}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          )}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" gutterBottom>
            <AutoAwesomeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Content Recommendations
          </Typography>
          {renderRecommendations()}
        </TabPanel>
      </Box>

      {/* Input Area (only for chat tab) */}
      {activeTab === 0 && (
        <Paper sx={{ p: 2, borderRadius: 0 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Ask me anything..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              disabled={isLoading}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default AITutorInterface;