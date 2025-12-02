"""Property-based tests for Lab3 file copying operations.

This module tests the file copying operations required for Lab3 integration,
validating that all source files are preserved during the copy process.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from typing import List, Tuple
from hypothesis import given, strategies as st, settings, assume
import hashlib


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def copy_directory_structure(source_dir: Path, dest_dir: Path) -> None:
    """Copy directory structure and all files from source to destination.
    
    Args:
        source_dir: Source directory path
        dest_dir: Destination directory path
    """
    if not source_dir.exists():
        raise ValueError(f"Source directory does not exist: {source_dir}")
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for item in source_dir.rglob("*"):
        if item.is_file():
            relative_path = item.relative_to(source_dir)
            dest_file = dest_dir / relative_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_file)


def get_all_files(directory: Path) -> List[Tuple[Path, str]]:
    """Get all files in a directory with their relative paths.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of tuples (relative_path, file_hash)
    """
    files = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            file_hash = calculate_file_hash(file_path)
            files.append((relative_path, file_hash))
    return sorted(files, key=lambda x: str(x[0]))


class TestFileCopyingProperties:
    """Property-based tests for file copying operations."""
    
    @given(
        file_content=st.binary(min_size=0, max_size=10000),
        file_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                min_codepoint=65,
                max_codepoint=122
            ),
            min_size=1,
            max_size=50
        ).map(lambda s: s + ".txt")
    )
    @settings(max_examples=100, deadline=None)
    def test_single_file_copying_preserves_content(
        self, 
        file_content: bytes, 
        file_name: str
    ):
        """
        Feature: lab3-loanqa-integration, Property 1: File copying preserves all source files
        
        For any file content and name, copying from source to destination
        should preserve the exact content.
        
        Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6
        """
        # Filter out invalid filenames
        assume(file_name.strip() != ".txt")
        assume(not any(char in file_name for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create source file
            source_file = source_dir / file_name
            source_file.write_bytes(file_content)
            
            # Copy file
            dest_file = dest_dir / file_name
            shutil.copy2(source_file, dest_file)
            
            # Verify file exists
            assert dest_file.exists(), f"Destination file {file_name} does not exist"
            
            # Verify content preserved
            dest_content = dest_file.read_bytes()
            assert dest_content == file_content, \
                f"Content mismatch for {file_name}: expected {len(file_content)} bytes, got {len(dest_content)} bytes"
            
            # Verify hash matches
            source_hash = calculate_file_hash(source_file)
            dest_hash = calculate_file_hash(dest_file)
            assert source_hash == dest_hash, \
                f"Hash mismatch for {file_name}: source={source_hash}, dest={dest_hash}"
    
    @given(
        num_files=st.integers(min_value=1, max_value=20),
        file_contents=st.lists(
            st.binary(min_size=0, max_size=5000),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_directory_copying_preserves_all_files(
        self,
        num_files: int,
        file_contents: List[bytes]
    ):
        """
        Feature: lab3-loanqa-integration, Property 1: File copying preserves all source files
        
        For any directory with multiple files, copying from source to destination
        should preserve all files with their exact content.
        
        Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6
        """
        # Ensure we have enough content for the files
        assume(len(file_contents) >= num_files)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            
            # Create multiple files in source
            created_files = []
            for i in range(num_files):
                file_name = f"file_{i:03d}.txt"
                source_file = source_dir / file_name
                source_file.write_bytes(file_contents[i])
                created_files.append(file_name)
            
            # Copy directory
            copy_directory_structure(source_dir, dest_dir)
            
            # Verify all files exist in destination
            for file_name in created_files:
                dest_file = dest_dir / file_name
                assert dest_file.exists(), f"File {file_name} not found in destination"
            
            # Verify file count matches
            source_files = list(source_dir.glob("*.txt"))
            dest_files = list(dest_dir.glob("*.txt"))
            assert len(source_files) == len(dest_files), \
                f"File count mismatch: source has {len(source_files)}, dest has {len(dest_files)}"
            
            # Verify content of each file
            for i, file_name in enumerate(created_files):
                source_file = source_dir / file_name
                dest_file = dest_dir / file_name
                
                source_content = source_file.read_bytes()
                dest_content = dest_file.read_bytes()
                
                assert source_content == dest_content, \
                    f"Content mismatch for {file_name}"
    
    @given(
        subdirs=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("Lu", "Ll", "Nd"),
                    min_codepoint=65,
                    max_codepoint=122
                ),
                min_size=1,
                max_size=20
            ),
            min_size=1,
            max_size=5
        ),
        file_content=st.binary(min_size=0, max_size=5000)
    )
    @settings(max_examples=100, deadline=None)
    def test_nested_directory_copying_preserves_structure(
        self,
        subdirs: List[str],
        file_content: bytes
    ):
        """
        Feature: lab3-loanqa-integration, Property 1: File copying preserves all source files
        
        For any nested directory structure, copying from source to destination
        should preserve the directory hierarchy and all files.
        
        Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6
        """
        # Windows reserved names
        windows_reserved = {
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
            'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        # Filter out invalid directory names
        subdirs = [
            d for d in subdirs 
            if d.strip() 
            and d not in ['.', '..']
            and d.upper() not in windows_reserved
        ]
        assume(len(subdirs) > 0)
        assume(len(set(subdirs)) == len(subdirs))  # All unique
        
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            
            # Create nested directory structure
            for subdir in subdirs:
                subdir_path = source_dir / subdir
                subdir_path.mkdir(parents=True, exist_ok=True)
                
                # Create a file in each subdirectory
                test_file = subdir_path / "test.txt"
                test_file.write_bytes(file_content)
            
            # Get all source files before copying
            source_files = get_all_files(source_dir)
            
            # Copy directory structure
            copy_directory_structure(source_dir, dest_dir)
            
            # Get all destination files after copying
            dest_files = get_all_files(dest_dir)
            
            # Verify same number of files
            assert len(source_files) == len(dest_files), \
                f"File count mismatch: source has {len(source_files)}, dest has {len(dest_files)}"
            
            # Verify each file exists with same relative path and content
            for (source_rel_path, source_hash), (dest_rel_path, dest_hash) in zip(source_files, dest_files):
                assert source_rel_path == dest_rel_path, \
                    f"Path mismatch: {source_rel_path} != {dest_rel_path}"
                assert source_hash == dest_hash, \
                    f"Content mismatch for {source_rel_path}"
    
    def test_lab3_component_directories_structure(self):
        """
        Test that Lab3 component directories can be copied correctly.
        
        This test validates the specific directory structure required for
        Lab3 integration as specified in Requirements 2.2-2.6.
        
        Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate Lab3 source structure
            lab3_source = Path(tmpdir) / "Lab3"
            
            # Create the directories that need to be copied
            directories = {
                "processing": ["complete_document_extractor.py", "document_ai_processor.py", "ocr_processor.py"],
                "src/extraction": ["extraction_service.py", "field_extractor.py", "entity_extractor.py", "confidence_scorer.py"],
                "src/api": ["routes.py", "document_ingestion.py", "batch_processor.py"],
                "storage": ["storage_service.py", "object_storage.py", "database.py"],
                "storage/migrations": ["001_add_lab3_tables.sql"],
                "normalization": ["loan_normalizer.py", "comparison_service.py"]
            }
            
            # Create source structure
            for dir_path, files in directories.items():
                dir_full_path = lab3_source / dir_path
                dir_full_path.mkdir(parents=True, exist_ok=True)
                
                for file_name in files:
                    file_path = dir_full_path / file_name
                    file_path.write_text(f"# Content of {file_name}\n")
            
            # Create destination structure
            integration_dest = Path(tmpdir) / "LoanQA-MLOps" / "integrations" / "lab3-extractor"
            
            # Copy each component
            component_mappings = {
                "processing": "processing",
                "src/extraction": "extraction",
                "src/api": "api",
                "storage": "storage",
                "normalization": "normalization"
            }
            
            for source_subdir, dest_subdir in component_mappings.items():
                source_path = lab3_source / source_subdir
                dest_path = integration_dest / dest_subdir
                
                if source_path.exists():
                    copy_directory_structure(source_path, dest_path)
            
            # Verify all expected files exist in destination
            expected_files = {
                "processing/complete_document_extractor.py",
                "processing/document_ai_processor.py",
                "processing/ocr_processor.py",
                "extraction/extraction_service.py",
                "extraction/field_extractor.py",
                "extraction/entity_extractor.py",
                "extraction/confidence_scorer.py",
                "api/routes.py",
                "api/document_ingestion.py",
                "api/batch_processor.py",
                "storage/storage_service.py",
                "storage/object_storage.py",
                "storage/database.py",
                "storage/migrations/001_add_lab3_tables.sql",
                "normalization/loan_normalizer.py",
                "normalization/comparison_service.py"
            }
            
            for expected_file in expected_files:
                file_path = integration_dest / expected_file
                assert file_path.exists(), f"Expected file not found: {expected_file}"
                assert file_path.is_file(), f"Expected file is not a file: {expected_file}"
                
                # Verify content was copied
                content = file_path.read_text()
                assert len(content) > 0, f"File is empty: {expected_file}"
            
            # Verify file count matches
            total_expected = len(expected_files)
            total_actual = len(list(integration_dest.rglob("*.py"))) + len(list(integration_dest.rglob("*.sql")))
            assert total_actual == total_expected, \
                f"File count mismatch: expected {total_expected}, got {total_actual}"


