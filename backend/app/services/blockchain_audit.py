"""
Blockchain Audit Trail Service
Provides immutable audit logging using blockchain technology for compliance and transparency
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Blockchain-specific models
BlockchainBase = declarative_base()

class BlockchainBlock(BlockchainBase):
    """Blockchain block storage in database"""
    __tablename__ = "blockchain_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    block_hash = Column(String(64), unique=True, nullable=False, index=True)
    previous_hash = Column(String(64), nullable=False, index=True)
    merkle_root = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    nonce = Column(Integer, nullable=False)
    difficulty = Column(Integer, default=4)
    transactions_count = Column(Integer, default=0)
    is_validated = Column(Boolean, default=False)

class BlockchainTransaction(BlockchainBase):
    """Blockchain transaction storage"""
    __tablename__ = "blockchain_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_hash = Column(String(64), unique=True, nullable=False, index=True)
    block_hash = Column(String(64), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    data_hash = Column(String(64), nullable=False)
    previous_state_hash = Column(String(64))
    new_state_hash = Column(String(64), nullable=False)
    user_id = Column(String(50))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    payload = Column(Text)  # JSON serialized data

class AuditEventType(Enum):
    """Types of events that can be audited"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout" 
    TRANSACTION_CREATE = "transaction_create"
    TRANSACTION_UPDATE = "transaction_update"
    CUSTOMER_CREATE = "customer_create"
    CUSTOMER_UPDATE = "customer_update"
    ALERT_CREATE = "alert_create"
    ALERT_RESOLVE = "alert_resolve"
    CASE_CREATE = "case_create"
    CASE_UPDATE = "case_update"
    REPORT_GENERATE = "report_generate"
    CONFIG_CHANGE = "config_change"
    MODEL_RETRAIN = "model_retrain"
    DATA_EXPORT = "data_export"
    COMPLIANCE_CHECK = "compliance_check"

@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class BlockchainTransactionData:
    """Blockchain transaction data"""
    event: AuditEvent
    data_hash: str
    previous_state_hash: Optional[str]
    new_state_hash: str
    nonce: int = 0

@dataclass
class Block:
    """Blockchain block data structure"""
    index: int
    timestamp: datetime
    transactions: List[BlockchainTransactionData]
    previous_hash: str
    nonce: int = 0
    hash: Optional[str] = None
    merkle_root: Optional[str] = None

