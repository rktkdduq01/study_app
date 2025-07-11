#!/bin/bash

# Encryption Key Rotation Management Script
# Usage: ./scripts/key-rotation.sh [command] [options]
# Example: ./scripts/key-rotation.sh rotate --force
# Example: ./scripts/key-rotation.sh status

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

# Logging
LOG_DIR="$PROJECT_ROOT/logs/security"
mkdir -p "$LOG_DIR"
ROTATION_LOG="$LOG_DIR/key-rotation-$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$ROTATION_LOG"
}

# Command and options
COMMAND=${1:-status}
FORCE_ROTATE=${2:-false}

log "${BLUE}🔐 Key Rotation Management${NC}"
log "${BLUE}Command: $COMMAND${NC}"
log "${BLUE}Log File: $ROTATION_LOG${NC}"

# Load environment
if [ -f "$PROJECT_ROOT/scripts/load-env.sh" ]; then
    source "$PROJECT_ROOT/scripts/load-env.sh" "${ENVIRONMENT:-development}"
fi

# Python script for key operations
run_key_operation() {
    local operation="$1"
    local options="$2"
    
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "venv_backend" ]; then
        source venv_backend/bin/activate
    fi
    
    # Create Python script for key operations
    cat > /tmp/key_rotation_script.py << EOF
import sys
import os
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.getcwd()))

