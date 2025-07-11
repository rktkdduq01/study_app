import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormHelperText,
  Chip,
  Stack,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
  Divider
} from '@mui/material';
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Publish as PublishIcon,
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  History as HistoryIcon,
  ContentCopy as CopyIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import { cmsService } from '../../services/cms';

interface ContentFormData {
  title: string;
  description: string;
  content_type: string;
  subject_id: number | '';
  difficulty_level: string;
  estimated_duration: number | '';
  learning_objectives: string[];
  prerequisites: number[];
  tags: string[];
  body: string;
  is_premium: boolean;
  slug: string;
  metadata: Record<string, any>;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`content-tabpanel-${index}`}
      aria-labelledby={`content-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

export const ContentEditor: React.FC = () => {
  const { contentId } = useParams<{ contentId?: string }>();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state: RootState) => state.auth);
  
  const [formData, setFormData] = useState<ContentFormData>({
    title: '',
    description: '',
    content_type: 'lesson',
    subject_id: '',
    difficulty_level: 'beginner',
    estimated_duration: '',
    learning_objectives: [],
    prerequisites: [],
    tags: [],
    body: '',
    is_premium: false,
    slug: '',
    metadata: {}
  });
  
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [publishDialogOpen, setPublishDialogOpen] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [newObjective, setNewObjective] = useState('');
  const [newTag, setNewTag] = useState('');
  const [versions, setVersions] = useState<any[]>([]);
  const [showVersions, setShowVersions] = useState(false);
  
  const isEditing = Boolean(contentId);
  const contentTypes = [
    { value: 'lesson', label: 'Lesson' },
    { value: 'quiz', label: 'Quiz' },
    { value: 'exercise', label: 'Exercise' },
    { value: 'video', label: 'Video' },
    { value: 'article', label: 'Article' },
    { value: 'interactive', label: 'Interactive' },
    { value: 'game', label: 'Game' },
    { value: 'assessment', label: 'Assessment' }
  ];
  
  const difficultyLevels = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
    { value: 'expert', label: 'Expert' }
  ];
  
  useEffect(() => {
    loadInitialData();
  }, [contentId]);
  
  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load subjects
      const subjectsResponse = await cmsService.getSubjects();
      setSubjects(subjectsResponse.data);
      
      // Load templates for current content type
      const templatesResponse = await cmsService.getTemplates({ 
        content_type: formData.content_type 
      });
      setTemplates(templatesResponse.items);
      
      // Load content if editing
      if (isEditing && contentId) {
        const content = await cmsService.getContent(parseInt(contentId));
        setFormData({
          title: content.title,
          description: content.description || '',
          content_type: content.content_type,
          subject_id: content.subject_id,
          difficulty_level: content.difficulty_level,
          estimated_duration: content.estimated_duration || '',
          learning_objectives: content.learning_objectives || [],
          prerequisites: content.prerequisites || [],
          tags: content.tags || [],
          body: content.body || '',
          is_premium: content.is_premium,
          slug: content.slug,
          metadata: content.metadata || {}
        });
        
        // Load versions
        const versionsResponse = await cmsService.getContentVersions(parseInt(contentId));
        setVersions(versionsResponse.data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };
  
  const handleInputChange = (field: keyof ContentFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Auto-generate slug from title
    if (field === 'title' && !isEditing) {
      const slug = value.toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-');
      setFormData(prev => ({
        ...prev,
        slug
      }));
    }
  };
  
  const handleAddObjective = () => {
    if (newObjective.trim()) {
      setFormData(prev => ({
        ...prev,
        learning_objectives: [...prev.learning_objectives, newObjective.trim()]
      }));
      setNewObjective('');
    }
  };
  
  const handleRemoveObjective = (index: number) => {
    setFormData(prev => ({
      ...prev,
      learning_objectives: prev.learning_objectives.filter((_, i) => i !== index)
    }));
  };
  
  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };
  
  const handleRemoveTag = (tagToRemove: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };
  
  const handleTemplateSelect = async (template: any) => {
    try {
      const variables = await cmsService.getTemplateVariables(template.id);
      // For demo, we'll just use the template body
      const preview = await cmsService.previewTemplate(template.id, {
        title: formData.title || 'Sample Title',
        content: 'Sample content...'
      });
      
      setFormData(prev => ({
        ...prev,
        body: preview.rendered,
        metadata: { ...prev.metadata, template_id: template.id }
      }));
      setSelectedTemplate(template);
    } catch (err: any) {
      setError(err.message || 'Failed to load template');
    }
  };
  
  const handleSave = async (isDraft = true) => {
    try {
      setSaving(true);
      setError(null);
      
      const payload = {
        ...formData,
        subject_id: Number(formData.subject_id),
        estimated_duration: formData.estimated_duration ? Number(formData.estimated_duration) : undefined
      };
      
      if (isEditing && contentId) {
        await cmsService.updateContent(parseInt(contentId), payload);
        setSuccess('Content updated successfully');
      } else {
        const newContent = await cmsService.createContent(payload);
        setSuccess('Content created successfully');
        navigate(`/cms/content/${newContent.id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save content');
    } finally {
      setSaving(false);
    }
  };
  
  const handlePublish = async () => {
    try {
      setLoading(true);
      
      if (!isEditing || !contentId) {
        throw new Error('Content must be saved before publishing');
      }
      
      await cmsService.publishContent(parseInt(contentId));
      setSuccess('Content published successfully');
      setPublishDialogOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to publish content');
    } finally {
      setLoading(false);
    }
  };
  
  const handlePreview = () => {
    setPreviewOpen(true);
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Box sx={{ maxWidth: '1200px', margin: '0 auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4">
          {isEditing ? 'Edit Content' : 'Create New Content'}
        </Typography>
        
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<PreviewIcon />}
            onClick={handlePreview}
            disabled={!formData.body}
          >
            Preview
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<SaveIcon />}
            onClick={() => handleSave()}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Draft'}
          </Button>
          
          {isEditing && (
            <>
              <Button
                variant="outlined"
                startIcon={<HistoryIcon />}
                onClick={() => setShowVersions(true)}
              >
                Versions
              </Button>
              
              <Button
                variant="contained"
                startIcon={<PublishIcon />}
                onClick={() => setPublishDialogOpen(true)}
                color="primary"
              >
                Publish
              </Button>
            </>
          )}
        </Stack>
      </Box>
      
      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      
      {/* Main Content */}
      <Card>
        <CardContent>
          <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
            <Tab label="Basic Info" />
            <Tab label="Content" />
            <Tab label="Settings" />
            <Tab label="Metadata" />
          </Tabs>
          
          {/* Basic Info Tab */}
          <TabPanel value={currentTab} index={0}>
            <Stack spacing={3}>
              <TextField
                fullWidth
                label="Title"
                value={formData.title}
                onChange={(e) => handleInputChange('title', e.target.value)}
                required
                helperText="Enter a descriptive title for your content"
              />
              
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                multiline
                rows={3}
                helperText="Brief description of what this content covers"
              />
              
              <TextField
                fullWidth
                label="Slug"
                value={formData.slug}
                onChange={(e) => handleInputChange('slug', e.target.value)}
                helperText="URL-friendly identifier (auto-generated from title)"
              />
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControl fullWidth>
                  <InputLabel>Content Type</InputLabel>
                  <Select
                    value={formData.content_type}
                    onChange={(e) => handleInputChange('content_type', e.target.value)}
                  >
                    {contentTypes.map(type => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={formData.subject_id}
                    onChange={(e) => handleInputChange('subject_id', e.target.value)}
                  >
                    {subjects.map(subject => (
                      <MenuItem key={subject.id} value={subject.id}>
                        {subject.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl fullWidth>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={formData.difficulty_level}
                    onChange={(e) => handleInputChange('difficulty_level', e.target.value)}
                  >
                    {difficultyLevels.map(level => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <TextField
                fullWidth
                label="Estimated Duration (minutes)"
                type="number"
                value={formData.estimated_duration}
                onChange={(e) => handleInputChange('estimated_duration', e.target.value)}
                helperText="How long should this content take to complete?"
              />
              
              {/* Learning Objectives */}
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Learning Objectives
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField
                    fullWidth
                    size="small"
                    placeholder="Add learning objective"
                    value={newObjective}
                    onChange={(e) => setNewObjective(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddObjective()}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={handleAddObjective}
                  >
                    Add
                  </Button>
                </Stack>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {formData.learning_objectives.map((objective, index) => (
                    <Chip
                      key={index}
                      label={objective}
                      onDelete={() => handleRemoveObjective(index)}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
              
              {/* Tags */}
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Tags
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mb: 1 }}>
                  <TextField
                    fullWidth
                    size="small"
                    placeholder="Add tag"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={handleAddTag}
                  >
                    Add
                  </Button>
                </Stack>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {formData.tags.map((tag, index) => (
                    <Chip
                      key={index}
                      label={tag}
                      onDelete={() => handleRemoveTag(tag)}
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
            </Stack>
          </TabPanel>
          
          {/* Content Tab */}
          <TabPanel value={currentTab} index={1}>
            <Stack spacing={3}>
              {/* Template Selection */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>Use Template</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={2}>
                    <Typography variant="body2" color="text.secondary">
                      Select a template to get started with pre-formatted content
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {templates.map(template => (
                        <Button
                          key={template.id}
                          variant={selectedTemplate?.id === template.id ? "contained" : "outlined"}
                          size="small"
                          onClick={() => handleTemplateSelect(template)}
                        >
                          {template.name}
                        </Button>
                      ))}
                    </Box>
                  </Stack>
                </AccordionDetails>
              </Accordion>
              
              {/* Content Body */}
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Content Body
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={20}
                  value={formData.body}
                  onChange={(e) => handleInputChange('body', e.target.value)}
                  placeholder="Enter your content here..."
                  helperText="Use Markdown or HTML for formatting"
                />
              </Box>
            </Stack>
          </TabPanel>
          
          {/* Settings Tab */}
          <TabPanel value={currentTab} index={2}>
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  Content Settings
                </Typography>
                <FormControl component="fieldset">
                  <Stack spacing={2}>
                    <Box>
                      <input
                        type="checkbox"
                        id="is_premium"
                        checked={formData.is_premium}
                        onChange={(e) => handleInputChange('is_premium', e.target.checked)}
                      />
                      <label htmlFor="is_premium" style={{ marginLeft: '8px' }}>
                        Premium Content
                      </label>
                    </Box>
                  </Stack>
                </FormControl>
              </Box>
            </Stack>
          </TabPanel>
          
          {/* Metadata Tab */}
          <TabPanel value={currentTab} index={3}>
            <Stack spacing={3}>
              <Typography variant="subtitle1">
                Additional Metadata
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={10}
                value={JSON.stringify(formData.metadata, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    handleInputChange('metadata', parsed);
                  } catch (err) {
                    // Invalid JSON, don't update
                  }
                }}
                placeholder="Enter metadata as JSON"
                helperText="Additional structured data for this content"
              />
            </Stack>
          </TabPanel>
        </CardContent>
      </Card>
      
      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Content Preview</DialogTitle>
        <DialogContent>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h4" gutterBottom>
              {formData.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {formData.description}
            </Typography>
            <Divider sx={{ my: 2 }} />
            <div dangerouslySetInnerHTML={{ __html: formData.body }} />
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Publish Dialog */}
      <Dialog
        open={publishDialogOpen}
        onClose={() => setPublishDialogOpen(false)}
      >
        <DialogTitle>Publish Content</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to publish this content? Once published, it will be visible to all users.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPublishDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handlePublish}
            variant="contained"
            color="primary"
            disabled={loading}
          >
            {loading ? 'Publishing...' : 'Publish'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};