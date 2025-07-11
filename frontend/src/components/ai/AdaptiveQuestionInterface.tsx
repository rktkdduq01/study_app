import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  TextField,
  Alert,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Tooltip,
  Zoom,
  Fade,
  Badge,
  Avatar,
  CircularProgress,
} from '@mui/material';
import {
  Lightbulb,
  CheckCircle,
  Cancel,
  TipsAndUpdates,
  Psychology,
  Timer,
  Star,
  EmojiEvents,
  NavigateNext,
  NavigateBefore,
  Help,
  Visibility,
  VisibilityOff,
  Timeline,
  AutoAwesome,
  Extension,
  Link,
  QuestionAnswer,
  Celebration,
  SentimentSatisfiedAlt,
  SentimentDissatisfied,
  MenuBook,
  EmojiObjects,
} from '@mui/icons-material';
import {
  AIGeneratedQuestion,
  AdaptiveHint,
  EnhancedOption,
  SolutionStep,
  ConceptConnection,
  FeedbackComponent,
} from '../../types/ai-learning';
import aiLearningService from '../../services/aiLearningService';
import ConceptConnectionVisualizer from './ConceptConnectionVisualizer';

interface AdaptiveQuestionInterfaceProps {
  question: AIGeneratedQuestion;
  onAnswerSubmit: (correct: boolean, answer: any) => void;
  studentId: string;
}

