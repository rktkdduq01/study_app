#!/bin/bash

# Git Hooks Setup Script
# This script installs git hooks for automated testing and quality checks
# Usage: ./scripts/setup-git-hooks.sh

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up Git hooks...${NC}"

# Check if we're in a git repository
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo -e "${RED}❌ Not a git repository. Please run 'git init' first.${NC}"
    exit 1
fi

# Git hooks directory
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

# Create pre-commit hook
echo -e "${YELLOW}📝 Creating pre-commit hook...${NC}"
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# Pre-commit hook for Quest Education Platform
# Runs automated tests and quality checks before commit

set -e

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Run pre-commit tests
if [ -f "$PROJECT_ROOT/scripts/pre-commit-tests.sh" ]; then
    echo "🔍 Running pre-commit tests..."
    bash "$PROJECT_ROOT/scripts/pre-commit-tests.sh"
else
    echo "⚠️  Pre-commit test script not found, skipping checks"
fi
EOF

# Create pre-push hook
echo -e "${YELLOW}📝 Creating pre-push hook...${NC}"
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash

# Pre-push hook for Quest Education Platform
# Runs comprehensive tests before pushing to remote

set -e

# Get project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "🚀 Running pre-push checks for branch: $BRANCH"

# Run tests based on branch
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "🔴 Pushing to main branch - running full test suite"
    TEST_TYPE="all"
elif [ "$BRANCH" = "develop" ]; then
    echo "🟡 Pushing to develop branch - running core tests"
    TEST_TYPE="backend,frontend"
else
    echo "🟢 Pushing to feature branch - running quick tests"
    TEST_TYPE="backend"
fi

# Run test runner if available
if [ -f "$PROJECT_ROOT/scripts/test-runner.sh" ]; then
    bash "$PROJECT_ROOT/scripts/test-runner.sh" development "$TEST_TYPE"
else
    echo "⚠️  Test runner script not found, skipping tests"
fi

echo "✅ Pre-push checks completed successfully"
EOF

# Create commit-msg hook for commit message validation
echo -e "${YELLOW}📝 Creating commit-msg hook...${NC}"
cat > "$HOOKS_DIR/commit-msg" << 'EOF'
#!/bin/bash

# Commit message hook for Quest Education Platform
# Validates commit message format and content

set -e

# Get commit message file
COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📝 Validating commit message..."

