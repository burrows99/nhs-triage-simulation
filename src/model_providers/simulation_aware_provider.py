import asyncio
import threading
import time
import json
import os
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor
import logging
from .ollama import OllamaProvider

logger = logging.getLogger(__name__)

class SimulationAwareProvider:
    """
    Wrapper for LLM providers that separates real-world inference time 
    from simulation time to prevent timing distortion in SimPy simulations.
    
    This provider:
    1. Pre-computes LLM responses in a separate thread pool
    2. Caches responses to avoid repeated API calls
    3. Returns cached responses instantly during simulation
    4. Estimates realistic triage time without blocking simulation
    """
    
    def __init__(self, base_provider: OllamaProvider, cache_size: int = 1000, persistent_cache_dir: str = "output/llm_cache"):
        self.base_provider = base_provider
        self.response_cache = {}
        self.cache_size = cache_size
        self.persistent_cache_dir = persistent_cache_dir
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="llm-worker")
        self.precompute_futures = {}
        self.inference_times = []  # Track real inference times for estimation
        self._lock = threading.Lock()
        
        # Progress tracking
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.progress_file = os.path.join(persistent_cache_dir, "progress.json")
        
        # Create persistent cache directory
        os.makedirs(self.persistent_cache_dir, exist_ok=True)
        
        # Load existing persistent cache
        self._load_persistent_cache()
        
        # Initialize progress tracking
        self._update_progress_file()
        
        logger.info(f"SimulationAwareProvider initialized with cache size {cache_size}, persistent cache: {self.persistent_cache_dir}")
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the underlying provider"""
        self.base_provider.configure(config)
    
    def setup(self, system_prompt: str) -> None:
        """Setup the underlying provider"""
        self.base_provider.setup(system_prompt)
    
    def _make_json_serializable(self, data: Any) -> Any:
        """Convert data to JSON-serializable format
        
        Args:
            data: Data that may contain non-serializable objects
            
        Returns:
            JSON-serializable version of the data
        """
        if data is None:
            return None
        elif hasattr(data, 'to_dict'):
            # Handle objects with to_dict method (like PatientContext)
            return self._make_json_serializable(data.to_dict())
        elif isinstance(data, dict):
            # Recursively handle dictionary values
            return {key: self._make_json_serializable(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            # Recursively handle list/tuple items
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, (str, int, float, bool)):
            # Already serializable
            return data
        else:
            # Convert other objects to string representation
            return str(data)
    
    def _create_cache_key(self, system_name: str, patient_id: str, timestamp: Optional[str] = None) -> str:
        """Create a standardized cache key for both setting and retrieving operations
        
        Args:
            system_name: Name of the triage system
            patient_id: Patient identifier
            timestamp: Optional timestamp string (ignored for consistency)
            
        Returns:
            Formatted cache key: system_name_patient_id
        """
        # Clean system name for filename
        clean_system = system_name.replace(' ', '_').replace('-', '_').lower()
        
        # Return consistent key without timestamp for cache reuse
        return f"{clean_system}_{patient_id}"
    
    def _generate_cache_key(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key using system name, patient ID, and datetime"""
        import re
        
        # Try to extract patient ID from prompt
        patient_id_match = re.search(r'patient[\s_-]*(?:id[:\s]*)?([a-zA-Z0-9-]+)', prompt, re.IGNORECASE)
        if patient_id_match:
            patient_id = patient_id_match.group(1)
        else:
            # Fallback to hash if no patient ID found
            import hashlib
            patient_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        
        # Extract triage system from options or use default
        triage_system = "unknown_system"
        if options and 'triage_system' in options:
            triage_system = options['triage_system']
        elif options and 'system_name' in options:
            triage_system = options['system_name']
        
        return self._create_cache_key(triage_system, patient_id)
    
    def _load_persistent_cache(self):
        """Load cached responses from disk"""
        cache_file = os.path.join(self.persistent_cache_dir, "llm_responses.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    persistent_data = json.load(f)
                
                # Load responses into memory cache
                loaded_count = 0
                for cache_key, response_data in persistent_data.items():
                    self.response_cache[cache_key] = response_data
                    if 'inference_time' in response_data:
                        self.inference_times.append(response_data['inference_time'])
                    loaded_count += 1
                
                logger.info(f"Loaded {loaded_count} cached responses from {cache_file}")
            except Exception as e:
                logger.error(f"Error loading persistent cache: {e}")
        else:
            logger.info(f"No existing cache found at {cache_file}")
    
    def _save_persistent_cache(self):
        """Save current cache to disk"""
        cache_file = os.path.join(self.persistent_cache_dir, "llm_responses.json")
        try:
            with self._lock:
                # Create a copy of the cache for saving
                cache_to_save = self.response_cache.copy()
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(cache_to_save)} cached responses to {cache_file}")
        except Exception as e:
            logger.error(f"Error saving persistent cache: {e}")
    
    def _get_cache_file_for_key(self, cache_key: str) -> str:
        """Get individual cache file path for a specific key"""
        return os.path.join(self.persistent_cache_dir, f"{cache_key}.json")
    
    def _create_cache_content(self, cache_key: str, response_data: Dict[str, Any], patient_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized cache content structure for both setting and retrieving operations
        
        Args:
            cache_key: The cache key identifier
            response_data: LLM response data with inference time and timestamp
            patient_data: Optional comprehensive patient data
            
        Returns:
            Standardized cache content dictionary
        """
        # Convert patient data to JSON-serializable format
        serializable_patient_data = None
        if patient_data:
            serializable_patient_data = self._make_json_serializable(patient_data)
        
        return {
            'cache_key': cache_key,
            'llm_response': response_data,
            'patient_data': serializable_patient_data,
            'created_at': response_data.get('timestamp', time.time())
        }
    
    def _extract_response_from_cache(self, cache_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract LLM response data from cache content, handling both old and new formats
        
        Args:
            cache_data: Raw cache data loaded from file
            
        Returns:
            LLM response data dictionary
        """
        # Handle both old format (direct response data) and new format (with patient data)
        if 'llm_response' in cache_data:
            # New format with patient data
            return cache_data['llm_response']
        else:
            # Old format - direct response data
            return cache_data
    
    def _load_individual_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load individual cached response from disk"""
        cache_file = self._get_cache_file_for_key(cache_key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    return self._extract_response_from_cache(cache_data)
            except Exception as e:
                logger.error(f"Error loading individual cache {cache_file}: {e}")
        return None
    
    def _save_individual_cache(self, cache_key: str, response_data: Dict[str, Any], patient_data: Optional[Dict[str, Any]] = None):
        """Save individual cached response to disk with optional patient data"""
        cache_file = self._get_cache_file_for_key(cache_key)
        try:
            # Create comprehensive cache data structure using dedicated function
            cache_content = self._create_cache_content(cache_key, response_data, patient_data)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_content, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved individual cache to {cache_file}")
        except Exception as e:
            logger.error(f"Error saving individual cache {cache_file}: {e}")
    
    def _update_progress_file(self):
        """Update progress tracking file in real-time"""
        try:
            progress_data = {
                'total_requests': self.total_requests,
                'completed_requests': self.completed_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (self.completed_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
                'progress_percentage': ((self.completed_requests + self.failed_requests) / self.total_requests * 100) if self.total_requests > 0 else 0,
                'pending_requests': self.total_requests - self.completed_requests - self.failed_requests,
                'timestamp': time.time(),
                'status': 'in_progress' if (self.completed_requests + self.failed_requests) < self.total_requests else 'completed'
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error updating progress file: {e}")
    
    def _log_progress(self):
        """Log current progress to console"""
        if self.total_requests > 0:
            completed_total = self.completed_requests + self.failed_requests
            progress_pct = (completed_total / self.total_requests) * 100
            success_pct = (self.completed_requests / self.total_requests) * 100 if self.total_requests > 0 else 0
            
            logger.info(f"LLM Cache Progress: {completed_total}/{self.total_requests} ({progress_pct:.1f}%) - Success: {self.completed_requests} ({success_pct:.1f}%), Failed: {self.failed_requests}")
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """Get current progress statistics"""
        return {
            'total_requests': self.total_requests,
            'completed_requests': self.completed_requests,
            'failed_requests': self.failed_requests,
            'pending_requests': self.total_requests - self.completed_requests - self.failed_requests,
            'progress_percentage': ((self.completed_requests + self.failed_requests) / self.total_requests * 100) if self.total_requests > 0 else 0,
            'success_rate': (self.completed_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        }
    
    def precompute_response(self, prompt: str, options: Optional[Dict[str, Any]] = None, patient_id: str = None, triage_system: str = None, patient_data: Optional[Dict[str, Any]] = None) -> str:
        """Precompute LLM response in background thread.
        Returns cache key for later retrieval.
        
        Args:
            prompt: The prompt to send to the LLM
            options: Optional configuration options
            patient_id: Patient identifier
            triage_system: Triage system name
            patient_data: Comprehensive patient data to store with cache
        """
        # If patient_id and triage_system provided directly, use them
        if patient_id and triage_system:
            cache_key = self._create_cache_key(triage_system, patient_id)
        else:
            # Add triage system to options for key generation
            if options is None:
                options = {}
            if triage_system:
                options['triage_system'] = triage_system
            cache_key = self._generate_cache_key(prompt, options)
        
        with self._lock:
            # Check if already cached in memory
            if cache_key in self.response_cache:
                logger.debug(f"Response already cached in memory for key {cache_key[:8]}...")
                return cache_key
            
            if cache_key in self.precompute_futures:
                logger.debug(f"Response already being computed for key {cache_key[:8]}...")
                return cache_key
        
        # Check persistent cache first
        persistent_data = self._load_individual_cache(cache_key)
        if persistent_data:
            with self._lock:
                self.response_cache[cache_key] = persistent_data
                if 'inference_time' in persistent_data:
                    self.inference_times.append(persistent_data['inference_time'])
            logger.debug(f"Loaded response from persistent cache for key {cache_key[:8]}...")
            return cache_key
        
        # Increment total requests counter
        with self._lock:
            self.total_requests += 1
        
        # Submit to thread pool for background computation
        future = self.executor.submit(self._compute_response, prompt, options, cache_key, patient_data)
        
        with self._lock:
            self.precompute_futures[cache_key] = future
        
        # Update progress tracking
        self._update_progress_file()
        
        logger.debug(f"Submitted LLM computation for cache key {cache_key[:8]}... (Total: {self.total_requests})")
        return cache_key
    
    def _compute_response(self, prompt: str, options: Optional[Dict[str, Any]], cache_key: str, patient_data: Optional[Dict[str, Any]] = None) -> str:
        """Compute LLM response in background thread"""
        try:
            start_time = time.time()
            logger.debug(f"Computing LLM response for key {cache_key[:8]}...")
            
            response = self.base_provider.generate_triage_decision(prompt, options)
            inference_time = time.time() - start_time
            
            response_data = {
                'response': response,
                'inference_time': inference_time,
                'timestamp': time.time()
            }
            
            with self._lock:
                # Store in memory cache
                self.response_cache[cache_key] = response_data
                
                # Track inference times for estimation
                self.inference_times.append(inference_time)
                if len(self.inference_times) > 100:  # Keep last 100 times
                    self.inference_times.pop(0)
                
                # Remove from futures
                if cache_key in self.precompute_futures:
                    del self.precompute_futures[cache_key]
                
                # Manage cache size
                if len(self.response_cache) > self.cache_size:
                    # Remove oldest entry
                    oldest_key = min(self.response_cache.keys(), 
                                   key=lambda k: self.response_cache[k]['timestamp'])
                    del self.response_cache[oldest_key]
            
            # Save to persistent cache with patient data (outside lock to avoid blocking)
            self._save_individual_cache(cache_key, response_data, patient_data)
            
            # Update progress tracking
            with self._lock:
                self.completed_requests += 1
            
            self._update_progress_file()
            
            # Log progress every 10 completions or on final completion
            if self.completed_requests % 10 == 0 or (self.completed_requests + self.failed_requests) == self.total_requests:
                self._log_progress()
            
            logger.debug(f"LLM response computed in {inference_time:.2f}s for key {cache_key[:8]}... ({self.completed_requests}/{self.total_requests})")
            return response
            
        except Exception as e:
            logger.error(f"Error computing LLM response for key {cache_key[:8]}...: {e}")
            
            error_data = {
                'response': f"Error: {str(e)}",
                'inference_time': 0.0,
                'timestamp': time.time(),
                'error': True
            }
            
            with self._lock:
                # Store error response in memory
                self.response_cache[cache_key] = error_data
                
                # Remove from futures
                if cache_key in self.precompute_futures:
                    del self.precompute_futures[cache_key]
            
            # Save error to persistent cache with patient data
            self._save_individual_cache(cache_key, error_data, patient_data)
            
            # Update progress tracking for failed request
            with self._lock:
                self.failed_requests += 1
            
            self._update_progress_file()
            
            # Log progress on failures too
            if self.failed_requests % 5 == 0 or (self.completed_requests + self.failed_requests) == self.total_requests:
                self._log_progress()
            
            return f"Error: {str(e)}"
    
    def get_cached_response(self, cache_key: str, timeout: float = 30.0) -> Optional[str]:
        """
        Get cached response, waiting for computation if necessary.
        This should be called during simulation and returns instantly if cached.
        """
        with self._lock:
            # Check if already in cache
            if cache_key in self.response_cache:
                response_data = self.response_cache[cache_key]
                logger.debug(f"Retrieved cached response for key {cache_key[:8]}...")
                return response_data['response']
            
            # Check if being computed
            if cache_key in self.precompute_futures:
                future = self.precompute_futures[cache_key]
            else:
                logger.warning(f"No cached response or computation found for key {cache_key[:8]}...")
                return None
        
        # Wait for computation to complete (outside lock)
        try:
            logger.debug(f"Waiting for LLM computation to complete for key {cache_key[:8]}...")
            future.result(timeout=timeout)
            
            # Now get from cache
            with self._lock:
                if cache_key in self.response_cache:
                    response_data = self.response_cache[cache_key]
                    return response_data['response']
                else:
                    logger.error(f"Response not found in cache after computation for key {cache_key[:8]}...")
                    return None
                    
        except Exception as e:
            logger.error(f"Error waiting for LLM computation for key {cache_key[:8]}...: {e}")
            return None
    
    def generate_triage_decision(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate triage decision. This method should NOT be called during simulation
        as it blocks. Use precompute_response + get_cached_response instead.
        """
        logger.warning("generate_triage_decision called directly - this may block simulation time!")
        return self.base_provider.generate_triage_decision(prompt, options)
    
    def estimate_inference_time(self) -> float:
        """
        Estimate LLM inference time based on historical data.
        Returns time in seconds.
        """
        with self._lock:
            if not self.inference_times:
                # Default estimate if no data
                return 2.0  # 2 seconds default
            
            # Return median of recent inference times
            import statistics
            return statistics.median(self.inference_times)
    
    def wait_for_precomputation(self, timeout: float = 300.0) -> bool:
        """Wait for all precomputation tasks to complete"""
        logger.info(f"Waiting for {len(self.precompute_futures)} precomputation tasks to complete...")
        
        start_time = time.time()
        completed_count = 0
        total_count = len(self.precompute_futures)
        
        # Wait for all futures to complete
        for cache_key, future in list(self.precompute_futures.items()):
            remaining_timeout = timeout - (time.time() - start_time)
            if remaining_timeout <= 0:
                logger.warning(f"Timeout reached while waiting for precomputation. {completed_count}/{total_count} completed.")
                return False
                
            try:
                future.result(timeout=remaining_timeout)
                completed_count += 1
                if completed_count % 10 == 0 or completed_count == total_count:
                    logger.info(f"Precomputation progress: {completed_count}/{total_count} completed")
            except Exception as e:
                logger.error(f"Error in precomputation task {cache_key[:8]}...: {e}")
                completed_count += 1
        
        elapsed_time = time.time() - start_time
        logger.info(f"Precomputation completed in {elapsed_time:.2f} seconds. {completed_count}/{total_count} tasks finished.")
        
        # Clear completed futures
        with self._lock:
            self.precompute_futures.clear()
            
        return True

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        with self._lock:
            memory_cache_size = len(self.response_cache)
            pending_computations = len(self.precompute_futures)
            avg_inference_time = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0.0
            total_inferences = len(self.inference_times)
        
        # Count persistent cache files
        persistent_cache_count = 0
        try:
            if os.path.exists(self.persistent_cache_dir):
                persistent_cache_count = len([f for f in os.listdir(self.persistent_cache_dir) 
                                            if f.endswith('.json')])
        except Exception:
            pass
        
        # Get progress stats
        progress_stats = self.get_progress_stats()
        
        return {
            'memory_cache_size': memory_cache_size,
            'max_cache_size': self.cache_size,
            'persistent_cache_size': persistent_cache_count,
            'persistent_cache_dir': self.persistent_cache_dir,
            'pending_computations': pending_computations,
            'avg_inference_time': avg_inference_time,
            'total_inferences': total_inferences,
            'progress': progress_stats
        }
    
    def health_check(self) -> bool:
        """Check if underlying provider is healthy"""
        return self.base_provider.health_check()
    
    def shutdown(self):
        """Shutdown the thread pool and clean up resources"""
        logger.info("Shutting down SimulationAwareProvider...")
        
        # Save current cache to persistent storage
        self._save_persistent_cache()
        
        self.executor.shutdown(wait=True)
        with self._lock:
            self.response_cache.clear()
            self.precompute_futures.clear()
        logger.info("SimulationAwareProvider shutdown complete")
    
    def force_save_cache(self):
        """Manually save current cache to persistent storage"""
        self._save_persistent_cache()
    
    def reset_progress_counters(self):
        """Reset progress tracking counters"""
        with self._lock:
            self.total_requests = 0
            self.completed_requests = 0
            self.failed_requests = 0
        
        self._update_progress_file()
        logger.info("Progress counters reset")
    
    def clear_persistent_cache(self):
        """Clear all persistent cache files"""
        try:
            # Remove main cache file
            cache_file = os.path.join(self.persistent_cache_dir, "llm_responses.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            # Remove progress file
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
            
            # Remove individual cache files
            for filename in os.listdir(self.persistent_cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.persistent_cache_dir, filename)
                    os.remove(file_path)
            
            # Clear memory cache and reset progress
            with self._lock:
                self.response_cache.clear()
                self.inference_times.clear()
                self.total_requests = 0
                self.completed_requests = 0
                self.failed_requests = 0
            
            # Update progress file with reset values
            self._update_progress_file()
            
            logger.info("Cleared all persistent cache files and reset progress")
        except Exception as e:
            logger.error(f"Error clearing persistent cache: {e}")