const AdaptiveQuestionInterface: React.FC<AdaptiveQuestionInterfaceProps> = ({
  question,
  onAnswerSubmit,
  studentId,
}) => {
  const [currentAnswer, setCurrentAnswer] = useState<any>(null);
  const [attempts, setAttempts] = useState(0);
  const [showHints, setShowHints] = useState(false);
  const [currentHintLevel, setCurrentHintLevel] = useState(0);
  const [showSolutionSteps, setShowSolutionSteps] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState<any>(null);
  const [showConceptConnections, setShowConceptConnections] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [isThinking, setIsThinking] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [stepAnswers, setStepAnswers] = useState<Record<number, string>>({});
  const [emotionalState, setEmotionalState] = useState<'neutral' | 'happy' | 'struggling'>('neutral');

  useEffect(() => {
    const timer = setInterval(() => setTimeSpent(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Update emotional state based on attempts and hints
    if (attempts >= 3 || currentHintLevel >= 3) {
      setEmotionalState('struggling');
    } else if (feedback?.correct) {
      setEmotionalState('happy');
    } else {
      setEmotionalState('neutral');
    }
  }, [attempts, currentHintLevel, feedback]);

  const handleAnswerChange = (answer: any) => {
    setCurrentAnswer(answer);
    setIsThinking(true);
    // Simulate thinking time
    setTimeout(() => setIsThinking(false), 800);
  };

  const handleSubmit = async () => {
    const isCorrect = checkAnswer();
    setAttempts(attempts + 1);

    // Generate personalized feedback
    const personalizedFeedback = await aiLearningService.generatePersonalizedFeedback(
      question.id,
      studentId,
      currentAnswer,
      timeSpent
    );

    setFeedback({
      correct: isCorrect,
      ...personalizedFeedback,
    });
    setShowFeedback(true);

    if (isCorrect) {
      setTimeout(() => {
        onAnswerSubmit(true, currentAnswer);
      }, 3000);
    }
  };

  const checkAnswer = (): boolean => {
    // This would be more sophisticated in real implementation
    if (question.data.options) {
      const correctOption = question.data.options.find(opt => opt.isCorrect);
      return currentAnswer === correctOption?.id;
    }
    return false;
  };

  const requestHint = async () => {
    if (currentHintLevel < question.adaptiveHints.length) {
      const hint = await aiLearningService.generateAdaptiveHint(
        question.id,
        studentId,
        currentAnswer,
        attempts
      );
      
      setShowHints(true);
      setCurrentHintLevel(currentHintLevel + 1);
    }
  };

  const renderMultipleChoice = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        {question.data.representations.verbal}
      </Typography>

      {/* Visual representation if available */}
      {question.data.representations.visual && (
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <img 
            src={question.data.representations.visual} 
            alt="Question visual"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        </Box>
      )}

      <List>
        {question.data.options?.map((option: EnhancedOption, index: number) => (
          <Fade in key={option.id} style={{ transitionDelay: `${index * 100}ms` }}>
            <ListItem
              component={Paper}
              elevation={selectedOption === option.id ? 8 : 2}
              sx={{
                mb: 2,
                p: 2,
                cursor: 'pointer',
                transition: 'all 0.3s',
                border: '2px solid',
                borderColor: selectedOption === option.id ? 'primary.main' : 'transparent',
                '&:hover': {
                  transform: 'translateX(8px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => {
                setSelectedOption(option.id);
                handleAnswerChange(option.id);
              }}
            >
              <ListItemIcon>
                <Avatar 
                  sx={{ 
                    bgcolor: selectedOption === option.id ? 'primary.main' : 'grey.300',
                    transition: 'all 0.3s',
                  }}
                >
                  {String.fromCharCode(65 + index)}
                </Avatar>
              </ListItemIcon>
              <ListItemText 
                primary={option.text}
                primaryTypographyProps={{
                  variant: 'body1',
                  sx: { fontWeight: selectedOption === option.id ? 600 : 400 }
                }}
              />
              {selectedOption === option.id && !showFeedback && (
                <Chip 
                  label="Selected" 
                  size="small" 
                  color="primary"
                  icon={<CheckCircle />}
                />
              )}
            </ListItem>
          </Fade>
        ))}
      </List>

      {/* Show why each option was selected after feedback */}
      {showFeedback && selectedOption && (
        <Collapse in={showFeedback}>
          <Alert 
            severity={feedback?.correct ? 'success' : 'error'}
            sx={{ mt: 2 }}
          >
            {question.data.options?.find(opt => opt.id === selectedOption)?.ifSelected.feedback}
          </Alert>
        </Collapse>
      )}
    </Box>
  );

  const renderSolutionSteps = () => (
    <Card sx={{ mb: 3, bgcolor: 'grey.50' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Timeline />
          Solution Steps
        </Typography>
        
        <Stepper activeStep={currentStep} orientation="vertical">
          {question.data.solutionSteps?.map((step: SolutionStep, index: number) => (
            <Step key={index}>
              <StepLabel>
                <Typography variant="subtitle2">
                  {step.description}
                </Typography>
                <Chip label={step.concept} size="small" sx={{ mt: 0.5 }} />
              </StepLabel>
              <StepContent>
                {step.checkPoint && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" gutterBottom>
                      {step.checkPoint.question}
                    </Typography>
                    <TextField
                      size="small"
                      value={stepAnswers[index] || ''}
                      onChange={(e) => setStepAnswers({
                        ...stepAnswers,
                        [index]: e.target.value
                      })}
                      placeholder="Your answer..."
                      sx={{ mr: 1 }}
                    />
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => {
                        if (stepAnswers[index]?.toLowerCase() === step.checkPoint?.expectedAnswer.toLowerCase()) {
                          setCurrentStep(currentStep + 1);
                        }
                      }}
                    >
                      Check
                    </Button>
                  </Box>
                )}
                <Typography variant="body2" color="text.secondary">
                  💡 {step.hint}
                </Typography>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </CardContent>
    </Card>
  );

  const renderAdaptiveHints = () => (
    <Box sx={{ mb: 3 }}>
      {question.adaptiveHints.slice(0, currentHintLevel).map((hint: AdaptiveHint, index: number) => (
        <Zoom in key={index}>
          <Alert 
            severity="info" 
            sx={{ mb: 1 }}
            icon={
              hint.type === 'conceptual' ? <Lightbulb /> :
              hint.type === 'procedural' ? <Timeline /> :
              hint.type === 'metacognitive' ? <Psychology /> :
              <EmojiEvents />
            }
          >
            <Typography variant="subtitle2" gutterBottom>
              Hint {index + 1} ({hint.type})
            </Typography>
            <Typography variant="body2">
              {hint.content}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Concept: {hint.conceptReinforced}
            </Typography>
          </Alert>
        </Zoom>
      ))}
      
      {currentHintLevel < question.adaptiveHints.length && (
        <Button
          size="small"
          onClick={requestHint}
          startIcon={<Help />}
          sx={{ mt: 1 }}
        >
          Need another hint? ({question.adaptiveHints.length - currentHintLevel} available)
        </Button>
      )}
    </Box>
  );

  const renderFeedback = () => (
    <Dialog open={showFeedback} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ textAlign: 'center' }}>
        {feedback?.correct ? (
          <Box>
            <Celebration sx={{ fontSize: 64, color: 'success.main' }} />
            <Typography variant="h5" color="success.main">
              Excellent Work! 🎉
            </Typography>
          </Box>
        ) : (
          <Box>
            <SentimentDissatisfied sx={{ fontSize: 64, color: 'warning.main' }} />
            <Typography variant="h5" color="warning.main">
              Not Quite, But Keep Going! 💪
            </Typography>
          </Box>
        )}
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body1" paragraph>
            {feedback?.feedback}
          </Typography>
          
          {feedback?.encouragement && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {feedback.encouragement}
            </Alert>
          )}
        </Box>

        {/* Concepts to Review */}
        {feedback?.conceptsToReview?.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              Concepts to Review:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {feedback.conceptsToReview.map((concept: string, index: number) => (
                <Chip
                  key={index}
                  label={concept}
                  size="small"
                  icon={<MenuBook />}
                  onClick={() => {/* Open concept explanation */}}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Next Steps */}
        {feedback?.nextSteps?.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Your Next Steps:
            </Typography>
            <List dense>
              {feedback.nextSteps.map((step: string, index: number) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <NavigateNext color="primary" />
                  </ListItemIcon>
                  <ListItemText primary={step} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </DialogContent>
      
      <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
        {!feedback?.correct && attempts < 3 && (
          <Button
            variant="contained"
            onClick={() => {
              setShowFeedback(false);
              setShowSolutionSteps(true);
            }}
            startIcon={<Psychology />}
          >
            Show Me How
          </Button>
        )}
        <Button
          variant={feedback?.correct ? 'contained' : 'outlined'}
          onClick={() => {
            if (feedback?.correct) {
              onAnswerSubmit(true, currentAnswer);
            } else {
              setShowFeedback(false);
            }
          }}
        >
          {feedback?.correct ? 'Continue' : 'Try Again'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Paper sx={{ p: 3 }}>
      {/* Question Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {question.type === 'conceptual' && <EmojiObjects />}
            {question.type === 'procedural' && <Timeline />}
            {question.type === 'analytical' && <Psychology />}
            {question.type === 'creative' && <AutoAwesome />}
            {question.purpose.replace('_', ' ').charAt(0).toUpperCase() + 
             question.purpose.replace('_', ' ').slice(1)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
            {question.conceptsCovered.map((concept, index) => (
              <Chip key={index} label={concept} size="small" />
            ))}
          </Box>
        </Box>
        
        <Box sx={{ textAlign: 'right' }}>
          <Typography variant="body2" color="text.secondary">
            Time: {Math.floor(timeSpent / 60)}:{(timeSpent % 60).toString().padStart(2, '0')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Attempts: {attempts}
          </Typography>
        </Box>
      </Box>

      {/* Emotional Support Badge */}
      {emotionalState !== 'neutral' && (
        <Zoom in>
          <Badge
            badgeContent={
              emotionalState === 'happy' ? '😊' : '🤔'
            }
            sx={{ position: 'absolute', top: 16, right: 16 }}
          >
            <Chip
              label={emotionalState === 'happy' ? 'Great job!' : 'You got this!'}
              color={emotionalState === 'happy' ? 'success' : 'info'}
              size="small"
            />
          </Badge>
        </Zoom>
      )}

      {/* Show concept connections */}
      <Box sx={{ mb: 2 }}>
        <Button
          size="small"
          startIcon={<Link />}
          onClick={() => setShowConceptConnections(!showConceptConnections)}
        >
          See Concept Connections
        </Button>
      </Box>
      
      <Collapse in={showConceptConnections}>
        <ConceptConnectionVisualizer connections={question.data.conceptConnections} />
      </Collapse>

      {/* Adaptive Hints */}
      {showHints && renderAdaptiveHints()}

      {/* Solution Steps */}
      {showSolutionSteps && renderSolutionSteps()}

      {/* Question Content */}
      {renderMultipleChoice()}

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Get a hint (-5 points)">
            <Button
              variant="outlined"
              size="small"
              startIcon={<Lightbulb />}
              onClick={requestHint}
              disabled={currentHintLevel >= question.adaptiveHints.length}
            >
              Hint ({question.adaptiveHints.length - currentHintLevel})
            </Button>
          </Tooltip>
          
          {!showSolutionSteps && attempts > 0 && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<Timeline />}
              onClick={() => setShowSolutionSteps(true)}
            >
              Show Steps
            </Button>
          )}
        </Box>

        <Button
          variant="contained"
          size="large"
          onClick={handleSubmit}
          disabled={!currentAnswer || isThinking}
          endIcon={isThinking ? <CircularProgress size={20} /> : <NavigateNext />}
        >
          {isThinking ? 'Thinking...' : 'Submit Answer'}
        </Button>
      </Box>

      {/* Feedback Dialog */}
      {renderFeedback()}
    </Paper>
  );
};

export default AdaptiveQuestionInterface;