#!/bin/bash

# SSL Certificate Management Script
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DOMAINS=(
    "educational-rpg.com"
    "www.educational-rpg.com"
    "api.educational-rpg.com"
)
EMAIL="admin@educational-rpg.com"
NGINX_CONTAINER="nginx-proxy"
CERT_PATH="/etc/letsencrypt/live"

echo -e "${BLUE}🔐 SSL Certificate Management${NC}"
echo -e "${BLUE}============================${NC}\n"

# Function to check if running in production
check_environment() {
    if [ "$ENVIRONMENT" != "production" ]; then
        echo -e "${RED}Error: This script should only be run in production${NC}"
        exit 1
    fi
}

# Function to install certbot
install_certbot() {
    echo -e "${YELLOW}Installing Certbot...${NC}"
    
    if ! command -v certbot &> /dev/null; then
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    echo -e "${GREEN}✓ Certbot installed${NC}\n"
}

# Function to generate certificates
generate_certificates() {
    echo -e "${YELLOW}Generating SSL certificates...${NC}"
    
    # Create webroot directory
    mkdir -p /var/www/certbot
    
    # Generate certificates for each domain
    for domain in "${DOMAINS[@]}"; do
        echo -e "${YELLOW}Generating certificate for $domain...${NC}"
        
        certbot certonly \
            --webroot \
            --webroot-path /var/www/certbot \
            --email $EMAIL \
            --agree-tos \
            --no-eff-email \
            --non-interactive \
            --domain $domain \
            --deploy-hook "docker exec $NGINX_CONTAINER nginx -s reload" || {
                echo -e "${RED}Failed to generate certificate for $domain${NC}"
                continue
            }
        
        echo -e "${GREEN}✓ Certificate generated for $domain${NC}"
    done
}

# Function to setup auto-renewal
setup_auto_renewal() {
    echo -e "${YELLOW}Setting up auto-renewal...${NC}"
    
    # Create renewal script
    cat > /usr/local/bin/renew-certificates.sh <<'EOF'
#!/bin/bash
certbot renew --quiet --deploy-hook "docker exec nginx-proxy nginx -s reload"
EOF
    
    chmod +x /usr/local/bin/renew-certificates.sh
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1") | crontab -
    
    echo -e "${GREEN}✓ Auto-renewal configured${NC}\n"
}

# Function to verify certificates
verify_certificates() {
    echo -e "${YELLOW}Verifying certificates...${NC}"
    
    for domain in "${DOMAINS[@]}"; do
        if [ -f "$CERT_PATH/$domain/fullchain.pem" ]; then
            # Check expiration
            expiry=$(openssl x509 -enddate -noout -in "$CERT_PATH/$domain/fullchain.pem" | cut -d= -f2)
            echo -e "${GREEN}✓ $domain - Expires: $expiry${NC}"
            
            # Verify certificate chain
            openssl verify -CAfile "$CERT_PATH/$domain/chain.pem" "$CERT_PATH/$domain/cert.pem" > /dev/null 2>&1 && \
                echo -e "${GREEN}  Certificate chain valid${NC}" || \
                echo -e "${RED}  Certificate chain invalid${NC}"
        else
            echo -e "${RED}✗ $domain - Certificate not found${NC}"
        fi
    done
    echo
}

# Function to backup certificates
backup_certificates() {
    echo -e "${YELLOW}Backing up certificates...${NC}"
    
    BACKUP_DIR="/backups/ssl/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Backup Let's Encrypt directory
    tar -czf "$BACKUP_DIR/letsencrypt.tar.gz" /etc/letsencrypt/
    
    # Upload to S3
    aws s3 cp "$BACKUP_DIR/letsencrypt.tar.gz" \
        "s3://educational-rpg-backups/ssl/letsencrypt-$(date +%Y%m%d_%H%M%S).tar.gz" \
        --storage-class STANDARD_IA
    
    echo -e "${GREEN}✓ Certificates backed up${NC}\n"
}

# Function to monitor certificate expiry
monitor_expiry() {
    echo -e "${YELLOW}Checking certificate expiry...${NC}"
    
    for domain in "${DOMAINS[@]}"; do
        if [ -f "$CERT_PATH/$domain/fullchain.pem" ]; then
            # Days until expiry
            expiry_date=$(openssl x509 -enddate -noout -in "$CERT_PATH/$domain/fullchain.pem" | cut -d= -f2)
            expiry_epoch=$(date -d "$expiry_date" +%s)
            current_epoch=$(date +%s)
            days_left=$(( ($expiry_epoch - $current_epoch) / 86400 ))
            
            if [ $days_left -lt 30 ]; then
                echo -e "${RED}⚠️  $domain expires in $days_left days${NC}"
                
                # Send alert
                SLACK_WEBHOOK=$(aws ssm get-parameter --name "/educational-rpg/production/slack-webhook" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null || echo "")
                if [ ! -z "$SLACK_WEBHOOK" ]; then
                    curl -X POST $SLACK_WEBHOOK \
                        -H 'Content-type: application/json' \
                        -d "{
                            \"text\": \"⚠️ SSL Certificate Expiry Warning\",
                            \"attachments\": [{
                                \"color\": \"warning\",
                                \"fields\": [
                                    {\"title\": \"Domain\", \"value\": \"$domain\", \"short\": true},
                                    {\"title\": \"Days Left\", \"value\": \"$days_left\", \"short\": true}
                                ]
                            }]
                        }" 2>/dev/null
                fi
            else
                echo -e "${GREEN}✓ $domain - $days_left days remaining${NC}"
            fi
        fi
    done
}

# Function to generate wildcard certificate
generate_wildcard() {
    echo -e "${YELLOW}Generating wildcard certificate...${NC}"
    
    certbot certonly \
        --manual \
        --preferred-challenges dns \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --domain "*.educational-rpg.com" \
        --domain "educational-rpg.com"
    
    echo -e "${GREEN}✓ Wildcard certificate generated${NC}\n"
}

# Main menu
show_menu() {
    echo -e "${BLUE}Select an option:${NC}"
    echo "1. Generate certificates for all domains"
    echo "2. Generate wildcard certificate"
    echo "3. Renew certificates"
    echo "4. Verify certificates"
    echo "5. Monitor expiry"
    echo "6. Backup certificates"
    echo "7. Setup auto-renewal"
    echo "8. Exit"
    echo
    read -p "Option: " option
    
    case $option in
        1) generate_certificates ;;
        2) generate_wildcard ;;
        3) certbot renew ;;
        4) verify_certificates ;;
        5) monitor_expiry ;;
        6) backup_certificates ;;
        7) setup_auto_renewal ;;
        8) exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
}

# Main execution
main() {
    check_environment
    install_certbot
    
    if [ $# -eq 0 ]; then
        # Interactive mode
        while true; do
            show_menu
            echo
        done
    else
        # Command line mode
        case $1 in
            generate) generate_certificates ;;
            wildcard) generate_wildcard ;;
            renew) certbot renew ;;
            verify) verify_certificates ;;
            monitor) monitor_expiry ;;
            backup) backup_certificates ;;
            auto-renew) setup_auto_renewal ;;
            *) echo -e "${RED}Unknown command: $1${NC}" ;;
        esac
    fi
}

# Run main function
main "$@"