import logging
import json
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.logging import RichHandler
from rich.markup import escape

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventType(Enum):
    PATIENT_ARRIVAL = "PATIENT_ARRIVAL"
    PATIENT_REGISTRATION = "PATIENT_REGISTRATION"
    TRIAGE_START = "TRIAGE_START"
    TRIAGE_ASSESSMENT = "TRIAGE_ASSESSMENT"
    TRIAGE_COMPLETE = "TRIAGE_COMPLETE"
    QUEUE_ASSIGNMENT = "QUEUE_ASSIGNMENT"
    DOCTOR_ASSIGNMENT = "DOCTOR_ASSIGNMENT"
    TREATMENT_START = "TREATMENT_START"
    TREATMENT_COMPLETE = "TREATMENT_COMPLETE"
    PREEMPTION_DECISION = "PREEMPTION_DECISION"
    PREEMPTION_EXECUTED = "PREEMPTION_EXECUTED"
    QUEUE_UPDATE = "QUEUE_UPDATE"
    SYSTEM_STATE = "SYSTEM_STATE"
    SIMULATION_START = "SIMULATION_START"
    SIMULATION_END = "SIMULATION_END"

@dataclass
class LogEvent:
    timestamp: float
    event_type: EventType
    level: LogLevel
    message: str
    data: Dict[str, Any]
    source: str

