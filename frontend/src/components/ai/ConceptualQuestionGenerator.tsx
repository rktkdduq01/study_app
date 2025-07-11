import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Tooltip,
  LinearProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  Avatar,
  Fade,
  Grow,
} from '@mui/material';
import {
  Psychology,
  Lightbulb,
  School,
  TipsAndUpdates,
  Extension,
  CheckCircle,
  Warning,
  Info,
  NavigateNext,
  ExpandMore,
  ExpandLess,
  AutoAwesome,
  Insights,
  Timeline,
  EmojiObjects,
  MenuBook,
  QuestionAnswer,
  VideoLibrary,
  Draw,
  Games,
  Group,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { 
  ConceptLevel, 
  AIGeneratedQuestion,
  ConceptExplanation,
  ScaffoldingStep,
  AdaptiveHint,
  VisualAid,
} from '../../types/ai-learning';
import aiLearningService from '../../services/aiLearningService';
import ConceptVisualization from './ConceptVisualization';
import AdaptiveQuestionInterface from './AdaptiveQuestionInterface';

interface ConceptualQuestionGeneratorProps {
  subject: string;
  topic: string;
  onComplete: (mastery: number) => void;
}

const ConceptualQuestionGenerator: React.FC<ConceptualQuestionGeneratorProps> = ({
  subject,
  topic,
  onComplete,
}) => {
  const { user } = useAppSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState<AIGeneratedQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [conceptLevel, setConceptLevel] = useState<ConceptLevel>(ConceptLevel.INTRODUCTION);
  const [showConceptExplanation, setShowConceptExplanation] = useState(true);
  const [activeTab, setActiveTab] = useState(0);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const [conceptMastery, setConceptMastery] = useState(0);
  const [showScaffolding, setShowScaffolding] = useState(false);
  const [currentScaffoldStep, setCurrentScaffoldStep] = useState(0);

  const currentQuestion = questions[currentQuestionIndex];

  useEffect(() => {
    if (user) {
      loadConceptualQuestions();
    }
  }, [user, subject, topic, conceptLevel]);

  const loadConceptualQuestions = async () => {
    try {
      setLoading(true);
      const generatedQuestions = await aiLearningService.generateConceptualQuestions(
        user!.id.toString(),
        subject,
        topic,
        conceptLevel
      );
      setQuestions(generatedQuestions);
    } catch (error) {
      console.error('Failed to generate questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async (correct: boolean, answer: any) => {
    // Update mastery based on performance
    const masteryIncrease = correct ? 15 : 5;
    const newMastery = Math.min(conceptMastery + masteryIncrease, 100);
    setConceptMastery(newMastery);

    if (correct && currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setShowConceptExplanation(true);
      setCurrentScaffoldStep(0);
    } else if (correct && currentQuestionIndex === questions.length - 1) {
      // Move to next concept level
      if (conceptLevel !== ConceptLevel.EVALUATION && newMastery >= 80) {
        moveToNextLevel();
      } else {
        onComplete(newMastery);
      }
    }
  };

  const moveToNextLevel = () => {
    const levels = Object.values(ConceptLevel);
    const currentIndex = levels.indexOf(conceptLevel);
    if (currentIndex < levels.length - 1) {
      setConceptLevel(levels[currentIndex + 1]);
      setCurrentQuestionIndex(0);
      setShowConceptExplanation(true);
    }
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const renderConceptExplanation = (explanation: ConceptExplanation) => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiObjects color="primary" />
          Understanding the Concept
        </Typography>
        
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {explanation.mainIdea}
          </Typography>
        </Alert>

        {/* Concept Breakdown */}
        <Box sx={{ mb: 3 }}>
          <Button
            onClick={() => toggleSection('breakdown')}
            endIcon={expandedSections.has('breakdown') ? <ExpandLess /> : <ExpandMore />}
            sx={{ mb: 1 }}
          >
            Concept Parts
          </Button>
          <Collapse in={expandedSections.has('breakdown')}>
            <List>
              {explanation.breakdown.map((part, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <Avatar sx={{ 
                      bgcolor: part.importance === 'core' ? 'primary.main' : 'grey.500',
                      width: 32,
                      height: 32,
                    }}>
                      {index + 1}
                    </Avatar>
                  </ListItemIcon>
                  <ListItemText
                    primary={part.part}
                    secondary={part.explanation}
                  />
                  {part.importance === 'core' && (
                    <Chip label="Core" size="small" color="primary" />
                  )}
                </ListItem>
              ))}
            </List>
          </Collapse>
        </Box>

        {/* Analogies */}
        <Box sx={{ mb: 3 }}>
          <Button
            onClick={() => toggleSection('analogies')}
            endIcon={expandedSections.has('analogies') ? <ExpandLess /> : <ExpandMore />}
            sx={{ mb: 1 }}
          >
            Real-World Connections
          </Button>
          <Collapse in={expandedSections.has('analogies')}>
            {explanation.analogies.map((analogy, index) => (
              <Card key={index} sx={{ mb: 1, bgcolor: 'primary.light' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    {analogy.concept} is like {analogy.analogyTo}
                  </Typography>
                  <Typography variant="body2">
                    {analogy.explanation}
                  </Typography>
                  {analogy.limitations && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      <Typography variant="caption">
                        Remember: {analogy.limitations}
                      </Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            ))}
          </Collapse>
        </Box>

        {/* Common Misconceptions */}
        <Box>
          <Button
            onClick={() => toggleSection('misconceptions')}
            endIcon={expandedSections.has('misconceptions') ? <ExpandLess /> : <ExpandMore />}
            sx={{ mb: 1 }}
            color="warning"
          >
            Common Mistakes to Avoid
          </Button>
          <Collapse in={expandedSections.has('misconceptions')}>
            {explanation.commonMisconceptions.map((misconception, index) => (
              <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  ❌ {misconception.description}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Why this happens: {misconception.whyItHappens}
                </Typography>
                <Typography variant="body2" color="success.main">
                  ✓ {misconception.correction}
                </Typography>
              </Alert>
            ))}
          </Collapse>
        </Box>
      </CardContent>
    </Card>
  );

  const renderScaffolding = (steps: ScaffoldingStep[]) => (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Psychology color="secondary" />
        Step-by-Step Guide
      </Typography>
      
      <Stepper activeStep={currentScaffoldStep} orientation="vertical">
        {steps.map((step, index) => (
          <Step key={index}>
            <StepLabel>
              {step.type === 'guided_discovery' && 'Discover'}
              {step.type === 'worked_example' && 'Example'}
              {step.type === 'partial_solution' && 'Try'}
              {step.type === 'conceptual_bridge' && 'Connect'}
            </StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                {step.content}
              </Typography>
              <Button
                variant="contained"
                size="small"
                onClick={() => setCurrentScaffoldStep(currentScaffoldStep + 1)}
                disabled={currentScaffoldStep !== index}
              >
                {index === steps.length - 1 ? 'Start Problem' : 'Continue'}
              </Button>
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Box>
  );

  const renderVisualAids = (aids: VisualAid[]) => (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Draw color="info" />
        Visual Learning
      </Typography>
      
      <Tabs value={activeTab} onChange={(_, value) => setActiveTab(value)}>
        {aids.map((aid, index) => (
          <Tab 
            key={index} 
            label={aid.type} 
            icon={
              aid.type === 'diagram' ? <Draw /> :
              aid.type === 'animation' ? <VideoLibrary /> :
              aid.type === 'interactive' ? <Games /> :
              <Info />
            }
          />
        ))}
      </Tabs>
      
      {aids.map((aid, index) => (
        <Box key={index} hidden={activeTab !== index} sx={{ mt: 2 }}>
          <ConceptVisualization visualAid={aid} />
        </Box>
      ))}
    </Box>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Creating personalized questions...
        </Typography>
      </Box>
    );
  }

  if (!currentQuestion) {
    return <Alert severity="error">No questions available</Alert>;
  }

  return (
    <Box>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" gutterBottom>
              {topic} - {conceptLevel.replace('_', ' ').toUpperCase()}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip 
                icon={<School />} 
                label={subject} 
                size="small" 
              />
              <Chip 
                icon={<Timeline />} 
                label={`Question ${currentQuestionIndex + 1} of ${questions.length}`} 
                size="small" 
              />
              <Chip 
                icon={<Insights />} 
                label={`${conceptMastery}% Mastery`} 
                size="small" 
                color={conceptMastery >= 80 ? 'success' : 'default'}
              />
            </Box>
          </Box>
          
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Concept Progress
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={conceptMastery} 
              sx={{ width: 200, height: 8, borderRadius: 4 }}
              color={conceptMastery >= 80 ? 'success' : 'primary'}
            />
          </Box>
        </Box>
      </Paper>

      {/* Concept Explanation */}
      {showConceptExplanation && currentQuestion.conceptExplanation && (
        <Fade in={showConceptExplanation}>
          <Box>
            {renderConceptExplanation(currentQuestion.conceptExplanation)}
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <Button
                variant="contained"
                onClick={() => {
                  setShowConceptExplanation(false);
                  setShowScaffolding(true);
                }}
                endIcon={<NavigateNext />}
              >
                I'm Ready to Practice
              </Button>
            </Box>
          </Box>
        </Fade>
      )}

      {/* Scaffolding */}
      {showScaffolding && !showConceptExplanation && currentQuestion.scaffolding.length > 0 && (
        <Grow in={showScaffolding}>
          <Box>
            {renderScaffolding(currentQuestion.scaffolding)}
            {currentScaffoldStep >= currentQuestion.scaffolding.length && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => setShowScaffolding(false)}
                  endIcon={<NavigateNext />}
                >
                  Start Problem
                </Button>
              </Box>
            )}
          </Box>
        </Grow>
      )}

      {/* Visual Aids */}
      {!showConceptExplanation && !showScaffolding && currentQuestion.visualAids && (
        renderVisualAids(currentQuestion.visualAids)
      )}

      {/* Question Interface */}
      {!showConceptExplanation && !showScaffolding && (
        <AdaptiveQuestionInterface
          question={currentQuestion}
          onAnswerSubmit={handleAnswerSubmit}
          studentId={user!.id.toString()}
        />
      )}

      {/* Real World Example */}
      {!showConceptExplanation && !showScaffolding && currentQuestion.realWorldExample && (
        <Card sx={{ mt: 3, bgcolor: 'info.light' }}>
          <CardContent>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Lightbulb />
              Real World Connection
            </Typography>
            <Typography variant="body2">
              {currentQuestion.realWorldExample}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ConceptualQuestionGenerator;