#!/bin/bash

# Grid2 import를 제거하고 layout import를 추가하는 함수
fix_grid2_import() {
    local file=$1
    echo "Processing $file..."
    
    # Grid2 import 라인 제거
    sed -i "/import.*Unstable_Grid2.*from.*@mui\/material/d" "$file"
    
    # 파일의 상대 경로 깊이 계산
    depth=$(echo "$file" | tr -cd '/' | wc -c)
    depth=$((depth - 1))  # src/ 제외
    
    # 상대 경로 생성
    relative_path=""
    for ((i=0; i<depth; i++)); do
        relative_path="../$relative_path"
    done
    
    # components/layout import 추가 (이미 있는지 확인)
    if ! grep -q "from.*components/layout" "$file"; then
        # 마지막 import 문 다음에 추가
        awk -v path="$relative_path" '
            /^import/ { last_import = NR }
            {
                print
                if (NR == last_import && !done) {
                    print "import { GridContainer, FlexContainer, FlexRow } from \047" path "components/layout\047;"
                    done = 1
                }
            }
        ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
    fi
}

# 파일 목록
files=(
    "src/pages/CreateCharacterPage.tsx"
    "src/pages/HomePage.tsx"
    "src/pages/ProfilePage.tsx"
    "src/pages/parent/ChildMonitoring.tsx"
    "src/pages/student/AILearningDashboard.tsx"
    "src/pages/student/AITutor.tsx"
    "src/pages/student/Achievements.tsx"
    "src/pages/student/Character.tsx"
    "src/pages/student/Friends.tsx"
    "src/pages/student/Leaderboard.tsx"
    "src/pages/student/QuestDetail.tsx"
    "src/pages/student/QuestList.tsx"
    "src/pages/student/SocialHub.tsx"
)

# 각 파일 처리
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        fix_grid2_import "$file"
    else
        echo "File not found: $file"
    fi
done

echo "Grid2 import fixes completed!"