#!/bin/bash

# Grid2 import를 제거하고 GridContainer import 추가
files=(
  "src/pages/student/AILearningDashboard.tsx"
  "src/pages/student/Achievements.tsx"
  "src/components/ai-tutor/GrowthRoadmapViewer.tsx"
  "src/pages/student/Leaderboard.tsx"
  "src/pages/student/Character.tsx"
  "src/pages/student/Friends.tsx"
  "src/pages/student/SocialHub.tsx"
  "src/pages/student/QuestList.tsx"
  "src/pages/student/QuestDetail.tsx"
  "src/pages/student/Dashboard.tsx"
  "src/pages/student/AITutor.tsx"
  "src/pages/ProfilePage.tsx"
  "src/pages/parent/Dashboard.tsx"
  "src/pages/parent/ChildMonitoring.tsx"
  "src/pages/HomePage.tsx"
  "src/pages/CreateCharacterPage.tsx"
  "src/components/quest/QuestListSkeleton.tsx"
  "src/components/learning/LearningProgress.tsx"
)

for file in "${files[@]}"; do
  echo "Processing $file..."
  
  # Grid2 import 라인 제거
  sed -i "/import.*Unstable_Grid2.*from.*@mui\/material/d" "$file"
  
  # layout import 추가 (이미 있는지 확인)
  if ! grep -q "from '.*\/components\/layout'" "$file"; then
    # 다른 import 문 다음에 추가
    sed -i "/^import.*from/a\\import { GridContainer, FlexContainer, FlexRow } from '../components/layout';" "$file"
  fi
done

echo "Grid2 import removal completed!"