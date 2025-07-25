"""
Vector Storage Agent
Handles embedding generation and vector database operations
"""

import asyncio
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import openai
from sentence_transformers import SentenceTransformer
from loguru import logger

# Vector database imports
import faiss
import chromadb
try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

from ..config.settings import settings
from ..models.database import ContentItem, ContentChunk
from ..models.schemas import ContentItemCreate
from ..core.database import get_db
from ..utils.text_processor import TextProcessor


class VectorStorageAgent:
    """
    Agent responsible for generating embeddings and managing vector storage
    """
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.embedding_model = None
        self.vector_db = None
        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small dimension
        
    async def initialize(self):
        """Initialize the vector storage agent"""
        await self._setup_embedding_model()
        await self._setup_vector_database()
        logger.info("Vector Storage Agent initialized")
    
    async def _setup_embedding_model(self):
        """Setup the embedding model based on configuration"""
        try:
            if settings.llm.embedding_model.startswith("text-embedding"):
                # Use OpenAI embeddings
                openai.api_key = settings.llm.openai_api_key
                self.embedding_model = "openai"
                logger.info(f"Using OpenAI embedding model: {settings.llm.embedding_model}")
                
            else:
                # Use Sentence Transformers
                self.embedding_model = SentenceTransformer(settings.llm.embedding_model)
                self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
                logger.info(f"Using Sentence Transformer model: {settings.llm.embedding_model}")
                
        except Exception as e:
            logger.error(f"Failed to setup embedding model: {e}")
            # Fallback to a lightweight model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embedding_dimension = 384
            logger.warning("Using fallback embedding model: all-MiniLM-L6-v2")
    
    async def _setup_vector_database(self):
        """Setup the vector database based on configuration"""
        try:
            if settings.vector_db.type == "faiss":
                await self._setup_faiss()
            elif settings.vector_db.type == "chroma":
                await self._setup_chroma()
            elif settings.vector_db.type == "pinecone" and PINECONE_AVAILABLE:
                await self._setup_pinecone()
            else:
                logger.warning(f"Unsupported vector DB type: {settings.vector_db.type}, using FAISS")
                await self._setup_faiss()
                
        except Exception as e:
            logger.error(f"Failed to setup vector database: {e}")
            # Fallback to FAISS
            await self._setup_faiss()
    
    async def _setup_faiss(self):
        """Setup FAISS vector database"""
        try:
            # Create FAISS index for similarity search
            self.vector_db = {
                'type': 'faiss',
                'index': faiss.IndexFlatIP(self.embedding_dimension),  # Inner product for cosine similarity
                'id_map': {},  # Maps FAISS index to chunk IDs
                'metadata': {}  # Store metadata for each vector
            }
            logger.info("FAISS vector database initialized")
            
        except Exception as e:
            logger.error(f"FAISS setup failed: {e}")
            raise
    
    async def _setup_chroma(self):
        """Setup ChromaDB vector database"""
        try:
            client = chromadb.Client()
            collection = client.get_or_create_collection(
                name=settings.vector_db.collection_name,
                metadata={"description": "AutoCurate content embeddings"}
            )
            
            self.vector_db = {
                'type': 'chroma',
                'client': client,
                'collection': collection
            }
            logger.info("ChromaDB vector database initialized")
            
        except Exception as e:
            logger.error(f"ChromaDB setup failed: {e}")
            raise
    
    async def _setup_pinecone(self):
        """Setup Pinecone vector database"""
        if not PINECONE_AVAILABLE:
            raise ImportError("Pinecone client not available")
        
        try:
            pinecone.init(
                api_key=settings.vector_db.pinecone_api_key,
                environment=settings.vector_db.pinecone_environment
            )
            
            # Create index if it doesn't exist
            index_name = settings.vector_db.collection_name
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine"
                )
            
            self.vector_db = {
                'type': 'pinecone',
                'index': pinecone.Index(index_name)
            }
            logger.info("Pinecone vector database initialized")
            
        except Exception as e:
            logger.error(f"Pinecone setup failed: {e}")
            raise
    
    async def process_content_item(self, content_item: ContentItem) -> bool:
        """
        Process a content item: chunk text, generate embeddings, and store vectors
        
        Args:
            content_item: ContentItem to process
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing content item: {content_item.id}")
            
            # Chunk the content
            chunks = await self._chunk_content(content_item)
            
            if not chunks:
                logger.warning(f"No chunks generated for content item {content_item.id}")
                return False
            
            # Generate embeddings for chunks
            embeddings = await self._generate_embeddings([chunk['text'] for chunk in chunks])
            
            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch for content item {content_item.id}")
                return False
            
            # Store embeddings and create chunk records
            db = next(get_db())
            try:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    # Store vector in vector database
                    vector_id = await self._store_vector(
                        embedding=embedding,
                        content_item_id=content_item.id,
                        chunk_index=i,
                        metadata=chunk['metadata']
                    )
                    
                    # Create chunk record in relational database
                    chunk_record = ContentChunk(
                        content_item_id=content_item.id,
                        chunk_text=chunk['text'],
                        chunk_index=i,
                        vector_id=vector_id,
                        embedding_model=str(settings.llm.embedding_model),
                        chunk_metadata=chunk['metadata']
                    )
                    
                    db.add(chunk_record)
                
                # Update content item processing status
                content_item.is_processed = True
                content_item.processing_status = "completed"
                
                db.commit()
                logger.info(f"Successfully processed content item {content_item.id} with {len(chunks)} chunks")
                return True
                
            except Exception as e:
                logger.error(f"Database error processing content item {content_item.id}: {e}")
                db.rollback()
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to process content item {content_item.id}: {e}")
            
            # Update processing status to failed
            db = next(get_db())
            try:
                content_item.processing_status = "failed"
                db.commit()
            except:
                pass
            finally:
                db.close()
            
            return False
    
    async def _chunk_content(self, content_item: ContentItem) -> List[Dict[str, Any]]:
        """
        Chunk content into smaller pieces for embedding
        
        Args:
            content_item: ContentItem to chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        content = content_item.cleaned_content or content_item.content
        if not content:
            return []
        
        # Use text processor to chunk content
        text_chunks = self.text_processor.chunk_text(
            content,
            chunk_size=settings.content.chunk_size,
            overlap=settings.content.chunk_overlap
        )
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = {
                'content_item_id': content_item.id,
                'chunk_index': i,
                'title': content_item.title,
                'url': content_item.url,
                'author': content_item.author,
                'published_date': content_item.published_date.isoformat() if content_item.published_date else None,
                'category': getattr(content_item.website, 'category', None),
                'word_count': len(chunk_text.split()),
                'language': content_item.language
            }
            
            chunks.append({
                'text': chunk_text,
                'metadata': chunk_metadata
            })
        
        return chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.embedding_model == "openai":
                return await self._generate_openai_embeddings(texts)
            else:
                return await self._generate_sentence_transformer_embeddings(texts)
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        embeddings = []
        
        # Process in batches to respect rate limits
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
                response = await openai.Embedding.acreate(
                    model=settings.llm.embedding_model,
                    input=batch
                )
                
                batch_embeddings = [item['embedding'] for item in response['data']]
                embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if len(texts) > batch_size:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"OpenAI embedding batch failed: {e}")
                raise
        
        return embeddings
    
    async def _generate_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Sentence Transformers"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                lambda: self.embedding_model.encode(texts, convert_to_numpy=True)
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Sentence Transformer embedding failed: {e}")
            raise
    
    async def _store_vector(self, embedding: List[float], content_item_id: int, 
                          chunk_index: int, metadata: Dict[str, Any]) -> str:
        """
        Store vector in the configured vector database
        
        Args:
            embedding: The embedding vector
            content_item_id: ID of the content item
            chunk_index: Index of the chunk within the content item
            metadata: Additional metadata
            
        Returns:
            str: Vector ID in the database
        """
        vector_id = f"{content_item_id}_{chunk_index}"
        
        try:
            if self.vector_db['type'] == 'faiss':
                await self._store_faiss_vector(vector_id, embedding, metadata)
            elif self.vector_db['type'] == 'chroma':
                await self._store_chroma_vector(vector_id, embedding, metadata)
            elif self.vector_db['type'] == 'pinecone':
                await self._store_pinecone_vector(vector_id, embedding, metadata)
            
            return vector_id
            
        except Exception as e:
            logger.error(f"Vector storage failed for {vector_id}: {e}")
            raise
    
    async def _store_faiss_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Store vector in FAISS index"""
        embedding_array = np.array([embedding], dtype=np.float32)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding_array)
        
        # Add to index
        index_id = self.vector_db['index'].ntotal
        self.vector_db['index'].add(embedding_array)
        
        # Store mappings
        self.vector_db['id_map'][index_id] = vector_id
        self.vector_db['metadata'][vector_id] = metadata
    
    async def _store_chroma_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Store vector in ChromaDB"""
        self.vector_db['collection'].add(
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[vector_id]
        )
    
    async def _store_pinecone_vector(self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]):
        """Store vector in Pinecone"""
        self.vector_db['index'].upsert(
            vectors=[(vector_id, embedding, metadata)]
        )
    
    async def search_similar_content(self, query: str, limit: int = 10, 
                                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity
        
        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters for metadata
            
        Returns:
            List of similar content with scores and metadata
        """
        try:
            # Generate embedding for query
            query_embedding = await self._generate_embeddings([query])
            query_vector = query_embedding[0]
            
            # Search based on vector database type
            if self.vector_db['type'] == 'faiss':
                return await self._search_faiss(query_vector, limit, filters)
            elif self.vector_db['type'] == 'chroma':
                return await self._search_chroma(query_vector, limit, filters)
            elif self.vector_db['type'] == 'pinecone':
                return await self._search_pinecone(query_vector, limit, filters)
            
            return []
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _search_faiss(self, query_vector: List[float], limit: int, 
                          filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search FAISS index"""
        query_array = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Search
        scores, indices = self.vector_db['index'].search(query_array, limit)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in self.vector_db['id_map']:
                vector_id = self.vector_db['id_map'][idx]
                metadata = self.vector_db['metadata'].get(vector_id, {})
                
                # Apply filters if provided
                if filters and not self._matches_filters(metadata, filters):
                    continue
                
                results.append({
                    'vector_id': vector_id,
                    'score': float(score),
                    'metadata': metadata
                })
        
        return results
    
    async def _search_chroma(self, query_vector: List[float], limit: int, 
                           filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search ChromaDB collection"""
        where_filter = self._build_chroma_filter(filters) if filters else None
        
        results = self.vector_db['collection'].query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where_filter
        )
        
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                'vector_id': results['ids'][0][i],
                'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                'metadata': results['metadatas'][0][i]
            })
        
        return search_results
    
    async def _search_pinecone(self, query_vector: List[float], limit: int, 
                             filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search Pinecone index"""
        pinecone_filter = self._build_pinecone_filter(filters) if filters else None
        
        results = self.vector_db['index'].query(
            vector=query_vector,
            top_k=limit,
            filter=pinecone_filter,
            include_metadata=True
        )
        
        search_results = []
        for match in results['matches']:
            search_results.append({
                'vector_id': match['id'],
                'score': match['score'],
                'metadata': match.get('metadata', {})
            })
        
        return search_results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if metadata matches the provided filters"""
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            else:
                if metadata[key] != value:
                    return False
        
        return True
    
    def _build_chroma_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build ChromaDB where filter from filters dict"""
        # ChromaDB uses a specific filter format
        where_filter = {}
        for key, value in filters.items():
            if isinstance(value, list):
                where_filter[key] = {"$in": value}
            else:
                where_filter[key] = {"$eq": value}
        
        return where_filter
    
    def _build_pinecone_filter(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Pinecone filter from filters dict"""
        # Pinecone filters work directly with metadata keys
        return filters
    
    async def get_content_chunks_by_ids(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve content chunks by their vector IDs
        
        Args:
            chunk_ids: List of vector IDs
            
        Returns:
            List of chunk data with text and metadata
        """
        db = next(get_db())
        try:
            chunks = db.query(ContentChunk).filter(
                ContentChunk.vector_id.in_(chunk_ids)
            ).all()
            
            chunk_data = []
            for chunk in chunks:
                chunk_data.append({
                    'id': chunk.id,
                    'vector_id': chunk.vector_id,
                    'text': chunk.chunk_text,
                    'metadata': chunk.chunk_metadata,
                    'content_item_id': chunk.content_item_id
                })
            
            return chunk_data
            
        finally:
            db.close()


async def process_pending_content():
    """Process all pending content items for embedding"""
    logger.info("Starting content processing job")
    
    db = next(get_db())
    try:
        # Get unprocessed content items
        pending_items = db.query(ContentItem).filter(
            ContentItem.is_processed == False,
            ContentItem.processing_status == "pending"
        ).limit(100).all()  # Process in batches
        
        if not pending_items:
            logger.info("No pending content items to process")
            return
        
        logger.info(f"Processing {len(pending_items)} content items")
        
        # Initialize vector storage agent
        agent = VectorStorageAgent()
        await agent.initialize()
        
        # Process each item
        for item in pending_items:
            try:
                # Update status to processing
                item.processing_status = "processing"
                db.commit()
                
                # Process the item
                success = await agent.process_content_item(item)
                
                if not success:
                    logger.error(f"Failed to process content item {item.id}")
                    
            except Exception as e:
                logger.error(f"Error processing content item {item.id}: {e}")
                item.processing_status = "failed"
                db.commit()
        
    finally:
        db.close()
    
    logger.info("Content processing job completed")