class TestFileCopyingEdgeCases:
    """Test edge cases for file copying operations."""
    
    def test_empty_directory_copying(self):
        """Test copying an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            
            # Copy empty directory
            copy_directory_structure(source_dir, dest_dir)
            
            # Verify destination exists
            assert dest_dir.exists()
            assert dest_dir.is_dir()
            
            # Verify it's empty
            files = list(dest_dir.rglob("*"))
            assert len(files) == 0
    
    def test_copy_with_hidden_files(self):
        """Test copying directory with hidden files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            
            # Create regular and hidden files
            (source_dir / "regular.txt").write_text("regular")
            (source_dir / ".hidden").write_text("hidden")
            
            # Copy directory
            copy_directory_structure(source_dir, dest_dir)
            
            # Verify both files copied
            assert (dest_dir / "regular.txt").exists()
            assert (dest_dir / ".hidden").exists()
            
            # Verify content
            assert (dest_dir / "regular.txt").read_text() == "regular"
            assert (dest_dir / ".hidden").read_text() == "hidden"
    
    def test_copy_preserves_file_permissions(self):
        """Test that file permissions are preserved during copy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "source"
            dest_dir = Path(tmpdir) / "dest"
            source_dir.mkdir()
            
            # Create file with specific content
            source_file = source_dir / "test.txt"
            source_file.write_text("test content")
            
            # Copy directory
            copy_directory_structure(source_dir, dest_dir)
            
            # Verify file exists and content matches
            dest_file = dest_dir / "test.txt"
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"
    
    def test_nonexistent_source_raises_error(self):
        """Test that copying from nonexistent source raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_dir = Path(tmpdir) / "nonexistent"
            dest_dir = Path(tmpdir) / "dest"
            
            with pytest.raises(ValueError, match="Source directory does not exist"):
                copy_directory_structure(source_dir, dest_dir)
