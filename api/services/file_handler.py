"""
File handling service for managing uploads and temporary files
"""

import os
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from fastapi import UploadFile
import aiofiles

from ..utils.validators import FileValidator, DataValidator
from ..utils.exceptions import FileValidationError, FileProcessingError


class FileHandler:
    """Service for handling file uploads and temporary file management."""
    
    def __init__(self, temp_dir: str = "/tmp/psychometric_api", max_age_hours: int = 24):
        """
        Initialize file handler.
        
        Args:
            temp_dir: Directory for temporary files (default: /tmp/psychometric_api for containers)
            max_age_hours: Maximum age of temporary files before cleanup
        """
        # Debug what's being passed in
        import traceback
        print(f"DEBUG: FileHandler.__init__ called with temp_dir='{temp_dir}'")
        print("Call stack:")
        traceback.print_stack(limit=5)
        
        # Force use of /tmp in containers for write permissions
        self.temp_dir = Path(temp_dir)
        print(f"DEBUG: Set self.temp_dir to {self.temp_dir}")
        
        self.temp_dir.mkdir(exist_ok=True, mode=0o777)
        self.max_age_hours = max_age_hours
        self.file_validator = FileValidator()
        self.data_validator = DataValidator()
        self.logger = logging.getLogger(__name__)
        
        # Create subdirectories
        self.uploads_dir = self.temp_dir / "uploads"
        self.processing_dir = self.temp_dir / "processing"
        self.uploads_dir.mkdir(exist_ok=True, mode=0o777)
        self.processing_dir.mkdir(exist_ok=True, mode=0o777)
    
    async def save_uploaded_file(self, file: UploadFile, assessment_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save an uploaded file to temporary storage.
        
        Args:
            file: Uploaded file object
            assessment_id: Optional assessment ID for organizing files
            
        Returns:
            Dictionary with file information
            
        Raises:
            FileValidationError: If file validation fails
            FileProcessingError: If file processing fails
        """
        try:
            # Validate file
            validation_result = self.file_validator.validate_file(file)
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            original_name = file.filename
            file_extension = Path(original_name).suffix
            temp_filename = f"{file_id}{file_extension}"
            
            # Determine file path
            if assessment_id:
                file_dir = self.uploads_dir / assessment_id
                file_dir.mkdir(exist_ok=True)
            else:
                file_dir = self.uploads_dir
            
            temp_file_path = file_dir / temp_filename
            
            # Save file
            async with aiofiles.open(temp_file_path, 'wb') as temp_file:
                content = await file.read()
                await temp_file.write(content)
            
            # Validate content
            content_validation = self.file_validator.validate_file_content(str(temp_file_path))
            
            file_info = {
                "file_id": file_id,
                "original_name": original_name,
                "temp_path": str(temp_file_path),
                "file_size": len(content),
                "content_type": file.content_type,
                "extension": file_extension,
                "assessment_id": assessment_id,
                "uploaded_at": datetime.now(),
                "validation": validation_result,
                "content_validation": content_validation
            }
            
            self.logger.info(f"File saved: {original_name} -> {temp_file_path}")
            return file_info
            
        except Exception as e:
            self.logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise FileProcessingError(f"Failed to save file: {str(e)}")
    
    async def save_batch_files(self, files: List[UploadFile], batch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save multiple uploaded files.
        
        Args:
            files: List of uploaded file objects
            batch_id: Optional batch ID for organizing files
            
        Returns:
            Dictionary with batch information
            
        Raises:
            FileValidationError: If file validation fails
            FileProcessingError: If file processing fails
        """
        try:
            # Validate batch
            batch_validation = self.file_validator.validate_batch_files(files)
            
            batch_id = batch_id or str(uuid.uuid4())
            batch_dir = self.uploads_dir / batch_id
            batch_dir.mkdir(exist_ok=True)
            
            saved_files = []
            total_size = 0
            
            for file in files:
                file_info = await self.save_uploaded_file(file, batch_id)
                saved_files.append(file_info)
                total_size += file_info["file_size"]
            
            batch_info = {
                "batch_id": batch_id,
                "total_files": len(files),
                "total_size": total_size,
                "files": saved_files,
                "uploaded_at": datetime.now(),
                "batch_validation": batch_validation
            }
            
            self.logger.info(f"Batch saved: {len(files)} files, {total_size} bytes")
            return batch_info
            
        except Exception as e:
            self.logger.error(f"Error saving batch files: {str(e)}")
            raise FileProcessingError(f"Failed to save batch files: {str(e)}")
    
    def move_to_processing(self, file_path: str, assessment_id: str) -> str:
        """
        Move file from uploads to processing directory.
        
        Args:
            file_path: Current file path
            assessment_id: Assessment ID
            
        Returns:
            New file path in processing directory
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileProcessingError(f"Source file not found: {file_path}")
            
            # Create processing directory for assessment
            processing_path = self.processing_dir / assessment_id
            processing_path.mkdir(exist_ok=True)
            
            # Move file
            dest_path = processing_path / source_path.name
            shutil.move(str(source_path), str(dest_path))
            
            self.logger.info(f"File moved to processing: {source_path} -> {dest_path}")
            return str(dest_path)
            
        except Exception as e:
            self.logger.error(f"Error moving file to processing: {str(e)}")
            raise FileProcessingError(f"Failed to move file: {str(e)}")
    
    def cleanup_temp_files(self, max_age_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep (uses instance default if None)
            
        Returns:
            Dictionary with cleanup statistics
        """
        max_age = max_age_hours or self.max_age_hours
        cutoff_time = datetime.now() - timedelta(hours=max_age)
        
        cleanup_stats = {
            "files_deleted": 0,
            "directories_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }
        
        try:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleanup_stats["files_deleted"] += 1
                            cleanup_stats["bytes_freed"] += file_size
                    except Exception as e:
                        cleanup_stats["errors"].append(f"Error deleting {file_path}: {str(e)}")
                
                # Clean up empty directories
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if dir_path.is_dir() and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            cleanup_stats["directories_deleted"] += 1
                    except Exception as e:
                        cleanup_stats["errors"].append(f"Error deleting directory {dir_path}: {str(e)}")
            
            self.logger.info(f"Cleanup completed: {cleanup_stats['files_deleted']} files, "
                           f"{cleanup_stats['bytes_freed']} bytes freed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
            cleanup_stats["errors"].append(str(e))
        
        return cleanup_stats
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileProcessingError(f"File not found: {file_path}")
            
            stat = path.stat()
            return {
                "file_path": str(path),
                "file_name": path.name,
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime),
                "created_time": datetime.fromtimestamp(stat.st_ctime),
                "extension": path.suffix,
                "is_file": path.is_file(),
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting file info: {str(e)}")
            raise FileProcessingError(f"Failed to get file info: {str(e)}")
    
    def create_temp_file(self, suffix: str = ".tmp", prefix: str = "psych_") -> str:
        """
        Create a temporary file.
        
        Args:
            suffix: File suffix
            prefix: File prefix
            
        Returns:
            Path to temporary file
        """
        try:
            temp_fd, temp_path = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=self.temp_dir
            )
            os.close(temp_fd)  # Close the file descriptor
            return temp_path
            
        except Exception as e:
            self.logger.error(f"Error creating temp file: {str(e)}")
            raise FileProcessingError(f"Failed to create temp file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                self.logger.info(f"File deleted: {file_path}")
                return True
            else:
                self.logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def delete_directory(self, dir_path: str) -> bool:
        """
        Delete a directory and all its contents.
        
        Args:
            dir_path: Path to the directory to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
                self.logger.info(f"Directory deleted: {dir_path}")
                return True
            else:
                self.logger.warning(f"Directory not found for deletion: {dir_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting directory {dir_path}: {str(e)}")
            return False
    
    def get_temp_dir_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the temporary directory.
        
        Returns:
            Dictionary with directory statistics
        """
        try:
            total_files = 0
            total_size = 0
            directories = 0
            
            for root, dirs, files in os.walk(self.temp_dir):
                directories += len(dirs)
                for file in files:
                    file_path = Path(root) / file
                    try:
                        total_files += 1
                        total_size += file_path.stat().st_size
                    except Exception:
                        pass  # Skip files that can't be accessed
            
            return {
                "total_files": total_files,
                "total_directories": directories,
                "total_size": total_size,
                "temp_dir": str(self.temp_dir),
                "free_space": shutil.disk_usage(self.temp_dir).free
            }
            
        except Exception as e:
            self.logger.error(f"Error getting temp dir stats: {str(e)}")
            return {
                "error": str(e),
                "temp_dir": str(self.temp_dir)
            }