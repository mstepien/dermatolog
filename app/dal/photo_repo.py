
import logging
from typing import List, Optional, Tuple, Dict

logger = logging.getLogger(__name__)

class PhotoRepository:
    def __init__(self):
        # In-memory storage instead of DuckDB
        # key: session_id, value: { photo_id: metadata_dict }
        self._storage: Dict[str, Dict[str, dict]] = {}

    def _get_session_store(self, session_id: str) -> Dict[str, dict]:
        if session_id not in self._storage:
            self._storage[session_id] = {}
        return self._storage[session_id]

    def find_duplicate(self, session_id: str, file_hash: str) -> Optional[str]:
        store = self._get_session_store(session_id)
        for photo_id, metadata in store.items():
            if metadata.get("md5_hash") == file_hash:
                return photo_id
        return None

    def create_photo(self, photo_id: str, session_id: str, filename: str, ext: str, creation_date: str, file_hash: str, content: bytes):
        store = self._get_session_store(session_id)
        store[photo_id] = {
            "id": photo_id,
            "filename": filename,
            "content": content,
            "creation_date": creation_date,
            "uploaded_at": str(logging.Formatter().formatTime(logging.LogRecord(None, None, None, None, None, None, None), "%Y-%m-%d %H:%M:%S")),
            "md5_hash": file_hash,
            "analysis_results": None,
            "analysis_date": None
        }

    def get_timeline_photos(self, session_id: str) -> List[Tuple]:
        store = self._get_session_store(session_id)
        results = []
        # Convert to the tuple format expected by router
        # (id, filename, creation_date, uploaded_at, analysis_results, analysis_date)
        for p in store.values():
            results.append((
                p["id"],
                p["filename"],
                p["creation_date"],
                p["uploaded_at"],
                p["analysis_results"],
                p["analysis_date"]
            ))
        # Sort by creation_date DESC, then uploaded_at DESC
        return sorted(results, key=lambda x: (x[2], x[3]), reverse=True)

    def save_analysis_results(self, photo_id: str, session_id: str, results_json: str):
        store = self._get_session_store(session_id)
        if photo_id in store:
            store[photo_id]["analysis_results"] = results_json
            store[photo_id]["analysis_date"] = str(logging.Formatter().formatTime(logging.LogRecord(None, None, None, None, None, None, None), "%H:%M:%S"))
            
    def get_analysis_results(self, photo_id: str, session_id: str) -> Optional[Tuple[str, str]]:
        store = self._get_session_store(session_id)
        p = store.get(photo_id)
        if p and p["analysis_results"]:
            return (p["analysis_results"], p["analysis_date"])
        return None

    def update_date(self, photo_id: str, session_id: str, new_date: str):
        store = self._get_session_store(session_id)
        if photo_id in store:
            store[photo_id]["creation_date"] = new_date

    def get_photo_metadata(self, photo_id: str, session_id: str) -> Optional[Tuple[str, bytes]]:
        store = self._get_session_store(session_id)
        p = store.get(photo_id)
        if p:
            return (p["filename"], p["content"])
        return None

    def delete_photo(self, photo_id: str, session_id: str):
        store = self._get_session_store(session_id)
        if photo_id in store:
            del store[photo_id]

    def clear_session(self, session_id: str):
        if session_id in self._storage:
            del self._storage[session_id]

photo_repo = PhotoRepository()