class BlockchainAuditService:
    """Blockchain-based audit trail service"""
    
    def __init__(self, database_url: str = "sqlite:///blockchain_audit.db"):
        self.difficulty = 4  # Proof of work difficulty
        self.blockchain: List[Block] = []
        self.pending_transactions: List[BlockchainTransactionData] = []
        self.database_url = database_url
        self._init_database()
        self._load_blockchain()
    
    def _init_database(self):
        """Initialize blockchain database"""
        try:
            self.engine = create_engine(self.database_url)
            BlockchainBase.metadata.create_all(bind=self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Blockchain database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize blockchain database: {e}")
            raise
    
    def _load_blockchain(self):
        """Load existing blockchain from database"""
        try:
            db = self.SessionLocal()
            blocks = db.query(BlockchainBlock).order_by(BlockchainBlock.id).all()
            
            if not blocks:
                # Create genesis block
                self._create_genesis_block()
            else:
                # Load blockchain from database
                for block_record in blocks:
                    transactions = db.query(BlockchainTransaction).filter(
                        BlockchainTransaction.block_hash == block_record.block_hash
                    ).all()
                    
                    block_transactions = []
                    for tx in transactions:
                        # Reconstruct transaction data
                        payload_data = json.loads(tx.payload) if tx.payload else {}
                        event = AuditEvent(**payload_data.get('event', {}))
                        
                        block_transactions.append(BlockchainTransactionData(
                            event=event,
                            data_hash=tx.data_hash,
                            previous_state_hash=tx.previous_state_hash,
                            new_state_hash=tx.new_state_hash,
                            nonce=0
                        ))
                    
                    block = Block(
                        index=block_record.id - 1,  # 0-indexed
                        timestamp=block_record.timestamp,
                        transactions=block_transactions,
                        previous_hash=block_record.previous_hash,
                        nonce=block_record.nonce,
                        hash=block_record.block_hash,
                        merkle_root=block_record.merkle_root
                    )
                    
                    self.blockchain.append(block)
            
            db.close()
            logger.info(f"Loaded blockchain with {len(self.blockchain)} blocks")
            
        except Exception as e:
            logger.error(f"Failed to load blockchain: {e}")
            self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_event = AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE.value,
            entity_type="system",
            entity_id="genesis",
            user_id="system",
            timestamp=datetime.now(timezone.utc),
            data={"message": "Blockchain initialized", "version": "1.0"}
        )
        
        genesis_transaction = BlockchainTransactionData(
            event=genesis_event,
            data_hash=self._calculate_hash(genesis_event.data),
            previous_state_hash=None,
            new_state_hash=self._calculate_hash(genesis_event.data)
        )
        
        genesis_block = Block(
            index=0,
            timestamp=datetime.now(timezone.utc),
            transactions=[genesis_transaction],
            previous_hash="0" * 64,
            nonce=0
        )
        
        genesis_block.merkle_root = self._calculate_merkle_root(genesis_block.transactions)
        genesis_block.hash = self._mine_block(genesis_block)
        
        self.blockchain.append(genesis_block)
        self._save_block_to_db(genesis_block)
        
        logger.info("Genesis block created")
    
    def record_audit_event(self, event: AuditEvent) -> str:
        """Record an audit event to the blockchain"""
        try:
            # Calculate state hashes
            data_hash = self._calculate_hash(event.data)
            previous_state_hash = self._get_last_state_hash(event.entity_type, event.entity_id)
            new_state_hash = self._calculate_hash({
                "data": event.data,
                "previous": previous_state_hash,
                "timestamp": event.timestamp.isoformat()
            })
            
            # Create blockchain transaction
            transaction = BlockchainTransactionData(
                event=event,
                data_hash=data_hash,
                previous_state_hash=previous_state_hash,
                new_state_hash=new_state_hash
            )
            
            # Add to pending transactions
            self.pending_transactions.append(transaction)
            
            # Create new block when we have enough transactions (or force creation)
            if len(self.pending_transactions) >= 10:  # Block size limit
                self._create_new_block()
            
            transaction_hash = self._calculate_transaction_hash(transaction)
            logger.info(f"Audit event recorded: {event.event_type} for {event.entity_type}:{event.entity_id}")
            
            return transaction_hash
            
        except Exception as e:
            logger.error(f"Failed to record audit event: {e}")
            raise
    
    def _create_new_block(self):
        """Create a new block with pending transactions"""
        if not self.pending_transactions:
            return
        
        try:
            previous_block = self.blockchain[-1] if self.blockchain else None
            previous_hash = previous_block.hash if previous_block else "0" * 64
            
            new_block = Block(
                index=len(self.blockchain),
                timestamp=datetime.now(timezone.utc),
                transactions=self.pending_transactions.copy(),
                previous_hash=previous_hash
            )
            
            # Calculate merkle root
            new_block.merkle_root = self._calculate_merkle_root(new_block.transactions)
            
            # Mine the block (proof of work)
            new_block.hash = self._mine_block(new_block)
            
            # Add to blockchain
            self.blockchain.append(new_block)
            
            # Save to database
            self._save_block_to_db(new_block)
            
            # Clear pending transactions
            self.pending_transactions = []
            
            logger.info(f"New block mined: {new_block.hash} with {len(new_block.transactions)} transactions")
            
        except Exception as e:
            logger.error(f"Failed to create new block: {e}")
            raise
    
    def _mine_block(self, block: Block) -> str:
        """Mine a block using proof of work"""
        target = "0" * self.difficulty
        
        while True:
            block_data = {
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "transactions": [self._calculate_transaction_hash(tx) for tx in block.transactions],
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "nonce": block.nonce
            }
            
            block_hash = self._calculate_hash(block_data)
            
            if block_hash.startswith(target):
                return block_hash
            
            block.nonce += 1
    
    def _calculate_hash(self, data: Any) -> str:
        """Calculate SHA-256 hash of data"""
        json_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_string.encode()).hexdigest()
    
    def _calculate_transaction_hash(self, transaction: BlockchainTransactionData) -> str:
        """Calculate hash of a transaction"""
        tx_data = {
            "event_type": transaction.event.event_type,
            "entity_type": transaction.event.entity_type,
            "entity_id": transaction.event.entity_id,
            "timestamp": transaction.event.timestamp.isoformat(),
            "data_hash": transaction.data_hash,
            "new_state_hash": transaction.new_state_hash
        }
        return self._calculate_hash(tx_data)
    
    def _calculate_merkle_root(self, transactions: List[BlockchainTransactionData]) -> str:
        """Calculate merkle root of transactions"""
        if not transactions:
            return self._calculate_hash("")
        
        tx_hashes = [self._calculate_transaction_hash(tx) for tx in transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])  # Duplicate last hash if odd number
            
            next_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                next_level.append(self._calculate_hash(combined))
            
            tx_hashes = next_level
        
        return tx_hashes[0]
    
    def _get_last_state_hash(self, entity_type: str, entity_id: str) -> Optional[str]:
        """Get the last state hash for an entity"""
        try:
            db = self.SessionLocal()
            last_transaction = db.query(BlockchainTransaction).filter(
                BlockchainTransaction.entity_type == entity_type,
                BlockchainTransaction.entity_id == entity_id
            ).order_by(BlockchainTransaction.timestamp.desc()).first()
            
            db.close()
            return last_transaction.new_state_hash if last_transaction else None
            
        except Exception as e:
            logger.error(f"Failed to get last state hash: {e}")
            return None
    
    def _save_block_to_db(self, block: Block):
        """Save block and transactions to database"""
        try:
            db = self.SessionLocal()
            
            # Save block
            db_block = BlockchainBlock(
                block_hash=block.hash,
                previous_hash=block.previous_hash,
                merkle_root=block.merkle_root,
                timestamp=block.timestamp,
                nonce=block.nonce,
                difficulty=self.difficulty,
                transactions_count=len(block.transactions),
                is_validated=True
            )
            db.add(db_block)
            db.flush()  # Get the ID
            
            # Save transactions
            for transaction in block.transactions:
                transaction_payload = {
                    "event": asdict(transaction.event),
                    "data_hash": transaction.data_hash,
                    "previous_state_hash": transaction.previous_state_hash,
                    "new_state_hash": transaction.new_state_hash
                }
                
                db_transaction = BlockchainTransaction(
                    transaction_hash=self._calculate_transaction_hash(transaction),
                    block_hash=block.hash,
                    event_type=transaction.event.event_type,
                    entity_type=transaction.event.entity_type,
                    entity_id=transaction.event.entity_id,
                    data_hash=transaction.data_hash,
                    previous_state_hash=transaction.previous_state_hash,
                    new_state_hash=transaction.new_state_hash,
                    user_id=transaction.event.user_id,
                    timestamp=transaction.event.timestamp,
                    payload=json.dumps(transaction_payload, default=str)
                )
                db.add(db_transaction)
            
            db.commit()
            db.close()
            
        except Exception as e:
            logger.error(f"Failed to save block to database: {e}")
            raise
    
    def verify_blockchain_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire blockchain"""
        try:
            results = {
                "is_valid": True,
                "total_blocks": len(self.blockchain),
                "errors": []
            }
            
            for i, block in enumerate(self.blockchain):
                # Verify block hash
                expected_hash = self._mine_block_verification(block)
                if block.hash != expected_hash:
                    results["is_valid"] = False
                    results["errors"].append(f"Block {i}: Invalid hash")
                
                # Verify previous hash linkage
                if i > 0:
                    previous_block = self.blockchain[i - 1]
                    if block.previous_hash != previous_block.hash:
                        results["is_valid"] = False
                        results["errors"].append(f"Block {i}: Invalid previous hash")
                
                # Verify merkle root
                expected_merkle = self._calculate_merkle_root(block.transactions)
                if block.merkle_root != expected_merkle:
                    results["is_valid"] = False
                    results["errors"].append(f"Block {i}: Invalid merkle root")
            
            logger.info(f"Blockchain verification completed: {results['is_valid']}")
            return results
            
        except Exception as e:
            logger.error(f"Blockchain verification failed: {e}")
            return {"is_valid": False, "errors": [str(e)]}
    
    def _mine_block_verification(self, block: Block) -> str:
        """Recalculate block hash for verification"""
        block_data = {
            "index": block.index,
            "timestamp": block.timestamp.isoformat(),
            "transactions": [self._calculate_transaction_hash(tx) for tx in block.transactions],
            "previous_hash": block.previous_hash,
            "merkle_root": block.merkle_root,
            "nonce": block.nonce
        }
        return self._calculate_hash(block_data)
    
    def get_audit_trail(self, entity_type: str = None, entity_id: str = None, 
                       event_type: str = None, start_date: datetime = None, 
                       end_date: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit trail with filters"""
        try:
            db = self.SessionLocal()
            query = db.query(BlockchainTransaction)
            
            if entity_type:
                query = query.filter(BlockchainTransaction.entity_type == entity_type)
            if entity_id:
                query = query.filter(BlockchainTransaction.entity_id == entity_id)
            if event_type:
                query = query.filter(BlockchainTransaction.event_type == event_type)
            if start_date:
                query = query.filter(BlockchainTransaction.timestamp >= start_date)
            if end_date:
                query = query.filter(BlockchainTransaction.timestamp <= end_date)
            
            transactions = query.order_by(
                BlockchainTransaction.timestamp.desc()
            ).limit(limit).all()
            
            results = []
            for tx in transactions:
                payload = json.loads(tx.payload) if tx.payload else {}
                results.append({
                    "transaction_hash": tx.transaction_hash,
                    "block_hash": tx.block_hash,
                    "event_type": tx.event_type,
                    "entity_type": tx.entity_type,
                    "entity_id": tx.entity_id,
                    "user_id": tx.user_id,
                    "timestamp": tx.timestamp.isoformat(),
                    "data_hash": tx.data_hash,
                    "event_data": payload.get("event", {}),
                    "is_verified": True  # All blockchain entries are verified
                })
            
            db.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []
    
    def force_block_creation(self):
        """Force creation of a new block with pending transactions"""
        if self.pending_transactions:
            self._create_new_block()
    
    def get_blockchain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        try:
            db = self.SessionLocal()
            
            total_blocks = db.query(BlockchainBlock).count()
            total_transactions = db.query(BlockchainTransaction).count()
            
            # Get recent activity
            recent_transactions = db.query(BlockchainTransaction).filter(
                BlockchainTransaction.timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
            ).count()
            
            # Get event type distribution
            event_types = db.query(
                BlockchainTransaction.event_type,
                db.func.count(BlockchainTransaction.id)
            ).group_by(BlockchainTransaction.event_type).all()
            
            db.close()
            
            return {
                "total_blocks": total_blocks,
                "total_transactions": total_transactions,
                "pending_transactions": len(self.pending_transactions),
                "recent_activity": recent_transactions,
                "event_type_distribution": [
                    {"event_type": event_type, "count": count}
                    for event_type, count in event_types
                ],
                "blockchain_length": len(self.blockchain),
                "last_block_time": self.blockchain[-1].timestamp.isoformat() if self.blockchain else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get blockchain stats: {e}")
            return {"error": str(e)}

# Global blockchain service instance
blockchain_service = None

def get_blockchain_service() -> BlockchainAuditService:
    """Get the global blockchain audit service instance"""
    global blockchain_service
    if blockchain_service is None:
        blockchain_service = BlockchainAuditService()
    return blockchain_service

def record_audit_event(event_type: str, entity_type: str, entity_id: str, 
                      user_id: str, data: Dict[str, Any], 
                      previous_state: Dict[str, Any] = None,
                      new_state: Dict[str, Any] = None,
                      ip_address: str = None) -> str:
    """Convenience function to record an audit event"""
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        timestamp=datetime.now(timezone.utc),
        data=data,
        previous_state=previous_state,
        new_state=new_state,
        ip_address=ip_address
    )
    
    service = get_blockchain_service()
    return service.record_audit_event(event)