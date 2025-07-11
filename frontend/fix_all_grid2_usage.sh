#!/bin/bash

# Function to replace Grid2 with GridContainer and Box
replace_grid2() {
    local file=$1
    echo "Processing $file..."
    
    # Replace Grid2 container with GridContainer
    sed -i 's/<Grid2 container/<GridContainer/g' "$file"
    sed -i 's/<Grid2/<Box/g' "$file"
    sed -i 's/<\/Grid2>/<\/Box>/g' "$file"
    sed -i 's/<\/Grid2>/<\/GridContainer>/g' "$file"
    
    # Fix closing tags for GridContainer
    sed -i 's/<GridContainer\([^>]*\)>/<GridContainer\1>/g' "$file"
    sed -i 's/<\/Box>\([^<]*\)<\/GridContainer>/<\/GridContainer>/g' "$file"
}

# List of files that use Grid2
files=(
    "src/pages/student/AILearningDashboard.tsx"
    "src/pages/student/AITutor.tsx"
    "src/pages/student/Achievements.tsx"
    "src/pages/student/Character.tsx"
    "src/pages/student/Friends.tsx"
    "src/pages/student/Leaderboard.tsx"
    "src/pages/student/QuestDetail.tsx"
    "src/pages/student/QuestList.tsx"
    "src/pages/student/SocialHub.tsx"
    "src/pages/parent/ChildMonitoring.tsx"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        replace_grid2 "$file"
    fi
done

echo "Grid2 replacement completed!"