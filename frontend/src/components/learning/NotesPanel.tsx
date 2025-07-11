import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Button,
  Chip,
  Tooltip,
  Collapse,
  Alert,
} from '@mui/material';
import {
  Close,
  Add,
  Delete,
  Edit,
  Save,
  Cancel,
  Bookmark,
  Note,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { formatDistanceToNow } from '../../utils/dateUtils';

interface Note {
  id: string;
  text: string;
  timestamp: number;
  createdAt: string;
  bookmarked: boolean;
}

interface NotesPanelProps {
  contentId: string;
  onClose: () => void;
}

const NotesPanel: React.FC<NotesPanelProps> = ({ contentId, onClose }) => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [newNote, setNewNote] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');
  const [showBookmarkedOnly, setShowBookmarkedOnly] = useState(false);
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());

  // Load notes from localStorage
  useEffect(() => {
    const savedNotes = localStorage.getItem(`notes_${contentId}`);
    if (savedNotes) {
      setNotes(JSON.parse(savedNotes));
    }
  }, [contentId]);

  // Save notes to localStorage
  useEffect(() => {
    localStorage.setItem(`notes_${contentId}`, JSON.stringify(notes));
  }, [notes, contentId]);

  const addNote = () => {
    if (newNote.trim()) {
      const note: Note = {
        id: Date.now().toString(),
        text: newNote,
        timestamp: Date.now(),
        createdAt: new Date().toISOString(),
        bookmarked: false,
      };
      setNotes([note, ...notes]);
      setNewNote('');
    }
  };

  const deleteNote = (id: string) => {
    setNotes(notes.filter(note => note.id !== id));
  };

  const startEditing = (note: Note) => {
    setEditingId(note.id);
    setEditText(note.text);
  };

  const saveEdit = () => {
    setNotes(notes.map(note => 
      note.id === editingId 
        ? { ...note, text: editText }
        : note
    ));
    setEditingId(null);
    setEditText('');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditText('');
  };

  const toggleBookmark = (id: string) => {
    setNotes(notes.map(note => 
      note.id === id 
        ? { ...note, bookmarked: !note.bookmarked }
        : note
    ));
  };

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedNotes);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedNotes(newExpanded);
  };

  const filteredNotes = showBookmarkedOnly 
    ? notes.filter(note => note.bookmarked)
    : notes;

  const isNoteExpanded = (note: Note) => {
    return expandedNotes.has(note.id) || note.text.length <= 100;
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Note />
            My Notes
          </Typography>
          <IconButton onClick={onClose} size="small">
            <Close />
          </IconButton>
        </Box>
        
        {/* Filter */}
        <Box sx={{ mt: 1 }}>
          <Chip
            label="All Notes"
            onClick={() => setShowBookmarkedOnly(false)}
            color={!showBookmarkedOnly ? 'primary' : 'default'}
            size="small"
            sx={{ mr: 1 }}
          />
          <Chip
            label="Bookmarked"
            onClick={() => setShowBookmarkedOnly(true)}
            color={showBookmarkedOnly ? 'primary' : 'default'}
            size="small"
            icon={<Bookmark />}
          />
        </Box>
      </Box>

      {/* Add Note */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <TextField
          fullWidth
          multiline
          rows={2}
          placeholder="Add a note..."
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
              addNote();
            }
          }}
          sx={{ mb: 1 }}
        />
        <Button
          fullWidth
          variant="contained"
          startIcon={<Add />}
          onClick={addNote}
          disabled={!newNote.trim()}
        >
          Add Note
        </Button>
      </Box>

      {/* Notes List */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        {filteredNotes.length === 0 ? (
          <Alert severity="info">
            {showBookmarkedOnly 
              ? "No bookmarked notes yet. Bookmark important notes for quick access!"
              : "No notes yet. Start taking notes to remember important points!"
            }
          </Alert>
        ) : (
          <List>
            {filteredNotes.map((note, index) => (
              <React.Fragment key={note.id}>
                {index > 0 && <Divider />}
                <ListItem sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                  {editingId === note.id ? (
                    <Box>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        autoFocus
                      />
                      <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                        <Button
                          size="small"
                          startIcon={<Save />}
                          onClick={saveEdit}
                        >
                          Save
                        </Button>
                        <Button
                          size="small"
                          startIcon={<Cancel />}
                          onClick={cancelEdit}
                        >
                          Cancel
                        </Button>
                      </Box>
                    </Box>
                  ) : (
                    <>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              wordBreak: 'break-word',
                              whiteSpace: 'pre-wrap',
                            }}
                          >
                            {isNoteExpanded(note) 
                              ? note.text 
                              : `${note.text.substring(0, 100)}...`
                            }
                          </Typography>
                          {note.text.length > 100 && (
                            <Button
                              size="small"
                              onClick={() => toggleExpand(note.id)}
                              endIcon={isNoteExpanded(note) ? <ExpandLess /> : <ExpandMore />}
                              sx={{ mt: 0.5 }}
                            >
                              {isNoteExpanded(note) ? 'Show less' : 'Show more'}
                            </Button>
                          )}
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            {formatDistanceToNow(note.createdAt)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', flexDirection: 'column', ml: 1 }}>
                          <Tooltip title={note.bookmarked ? 'Remove bookmark' : 'Bookmark'}>
                            <IconButton
                              size="small"
                              onClick={() => toggleBookmark(note.id)}
                              color={note.bookmarked ? 'primary' : 'inherit'}
                            >
                              <Bookmark />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => startEditing(note)}
                            >
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              onClick={() => deleteNote(note.id)}
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                    </>
                  )}
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        )}
      </Box>

      {/* Summary */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider', bgcolor: 'grey.50' }}>
        <Typography variant="caption" color="text.secondary">
          {notes.length} note{notes.length !== 1 ? 's' : ''} • 
          {notes.filter(n => n.bookmarked).length} bookmarked
        </Typography>
      </Box>
    </Paper>
  );
};

export default NotesPanel;