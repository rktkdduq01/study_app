import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Button,
  List,
  ListItem,
  ListItemAvatar,
  Divider,
  CircularProgress,
  Tooltip,
  Fab,
  Zoom,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  Collapse,
  Alert,
  InputAdornment,
} from '@mui/material';
import {
  Send,
  Psychology,
  Lightbulb,
  School,
  TrendingUp,
  Mic,
  MicOff,
  AttachFile,
  EmojiEmotions,
  Settings,
  Close,
  ExpandMore,
  ExpandLess,
  Timeline,
  EmojiEvents,
  Help,
  Celebration,
  SentimentSatisfied,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import {
  TutorMessage,
  MessageType,
  ConversationContext,
  TutorPersonality,
  MessageAction,
} from '../../types/ai-tutor';
import aiTutorService from '../../services/aiTutorService';
import { useNavigate } from 'react-router-dom';
import QuestRecommendationCard from './QuestRecommendationCard';
import GrowthRoadmapViewer from './GrowthRoadmapViewer';
import { motion, AnimatePresence } from 'framer-motion';

interface AITutorChatProps {
  context?: ConversationContext;
  onClose?: () => void;
  embedded?: boolean;
}

const AITutorChat: React.FC<AITutorChatProps> = ({
  context = ConversationContext.GENERAL_HELP,
  onClose,
  embedded = false,
}) => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { character } = useAppSelector((state) => state.character);
  
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [showRoadmap, setShowRoadmap] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [personality, setPersonality] = useState<TutorPersonality>(TutorPersonality.FRIENDLY);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  
  const messagesEndRef = useRef<null | HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user && !sessionStarted) {
      startSession();
    }
  }, [user, sessionStarted]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const startSession = async () => {
    try {
      const session = await aiTutorService.startTutorSession(
        user!.id.toString(),
        context
      );
      setSessionStarted(true);
      
      // Welcome message
      const welcomeMessage: TutorMessage = {
        id: Date.now().toString(),
        type: MessageType.AI_TUTOR,
        content: getWelcomeMessage(),
        timestamp: new Date().toISOString(),
        sender: {
          name: 'AI Tutor',
          avatar: '/ai-tutor-avatar.png',
          isAI: true,
        },
        actions: [
          {
            id: '1',
            label: 'Show me recommended quests',
            type: 'primary',
            action: 'show_quests',
          },
          {
            id: '2',
            label: 'View my growth roadmap',
            type: 'secondary',
            action: 'show_roadmap',
          },
          {
            id: '3',
            label: 'I need help with homework',
            type: 'secondary',
            action: 'homework_help',
          },
        ],
      };
      setMessages([welcomeMessage]);
    } catch (error) {
      console.error('Failed to start tutor session:', error);
    }
  };

  const getWelcomeMessage = () => {
    const greetings = [
      `Hey ${character?.name || 'there'}! 👋 I'm your AI learning buddy. What would you like to work on today?`,
      `Welcome back, ${character?.name || 'champion'}! 🌟 Ready to level up your skills?`,
      `Hi ${character?.name || 'friend'}! 🎯 I'm here to help you on your learning journey. What's on your mind?`,
    ];
    return greetings[Math.floor(Math.random() * greetings.length)];
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !user) return;

    const userMessage: TutorMessage = {
      id: Date.now().toString(),
      type: MessageType.USER,
      content: input,
      timestamp: new Date().toISOString(),
      sender: {
        name: character?.name || 'You',
        avatar: character?.avatar_url,
        isAI: false,
      },
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await aiTutorService.sendMessage(input, context);
      
      const aiMessage: TutorMessage = {
        id: (Date.now() + 1).toString(),
        type: MessageType.AI_TUTOR,
        content: response.message,
        timestamp: new Date().toISOString(),
        sender: {
          name: 'AI Tutor',
          avatar: '/ai-tutor-avatar.png',
          isAI: true,
        },
        metadata: {
          questRecommendations: response.questRecommendations,
          growthInsights: response.growthInsights,
        },
      };

      // Add quest recommendations as separate messages if any
      if (response.questRecommendations && response.questRecommendations.length > 0) {
        const questMessage: TutorMessage = {
          id: (Date.now() + 2).toString(),
          type: MessageType.QUEST_RECOMMENDATION,
          content: 'Based on our conversation, here are some quests I recommend for you:',
          timestamp: new Date().toISOString(),
          sender: {
            name: 'AI Tutor',
            avatar: '/ai-tutor-avatar.png',
            isAI: true,
          },
          metadata: {
            questRecommendations: response.questRecommendations,
          },
        };
        setMessages(prev => [...prev, aiMessage, questMessage]);
      } else {
        setMessages(prev => [...prev, aiMessage]);
      }

      // Handle emotional support
      if (response.emotionalSupport) {
        handleEmotionalSupport(response.emotionalSupport);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: TutorMessage = {
        id: (Date.now() + 1).toString(),
        type: MessageType.SYSTEM,
        content: 'Oops! Something went wrong. Let me try again...',
        timestamp: new Date().toISOString(),
        sender: {
          name: 'System',
          isAI: true,
        },
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleEmotionalSupport = (support: any) => {
    // Show emotional support as a special message or notification
    const supportMessage: TutorMessage = {
      id: Date.now().toString(),
      type: MessageType.ENCOURAGEMENT,
      content: support.message,
      timestamp: new Date().toISOString(),
      sender: {
        name: 'AI Tutor',
        avatar: '/ai-tutor-avatar.png',
        isAI: true,
      },
    };
    setTimeout(() => {
      setMessages(prev => [...prev, supportMessage]);
    }, 1000);
  };

  const handleActionClick = async (action: MessageAction) => {
    switch (action.action) {
      case 'show_quests':
        handleShowRecommendedQuests();
        break;
      case 'show_roadmap':
        setShowRoadmap(true);
        break;
      case 'homework_help':
        setInput("I need help with my homework. The topic is ");
        inputRef.current?.focus();
        break;
      case 'navigate':
        navigate(action.data);
        break;
      default:
        break;
    }
  };

  const handleShowRecommendedQuests = async () => {
    setIsTyping(true);
    try {
      const recommendations = await aiTutorService.getQuestRecommendations({
        studentId: user!.id.toString(),
        currentLevel: character?.total_level || 1,
        recentPerformance: {
          averageScore: 85,
          completionRate: 0.9,
          strugglingConcepts: [],
          strongConcepts: [],
          preferredDifficulty: 'medium',
          learningPace: 'medium',
        },
        interests: ['math', 'science'],
      });

      const questMessage: TutorMessage = {
        id: Date.now().toString(),
        type: MessageType.QUEST_RECOMMENDATION,
        content: "I've found some perfect quests for you! These match your current level and will help you grow:",
        timestamp: new Date().toISOString(),
        sender: {
          name: 'AI Tutor',
          avatar: '/ai-tutor-avatar.png',
          isAI: true,
        },
        metadata: {
          questRecommendations: recommendations,
        },
      };
      setMessages(prev => [...prev, questMessage]);
    } catch (error) {
      console.error('Failed to get quest recommendations:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickAction = (action: string) => {
    const quickMessages: Record<string, string> = {
      hint: "I'm stuck on this problem. Can you give me a hint?",
      explain: "Can you explain this concept to me?",
      practice: "I want to practice more problems like this.",
      progress: "How am I doing? Show me my progress.",
      motivate: "I'm feeling a bit discouraged. Can you help?",
      break: "Should I take a break now?",
    };

    if (quickMessages[action]) {
      setInput(quickMessages[action]);
      handleSendMessage();
    }
  };

  const toggleMessageExpansion = (messageId: string) => {
    const newExpanded = new Set(expandedMessages);
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId);
    } else {
      newExpanded.add(messageId);
    }
    setExpandedMessages(newExpanded);
  };

  const renderMessage = (message: TutorMessage) => {
    const isExpanded = expandedMessages.has(message.id);
    
    return (
      <ListItem
        key={message.id}
        sx={{
          flexDirection: message.sender.isAI ? 'row' : 'row-reverse',
          alignItems: 'flex-start',
          mb: 2,
        }}
      >
        <ListItemAvatar sx={{ minWidth: 40 }}>
          <Avatar
            src={message.sender.avatar}
            sx={{
              bgcolor: message.sender.isAI ? 'primary.main' : 'secondary.main',
              width: 36,
              height: 36,
            }}
          >
            {message.sender.isAI ? <Psychology /> : character?.name?.charAt(0)}
          </Avatar>
        </ListItemAvatar>
        
        <Box sx={{ flex: 1, mx: 1 }}>
          <Paper
            sx={{
              p: 2,
              bgcolor: message.sender.isAI ? 'grey.100' : 'primary.light',
              color: message.sender.isAI ? 'text.primary' : 'primary.contrastText',
              borderRadius: 2,
              position: 'relative',
              maxWidth: '80%',
              float: message.sender.isAI ? 'left' : 'right',
            }}
          >
            {/* Message Type Indicator */}
            {message.type === MessageType.QUEST_RECOMMENDATION && (
              <Chip
                icon={<EmojiEvents />}
                label="Quest Recommendations"
                size="small"
                color="success"
                sx={{ mb: 1 }}
              />
            )}
            {message.type === MessageType.ENCOURAGEMENT && (
              <Chip
                icon={<Celebration />}
                label="Encouragement"
                size="small"
                color="warning"
                sx={{ mb: 1 }}
              />
            )}

            <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </Typography>

            {/* Quest Recommendations */}
            {message.metadata?.questRecommendations && (
              <Box sx={{ mt: 2 }}>
                <Divider sx={{ my: 2 }} />
                {message.metadata.questRecommendations.map((quest, index) => (
                  <QuestRecommendationCard
                    key={index}
                    recommendation={quest}
                    onSelect={() => navigate(`/student/quests/${quest.questId}`)}
                  />
                ))}
              </Box>
            )}

            {/* Growth Insights */}
            {message.metadata?.growthInsights && message.metadata.growthInsights.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Button
                  size="small"
                  onClick={() => toggleMessageExpansion(message.id)}
                  endIcon={isExpanded ? <ExpandLess /> : <ExpandMore />}
                >
                  Growth Insights ({message.metadata.growthInsights.length})
                </Button>
                <Collapse in={isExpanded}>
                  {message.metadata.growthInsights.map((insight, index) => (
                    <Alert
                      key={index}
                      severity={insight.type === 'achievement' ? 'success' : 'info'}
                      sx={{ mt: 1 }}
                    >
                      <Typography variant="subtitle2">{insight.title}</Typography>
                      <Typography variant="body2">{insight.description}</Typography>
                    </Alert>
                  ))}
                </Collapse>
              </Box>
            )}

            {/* Action Buttons */}
            {message.actions && (
              <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
                {message.actions.map((action) => (
                  <Button
                    key={action.id}
                    size="small"
                    variant={action.type === 'primary' ? 'contained' : 'outlined'}
                    color={action.type as any}
                    onClick={() => handleActionClick(action)}
                  >
                    {action.label}
                  </Button>
                ))}
              </Box>
            )}

            <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
              {new Date(message.timestamp).toLocaleTimeString()}
            </Typography>
          </Paper>
        </Box>
      </ListItem>
    );
  };

  return (
    <Paper
      sx={{
        height: embedded ? '600px' : '100vh',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
            <Psychology />
          </Avatar>
          <Box>
            <Typography variant="h6">AI Learning Tutor</Typography>
            <Typography variant="caption">
              Always here to help you learn!
            </Typography>
          </Box>
        </Box>
        
        <Box>
          <Tooltip title="View Growth Roadmap">
            <IconButton color="inherit" onClick={() => setShowRoadmap(true)}>
              <Timeline />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton color="inherit" onClick={() => setShowSettings(true)}>
              <Settings />
            </IconButton>
          </Tooltip>
          {onClose && (
            <IconButton color="inherit" onClick={onClose}>
              <Close />
            </IconButton>
          )}
        </Box>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List>
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {renderMessage(message)}
              </motion.div>
            ))}
          </AnimatePresence>
        </List>
        
        {isTyping && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 6 }}>
            <CircularProgress size={20} />
            <Typography variant="body2" color="text.secondary">
              AI Tutor is thinking...
            </Typography>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Quick Actions */}
      {showQuickActions && (
        <Box sx={{ px: 2, pb: 1 }}>
          <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1 }}>
            <Chip
              icon={<Lightbulb />}
              label="Get Hint"
              onClick={() => handleQuickAction('hint')}
              clickable
            />
            <Chip
              icon={<Help />}
              label="Explain"
              onClick={() => handleQuickAction('explain')}
              clickable
            />
            <Chip
              icon={<School />}
              label="Practice"
              onClick={() => handleQuickAction('practice')}
              clickable
            />
            <Chip
              icon={<TrendingUp />}
              label="Progress"
              onClick={() => handleQuickAction('progress')}
              clickable
            />
            <Chip
              icon={<SentimentSatisfied />}
              label="Motivate"
              onClick={() => handleQuickAction('motivate')}
              clickable
            />
          </Box>
        </Box>
      )}

      {/* Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <TextField
          ref={inputRef}
          fullWidth
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendMessage();
            }
          }}
          placeholder="Ask me anything about learning..."
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={handleSendMessage} disabled={!input.trim()}>
                  <Send />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        
        <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
          <Tooltip title="Voice input">
            <IconButton size="small" onClick={() => setIsListening(!isListening)}>
              {isListening ? <MicOff /> : <Mic />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Attach file">
            <IconButton size="small">
              <AttachFile />
            </IconButton>
          </Tooltip>
          <Tooltip title="Toggle quick actions">
            <IconButton 
              size="small" 
              onClick={() => setShowQuickActions(!showQuickActions)}
            >
              <EmojiEmotions />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Growth Roadmap Dialog */}
      <Dialog
        open={showRoadmap}
        onClose={() => setShowRoadmap(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Your Growth Roadmap
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setShowRoadmap(false)}
          >
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {user && <GrowthRoadmapViewer studentId={user.id.toString()} />}
        </DialogContent>
      </Dialog>

      {/* Floating Action Button for minimized view */}
      {!embedded && (
        <Zoom in={true}>
          <Fab
            color="primary"
            sx={{
              position: 'fixed',
              bottom: 16,
              right: 16,
              display: 'none', // Show when chat is minimized
            }}
          >
            <Badge badgeContent={messages.length} color="error">
              <Psychology />
            </Badge>
          </Fab>
        </Zoom>
      )}
    </Paper>
  );
};

export default AITutorChat;