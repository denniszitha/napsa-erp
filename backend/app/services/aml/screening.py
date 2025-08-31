from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from difflib import SequenceMatcher
import re

from app.models.aml import WatchlistEntry, ScreeningResult, CustomerProfile, Transaction
from app.models.aml.sanctions import MatchStatus


class ScreeningService:
    """Service for screening customers and transactions against watchlists and sanctions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.match_threshold = 0.85  # 85% similarity threshold
    
    def screen_customer(
        self,
        customer_id: int,
        screening_type: str = "periodic"
    ) -> List[Dict[str, Any]]:
        """Screen a customer against all active watchlists"""
        
        customer = self.db.query(CustomerProfile).filter(
            CustomerProfile.id == customer_id
        ).first()
        
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        # Prepare search terms
        search_terms = self._prepare_customer_search_terms(customer)
        
        results = []
        for term in search_terms:
            matches = self._search_watchlists(term)
            for match in matches:
                # Create screening result
                result = ScreeningResult(
                    screening_id=f"SCR-{customer_id}-{datetime.utcnow().timestamp()}",
                    customer_id=customer_id,
                    screening_type=screening_type,
                    searched_name=term,
                    watchlist_entry_id=match["entry_id"],
                    match_score=match["score"],
                    match_status=self._determine_match_status(match["score"]),
                    matched_fields=match["matched_fields"],
                    algorithm_used=match["algorithm"]
                )
                self.db.add(result)
                results.append(result)
        
        self.db.commit()
        return results
    
    def screen_transaction(
        self,
        transaction_id: int
    ) -> List[Dict[str, Any]]:
        """Screen a transaction and its parties against watchlists"""
        
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")
        
        results = []
        
        # Screen counterparty name
        if transaction.counterparty_name:
            matches = self._search_watchlists(transaction.counterparty_name)
            for match in matches:
                result = ScreeningResult(
                    screening_id=f"SCR-TXN-{transaction_id}-{datetime.utcnow().timestamp()}",
                    transaction_id=transaction_id,
                    screening_type="transaction",
                    searched_name=transaction.counterparty_name,
                    watchlist_entry_id=match["entry_id"],
                    match_score=match["score"],
                    match_status=self._determine_match_status(match["score"]),
                    matched_fields=match["matched_fields"],
                    algorithm_used=match["algorithm"]
                )
                self.db.add(result)
                results.append(result)
                
                # Update transaction flags
                if match["score"] > self.match_threshold:
                    transaction.sanctions_hit = True
                    transaction.watchlist_hit = True
        
        self.db.commit()
        return results
    
    def _prepare_customer_search_terms(self, customer: CustomerProfile) -> List[str]:
        """Prepare search terms from customer data"""
        terms = []
        
        # Individual names
        if customer.first_name and customer.last_name:
            terms.append(f"{customer.first_name} {customer.last_name}")
            terms.append(f"{customer.last_name}, {customer.first_name}")
        
        # Company name
        if customer.company_name:
            terms.append(customer.company_name)
        
        # Account name
        if customer.account_name:
            terms.append(customer.account_name)
        
        return terms
    
    def _search_watchlists(self, search_term: str) -> List[Dict[str, Any]]:
        """Search all active watchlists for matches"""
        
        # Normalize search term
        normalized_term = self._normalize_name(search_term)
        
        # Query all active watchlist entries
        entries = self.db.query(WatchlistEntry).filter(
            WatchlistEntry.is_active == True
        ).all()
        
        matches = []
        for entry in entries:
            # Check main name
            score = self._calculate_similarity(normalized_term, self._normalize_name(entry.full_name))
            if score > self.match_threshold:
                matches.append({
                    "entry_id": entry.id,
                    "score": score * 100,
                    "matched_fields": {"full_name": entry.full_name},
                    "algorithm": "fuzzy"
                })
                continue
            
            # Check aliases
            if entry.aliases:
                for alias in entry.aliases:
                    alias_score = self._calculate_similarity(normalized_term, self._normalize_name(alias))
                    if alias_score > self.match_threshold:
                        matches.append({
                            "entry_id": entry.id,
                            "score": alias_score * 100,
                            "matched_fields": {"alias": alias},
                            "algorithm": "fuzzy"
                        })
                        break
        
        return matches
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison"""
        if not name:
            return ""
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove special characters
        name = re.sub(r'[^\w\s]', ' ', name)
        
        # Remove extra spaces
        name = ' '.join(name.split())
        
        return name
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _determine_match_status(self, score: float) -> MatchStatus:
        """Determine match status based on score"""
        if score >= 95:
            return MatchStatus.CONFIRMED_MATCH
        elif score >= 85:
            return MatchStatus.POSSIBLE_MATCH
        else:
            return MatchStatus.NO_MATCH