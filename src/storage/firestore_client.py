"""
Firestore database client and operations.
Handles all interactions with Google Cloud Firestore.
"""

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Client, DocumentReference, DocumentSnapshot
from typing import Dict, List, Optional, Any, Iterator
from datetime import datetime
import uuid
from loguru import logger

from config.config import Config


class FirestoreClient:
    """Singleton Firestore client for database operations"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'projectId': Config.FIRESTORE_PROJECT_ID,
            })
            logger.info(f"Firebase initialized for project: {Config.FIRESTORE_PROJECT_ID}")
        
        self.db: Client = firestore.client()
    
    def get_collection(self, collection_name: str):
        """Get a Firestore collection reference"""
        return self.db.collection(collection_name)
    
    # ===== CREATE Operations =====
    
    def add_document(
        self,
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """
        Add a document to a collection.
        
        Args:
            collection: Collection name
            data: Document data
            document_id: Optional document ID (auto-generated if not provided)
        
        Returns:
            Document ID
        """
        try:
            if document_id:
                self.db.collection(collection).document(document_id).set(data)
                logger.debug(f"Added document {document_id} to {collection}")
                return document_id
            else:
                doc_ref = self.db.collection(collection).add(data)
                doc_id = doc_ref[1].id
                logger.debug(f"Added document {doc_id} to {collection}")
                return doc_id
        except Exception as e:
            logger.error(f"Error adding document to {collection}: {e}")
            raise
    
    def batch_add_documents(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 500
    ) -> int:
        """
        Add multiple documents in batches.
        
        Args:
            collection: Collection name
            documents: List of document data
            batch_size: Number of documents per batch (max 500)
        
        Returns:
            Number of documents added
        """
        count = 0
        batch = self.db.batch()
        
        for i, doc_data in enumerate(documents):
            doc_ref = self.db.collection(collection).document()
            batch.set(doc_ref, doc_data)
            count += 1
            
            # Commit batch every batch_size documents
            if (i + 1) % batch_size == 0:
                batch.commit()
                logger.info(f"Committed batch of {batch_size} documents to {collection}")
                batch = self.db.batch()
        
        # Commit remaining documents
        if count % batch_size != 0:
            batch.commit()
            logger.info(f"Committed final batch to {collection}")
        
        logger.info(f"Added {count} documents to {collection}")
        return count
    
    # ===== READ Operations =====
    
    def get_document(
        self,
        collection: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        try:
            doc = self.db.collection(collection).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting document {document_id} from {collection}: {e}")
            raise
    
    def query_documents(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query documents with filters.
        
        Args:
            collection: Collection name
            filters: List of (field, operator, value) tuples
            order_by: Field to order by
            limit: Maximum number of results
        
        Returns:
            List of documents
        """
        try:
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            # Apply ordering
            if order_by:
                query = query.order_by(order_by)
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying {collection}: {e}")
            raise
    
    def get_all_documents(
        self,
        collection: str,
        batch_size: int = 1000
    ) -> Iterator[Dict[str, Any]]:
        """
        Get all documents from a collection (generator for large collections).
        
        Args:
            collection: Collection name
            batch_size: Number of documents to fetch per batch
        
        Yields:
            Document data
        """
        try:
            docs = self.db.collection(collection).stream()
            for doc in docs:
                yield doc.to_dict()
        except Exception as e:
            logger.error(f"Error getting all documents from {collection}: {e}")
            raise
    
    # ===== UPDATE Operations =====
    
    def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Update a document"""
        try:
            self.db.collection(collection).document(document_id).update(data)
            logger.debug(f"Updated document {document_id} in {collection}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {document_id} in {collection}: {e}")
            raise
    
    def upsert_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Insert or update a document"""
        try:
            self.db.collection(collection).document(document_id).set(data, merge=True)
            logger.debug(f"Upserted document {document_id} in {collection}")
            return True
        except Exception as e:
            logger.error(f"Error upserting document {document_id} in {collection}: {e}")
            raise
    
    # ===== DELETE Operations =====
    
    def delete_document(
        self,
        collection: str,
        document_id: str
    ) -> bool:
        """Delete a document"""
        try:
            self.db.collection(collection).document(document_id).delete()
            logger.debug(f"Deleted document {document_id} from {collection}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from {collection}: {e}")
            raise
    
    def delete_collection(
        self,
        collection: str,
        batch_size: int = 500
    ) -> int:
        """
        Delete all documents in a collection.
        WARNING: This is destructive!
        
        Args:
            collection: Collection name
            batch_size: Number of documents to delete per batch
        
        Returns:
            Number of documents deleted
        """
        count = 0
        docs = self.db.collection(collection).limit(batch_size).stream()
        deleted = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted += 1
            count += 1
        
        if deleted >= batch_size:
            # Recursively delete remaining documents
            count += self.delete_collection(collection, batch_size)
        
        logger.warning(f"Deleted {count} documents from {collection}")
        return count
    
    # ===== Utility Methods =====
    
    def collection_exists(self, collection: str) -> bool:
        """Check if a collection has any documents"""
        docs = self.db.collection(collection).limit(1).stream()
        return len(list(docs)) > 0
    
    def count_documents(self, collection: str) -> int:
        """Count documents in a collection (expensive for large collections)"""
        docs = self.db.collection(collection).stream()
        return len(list(docs))
    
    def generate_id(self) -> str:
        """Generate a unique document ID"""
        return str(uuid.uuid4())


# Singleton instance - initialize when needed
_db_client_instance = None


def get_db_client() -> FirestoreClient:
    """Get or create the Firestore client instance"""
    global _db_client_instance
    if _db_client_instance is None:
        _db_client_instance = FirestoreClient()
    return _db_client_instance
