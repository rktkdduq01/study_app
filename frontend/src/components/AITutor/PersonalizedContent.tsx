import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  IconButton,
  Collapse,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as UncheckedIcon,
  Lightbulb as TipIcon,
  Quiz as QuizIcon,
  Book as LessonIcon,
  Code as CodeIcon,
  Visibility as ViewIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { aiTutorService, LearningContent } from '../../services/aiTutor';

interface PersonalizedContentProps {
  subject: string;
  topic: string;
  difficultyLevel: number;
  onComplete?: () => void;
}

export const PersonalizedContent: React.FC<PersonalizedContentProps> = ({
  subject,
  topic,
  difficultyLevel,
  onComplete
}) => {
  const [content, setContent] = useState<LearningContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [showPractice, setShowPractice] = useState(false);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    loadContent();
  }, [subject, topic, difficultyLevel]);

  const loadContent = async () => {
    setLoading(true);
    setError(null);
    try {
      const generatedContent = await aiTutorService.generateContent({
        subject,
        topic,
        difficultyLevel,
        contentType: 'lesson'
      });
      setContent(generatedContent);
    } catch (err) {
      setError('Failed to load personalized content. Please try again.');
      console.error('Content loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStepComplete = (stepIndex: number) => {
    setCompletedSteps(prev => new Set(prev).add(stepIndex));
    if (stepIndex < (content?.sections.length || 0) - 1) {
      setActiveStep(stepIndex + 1);
    }
  };

  const handlePracticeAnswer = (questionIndex: number, answer: string) => {
    setUserAnswers(prev => ({ ...prev, [questionIndex]: answer }));
  };

  const checkAnswers = () => {
    setShowResults(true);
  };

  const getScore = () => {
    if (!content?.practiceProblems) return 0;
    let correct = 0;
    content.practiceProblems.forEach((problem, index) => {
      if (userAnswers[index] === problem.correctAnswer) {
        correct++;
      }
    });
    return (correct / content.practiceProblems.length) * 100;
  };

  const getSectionIcon = (sectionType: string) => {
    switch (sectionType) {
      case 'explanation':
        return <LessonIcon />;
      case 'example':
        return <CodeIcon />;
      case 'tip':
        return <TipIcon />;
      case 'practice':
        return <QuizIcon />;
      default:
        return <LessonIcon />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Generating personalized content...</Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={loadContent}>
          Retry
        </Button>
      }>
        {error}
      </Alert>
    );
  }

  if (!content) return null;

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">{content.title || `${topic} - Personalized Lesson`}</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip label={subject} color="primary" size="small" />
              <Chip label={`Level ${difficultyLevel}`} color="secondary" size="small" />
            </Box>
          </Box>
          
          {content.adaptationReason && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Why this content?</strong> {content.adaptationReason}
              </Typography>
            </Alert>
          )}

          {/* Progress */}
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Progress: {completedSteps.size} / {content.sections.length} sections
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={(completedSteps.size / content.sections.length) * 100} 
              sx={{ mt: 1 }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Content Sections */}
      <Stepper activeStep={activeStep} orientation="vertical">
        {content.sections.map((section, index) => (
          <Step key={index}>
            <StepLabel
              optional={
                completedSteps.has(index) && (
                  <Typography variant="caption">Completed</Typography>
                )
              }
              StepIconComponent={() => (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {completedSteps.has(index) ? (
                    <CheckIcon color="success" />
                  ) : index === activeStep ? (
                    getSectionIcon(section.type)
                  ) : (
                    <UncheckedIcon />
                  )}
                </Box>
              )}
            >
              <Typography variant="h6">{section.type.charAt(0).toUpperCase() + section.type.slice(1)}</Typography>
            </StepLabel>
            <StepContent>
              <Paper sx={{ p: 3, mb: 2 }} elevation={2}>
                <Typography variant="body1" paragraph>
                  {section.content}
                </Typography>

                {/* Examples */}
                {section.examples && section.examples.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Examples:</Typography>
                    <List>
                      {section.examples.map((example, idx) => (
                        <ListItem key={idx}>
                          <ListItemIcon>
                            <CheckIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary={example} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}

                {/* Visual Descriptions */}
                {section.visuals && section.visuals.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>Visual Aids:</Typography>
                    {section.visuals.map((visual, idx) => (
                      <Alert key={idx} severity="info" icon={<ViewIcon />} sx={{ mt: 1 }}>
                        {visual}
                      </Alert>
                    ))}
                  </Box>
                )}

                <Box sx={{ mt: 3, display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    onClick={() => handleStepComplete(index)}
                    disabled={completedSteps.has(index)}
                  >
                    {completedSteps.has(index) ? 'Completed' : 'Mark as Complete'}
                  </Button>
                  {index === content.sections.length - 1 && (
                    <Button
                      variant="outlined"
                      onClick={() => setShowPractice(true)}
                      startIcon={<QuizIcon />}
                    >
                      Practice Problems
                    </Button>
                  )}
                </Box>
              </Paper>
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {/* Practice Problems */}
      <Collapse in={showPractice}>
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Practice Problems</Typography>
            <Divider sx={{ mb: 2 }} />
            
            {content.practiceProblems.map((problem, index) => (
              <Box key={index} sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Question {index + 1}: {problem.question}
                </Typography>
                
                {problem.type === 'multiple_choice' && problem.options && (
                  <List>
                    {problem.options.map((option, optIdx) => (
                      <ListItem
                        key={optIdx}
                        onClick={() => handlePracticeAnswer(index, option)}
                        sx={{
                          cursor: 'pointer',
                          '&:hover': { bgcolor: 'action.hover' },
                          border: 1,
                          borderColor: userAnswers[index] === option ? 'primary.main' : 'divider',
                          borderRadius: 1,
                          mb: 1,
                          bgcolor: userAnswers[index] === option ? 'action.selected' : 'background.paper',
                          transition: 'all 0.2s ease'
                        }}
                      >
                        <ListItemText primary={option} />
                      </ListItem>
                    ))}
                  </List>
                )}
                
                {showResults && (
                  <Alert 
                    severity={userAnswers[index] === problem.correctAnswer ? 'success' : 'error'}
                    sx={{ mt: 2 }}
                  >
                    <Typography variant="body2">
                      {userAnswers[index] === problem.correctAnswer ? 'Correct!' : 'Incorrect.'}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      <strong>Explanation:</strong> {problem.explanation}
                    </Typography>
                  </Alert>
                )}
              </Box>
            ))}
            
            <Box sx={{ mt: 3, display: 'flex', gap: 2, alignItems: 'center' }}>
              {!showResults ? (
                <Button
                  variant="contained"
                  onClick={checkAnswers}
                  disabled={Object.keys(userAnswers).length !== content.practiceProblems.length}
                >
                  Check Answers
                </Button>
              ) : (
                <>
                  <Typography variant="h6">
                    Score: {getScore().toFixed(0)}%
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setUserAnswers({});
                      setShowResults(false);
                    }}
                    startIcon={<RefreshIcon />}
                  >
                    Try Again
                  </Button>
                  {getScore() === 100 && onComplete && (
                    <Button
                      variant="contained"
                      color="success"
                      onClick={onComplete}
                    >
                      Complete Lesson
                    </Button>
                  )}
                </>
              )}
            </Box>
          </CardContent>
        </Card>
      </Collapse>

      {/* Resources */}
      {content.resources && content.resources.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Additional Resources</Typography>
            <List>
              {content.resources.map((resource, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <LessonIcon />
                  </ListItemIcon>
                  <ListItemText primary={resource} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};