try:
    from app.core.key_rotation import key_manager, encryption_service
    
    def rotate_keys(force=False):
        """Rotate encryption keys"""
        print(f"Starting key rotation (force={force})...")
        
        try:
            rotated_keys = key_manager.rotate_keys(force=force)
            
            if rotated_keys:
                print(f"✅ Successfully rotated {len(rotated_keys)} keys:")
                for key_id in rotated_keys:
                    print(f"  - {key_id}")
            else:
                print("ℹ️  No keys needed rotation")
            
            return True
            
        except Exception as e:
            print(f"❌ Key rotation failed: {e}")
            return False
    
    def cleanup_keys():
        """Clean up expired keys"""
        print("Cleaning up expired keys...")
        
        try:
            cleaned_keys = key_manager.cleanup_expired_keys()
            
            if cleaned_keys:
                print(f"✅ Cleaned up {len(cleaned_keys)} expired keys:")
                for key_id in cleaned_keys:
                    print(f"  - {key_id}")
            else:
                print("ℹ️  No expired keys to clean up")
            
            return True
            
        except Exception as e:
            print(f"❌ Key cleanup failed: {e}")
            return False
    
    def show_status():
        """Show key status"""
        print("Key Management Status:")
        print("=" * 50)
        
        try:
            status = key_manager.get_key_status()
            
            print(f"Total Keys: {status['total_keys']}")
            print(f"Active Keys: {status['active_keys']}")
            print(f"Expired Keys: {status['expired_keys']}")
            
            if status['next_rotation']:
                next_rotation = datetime.fromisoformat(status['next_rotation'])
                print(f"Next Rotation: {next_rotation.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            print("\nKeys by Type:")
            for key_type, counts in status['keys_by_type'].items():
                print(f"  {key_type}: {counts['active']} active, {counts['expired']} expired")
            
            print("\nKeys by Usage:")
            for usage, counts in status['keys_by_usage'].items():
                print(f"  {usage}: {counts['active']} active, {counts['expired']} expired")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to get key status: {e}")
            return False
    
    def generate_key(key_type, usage):
        """Generate a new key"""
        print(f"Generating new {key_type} key for {usage}...")
        
        try:
            if key_type == "symmetric":
                key_id = key_manager.generate_symmetric_key(usage)
            elif key_type == "asymmetric":
                key_id = key_manager.generate_asymmetric_key_pair(usage)
            elif key_type == "jwt":
                key_id = key_manager.generate_jwt_secret()
            else:
                print(f"❌ Unknown key type: {key_type}")
                return False
            
            print(f"✅ Generated new key: {key_id}")
            return True
            
        except Exception as e:
            print(f"❌ Key generation failed: {e}")
            return False
    
    def test_encryption():
        """Test encryption/decryption functionality"""
        print("Testing encryption functionality...")
        
        try:
            # Test data encryption
            test_data = "This is a test message for encryption"
            encrypted = encryption_service.encrypt_data(test_data)
            decrypted = encryption_service.decrypt_data(encrypted)
            
            if decrypted == test_data:
                print("✅ Symmetric encryption test passed")
            else:
                print("❌ Symmetric encryption test failed")
                return False
            
            # Test data signing
            signature = encryption_service.sign_data(test_data)
            is_valid = encryption_service.verify_signature(test_data, signature)
            
            if is_valid:
                print("✅ Asymmetric signing test passed")
            else:
                print("❌ Asymmetric signing test failed")
                return False
            
            print("✅ All encryption tests passed")
            return True
            
        except Exception as e:
            print(f"❌ Encryption test failed: {e}")
            return False
    
    # Main execution
    operation = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if operation == "rotate":
        force = len(sys.argv) > 2 and sys.argv[2] == "--force"
        success = rotate_keys(force)
    elif operation == "cleanup":
        success = cleanup_keys()
    elif operation == "status":
        success = show_status()
    elif operation == "test":
        success = test_encryption()
    elif operation == "generate":
        if len(sys.argv) < 4:
            print("Usage: generate <key_type> <usage>")
            print("Key types: symmetric, asymmetric, jwt")
            sys.exit(1)
        key_type = sys.argv[2]
        usage = sys.argv[3]
        success = generate_key(key_type, usage)
    else:
        print(f"Unknown operation: {operation}")
        print("Available operations: rotate, cleanup, status, test, generate")
        sys.exit(1)
    
    sys.exit(0 if success else 1)
    
except ImportError as e:
    print(f"❌ Failed to import key rotation modules: {e}")
    print("Make sure you're in the backend directory and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
EOF
    
    # Run the Python script
    if python /tmp/key_rotation_script.py "$operation" $options >> "$ROTATION_LOG" 2>&1; then
        log "${GREEN}✅ Key operation completed successfully${NC}"
        return 0
    else
        log "${RED}❌ Key operation failed${NC}"
        return 1
    fi
    
    # Clean up
    rm -f /tmp/key_rotation_script.py
}

# Backup keys before rotation
backup_keys() {
    log "${BLUE}📦 Creating key backup${NC}"
    
    local backup_dir="$PROJECT_ROOT/backups/keys"
    local backup_file="$backup_dir/keys-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
    
    mkdir -p "$backup_dir"
    
    if [ -d "$PROJECT_ROOT/backend/keys" ]; then
        tar -czf "$backup_file" -C "$PROJECT_ROOT/backend" keys/
        log "${GREEN}✅ Keys backed up to: $backup_file${NC}"
    else
        log "${YELLOW}⚠️  No keys directory found to backup${NC}"
    fi
}

# Send rotation notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Send to webhook if configured
    if [ -n "$SLACK_WEBHOOK" ]; then
        local emoji="✅"
        local color="good"
        
        if [ "$status" = "failed" ]; then
            emoji="❌"
            color="danger"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
             --data "{\"text\":\"$emoji Key Rotation Alert\", \"attachments\":[{\"color\":\"$color\", \"text\":\"$message\"}]}" \
             "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
    
    # Log to security log
    echo "$(date -Iseconds) - Key Rotation - $status - $message" >> "$LOG_DIR/security-events.log"
}

# Validate environment
validate_environment() {
    log "${BLUE}🔍 Validating environment${NC}"
    
    # Check if in production
    if [ "$ENVIRONMENT" = "production" ]; then
        log "${YELLOW}⚠️  Running in PRODUCTION environment${NC}"
        
        if [ "$COMMAND" = "rotate" ] && [ "$FORCE_ROTATE" = "--force" ]; then
            log "${RED}🚨 WARNING: Force rotation in production!${NC}"
            read -p "Are you sure you want to force rotate keys in production? (yes/no): " -r
            if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                log "${YELLOW}Operation cancelled by user${NC}"
                exit 0
            fi
        fi
    fi
    
    # Check key encryption password
    if [ -z "$KEY_ENCRYPTION_PASSWORD" ]; then
        log "${YELLOW}⚠️  KEY_ENCRYPTION_PASSWORD not set, using default${NC}"
    fi
    
    # Check required dependencies
    cd "$PROJECT_ROOT/backend"
    if [ ! -f "requirements.txt" ] || ! grep -q "cryptography" requirements.txt; then
        log "${RED}❌ Cryptography dependency not found${NC}"
        exit 1
    fi
}

