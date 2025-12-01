"""
Upload handler for Substack export data.
Handles zip extraction, validation, and dataset management.
"""
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from config import (
    DATA_DIR,
    MANIFEST_FILE,
    OPTIONAL_FILES,
    REQUIRED_DIRS,
    REQUIRED_FILES,
    REQUIRED_PATTERNS,
)


def ensure_data_dir() -> Path:
    """Ensure the .data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)
    return DATA_DIR


def generate_dataset_id() -> str:
    """Generate a unique dataset ID based on current timestamp."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def find_email_list_file(dir_path: Path) -> Optional[Path]:
    """Find the email list CSV file using glob pattern."""
    for pattern in REQUIRED_PATTERNS:
        matches = list(dir_path.glob(pattern))
        if matches:
            return matches[0]
    return None


def validate_export_structure(dir_path: Path) -> tuple[bool, list[str]]:
    """
    Validate that a directory contains a valid Substack export.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required files
    for filename in REQUIRED_FILES:
        if not (dir_path / filename).exists():
            errors.append(f"Missing required file: {filename}")

    # Check required patterns (like email_list*.csv)
    for pattern in REQUIRED_PATTERNS:
        if not list(dir_path.glob(pattern)):
            errors.append(f"Missing required file matching: {pattern}")

    # Check required directories
    for dirname in REQUIRED_DIRS:
        if not (dir_path / dirname).is_dir():
            errors.append(f"Missing required directory: {dirname}")

    # Check posts directory has content
    posts_dir = dir_path / "posts"
    if posts_dir.is_dir():
        opens_files = list(posts_dir.glob("*.opens.csv"))
        delivers_files = list(posts_dir.glob("*.delivers.csv"))
        if not opens_files and not delivers_files:
            errors.append("Posts directory exists but contains no engagement data")

    return len(errors) == 0, errors


def extract_substack_export(zip_file, target_dir: Path) -> tuple[bool, str]:
    """
    Extract a Substack export zip file to the target directory.

    Args:
        zip_file: File-like object or path to zip file
        target_dir: Directory to extract to

    Returns:
        Tuple of (success, message)
    """
    try:
        target_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_file, 'r') as zf:
            # Check for nested directory structure
            # Substack exports sometimes have a root folder
            namelist = zf.namelist()

            # Find the root - check if all files share a common prefix directory
            root_dirs = set()
            for name in namelist:
                parts = name.split('/')
                if len(parts) > 1 and parts[0]:
                    root_dirs.add(parts[0])

            # If there's exactly one root directory, extract with flattening
            if len(root_dirs) == 1:
                root_dir = list(root_dirs)[0]
                for member in zf.namelist():
                    if member.startswith(root_dir + '/'):
                        # Remove the root directory prefix
                        new_path = member[len(root_dir) + 1:]
                        if new_path:  # Skip the root directory itself
                            if member.endswith('/'):
                                # It's a directory
                                (target_dir / new_path).mkdir(parents=True, exist_ok=True)
                            else:
                                # It's a file
                                (target_dir / new_path).parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(member) as src, open(target_dir / new_path, 'wb') as dst:
                                    dst.write(src.read())
            else:
                # Extract directly
                zf.extractall(target_dir)

        return True, "Export extracted successfully"

    except zipfile.BadZipFile:
        return False, "Invalid zip file"
    except Exception as e:
        return False, f"Extraction failed: {str(e)}"


def get_dataset_stats(dir_path: Path) -> dict:
    """Get statistics about a dataset."""
    stats = {
        "subscriber_count": 0,
        "post_count": 0,
        "has_subscriber_details": False,
        "email_list_file": None,
    }

    # Find email list file
    email_list = find_email_list_file(dir_path)
    if email_list:
        stats["email_list_file"] = email_list.name
        try:
            df = pd.read_csv(email_list)
            stats["subscriber_count"] = len(df)
        except Exception:
            pass

    # Count posts
    posts_file = dir_path / "posts.csv"
    if posts_file.exists():
        try:
            df = pd.read_csv(posts_file)
            stats["post_count"] = len(df)
        except Exception:
            pass

    # Check for subscriber details
    for filename in OPTIONAL_FILES:
        if (dir_path / filename).exists():
            if filename == "subscriber_details.csv":
                stats["has_subscriber_details"] = True

    return stats


def create_manifest(dir_path: Path, source_filename: str) -> dict:
    """Create a manifest file for the dataset."""
    stats = get_dataset_stats(dir_path)

    manifest = {
        "upload_date": datetime.now().isoformat(),
        "source_filename": source_filename,
        "has_subscriber_details": stats["has_subscriber_details"],
        "subscriber_count": stats["subscriber_count"],
        "post_count": stats["post_count"],
        "email_list_file": stats["email_list_file"],
    }

    manifest_path = dir_path / MANIFEST_FILE
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def load_manifest(dir_path: Path) -> Optional[dict]:
    """Load manifest from a dataset directory."""
    manifest_path = dir_path / MANIFEST_FILE
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return None


def get_available_datasets() -> list[dict]:
    """
    Get list of available datasets in the .data directory.

    Returns:
        List of dicts with dataset info, sorted by upload date (newest first)
    """
    ensure_data_dir()
    datasets = []

    for item in DATA_DIR.iterdir():
        if item.is_dir():
            manifest = load_manifest(item)
            if manifest:
                datasets.append({
                    "path": str(item),
                    "id": item.name,
                    **manifest
                })
            else:
                # Try to validate and create manifest if missing
                is_valid, _ = validate_export_structure(item)
                if is_valid:
                    stats = get_dataset_stats(item)
                    datasets.append({
                        "path": str(item),
                        "id": item.name,
                        "upload_date": None,
                        "source_filename": "Unknown",
                        **stats
                    })

    # Sort by upload date (newest first), with None dates last
    datasets.sort(
        key=lambda x: x.get("upload_date") or "0000-00-00",
        reverse=True
    )

    return datasets


def delete_dataset(dataset_path: str) -> tuple[bool, str]:
    """
    Delete a dataset directory.

    Args:
        dataset_path: Path to the dataset directory

    Returns:
        Tuple of (success, message)
    """
    try:
        path = Path(dataset_path)
        if not path.exists():
            return False, "Dataset not found"

        if not path.is_relative_to(DATA_DIR.resolve()):
            return False, "Invalid dataset path"

        shutil.rmtree(path)
        return True, "Dataset deleted successfully"

    except Exception as e:
        return False, f"Failed to delete dataset: {str(e)}"


def add_subscriber_details(dataset_path: str, file_content) -> tuple[bool, str]:
    """
    Add subscriber_details.csv to an existing dataset.

    Args:
        dataset_path: Path to the dataset directory
        file_content: File-like object with CSV content

    Returns:
        Tuple of (success, message)
    """
    try:
        path = Path(dataset_path)
        if not path.exists():
            return False, "Dataset not found"

        # Save the file
        details_path = path / "subscriber_details.csv"

        # Read and validate it's a proper CSV
        content = file_content.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        # Basic validation - try to parse as CSV
        from io import StringIO
        df = pd.read_csv(StringIO(content))

        # Check for expected columns
        expected_cols = ['Email', 'Type', 'Emails received (6mo)']
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            return False, f"Missing expected columns: {', '.join(missing)}"

        # Save the file
        with open(details_path, 'w') as f:
            f.write(content)

        # Update manifest
        manifest = load_manifest(path)
        if manifest:
            manifest["has_subscriber_details"] = True
            with open(path / MANIFEST_FILE, 'w') as f:
                json.dump(manifest, f, indent=2)

        return True, f"Added subscriber details ({len(df)} subscribers)"

    except pd.errors.EmptyDataError:
        return False, "File is empty"
    except pd.errors.ParserError as e:
        return False, f"Invalid CSV format: {str(e)}"
    except Exception as e:
        return False, f"Failed to add subscriber details: {str(e)}"


def process_upload(zip_file, filename: str) -> tuple[bool, str, Optional[str]]:
    """
    Process a complete Substack export upload.

    Args:
        zip_file: File-like object containing the zip
        filename: Original filename

    Returns:
        Tuple of (success, message, dataset_path or None)
    """
    ensure_data_dir()

    # Generate unique dataset ID
    dataset_id = generate_dataset_id()
    target_dir = DATA_DIR / dataset_id

    # Extract zip
    success, msg = extract_substack_export(zip_file, target_dir)
    if not success:
        # Clean up on failure
        if target_dir.exists():
            shutil.rmtree(target_dir)
        return False, msg, None

    # Validate structure
    is_valid, errors = validate_export_structure(target_dir)
    if not is_valid:
        # Clean up on failure
        shutil.rmtree(target_dir)
        return False, "Invalid export structure:\n- " + "\n- ".join(errors), None

    # Create manifest
    manifest = create_manifest(target_dir, filename)

    return True, f"Successfully imported {manifest['subscriber_count']} subscribers and {manifest['post_count']} posts", str(target_dir)