# Check minimum length
if [ ${#COMMIT_MSG} -lt 10 ]; then
    echo -e "${RED}❌ Commit message too short (minimum 10 characters)${NC}"
    echo -e "${YELLOW}Current message: '$COMMIT_MSG'${NC}"
    exit 1
fi

# Check maximum length for first line
FIRST_LINE=$(echo "$COMMIT_MSG" | head -n1)
if [ ${#FIRST_LINE} -gt 72 ]; then
    echo -e "${YELLOW}⚠️  Warning: First line is longer than 72 characters${NC}"
    echo -e "${YELLOW}Consider shortening: '$FIRST_LINE'${NC}"
fi

# Check for conventional commit format (optional but recommended)
if echo "$FIRST_LINE" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+\))?: .+'; then
    echo -e "${GREEN}✅ Conventional commit format detected${NC}"
elif echo "$FIRST_LINE" | grep -qE '^(add|update|remove|fix|improve|refactor): .+'; then
    echo -e "${GREEN}✅ Descriptive commit format detected${NC}"
else
    echo -e "${YELLOW}💡 Tip: Consider using conventional commit format:${NC}"
    echo -e "${YELLOW}  feat: add new feature${NC}"
    echo -e "${YELLOW}  fix: resolve bug${NC}"
    echo -e "${YELLOW}  docs: update documentation${NC}"
    echo -e "${YELLOW}  test: add tests${NC}"
fi

# Check for issue references
if echo "$COMMIT_MSG" | grep -qE '#[0-9]+'; then
    echo -e "${GREEN}✅ Issue reference found${NC}"
fi

# Prevent commits to main branch (optional safety check)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    # Allow if it's a merge commit
    if ! echo "$COMMIT_MSG" | grep -q "^Merge"; then
        echo -e "${RED}❌ Direct commits to main branch are not allowed${NC}"
        echo -e "${YELLOW}Please create a feature branch and use pull requests${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Commit message validation passed${NC}"
EOF

# Create post-commit hook for notifications
echo -e "${YELLOW}📝 Creating post-commit hook...${NC}"
cat > "$HOOKS_DIR/post-commit" << 'EOF'
#!/bin/bash

# Post-commit hook for Quest Education Platform
# Sends notifications and performs post-commit tasks

# Get commit info
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)
AUTHOR=$(git log -1 --pretty=%an)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "📦 Commit completed:"
echo "  Hash: $COMMIT_HASH"
echo "  Branch: $BRANCH"
echo "  Author: $AUTHOR"
echo "  Message: $(echo "$COMMIT_MSG" | head -n1)"

# Optional: Send to webhook or notification service
# curl -X POST "$WEBHOOK_URL" -d "{\"commit\": \"$COMMIT_HASH\", \"branch\": \"$BRANCH\"}"
EOF

# Create pre-rebase hook
echo -e "${YELLOW}📝 Creating pre-rebase hook...${NC}"
cat > "$HOOKS_DIR/pre-rebase" << 'EOF'
#!/bin/bash

# Pre-rebase hook for Quest Education Platform
# Prevents rebasing of published commits

# Get the branch being rebased
BRANCH="$1"
COMMIT="$2"

# Prevent rebasing commits that have been pushed to origin
if [ -n "$COMMIT" ]; then
    # Check if commit exists on origin
    if git merge-base --is-ancestor "$COMMIT" origin/"$BRANCH" 2>/dev/null; then
        echo "❌ Cannot rebase published commits"
        echo "The commit $COMMIT has already been pushed to origin"
        echo "Use 'git revert' instead of rebase for published commits"
        exit 1
    fi
fi

echo "✅ Pre-rebase check passed"
EOF

# Make all hooks executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-push"
chmod +x "$HOOKS_DIR/commit-msg"
chmod +x "$HOOKS_DIR/post-commit"
chmod +x "$HOOKS_DIR/pre-rebase"

# Make our test scripts executable too
chmod +x "$PROJECT_ROOT/scripts/pre-commit-tests.sh"
if [ -f "$PROJECT_ROOT/scripts/test-runner.sh" ]; then
    chmod +x "$PROJECT_ROOT/scripts/test-runner.sh"
fi

echo -e "\n${GREEN}✅ Git hooks installed successfully!${NC}"
echo -e "\n${BLUE}📋 Installed hooks:${NC}"
echo -e "  ${GREEN}✓${NC} pre-commit: Runs code quality checks"
echo -e "  ${GREEN}✓${NC} pre-push: Runs tests before push"
echo -e "  ${GREEN}✓${NC} commit-msg: Validates commit messages"
echo -e "  ${GREEN}✓${NC} post-commit: Shows commit info"
echo -e "  ${GREEN}✓${NC} pre-rebase: Prevents rebasing published commits"

echo -e "\n${YELLOW}💡 Tips:${NC}"
echo -e "  • Run 'git commit -m \"message\" --no-verify' to skip pre-commit checks"
echo -e "  • Run 'git push --no-verify' to skip pre-push checks"
echo -e "  • Use conventional commit format for better changelog generation"
echo -e "  • Reference issue numbers in commit messages (e.g., 'fixes #123')"

echo -e "\n${BLUE}🧪 Test the hooks:${NC}"
echo -e "  1. Make a small change to a file"
echo -e "  2. Run 'git add .' and 'git commit -m \"test: testing git hooks\"'"
echo -e "  3. The pre-commit hook should run automatically"

# Optional: Create a .gitmessage template
echo -e "\n${YELLOW}📝 Creating git commit message template...${NC}"
cat > "$PROJECT_ROOT/.gitmessage" << 'EOF'
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Type should be one of the following:
# * feat: A new feature
# * fix: A bug fix
# * docs: Documentation only changes
# * style: Changes that do not affect the meaning of the code
# * refactor: A code change that neither fixes a bug nor adds a feature
# * perf: A code change that improves performance
# * test: Adding missing tests or correcting existing tests
# * chore: Changes to the build process or auxiliary tools
#
# Scope: Optional, indicates the scope of the change (e.g., auth, api, ui)
# Subject: Brief description of the change (50 chars or less)
# Body: Detailed description of the change
# Footer: Breaking changes, issue references (e.g., "Closes #123")
EOF

# Set the commit template
git config commit.template .gitmessage

echo -e "${GREEN}✅ Git commit message template created and configured${NC}"
echo -e "\n${BLUE}🎉 Git hooks setup completed successfully!${NC}"