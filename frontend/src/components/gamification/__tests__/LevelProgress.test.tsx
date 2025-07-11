import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LevelProgress from '../LevelProgress';

describe('LevelProgress', () => {
  const defaultProps = {
    currentLevel: 5,
    currentExp: 250,
    expToNextLevel: 500,
    totalExp: 1250
  };

  it('should render level information', () => {
    render(<LevelProgress {...defaultProps} />);

    expect(screen.getByText(/레벨 5/i)).toBeInTheDocument();
    expect(screen.getByText(/250 \/ 500 XP/i)).toBeInTheDocument();
  });

  it('should show correct progress percentage', () => {
    render(<LevelProgress {...defaultProps} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    expect(progressBar).toHaveStyle({ width: '50%' });
  });

  it('should show 0% progress when no experience', () => {
    render(
      <LevelProgress
        currentLevel={1}
        currentExp={0}
        expToNextLevel={100}
        totalExp={0}
      />
    );

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '0');
  });

  it('should show 100% progress when at level threshold', () => {
    render(
      <LevelProgress
        currentLevel={5}
        currentExp={500}
        expToNextLevel={500}
        totalExp={1500}
      />
    );

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '100');
  });

  it('should display total experience on hover', async () => {
    const user = userEvent.setup();
    render(<LevelProgress {...defaultProps} />);

    const container = screen.getByTestId('level-progress-container');
    
    await user.hover(container);
    
    expect(await screen.findByText(/총 경험치: 1,250/i)).toBeInTheDocument();
  });

  it('should apply compact styling when specified', () => {
    render(<LevelProgress {...defaultProps} compact />);

    const container = screen.getByTestId('level-progress-container');
    expect(container).toHaveClass('compact');
  });

  it('should show level up animation when level increases', () => {
    const { rerender } = render(<LevelProgress {...defaultProps} />);

    rerender(
      <LevelProgress
        currentLevel={6}
        currentExp={0}
        expToNextLevel={600}
        totalExp={1500}
      />
    );

    const levelUpAnimation = screen.getByTestId('level-up-animation');
    expect(levelUpAnimation).toBeInTheDocument();
  });

  it('should format large numbers correctly', () => {
    render(
      <LevelProgress
        currentLevel={50}
        currentExp={12500}
        expToNextLevel={50000}
        totalExp={1250000}
      />
    );

    expect(screen.getByText(/12,500 \/ 50,000 XP/i)).toBeInTheDocument();
  });

  it('should show different color themes based on level', () => {
    const { rerender } = render(
      <LevelProgress
        currentLevel={1}
        currentExp={50}
        expToNextLevel={100}
        totalExp={50}
      />
    );

    let progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('level-beginner');

    rerender(
      <LevelProgress
        currentLevel={10}
        currentExp={500}
        expToNextLevel={1000}
        totalExp={5000}
      />
    );

    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('level-intermediate');

    rerender(
      <LevelProgress
        currentLevel={30}
        currentExp={1500}
        expToNextLevel={3000}
        totalExp={45000}
      />
    );

    progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveClass('level-advanced');
  });

  it('should show milestone indicators', () => {
    render(
      <LevelProgress
        currentLevel={9}
        currentExp={900}
        expToNextLevel={1000}
        totalExp={4900}
        showMilestones
      />
    );

    // Should show milestone indicator for level 10
    expect(screen.getByText(/다음 마일스톤: 레벨 10/i)).toBeInTheDocument();
  });

  it('should handle subject-specific progress', () => {
    render(
      <LevelProgress
        currentLevel={5}
        currentExp={250}
        expToNextLevel={500}
        totalExp={1250}
        subject="math"
      />
    );

    expect(screen.getByText(/수학 레벨 5/i)).toBeInTheDocument();
    expect(screen.getByTestId('math-icon')).toBeInTheDocument();
  });

  it('should show experience gain animation', () => {
    const { rerender } = render(
      <LevelProgress
        currentLevel={5}
        currentExp={250}
        expToNextLevel={500}
        totalExp={1250}
      />
    );

    rerender(
      <LevelProgress
        currentLevel={5}
        currentExp={350}
        expToNextLevel={500}
        totalExp={1350}
        expGained={100}
      />
    );

    expect(screen.getByText(/\+100 XP/i)).toBeInTheDocument();
    expect(screen.getByTestId('exp-gain-animation')).toBeInTheDocument();
  });
});