# Main execution
case $COMMAND in
    "rotate")
        log "\n${BLUE}🔄 Starting key rotation${NC}"
        validate_environment
        backup_keys
        
        if [ "$FORCE_ROTATE" = "--force" ]; then
            log "${YELLOW}⚠️  Force rotation enabled${NC}"
            options="--force"
        else
            options=""
        fi
        
        if run_key_operation "rotate" "$options"; then
            send_notification "success" "Key rotation completed successfully"
            log "\n${GREEN}✅ Key rotation completed successfully${NC}"
        else
            send_notification "failed" "Key rotation failed - check logs"
            log "\n${RED}❌ Key rotation failed${NC}"
            exit 1
        fi
        ;;
        
    "cleanup")
        log "\n${BLUE}🧹 Cleaning up expired keys${NC}"
        validate_environment
        
        if run_key_operation "cleanup"; then
            log "\n${GREEN}✅ Key cleanup completed${NC}"
        else
            log "\n${RED}❌ Key cleanup failed${NC}"
            exit 1
        fi
        ;;
        
    "status")
        log "\n${BLUE}📊 Checking key status${NC}"
        run_key_operation "status"
        ;;
        
    "test")
        log "\n${BLUE}🧪 Testing encryption functionality${NC}"
        if run_key_operation "test"; then
            log "\n${GREEN}✅ Encryption tests passed${NC}"
        else
            log "\n${RED}❌ Encryption tests failed${NC}"
            exit 1
        fi
        ;;
        
    "generate")
        KEY_TYPE=${2:-"symmetric"}
        USAGE=${3:-"general_encryption"}
        
        log "\n${BLUE}🔑 Generating new key${NC}"
        log "Type: $KEY_TYPE"
        log "Usage: $USAGE"
        
        if run_key_operation "generate" "$KEY_TYPE $USAGE"; then
            log "\n${GREEN}✅ Key generation completed${NC}"
        else
            log "\n${RED}❌ Key generation failed${NC}"
            exit 1
        fi
        ;;
        
    "schedule")
        log "\n${BLUE}⏰ Setting up key rotation schedule${NC}"
        
        # Create cron job for key rotation
        CRON_SCRIPT="$SCRIPT_DIR/key-rotation.sh"
        CRON_JOB="0 2 * * 0 $CRON_SCRIPT rotate >> $LOG_DIR/key-rotation-cron.log 2>&1"
        
        # Add to crontab if not already present
        if ! crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
            (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
            log "${GREEN}✅ Weekly key rotation scheduled for Sundays at 2 AM${NC}"
        else
            log "${YELLOW}⚠️  Key rotation cron job already exists${NC}"
        fi
        ;;
        
    "help"|"-h"|"--help")
        cat << EOF

Key Rotation Management Script

Usage: $0 [command] [options]

Commands:
  status              Show current key status
  rotate [--force]    Rotate expired keys (or force all)
  cleanup             Clean up old expired keys
  test                Test encryption functionality
  generate <type> <usage>  Generate new key
  schedule            Set up automatic rotation schedule
  help                Show this help message

Key Types (for generate):
  symmetric           Symmetric encryption key
  asymmetric          Asymmetric key pair
  jwt                 JWT signing secret

Examples:
  $0 status
  $0 rotate
  $0 rotate --force
  $0 cleanup
  $0 test
  $0 generate symmetric backup_encryption
  $0 generate asymmetric document_signing
  $0 schedule

Environment Variables:
  ENVIRONMENT              Current environment (development/staging/production)
  KEY_ENCRYPTION_PASSWORD  Master password for key encryption
  SLACK_WEBHOOK           Webhook for notifications

EOF
        ;;
        
    *)
        log "${RED}❌ Unknown command: $COMMAND${NC}"
        log "Use '$0 help' for usage information"
        exit 1
        ;;
esac

log "\n${BLUE}📄 Log file: $ROTATION_LOG${NC}"
exit 0