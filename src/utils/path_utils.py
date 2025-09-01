import os
from pathlib import Path
from typing import Union


class PathUtils:
    """Utility class for handling relative paths in the simulation"""
    
    @staticmethod
    def get_project_root() -> Path:
        """Get the project root directory"""
        # Find the project root by looking for key files
        current_path = Path(__file__).parent
        
        # Go up directories until we find the project root
        while current_path != current_path.parent:
            if (current_path / 'src').exists() and (current_path / 'requirements.txt').exists():
                return current_path
            current_path = current_path.parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    @staticmethod
    def resolve_relative_path(relative_path: Union[str, Path]) -> Path:
        """Resolve a relative path from the project root"""
        project_root = PathUtils.get_project_root()
        return project_root / relative_path
    
    @staticmethod
    def get_csv_directory() -> Path:
        """Get the CSV data directory path"""
        return PathUtils.resolve_relative_path('output/csv')
    
    @staticmethod
    def get_metrics_output_directory() -> Path:
        """Get the metrics output directory path"""
        return PathUtils.resolve_relative_path('metrics_output')
    
    @staticmethod
    def get_config_directory() -> Path:
        """Get the configuration directory path"""
        return PathUtils.resolve_relative_path('src/config')
    
    @staticmethod
    def ensure_directory_exists(path: Union[str, Path]) -> Path:
        """Ensure a directory exists, create if it doesn't"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    
    @staticmethod
    def get_relative_path_from_root(absolute_path: Union[str, Path]) -> Path:
        """Convert an absolute path to relative from project root"""
        project_root = PathUtils.get_project_root()
        absolute_path_obj = Path(absolute_path)
        
        try:
            return absolute_path_obj.relative_to(project_root)
        except ValueError:
            # If path is not under project root, return as-is
            return absolute_path_obj
    
    @staticmethod
    def validate_path_exists(path: Union[str, Path], path_type: str = "path") -> bool:
        """Validate that a path exists"""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"{path_type.title()} does not exist: {path_obj}")
        return True
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get a safe filename by removing invalid characters"""
        import re
        # Remove invalid characters for filenames
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        # Remove leading/trailing underscores
        return safe_name.strip('_')