import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Card,
  CardContent,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Lightbulb as LightbulbIcon,
  Code as CodeIcon,
  Quiz as QuizIcon,
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as UncheckedIcon,
  Visibility as VisibilityIcon,
  Timer as TimerIcon,
  Psychology as PsychologyIcon,
} from '@mui/icons-material';
import { aiTutorServiceNew } from '../../services/aiTutorServiceNew';

interface PersonalizedContentViewerProps {
  subject: string;
  topic: string;
  difficulty: string;
  onComplete?: () => void;
  sessionId?: number;
}

interface ContentSection {
  type: string;
  title?: string;
  content?: string;
  visual?: boolean;
  interactive?: boolean;
  animation_url?: string;
  steps?: any[];
  practice?: any;
  problem?: string;
  solution_steps?: any[];
  [key: string]: any; // Allow additional properties
}

const PersonalizedContentViewer: React.FC<PersonalizedContentViewerProps> = ({
  subject,
  topic,
  difficulty,
  onComplete,
  sessionId,
}) => {
  const [content, setContent] = useState<any>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [sectionProgress, setSectionProgress] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [timeSpent, setTimeSpent] = useState(0);
  const [showHints, setShowHints] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadContent();
  }, [subject, topic, difficulty]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeSpent(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const loadContent = async () => {
    try {
      setLoading(true);
      const data = await aiTutorServiceNew.generatePersonalizedContent(
        subject,
        topic,
        'explanation'
      );
      setContent(data);
    } catch (error) {
      console.error('Failed to load content:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSectionComplete = (index: number) => {
    setSectionProgress(prev => ({ ...prev, [index]: true }));
    
    if (sessionId) {
      aiTutorServiceNew.provideFeedback(sessionId, {
        type: 'progress_check',
        section_completed: index,
        total_sections: content?.content?.sections?.length || 0,
      });
    }

    // Move to next section
    if (index < (content?.content?.sections?.length || 0) - 1) {
      setActiveStep(index + 1);
    } else if (onComplete) {
      onComplete();
    }
  };

  const handlePracticeAttempt = async (sectionIndex: number, answer: any) => {
    if (sessionId) {
      const feedback = await aiTutorServiceNew.provideFeedback(sessionId, {
        type: 'question_attempt',
        question: content.content.sections[sectionIndex].practice.question,
        answer,
        is_correct: answer === content.content.sections[sectionIndex].practice.answer,
        time_taken: timeSpent,
        attempt_number: 1,
      });
      
      return feedback;
    }
    return null;
  };

  const renderSection = (section: ContentSection, index: number) => {
    switch (section.type) {
      case 'concept':
        return (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                {section.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {section.content}
              </Typography>
              {section.visual && (
                <Box sx={{ my: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Visual representation: {section.visual}
                  </Typography>
                </Box>
              )}
              {section.interactive && (
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  sx={{ mt: 2 }}
                  onClick={() => window.open('/interactive/' + topic, '_blank')}
                >
                  Launch Interactive Demo
                </Button>
              )}
            </CardContent>
          </Card>
        );

      case 'example':
        return (
          <Card sx={{ mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {section.title}
              </Typography>
              <Typography variant="body1" paragraph>
                {section.content}
              </Typography>
              {section.practice && (
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>Practice Question</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" gutterBottom>
                      {section.practice.question}
                    </Typography>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => setShowHints({ ...showHints, [`${index}_practice`]: true })}
                    >
                      Show Answer
                    </Button>
                    {showHints[`${index}_practice`] && (
                      <Alert severity="success" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          <strong>Answer:</strong> {section.practice.answer}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Explanation:</strong> {section.practice.explanation}
                        </Typography>
                      </Alert>
                    )}
                  </AccordionDetails>
                </Accordion>
              )}
            </CardContent>
          </Card>
        );

      case 'animation':
        return (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <VisibilityIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                {section.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {section.content}
              </Typography>
              <Box sx={{ bgcolor: 'black', p: 2, borderRadius: 1, textAlign: 'center' }}>
                <Typography color="white">
                  Animation: {section.animation_url}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        );

      case 'worked_example':
        return (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <CodeIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Worked Example
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                <strong>Problem:</strong> {section.problem}
              </Typography>
              <List>
                {section.solution_steps?.map((step: any, stepIndex: number) => (
                  <ListItem key={stepIndex}>
                    <ListItemIcon>
                      {sectionProgress[`${index}_${stepIndex}`] ? 
                        <CheckIcon color="success" /> : 
                        <UncheckedIcon />
                      }
                    </ListItemIcon>
                    <ListItemText
                      primary={step.step}
                      secondary={step.result}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        );

      default:
        return (
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="body1">
                {JSON.stringify(section, null, 2)}
              </Typography>
            </CardContent>
          </Card>
        );
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading personalized content...</Typography>
      </Box>
    );
  }

  if (!content) {
    return (
      <Alert severity="error">
        Failed to load content. Please try again.
      </Alert>
    );
  }

  const sections = content.content?.sections || [];
  const metadata = content.metadata || {};
  const completedSections = Object.values(sectionProgress).filter(Boolean).length;
  const progress = (completedSections / sections.length) * 100;

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5">{topic}</Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip label={subject} size="small" />
              <Chip label={difficulty} size="small" color="primary" />
              <Chip 
                icon={<TimerIcon />} 
                label={formatTime(timeSpent)} 
                size="small" 
                color="secondary" 
              />
            </Box>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" color="text.secondary">
              Estimated time: {metadata.estimated_completion_time} min
            </Typography>
            <LinearProgress
              variant="determinate"
              value={progress}
              sx={{ mt: 1, width: 200 }}
            />
          </Box>
        </Box>
      </Paper>

      {/* Learning Objectives */}
      {metadata.skills_targeted && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Skills you'll develop:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {metadata.skills_targeted.map((skill: string, index: number) => (
              <Chip key={index} label={skill} size="small" variant="outlined" />
            ))}
          </Box>
        </Alert>
      )}

      {/* Content Sections */}
      <Stepper activeStep={activeStep} orientation="vertical">
        {sections.map((section: ContentSection, index: number) => (
          <Step key={index}>
            <StepLabel>
              Section {index + 1}: {section.title || section.type}
            </StepLabel>
            <StepContent>
              {renderSection(section, index)}
              <Box sx={{ mb: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => handleSectionComplete(index)}
                  sx={{ mt: 1, mr: 1 }}
                >
                  {index === sections.length - 1 ? 'Complete' : 'Continue'}
                </Button>
                {index > 0 && (
                  <Button
                    onClick={() => setActiveStep(index - 1)}
                    sx={{ mt: 1, mr: 1 }}
                  >
                    Back
                  </Button>
                )}
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {/* Practice Problems */}
      {content.practice_problems && content.practice_problems.length > 0 && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            <QuizIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Practice Problems
          </Typography>
          <List>
            {content.practice_problems.map((problem: any, index: number) => (
              <ListItem key={index}>
                <ListItemText
                  primary={`Problem ${problem.id}: ${problem.question}`}
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Chip 
                        label={problem.type} 
                        size="small" 
                        sx={{ mr: 1 }} 
                      />
                      <Button
                        size="small"
                        startIcon={<LightbulbIcon />}
                        onClick={() => setShowHints({ ...showHints, [`problem_${index}`]: true })}
                      >
                        Hint
                      </Button>
                      {showHints[`problem_${index}`] && (
                        <Alert severity="info" sx={{ mt: 1 }}>
                          {problem.hints?.[0] || 'Think about the concepts we just learned.'}
                        </Alert>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      )}

      {/* Adaptive Features Notice */}
      {content.adaptive_features && (
        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="subtitle2">
            This content adapts to your learning style!
          </Typography>
          <Typography variant="body2">
            Features: Hints • Real-time feedback • Progress tracking • Difficulty adjustment
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default PersonalizedContentViewer;