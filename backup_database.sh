#!/bin/bash

# NAPSA ERM Database Backup Script
# Creates timestamped backups of the PostgreSQL database

# Configuration
DB_CONTAINER="napsa-postgres"
DB_NAME="napsa_erm"
DB_USER="napsa_admin"
BACKUP_DIR="/var/napsa-erm/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="napsa_erm_backup_${TIMESTAMP}.sql"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}NAPSA ERM Database Backup Tool${NC}"
echo -e "${GREEN}======================================${NC}"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${YELLOW}Creating backup directory: $BACKUP_DIR${NC}"
    mkdir -p "$BACKUP_DIR"
fi

# Check if container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}Error: Database container '$DB_CONTAINER' is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting database backup...${NC}"
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"

# Perform the backup
docker exec $DB_CONTAINER pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    --format=plain \
    > "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null

# Check if backup was successful
if [ $? -eq 0 ] && [ -s "$BACKUP_DIR/$BACKUP_FILE" ]; then
    # Get file size
    FILE_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    
    # Count tables in backup
    TABLE_COUNT=$(grep -c "CREATE TABLE" "$BACKUP_DIR/$BACKUP_FILE" 2>/dev/null || echo "0")
    
    # Compress the backup
    echo -e "${YELLOW}Compressing backup...${NC}"
    gzip -9 "$BACKUP_DIR/$BACKUP_FILE"
    COMPRESSED_FILE="${BACKUP_FILE}.gz"
    COMPRESSED_SIZE=$(ls -lh "$BACKUP_DIR/$COMPRESSED_FILE" | awk '{print $5}')
    
    echo -e "${GREEN}✅ Backup completed successfully!${NC}"
    echo -e "Original size: $FILE_SIZE"
    echo -e "Compressed size: $COMPRESSED_SIZE"
    echo -e "Tables backed up: $TABLE_COUNT"
    echo -e "Backup location: $BACKUP_DIR/$COMPRESSED_FILE"
    
    # Keep only last 7 backups
    echo -e "${YELLOW}Cleaning old backups (keeping last 7)...${NC}"
    cd "$BACKUP_DIR"
    ls -t napsa_erm_backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
    
    # List current backups
    echo -e "${GREEN}Current backups:${NC}"
    ls -lah napsa_erm_backup_*.sql.gz 2>/dev/null | head -7
    
else
    echo -e "${RED}❌ Backup failed!${NC}"
    rm -f "$BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Backup process completed${NC}"
echo -e "${GREEN}======================================${NC}"