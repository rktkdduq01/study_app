import React, { useRef, useState, useEffect } from 'react';
import {
  Box,
  IconButton,
  Slider,
  Typography,
  Paper,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  VolumeOff,
  Fullscreen,
  FullscreenExit,
  Speed,
  Subtitles,
  Settings,
  Replay10,
  Forward10,
} from '@mui/icons-material';
import { SubtitleTrack } from '../../../types/learning';

interface VideoPlayerProps {
  videoUrl: string;
  subtitles?: SubtitleTrack[];
  onComplete: () => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  videoUrl,
  subtitles = [],
  onComplete,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showControls, setShowControls] = useState(true);
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const updateDuration = () => setDuration(video.duration);
    const handleEnded = () => {
      setPlaying(false);
      onComplete();
    };

    video.addEventListener('timeupdate', updateTime);
    video.addEventListener('loadedmetadata', updateDuration);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('timeupdate', updateTime);
      video.removeEventListener('loadedmetadata', updateDuration);
      video.removeEventListener('ended', handleEnded);
    };
  }, [onComplete]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setPlaying(!playing);
    }
  };

  const handleVolumeChange = (event: Event, newValue: number | number[]) => {
    const volumeValue = newValue as number;
    setVolume(volumeValue);
    if (videoRef.current) {
      videoRef.current.volume = volumeValue;
    }
    setMuted(volumeValue === 0);
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !muted;
      setMuted(!muted);
    }
  };

  const handleSeek = (event: Event, newValue: number | number[]) => {
    const time = newValue as number;
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const skip = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const changePlaybackRate = (rate: number) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
    setSettingsAnchor(null);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        position: 'relative',
        width: '100%',
        backgroundColor: 'black',
        borderRadius: 2,
        overflow: 'hidden',
      }}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={videoUrl}
        style={{
          width: '100%',
          height: 'auto',
          display: 'block',
        }}
        onClick={togglePlay}
      >
        {subtitles.map((track, index) => (
          <track
            key={index}
            kind="subtitles"
            src={track.url}
            srcLang={track.language}
            label={track.label}
            default={index === 0}
          />
        ))}
      </video>

      {/* Video Controls */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)',
          opacity: showControls ? 1 : 0,
          transition: 'opacity 0.3s',
        }}
      >
        {/* Progress Bar */}
        <Slider
          value={currentTime}
          max={duration}
          onChange={handleSeek}
          sx={{ mb: 1 }}
          size="small"
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Play/Pause */}
          <IconButton onClick={togglePlay} sx={{ color: 'white' }}>
            {playing ? <Pause /> : <PlayArrow />}
          </IconButton>

          {/* Skip buttons */}
          <IconButton onClick={() => skip(-10)} sx={{ color: 'white' }}>
            <Replay10 />
          </IconButton>
          <IconButton onClick={() => skip(10)} sx={{ color: 'white' }}>
            <Forward10 />
          </IconButton>

          {/* Time display */}
          <Typography variant="body2" sx={{ color: 'white', mx: 1 }}>
            {formatTime(currentTime)} / {formatTime(duration)}
          </Typography>

          <Box sx={{ flex: 1 }} />

          {/* Volume */}
          <IconButton onClick={toggleMute} sx={{ color: 'white' }}>
            {muted ? <VolumeOff /> : <VolumeUp />}
          </IconButton>
          <Slider
            value={muted ? 0 : volume}
            onChange={handleVolumeChange}
            sx={{ width: 100, color: 'white' }}
            size="small"
          />

          {/* Settings */}
          <IconButton
            onClick={(e) => setSettingsAnchor(e.currentTarget)}
            sx={{ color: 'white' }}
          >
            <Settings />
          </IconButton>

          {/* Fullscreen */}
          <IconButton onClick={toggleFullscreen} sx={{ color: 'white' }}>
            {isFullscreen ? <FullscreenExit /> : <Fullscreen />}
          </IconButton>
        </Box>
      </Paper>

      {/* Settings Menu */}
      <Menu
        anchorEl={settingsAnchor}
        open={Boolean(settingsAnchor)}
        onClose={() => setSettingsAnchor(null)}
      >
        <MenuItem disabled>
          <ListItemIcon>
            <Speed />
          </ListItemIcon>
          <ListItemText>Playback Speed</ListItemText>
        </MenuItem>
        {[0.5, 0.75, 1, 1.25, 1.5, 2].map((rate) => (
          <MenuItem
            key={rate}
            onClick={() => changePlaybackRate(rate)}
            selected={playbackRate === rate}
          >
            <ListItemText inset>{rate}x</ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default VideoPlayer;