import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Menu,
  MenuList,
  MenuItem as MenuItemList,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Pagination,
  Skeleton,
  Tooltip,
  Badge,
  Avatar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Publish as PublishIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingIcon,
  Star as StarIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { cmsService, ContentType, SearchFilters } from '../../services/cms';
import { format } from 'date-fns';

const ITEMS_PER_PAGE = 20;

export const ContentList: React.FC = () => {
  const navigate = useNavigate();
  
  const [contents, setContents] = useState<ContentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [selectedContent, setSelectedContent] = useState<ContentType | null>(null);
  const [actionMenuAnchor, setActionMenuAnchor] = useState<HTMLElement | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [subjects, setSubjects] = useState<any[]>([]);
  
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
  
  const statusOptions = [
    { value: 'draft', label: 'Draft', color: 'default' },
    { value: 'review', label: 'Review', color: 'warning' },
    { value: 'published', label: 'Published', color: 'success' },
    { value: 'archived', label: 'Archived', color: 'error' }
  ];
  
  const difficultyOptions = [
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' },
    { value: 'expert', label: 'Expert' }
  ];
  
  useEffect(() => {
    loadContents();
    loadSubjects();
  }, [page, searchQuery, filters]);
  
  const loadContents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await cmsService.searchContent(
        searchQuery,
        filters,
        ITEMS_PER_PAGE,
        (page - 1) * ITEMS_PER_PAGE
      );
      
      setContents(response.items);
      setTotalPages(Math.ceil(response.total / ITEMS_PER_PAGE));
    } catch (err: any) {
      setError(err.message || 'Failed to load content');
    } finally {
      setLoading(false);
    }
  };
  
  const loadSubjects = async () => {
    try {
      const response = await cmsService.getSubjects();
      setSubjects(response.data);
    } catch (err) {
      console.error('Failed to load subjects:', err);
    }
  };
  
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1);
  };
  
  const handleFilterChange = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
    setPage(1);
  };
  
  const handleClearFilters = () => {
    setFilters({});
    setSearchQuery('');
    setPage(1);
  };
  
  const handleActionMenuOpen = (event: React.MouseEvent<HTMLElement>, content: ContentType) => {
    setActionMenuAnchor(event.currentTarget);
    setSelectedContent(content);
  };
  
  const handleActionMenuClose = () => {
    setActionMenuAnchor(null);
    setSelectedContent(null);
  };
  
  const handleEdit = (content: ContentType) => {
    navigate(`/cms/content/${content.id}/edit`);
    handleActionMenuClose();
  };
  
  const handleView = (content: ContentType) => {
    navigate(`/cms/content/${content.id}/view`);
    handleActionMenuClose();
  };
  
  const handlePublish = async (content: ContentType) => {
    try {
      await cmsService.publishContent(content.id);
      await loadContents();
    } catch (err: any) {
      setError(err.message || 'Failed to publish content');
    }
    handleActionMenuClose();
  };
  
  const handleDelete = async () => {
    if (!selectedContent) return;
    
    try {
      await cmsService.deleteContent(selectedContent.id);
      await loadContents();
      setDeleteDialogOpen(false);
    } catch (err: any) {
      setError(err.message || 'Failed to delete content');
    }
  };
  
  const getStatusColor = (status: string) => {
    const statusOption = statusOptions.find(opt => opt.value === status);
    return statusOption?.color || 'default';
  };
  
  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMM dd, yyyy');
  };
  
  const getContentTypeIcon = (type: string) => {
    switch (type) {
      case 'lesson': return '📚';
      case 'quiz': return '❓';
      case 'exercise': return '✏️';
      case 'video': return '🎥';
      case 'article': return '📄';
      case 'interactive': return '🎮';
      case 'game': return '🎯';
      case 'assessment': return '📊';
      default: return '📝';
    }
  };
  
  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Content Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/cms/content/create')}
        >
          Create Content
        </Button>
      </Box>
      
      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            {/* Search Bar */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                placeholder="Search content..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'action.active' }} />
                }}
              />
              <Button
                variant="outlined"
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
              >
                Filters
              </Button>
              {(Object.keys(filters).length > 0 || searchQuery) && (
                <Button onClick={handleClearFilters}>
                  Clear All
                </Button>
              )}
            </Box>
            
            {/* Filters */}
            {showFilters && (
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Content Type</InputLabel>
                  <Select
                    value={filters.content_type || ''}
                    onChange={(e) => handleFilterChange('content_type', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    {contentTypes.map(type => (
                      <MenuItem key={type.value} value={type.value}>
                        {type.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status || ''}
                    onChange={(e) => handleFilterChange('status', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    {statusOptions.map(status => (
                      <MenuItem key={status.value} value={status.value}>
                        {status.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={filters.subject_id || ''}
                    onChange={(e) => handleFilterChange('subject_id', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    {subjects.map(subject => (
                      <MenuItem key={subject.id} value={subject.id}>
                        {subject.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={filters.difficulty_level || ''}
                    onChange={(e) => handleFilterChange('difficulty_level', e.target.value)}
                  >
                    <MenuItem value="">All</MenuItem>
                    {difficultyOptions.map(level => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Premium</InputLabel>
                  <Select
                    value={filters.is_premium?.toString() || ''}
                    onChange={(e) => handleFilterChange('is_premium', e.target.value === 'true')}
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="true">Premium</MenuItem>
                    <MenuItem value="false">Free</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>
      
      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {/* Content Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Content</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Views</TableCell>
              <TableCell>Rating</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              // Loading skeleton
              Array.from({ length: 5 }).map((_, index) => (
                <TableRow key={index}>
                  <TableCell><Skeleton width="80%" /></TableCell>
                  <TableCell><Skeleton width="60%" /></TableCell>
                  <TableCell><Skeleton width="50%" /></TableCell>
                  <TableCell><Skeleton width="70%" /></TableCell>
                  <TableCell><Skeleton width="40%" /></TableCell>
                  <TableCell><Skeleton width="50%" /></TableCell>
                  <TableCell><Skeleton width="60%" /></TableCell>
                  <TableCell><Skeleton width="30%" /></TableCell>
                </TableRow>
              ))
            ) : contents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No content found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              contents.map((content) => (
                <TableRow key={content.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {getContentTypeIcon(content.content_type)}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {content.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {content.description}
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                          {content.is_premium && (
                            <Chip label="Premium" size="small" color="primary" />
                          )}
                          {content.is_featured && (
                            <Chip
                              label="Featured"
                              size="small"
                              color="secondary"
                              icon={<StarIcon />}
                            />
                          )}
                        </Stack>
                      </Box>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Chip
                      label={content.content_type}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Chip
                      label={content.status}
                      size="small"
                      color={getStatusColor(content.status) as any}
                      icon={content.status === 'published' ? <CheckCircleIcon /> : <ScheduleIcon />}
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {subjects.find(s => s.id === content.subject_id)?.name || 'Unknown'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TrendingIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {content.view_count.toLocaleString()}
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <StarIcon fontSize="small" color="action" />
                      <Typography variant="body2">
                        {content.average_rating.toFixed(1)} ({content.total_ratings})
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(content.created_at)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <IconButton
                      onClick={(e) => handleActionMenuOpen(e, content)}
                      size="small"
                    >
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      {/* Pagination */}
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={(_, newPage) => setPage(newPage)}
            color="primary"
          />
        </Box>
      )}
      
      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={handleActionMenuClose}
      >
        <MenuItemList onClick={() => selectedContent && handleView(selectedContent)}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View</ListItemText>
        </MenuItemList>
        
        <MenuItemList onClick={() => selectedContent && handleEdit(selectedContent)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItemList>
        
        {selectedContent?.status === 'draft' && (
          <MenuItemList onClick={() => selectedContent && handlePublish(selectedContent)}>
            <ListItemIcon>
              <PublishIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Publish</ListItemText>
          </MenuItemList>
        )}
        
        <MenuItemList
          onClick={() => setDeleteDialogOpen(true)}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItemList>
      </Menu>
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Content</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedContent?.title}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleDelete}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};