import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BadgeDisplay from '../BadgeDisplay';
import { Badge, BadgeCategory, BadgeRarity } from '../../../types/gamification';

describe('BadgeDisplay', () => {
  const mockBadges: Badge[] = [
    {
      id: 1,
      name: 'First Steps',
      description: 'Complete your first quest',
      category: BadgeCategory.QUEST,
      rarity: BadgeRarity.COMMON,
      icon_url: '/badges/first-steps.png',
      points: 10,
      unlocked_at: '2024-01-09T12:00:00Z'
    },
    {
      id: 2,
      name: 'Math Novice',
      description: 'Reach level 5 in Math',
      category: BadgeCategory.SUBJECT,
      rarity: BadgeRarity.UNCOMMON,
      icon_url: '/badges/math-novice.png',
      points: 25,
      unlocked_at: '2024-01-10T12:00:00Z'
    },
    {
      id: 3,
      name: 'Week Warrior',
      description: 'Maintain a 7-day streak',
      category: BadgeCategory.STREAK,
      rarity: BadgeRarity.RARE,
      icon_url: '/badges/week-warrior.png',
      points: 50,
      unlocked_at: null // Locked badge
    }
  ];

  it('should render all badges', () => {
    render(<BadgeDisplay badges={mockBadges} />);

    expect(screen.getByText('First Steps')).toBeInTheDocument();
    expect(screen.getByText('Math Novice')).toBeInTheDocument();
    expect(screen.getByText('Week Warrior')).toBeInTheDocument();
  });

  it('should show locked and unlocked states', () => {
    render(<BadgeDisplay badges={mockBadges} />);

    const unlockedBadges = screen.getAllByTestId('badge-unlocked');
    const lockedBadges = screen.getAllByTestId('badge-locked');

    expect(unlockedBadges).toHaveLength(2);
    expect(lockedBadges).toHaveLength(1);
  });

  it('should display badge details on hover', async () => {
    const user = userEvent.setup();
    render(<BadgeDisplay badges={mockBadges} />);

    const firstBadge = screen.getByText('First Steps').closest('[data-testid^="badge-"]');
    
    await user.hover(firstBadge!);

    expect(await screen.findByText('Complete your first quest')).toBeInTheDocument();
    expect(screen.getByText('10 포인트')).toBeInTheDocument();
    expect(screen.getByText(/2024년 1월 9일/i)).toBeInTheDocument();
  });

  it('should show rarity colors', () => {
    render(<BadgeDisplay badges={mockBadges} />);

    const commonBadge = screen.getByText('First Steps').closest('[data-testid^="badge-"]');
    const uncommonBadge = screen.getByText('Math Novice').closest('[data-testid^="badge-"]');
    const rareBadge = screen.getByText('Week Warrior').closest('[data-testid^="badge-"]');

    expect(commonBadge).toHaveClass('rarity-common');
    expect(uncommonBadge).toHaveClass('rarity-uncommon');
    expect(rareBadge).toHaveClass('rarity-rare');
  });

  it('should filter badges by category', async () => {
    const user = userEvent.setup();
    render(<BadgeDisplay badges={mockBadges} showFilters />);

    // Click on QUEST category filter
    const questFilter = screen.getByRole('button', { name: /퀘스트/i });
    await user.click(questFilter);

    // Only quest badges should be visible
    expect(screen.getByText('First Steps')).toBeInTheDocument();
    expect(screen.queryByText('Math Novice')).not.toBeInTheDocument();
    expect(screen.queryByText('Week Warrior')).not.toBeInTheDocument();
  });

  it('should filter badges by unlocked status', async () => {
    const user = userEvent.setup();
    render(<BadgeDisplay badges={mockBadges} showFilters />);

    // Click on "Unlocked" filter
    const unlockedFilter = screen.getByRole('button', { name: /획득한 배지/i });
    await user.click(unlockedFilter);

    // Only unlocked badges should be visible
    expect(screen.getByText('First Steps')).toBeInTheDocument();
    expect(screen.getByText('Math Novice')).toBeInTheDocument();
    expect(screen.queryByText('Week Warrior')).not.toBeInTheDocument();
  });

  it('should show empty state when no badges', () => {
    render(<BadgeDisplay badges={[]} />);

    expect(screen.getByText(/아직 획득한 배지가 없습니다/i)).toBeInTheDocument();
  });

  it('should handle grid and list view modes', async () => {
    const user = userEvent.setup();
    render(<BadgeDisplay badges={mockBadges} showViewToggle />);

    const container = screen.getByTestId('badges-container');
    expect(container).toHaveClass('grid-view');

    // Switch to list view
    const listViewButton = screen.getByRole('button', { name: /리스트 보기/i });
    await user.click(listViewButton);

    expect(container).toHaveClass('list-view');
  });

  it('should show progress for locked badges', () => {
    const badgesWithProgress = [
      {
        ...mockBadges[2],
        progress: 5,
        max_progress: 7
      }
    ];

    render(<BadgeDisplay badges={badgesWithProgress} />);

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '71'); // 5/7 = ~71%
    expect(screen.getByText('5/7')).toBeInTheDocument();
  });

  it('should show badge showcase for featured badges', () => {
    const featuredBadges = mockBadges.slice(0, 2);
    
    render(<BadgeDisplay badges={featuredBadges} showcase />);

    const showcaseContainer = screen.getByTestId('badge-showcase');
    expect(showcaseContainer).toBeInTheDocument();
    expect(showcaseContainer).toHaveClass('showcase');
  });

  it('should handle badge click events', async () => {
    const user = userEvent.setup();
    const onBadgeClick = jest.fn();
    
    render(<BadgeDisplay badges={mockBadges} onBadgeClick={onBadgeClick} />);

    const firstBadge = screen.getByText('First Steps').closest('[data-testid^="badge-"]');
    await user.click(firstBadge!);

    expect(onBadgeClick).toHaveBeenCalledWith(mockBadges[0]);
  });

  it('should sort badges by different criteria', async () => {
    const user = userEvent.setup();
    render(<BadgeDisplay badges={mockBadges} showSort />);

    // Sort by points
    const sortSelect = screen.getByRole('combobox', { name: /정렬/i });
    await user.selectOptions(sortSelect, 'points');

    const badgeNames = screen.getAllByTestId(/^badge-/).map(
      el => el.querySelector('[data-testid="badge-name"]')?.textContent
    );

    expect(badgeNames).toEqual(['Week Warrior', 'Math Novice', 'First Steps']);
  });

  it('should show total badge points', () => {
    render(<BadgeDisplay badges={mockBadges} showStats />);

    const totalPoints = mockBadges
      .filter(b => b.unlocked_at)
      .reduce((sum, b) => sum + b.points, 0);

    expect(screen.getByText(`총 ${totalPoints} 포인트`)).toBeInTheDocument();
    expect(screen.getByText('2/3 배지 획득')).toBeInTheDocument();
  });
});