class HospitalLogger:
    """Unified centralized logging system with rich text formatting"""
    
    def __init__(self, log_to_console: bool = True, log_to_file: bool = False, 
                 log_file_path: str = "simulation.log", min_level: LogLevel = LogLevel.INFO):
        self.min_level = min_level
        self.events: List[LogEvent] = []
        
        # Setup unified rich logging
        handlers = []
        
        # Console handler with rich formatting
        if log_to_console:
            console = Console(force_terminal=True, color_system="auto")
            console_handler = RichHandler(console=console, show_time=False, show_path=False, markup=True)
            console_handler.setLevel(getattr(logging, min_level.value))
            handlers.append(console_handler)
        
        # File handler with rich formatting
        if log_to_file:
            # Create rich text log file with HTML export capability
            self.log_file_path = log_file_path
            self.rich_log_file = log_file_path.replace('.log', '_rich.html')
            
            # Standard file handler for plain text logs
            file_handler = logging.FileHandler(log_file_path, mode='w')
            file_handler.setLevel(getattr(logging, min_level.value))
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
            
            # Rich console for HTML export (no output, just recording)
            self.file_console = Console(record=True, width=120, file=None)
            self.log_to_file_enabled = True
        else:
            self.log_to_file_enabled = False
            self.file_console = None
        
        # Configure unified logger
        logging.basicConfig(
            level=getattr(logging, min_level.value),
            format='%(message)s',
            handlers=handlers,
            force=True
        )
        
        self.logger = logging.getLogger('hospital_simulation')
        self.console = Console(force_terminal=True, color_system="auto") if log_to_console else None
        
        # Event type emojis and colors
        self.event_styles = {
            EventType.PATIENT_ARRIVAL: {"emoji": "🚑", "color": "blue", "style": "bold"},
            EventType.PATIENT_REGISTRATION: {"emoji": "📝", "color": "cyan", "style": "normal"},
            EventType.TRIAGE_START: {"emoji": "🩺", "color": "yellow", "style": "normal"},
            EventType.TRIAGE_ASSESSMENT: {"emoji": "⚕️", "color": "magenta", "style": "bold"},
            EventType.TRIAGE_COMPLETE: {"emoji": "✅", "color": "green", "style": "normal"},
            EventType.QUEUE_ASSIGNMENT: {"emoji": "📋", "color": "cyan", "style": "normal"},
            EventType.DOCTOR_ASSIGNMENT: {"emoji": "👨‍⚕️", "color": "blue", "style": "bold"},
            EventType.TREATMENT_START: {"emoji": "🏥", "color": "green", "style": "bold"},
            EventType.TREATMENT_COMPLETE: {"emoji": "🎉", "color": "bright_green", "style": "bold"},
            EventType.PREEMPTION_DECISION: {"emoji": "⚡", "color": "red", "style": "bold"},
            EventType.PREEMPTION_EXECUTED: {"emoji": "🔄", "color": "bright_red", "style": "bold"},
            EventType.QUEUE_UPDATE: {"emoji": "📊", "color": "white", "style": "dim"},
            EventType.SYSTEM_STATE: {"emoji": "💻", "color": "white", "style": "dim"},
            EventType.SIMULATION_START: {"emoji": "🚀", "color": "bright_blue", "style": "bold"},
            EventType.SIMULATION_END: {"emoji": "🏁", "color": "bright_green", "style": "bold"}
        }
        
        # Priority colors for triage
        self.priority_colors = {
            "RED": "bright_red",
            "ORANGE": "orange3",
            "YELLOW": "yellow",
            "GREEN": "green",
            "BLUE": "blue"
        }
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if event should be logged based on minimum level"""
        level_order = {LogLevel.DEBUG: 0, LogLevel.INFO: 1, LogLevel.WARNING: 2, 
                      LogLevel.ERROR: 3, LogLevel.CRITICAL: 4}
        return level_order[level] >= level_order[self.min_level]
    
    def log_event(self, timestamp: float, event_type: EventType, message: str, 
                  data: Dict[str, Any] = None, level: LogLevel = LogLevel.INFO, 
                  source: str = "unknown", simulation_state = None) -> None:
        """Log a simulation event with unified rich formatting"""
        if not self._should_log(level):
            return
            
        if data is None:
            data = {}
        
        # Enhance data with simulation state summary
        enhanced_data = self._enhance_log_data_with_simulation_state(data, simulation_state)
            
        event = LogEvent(
            timestamp=timestamp,
            event_type=event_type,
            level=level,
            message=message,
            data=enhanced_data,
            source=source
        )
        
        self.events.append(event)
        
        # Unified logging with rich formatting
        formatted_message = self._format_rich_message(event)
        log_method = getattr(self.logger, level.value.lower())
        
        # Log to standard logger (console and plain text file)
        log_method(formatted_message)
        
        # Also log to rich file console for HTML export
        if self.log_to_file_enabled:
            # Don't add timestamp since formatted_message already contains it
            self.file_console.print(formatted_message)
    
    def _enhance_log_data_with_simulation_state(self, data: dict, simulation_state) -> dict:
        """Enhance log data with simulation state summary"""
        enhanced_data = data.copy()
        
        # Add simulation state summary if provided
        if simulation_state is not None:
            enhanced_data["simulation_state"] = simulation_state.get_log_summary()
        
        return enhanced_data
    
    def _format_rich_message(self, event: LogEvent) -> str:
        """Format event with unified rich markup for both console and file"""
        # Get event styling
        style_info = self.event_styles.get(event.event_type, {"emoji": "📄", "color": "white", "style": "normal"})
        
        # Format timestamp with rich markup
        timestamp_str = f"[bold cyan]Time {event.timestamp:6.1f}[/bold cyan]"
        
        # Format emoji with color
        emoji_str = f"[{style_info['color']}] {style_info['emoji']} [/{style_info['color']}]"
        
        # Format message with appropriate colors and style
        color_style = f"{style_info['color']}"
        if style_info['style'] == 'bold':
            color_style = f"bold {style_info['color']}"
        elif style_info['style'] == 'dim':
            color_style = f"dim {style_info['color']}"
        
        message_str = f"[{color_style}]{event.message}[/{color_style}]"
        
        # Add priority coloring for triage events
        if event.event_type in [EventType.TRIAGE_ASSESSMENT, EventType.DOCTOR_ASSIGNMENT, EventType.TREATMENT_START]:
            message_str = self._colorize_priority_in_markup(event.message, color_style)
        
        # Level and source info
        level_str = ""
        if event.level != LogLevel.INFO:
            level_color = self._get_level_color(event.level)
            level_str = f" [bold {level_color}][{event.level.value}][/bold {level_color}]"
        
        source_str = ""
        if event.source != "unknown":
            source_str = f" [dim white]({event.source})[/dim white]"
        
        # Combine components
        full_message = f"{timestamp_str}:{emoji_str}{message_str}{level_str}{source_str}"
        
        # Add simulation state summary if present
        if event.data and "simulation_state" in event.data:
            sim_state = event.data["simulation_state"]
            state_str = (
                f" [dim blue]| SimState[T:{sim_state['simulation_time']:.1f}, "
                f"Arr:{sim_state['total_arrivals']}, "
                f"Comp:{sim_state['total_completed']}, "
                f"InSys:{sim_state['patients_in_system']}, "
                f"Busy:{sim_state['busy_doctors']}, "
                f"Avail:{sim_state['available_doctors']}, "
                f"Preempt:{sim_state['preemptions_count']}][/dim blue]"
            )
            full_message += state_str
        
        return full_message
    
    def _colorize_priority_in_markup(self, message: str, base_style: str) -> str:
        """Add priority-specific coloring to triage messages using markup"""
        for priority, color in self.priority_colors.items():
            if priority in message:
                # Replace priority word with colored version
                colored_priority = f"[bold {color}]{priority}[/bold {color}]"
                message = message.replace(priority, colored_priority)
        return f"[{base_style}]{message}[/{base_style}]"
    
    def _get_level_color(self, level: LogLevel) -> str:
        """Get color for log level"""
        level_colors = {
            LogLevel.DEBUG: "dim white",
            LogLevel.INFO: "white",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red",
            LogLevel.CRITICAL: "bright_red"
        }
        return level_colors.get(level, "white")
    
    # Convenience methods for different event types
    def log_patient_arrival(self, timestamp: float, patient_id: str, condition: str, 
                           vital_signs: Dict = None, simulation_state = None) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.PATIENT_ARRIVAL,
            message=f"Patient {patient_id} arrives with {condition}",
            simulation_state=simulation_state,
            data={"patient_id": patient_id, "condition": condition, "vital_signs": vital_signs or {}},
            source="patient_provider"
        )
    
    def log_triage_start(self, timestamp: float, patient_id: str, nurse_id: str = None) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.TRIAGE_START,
            message=f"Triage assessment started for Patient {patient_id}",
            data={"patient_id": patient_id, "nurse_id": nurse_id},
            source="triage_system"
        )
    
    def log_triage_assessment(self, timestamp: float, patient_id: str, priority: str, 
                             reason: str) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.TRIAGE_ASSESSMENT,
            message=f"Patient {patient_id} assessed as {priority} priority - {reason}",
            data={
                "patient_id": patient_id,
                "priority": priority,
                "reason": reason
            },
            source="triage_system"
        )
    
    def log_queue_assignment(self, timestamp: float, patient_id: str, priority: str, 
                           queue_position: int) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.QUEUE_ASSIGNMENT,
            message=f"Patient {patient_id} assigned to {priority} queue (position {queue_position})",
            data={"patient_id": patient_id, "priority": priority, "queue_position": queue_position},
            source="hospital_core"
        )
    
    def log_doctor_assignment(self, timestamp: float, patient_id: str, doctor_id: str, 
                             priority: str) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.DOCTOR_ASSIGNMENT,
            message=f"Doctor {doctor_id} assigned to Patient {patient_id} ({priority})",
            data={"patient_id": patient_id, "doctor_id": doctor_id, "priority": priority},
            source="hospital_core"
        )
    
    def log_treatment_start(self, timestamp: float, patient_id: str, doctor_id: str) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.TREATMENT_START,
            message=f"Treatment started: Doctor {doctor_id} treating Patient {patient_id}",
            data={"patient_id": patient_id, "doctor_id": doctor_id},
            source="simulation_engine"
        )
    
    def log_treatment_complete(self, timestamp: float, patient_id: str, doctor_id: str, 
                              wait_time: float) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.TREATMENT_COMPLETE,
            message=f"Treatment completed: Doctor {doctor_id} finished Patient {patient_id} (wait: {wait_time:.1f}min)",
            data={"patient_id": patient_id, "doctor_id": doctor_id, "wait_time": wait_time},
            source="simulation_engine"
        )
    
    def log_preemption_decision(self, timestamp: float, decision: bool, reason: str, 
                               new_patient_id: str, affected_patients: List[str] = None) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Preemption {'APPROVED' if decision else 'DENIED'}: {reason}",
            data={
                "decision": decision,
                "reason": reason,
                "new_patient_id": new_patient_id,
                "affected_patients": affected_patients or []
            },
            level=LogLevel.WARNING if decision else LogLevel.INFO,
            source="preemption_agent"
        )
    
    def log_system_state(self, timestamp: float, queue_lengths: Dict[str, int], 
                        doctor_status: Dict[str, Dict], total_patients: int) -> None:
        self.log_event(
            timestamp=timestamp,
            event_type=EventType.SYSTEM_STATE,
            message=f"System state: {total_patients} patients, queues: {queue_lengths}",
            data={
                "queue_lengths": queue_lengths,
                "doctor_status": doctor_status,
                "total_patients": total_patients
            },
            level=LogLevel.DEBUG,
            source="hospital_core"
        )
    
    def get_events_by_type(self, event_type: EventType) -> List[LogEvent]:
        """Get all events of a specific type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_by_patient(self, patient_id: str) -> List[LogEvent]:
        """Get all events related to a specific patient"""
        return [event for event in self.events 
                if "patient_id" in event.data and event.data["patient_id"] == patient_id]
    
    def export_to_json(self, filename: str) -> None:
        """Export all events to JSON file"""
        events_data = []
        for event in self.events:
            event_dict = asdict(event)
            event_dict['event_type'] = event.event_type.value
            event_dict['level'] = event.level.value
            events_data.append(event_dict)
        
        with open(filename, 'w') as f:
            json.dump(events_data, f, indent=2)
    
    def export_rich_html(self, filename: str = None) -> str:
        """Export rich formatted logs to HTML file"""
        if not self.log_to_file_enabled or self.file_console is None:
            return "Rich file logging not enabled"
        
        if filename is None:
            filename = self.rich_log_file
        
        # Generate HTML with rich formatting
        html_content = self.file_console.export_html(
            inline_styles=True
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return f"Rich HTML log exported to: {filename}"
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of logged events"""
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_events": len(self.events),
            "event_type_counts": event_counts,
            "time_range": {
                "start": min(event.timestamp for event in self.events) if self.events else 0,
                "end": max(event.timestamp for event in self.events) if self.events else 0
            }
        }

# Global logger instance
_global_logger: Optional[HospitalLogger] = None

def get_logger() -> HospitalLogger:
    """Get the global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = HospitalLogger()
    return _global_logger

def initialize_logger(log_to_console: bool = True, log_to_file: bool = False, 
                     log_file_path: str = "simulation.log", 
                     min_level: LogLevel = LogLevel.INFO) -> HospitalLogger:
    """Initialize the global logger with specific settings"""
    global _global_logger
    _global_logger = HospitalLogger(log_to_console, log_to_file, log_file_path, min_level)
    return _global_logger