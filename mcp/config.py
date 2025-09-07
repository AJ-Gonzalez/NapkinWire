"""
Configuration Management for NapkinWire
Handles YAML configuration loading with validation and environment variable overrides.
"""

import os
import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class PathsConfig:
    """Configuration for file and directory paths."""
    tickets_path: str = "tickets.json"
    logs_path: Optional[str] = None
    project_root: Optional[str] = None
    roadmap_path: str = "roadmap.md"
    queue_path: str = "ticket_queue"


@dataclass
class AppConfig:
    """Application-level configuration."""
    log_level: str = "INFO"
    dev_mode: bool = False
    diagram_timeout: int = 60


@dataclass
class InitiativeFeedConfig:
    """Initiative feed specific configuration."""
    db_path: str = "initiative_feed.db"
    retention_days: int = 30
    max_entries: int = 50


@dataclass
class Config:
    """Main configuration class."""
    paths: PathsConfig = field(default_factory=PathsConfig)
    app: AppConfig = field(default_factory=AppConfig)
    initiative_feed: InitiativeFeedConfig = field(default_factory=InitiativeFeedConfig)


class ConfigManager:
    """Manages configuration loading, validation, and environment overrides."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

    def _load_config(self) -> Config:
        """Load configuration from YAML file with fallback to defaults."""
        config_data = {}

        # Try to load from YAML file
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
                logging.info(f"Loaded configuration from {self.config_path}")
            except yaml.YAMLError as e:
                logging.error(f"Error parsing {self.config_path}: {e}")
                logging.info("Using default configuration")
            except Exception as e:
                logging.error(f"Error reading {self.config_path}: {e}")
                logging.info("Using default configuration")
        else:
            logging.info(f"Config file {self.config_path} not found, using defaults")

        # Apply environment variable overrides
        self._apply_env_overrides(config_data)

        # Create config objects with validation
        try:
            paths_data = config_data.get('paths', {})
            app_data = config_data.get('app', {})
            feed_data = config_data.get('initiative_feed', {})

            paths = PathsConfig(**paths_data)
            app = AppConfig(**app_data)
            initiative_feed = InitiativeFeedConfig(**feed_data)

            return Config(paths=paths, app=app, initiative_feed=initiative_feed)
        except TypeError as e:
            logging.error(f"Configuration validation error: {e}")
            logging.info("Using default configuration")
            return Config()

    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration."""
        # Override project root from environment
        env_project = os.getenv('NAPKINWIRE_PROJECT')
        if env_project:
            if 'paths' not in config_data:
                config_data['paths'] = {}
            config_data['paths']['project_root'] = env_project

        # Override config file path
        env_config = os.getenv('NAPKINWIRE_CONFIG')
        if env_config and env_config != self.config_path:
            self.config_path = env_config

        # Override tickets path
        env_tickets = os.getenv('NAPKINWIRE_TICKETS_PATH')
        if env_tickets:
            if 'paths' not in config_data:
                config_data['paths'] = {}
            config_data['paths']['tickets_path'] = env_tickets

        # Override logs path
        env_logs = os.getenv('NAPKINWIRE_LOGS_PATH')
        if env_logs:
            if 'paths' not in config_data:
                config_data['paths'] = {}
            config_data['paths']['logs_path'] = env_logs

    def _setup_logging(self) -> None:
        """Setup logging based on configuration."""
        log_level = getattr(logging, self.config.app.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def get_absolute_path(self, relative_path: str) -> str:
        """Convert relative path to absolute using project root."""
        if os.path.isabs(relative_path):
            return relative_path

        project_root = self.config.paths.project_root or os.getcwd()
        return os.path.join(project_root, relative_path)

    def get_tickets_path(self) -> str:
        """Get absolute path to tickets.json file."""
        return self.get_absolute_path(self.config.paths.tickets_path)

    def get_logs_path(self) -> Optional[str]:
        """Get path to Claude logs directory."""
        if self.config.paths.logs_path:
            return self.get_absolute_path(self.config.paths.logs_path)
        return None

    def get_roadmap_path(self) -> str:
        """Get absolute path to roadmap.md file."""
        return self.get_absolute_path(self.config.paths.roadmap_path)

    def get_queue_path(self) -> str:
        """Get absolute path to ticket queue directory."""
        return self.get_absolute_path(self.config.paths.queue_path)

    def get_feed_db_path(self) -> str:
        """Get absolute path to initiative feed database."""
        return self.get_absolute_path(self.config.initiative_feed.db_path)


# Global configuration instance
config_manager = ConfigManager()

# Backward compatibility - expose TICKETS for existing code
TICKETS = config_manager.get_tickets_path()