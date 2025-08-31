#!/bin/bash

# NAPSA ERM Database Restore Script
# Restores database from a backup file

# Configuration
DB_CONTAINER="napsa-postgres"
DB_NAME="napsa_erm"
DB_USER="napsa_admin"
BACKUP_DIR="/var/napsa-erm/backups"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}NAPSA ERM Database Restore Tool${NC}"
echo -e "${GREEN}======================================${NC}"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Error: Backup directory '$BACKUP_DIR' does not exist${NC}"
    exit 1
fi

# List available backups
echo -e "${YELLOW}Available backups:${NC}"
ls -lah "$BACKUP_DIR"/*.gz 2>/dev/null | awk '{print NR". "$9" ("$5")"}'

# Get user input
echo ""
read -p "Enter backup file name (or number from list): " BACKUP_CHOICE

# Handle numeric choice
if [[ "$BACKUP_CHOICE" =~ ^[0-9]+$ ]]; then
    BACKUP_FILE=$(ls -1 "$BACKUP_DIR"/*.gz 2>/dev/null | sed -n "${BACKUP_CHOICE}p")
else
    # Handle direct filename
    if [[ "$BACKUP_CHOICE" == /* ]]; then
        BACKUP_FILE="$BACKUP_CHOICE"
    else
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_CHOICE"
    fi
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file '$BACKUP_FILE' does not exist${NC}"
    exit 1
fi

echo -e "${YELLOW}Selected backup: $BACKUP_FILE${NC}"

# Confirmation
echo -e "${RED}⚠️  WARNING: This will replace all current data in the database!${NC}"
read -p "Are you sure you want to restore? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Check if container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}Error: Database container '$DB_CONTAINER' is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting database restore...${NC}"

# Create a temporary uncompressed file
TEMP_FILE="/tmp/restore_$(date +%s).sql"
echo "Decompressing backup..."
zcat "$BACKUP_FILE" > "$TEMP_FILE"

# Restore the database
echo "Restoring database..."
docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < "$TEMP_FILE"

# Check if restore was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database restored successfully!${NC}"
    
    # Verify restore
    echo -e "${YELLOW}Verifying restore...${NC}"
    USER_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ')
    RISK_COUNT=$(docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM risks;" 2>/dev/null | tr -d ' ')
    
    echo "Users in database: $USER_COUNT"
    echo "Risks in database: $RISK_COUNT"
else
    echo -e "${RED}❌ Restore failed!${NC}"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Clean up
rm -f "$TEMP_FILE"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Restore process completed${NC}"
echo -e "${GREEN}======================================${NC}"