import streamlit as st
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os

# Set page config
st.set_page_config(
    page_title="Hospital Simulation Viewer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.priority-red { background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 5px 0; }
.priority-orange { background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 5px 0; }
.priority-yellow { background-color: #fffde7; border-left: 4px solid #ffeb3b; padding: 10px; margin: 5px 0; }
.priority-green { background-color: #e8f5e8; border-left: 4px solid #4caf50; padding: 10px; margin: 5px 0; }
.priority-blue { background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 10px; margin: 5px 0; }
.event-card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin: 10px 0; border: 1px solid #dee2e6; }
.hospital-status { background-color: #e7f3ff; border-radius: 8px; padding: 15px; margin: 10px 0; }
.patient-card { background-color: #ffffff; border-radius: 8px; padding: 12px; margin: 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

def load_simulation_data(file_path: str) -> Optional[Dict[str, Any]]:
    """Load simulation data from JSON file"""
    backend_path = os.path.join('backend', os.path.basename(file_path))
    try:
        with open(backend_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Simulation file not found: {backend_path}")
        return None
    except json.JSONDecodeError:
        st.error(f"Invalid JSON file: {backend_path}")
        return None

def get_priority_color(priority: str) -> str:
    """Get color class for priority"""
    colors = {
        "red": "priority-red",
        "orange": "priority-orange", 
        "yellow": "priority-yellow",
        "green": "priority-green",
        "blue": "priority-blue"
    }
    return colors.get(priority, "priority-green")

def format_event_time(timestamp: float, start_time: str) -> str:
    """Format event timestamp to readable time"""
    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    event_dt = start_dt + timedelta(minutes=timestamp)
    return event_dt.strftime("%H:%M:%S")

def display_patient_journey(events: List[Dict[str, Any]], patient_name: str):
    """Display journey for a specific patient"""
    patient_events = [e for e in events if e['patient_name'] == patient_name]
    
    if not patient_events:
        st.warning(f"No events found for patient: {patient_name}")
        return
    
    st.subheader(f"🏥 Patient Journey: {patient_name}")
    
    for event in patient_events:
        priority = event.get('priority', 'green')
        event_time = format_event_time(event['timestamp'], event['real_time'])
        
        with st.container():
            st.markdown(f"""
            <div class="{get_priority_color(priority)}">
                <strong>{event_time}</strong> - {event['event_type'].replace('_', ' ').title()}
                {f"<br>📍 Resource: {event['resource_name']}" if event['resource_name'] else ""}
                {f"<br>🚨 Priority: {priority.upper()}" if priority else ""}
                {f"<br>📋 Details: {event['details']}" if event['details'] else ""}
            </div>
            """, unsafe_allow_html=True)

def display_hospital_status(events: List[Dict[str, Any]]):
    """Display current hospital status"""
    # Get latest hospital status event
    status_events = [e for e in events if e['event_type'] == 'HOSPITAL_STATUS']
    
    if not status_events:
        st.warning("No hospital status data available")
        return
    
    latest_status = status_events[-1]
    stats = latest_status['details']['statistics']
    queues = latest_status['details']['queue_summary']
    
    st.subheader("🏥 Hospital Status")
    
    # Display statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Doctors", stats['total_doctors'])
        st.metric("Available Doctors", stats['available_doctors'])
    
    with col2:
        st.metric("Total Patients", stats['total_patients'])
        st.metric("Total Beds", stats['total_beds'])
    
    with col3:
        st.metric("Available Beds", stats['available_beds'])
        st.metric("MRI Machines", stats['total_mri_machines'])
    
    with col4:
        st.metric("Available MRI", stats['available_mri_machines'])
        st.metric("Ultrasonic Machines", stats['total_ultrasonic_machines'])
    
    # Display queue information
    st.subheader("📋 Resource Queues")
    
    for resource_name, queue_data in queues.items():
        total_in_queue = sum(queue_data.values())
        if total_in_queue > 0:
            st.markdown(f"""
            <div class="hospital-status">
                <h4>{resource_name.replace('_', ' ')}</h4>
                <p>Total patients in queue: <strong>{total_in_queue}</strong></p>
                <ul>
                    {chr(10).join([f'<li style="color: {get_priority_color(priority).split("-")[1]}">🔴 {priority.upper()}: {count}</li>' for priority, count in queue_data.items() if count > 0])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

def display_hospital_layout(active_patients: Dict[str, Any], resource_status: Dict[str, List[str]], processed_patients: Optional[List[Dict[str, Any]]] = None, simulation_data: Optional[Dict[str, Any]] = None, current_event: Optional[Dict[str, Any]] = None):
    """Display visual hospital layout with resources and patient queues"""
    st.markdown("### 🏥 Hospital Layout with Live Patient Queues")
    
    # Create columns for different areas - ordered: Triage, Routing Agent, Doctors, Equipment, Beds, Processed
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.markdown("#### 🚪 Entrance & Triage")
        
        # Get patients at entrance or being triaged
        entrance_patients = [name for name, info in active_patients.items() 
                           if info.get('location') in ['Entrance', 'Triage']]
        
        with st.container():
            # Get patient details for entrance/triage
            entrance_patient_cards: List[str] = []
            for p in entrance_patients:
                if p in active_patients:
                    patient_info = active_patients[p]
                    priority = patient_info.get('priority', 'pending')
                    status = patient_info.get('status', 'Unknown')
                    
                    # Handle pending priority with gray color
                    if priority == 'pending':
                        priority_color = '#9e9e9e'  # Gray for pending
                        priority_display = 'PENDING'
                    else:
                        priority_color = get_priority_color_hex(priority)
                        priority_display = priority.upper()
                    
                    entrance_patient_cards.append(
                        f'<div style="background: {priority_color}; color: white; padding: 6px; margin: 3px 0; border-radius: 4px; font-size: 11px;">'
                        f'<strong>{p}</strong><br>'
                        f'🚨 {priority_display}<br>'
                        f'📋 {status}'
                        f'</div>'
                    )
            
            if entrance_patient_cards:
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #2196f3; min-height: 120px;">
                    <h5 style="color: #1976d2; margin: 0 0 8px 0;">🚪 Entrance/Triage</h5>
                    <div style="max-height: 200px; overflow-y: auto;">
                        {''.join(entrance_patient_cards)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #cccccc; min-height: 120px; display: flex; align-items: center; justify-content: center;">
                    <div style="text-align: center;">
                        <h5 style="color: #666; margin: 0;">🚪 Entrance/Triage</h5>
                        <p style="color: #999; font-size: 12px; margin: 5px 0;">✅ No patients</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("#### 🤖 Routing Agent")
        
        # Check if current event is a routing decision
        if current_event and current_event.get('event_type') == 'ROUTING_DECISION':
            details = current_event.get('details', {})
            assign_doctor = details.get('assign_doctor', False)
            assign_bed = details.get('assign_bed', False)
            patient_name = current_event.get('patient_name', 'Unknown')
            priority = current_event.get('priority', 'unknown')
            
            st.markdown(f"""
            <div style="background: #fff3e0; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #ff9800; min-height: 120px;">
                <h5 style="color: #f57c00; margin: 0 0 8px 0;">🤖 Processing Decision</h5>
                <p style="margin: 5px 0; font-size: 12px;"><strong>👤 Patient:</strong> {patient_name}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>🚨 Priority:</strong> {priority.upper()}</p>
                <div style="background: #f5f5f5; padding: 8px; border-radius: 4px; margin: 8px 0;">
                    <p style="margin: 3px 0; font-size: 11px;">👨‍⚕️ <strong>Doctor:</strong> <span style="color: {'green' if assign_doctor else 'red'}; font-weight: bold;">{'✅ YES' if assign_doctor else '❌ NO'}</span></p>
                    <p style="margin: 3px 0; font-size: 11px;">🛏️ <strong>Urgent Bed:</strong> <span style="color: {'green' if assign_bed else 'red'}; font-weight: bold;">{'✅ YES' if assign_bed else '❌ NO'}</span></p>
                </div>
                <p style="margin: 5px 0; font-size: 10px; color: #666; font-style: italic;">💡 {('High priority: Both doctor and bed' if assign_bed else 'Standard: Doctor only')}</p>
            </div>
            """, unsafe_allow_html=True)
        elif current_event and current_event.get('event_type') == 'TRIAGE_COMPLETE':
            patient_name = current_event.get('patient_name', 'Unknown')
            priority = current_event.get('priority', 'unknown')
            
            st.markdown(f"""
            <div style="background: #e3f2fd; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #2196f3; min-height: 120px;">
                <h5 style="color: #1976d2; margin: 0 0 8px 0;">🤖 Awaiting Patient</h5>
                <p style="margin: 5px 0; font-size: 12px;"><strong>👤 From Triage:</strong> {patient_name}</p>
                <p style="margin: 5px 0; font-size: 12px;"><strong>🚨 Priority:</strong> {priority.upper()}</p>
                <div style="background: #f5f5f5; padding: 8px; border-radius: 4px; margin: 8px 0;">
                    <p style="margin: 3px 0; font-size: 11px; color: #666;">⏳ Analyzing patient priority...</p>
                    <p style="margin: 3px 0; font-size: 11px; color: #666;">🔄 Determining routing decision...</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Find routing decision for current patient if available
            current_patient_routing = None
            current_patient_name = current_event.get('patient_name') if current_event else None
            
            if current_patient_name and simulation_data and 'events' in simulation_data:
                # Look for routing decision for the current patient
                for event in simulation_data['events']:
                    if (event.get('event_type') == 'ROUTING_DECISION' and 
                        event.get('patient_name') == current_patient_name):
                        current_patient_routing = event
                        break
            
            # If no current patient routing found, get the most recent routing decision
            if not current_patient_routing and simulation_data and 'events' in simulation_data:
                for event in reversed(simulation_data['events']):
                    if event.get('event_type') == 'ROUTING_DECISION':
                        current_patient_routing = event
                        break
            
            latest_routing_decision = current_patient_routing
            
            if latest_routing_decision:
                details = latest_routing_decision.get('details', {})
                assign_doctor = details.get('assign_doctor', False)
                assign_bed = details.get('assign_bed', False)
                patient_name = latest_routing_decision.get('patient_name', 'Unknown')
                priority = latest_routing_decision.get('priority', 'unknown')
                
                st.markdown(f"""
                <div style="background: #fff3e0; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #ff9800; min-height: 120px;">
                    <h5 style="color: #f57c00; margin: 0 0 8px 0;">🤖 Current Decision</h5>
                    <p style="margin: 5px 0; font-size: 12px;"><strong>👤 Patient:</strong> {patient_name}</p>
                    <p style="margin: 5px 0; font-size: 12px;"><strong>🚨 Priority:</strong> {priority.upper()}</p>
                    <div style="background: #f5f5f5; padding: 8px; border-radius: 4px; margin: 8px 0;">
                        <p style="margin: 3px 0; font-size: 11px;">👨‍⚕️ <strong>Doctor:</strong> <span style="color: {'green' if assign_doctor else 'red'}; font-weight: bold;">{'✅ YES' if assign_doctor else '❌ NO'}</span></p>
                        <p style="margin: 3px 0; font-size: 11px;">🛏️ <strong>Urgent Bed:</strong> <span style="color: {'green' if assign_bed else 'red'}; font-weight: bold;">{'✅ YES' if assign_bed else '❌ NO'}</span></p>
                    </div>
                    <p style="margin: 5px 0; font-size: 10px; color: #666; font-style: italic;">💡 {('High priority: Both doctor and bed' if assign_bed else 'Standard: Doctor only')}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #cccccc; min-height: 120px; display: flex; align-items: center; justify-content: center;">
                    <div style="text-align: center;">
                        <h5 style="color: #666; margin: 0;">🤖 Routing Agent</h5>
                        <p style="color: #999; font-size: 12px; margin: 5px 0;">⏳ Waiting for patients</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with col3:
        st.markdown("#### 👨‍⚕️ Doctors")
        doctors = ["Dr. Emergency", "Dr. Heart", "Dr. General"]
        
        for doctor in doctors:
            # Get patients in this doctor's queue or with this doctor
            doctor_patients = resource_status.get(doctor, [])
            queue_patients = [name for name, info in active_patients.items() 
                            if doctor in info.get('location', '') and 'Queue' in info.get('location', '')]
            
            # Combine queue and active patients
            all_patients = list(set(doctor_patients + queue_patients))
            
            with st.container():
                # Group patients by priority for this doctor
                 priority_queues: Dict[str, List[Tuple[str, str]]] = {"red": [], "orange": [], "yellow": [], "green": [], "blue": []}
                 for p in all_patients:
                     if p in active_patients:
                         patient_info = active_patients[p]
                         priority = patient_info.get('priority', 'green')
                         status = patient_info.get('status', 'Unknown')
                         if priority in priority_queues:
                             priority_queues[priority].append((p, status))
                 
                 # Check if doctor has any patients
                 has_patients = any(len(queue) > 0 for queue in priority_queues.values())
                 
                 if has_patients:
                     priority_sections: List[str] = []
                     for priority, patients in priority_queues.items():
                          if patients:
                              priority_color = get_priority_color_hex(priority)
                              patient_cards: List[str] = []
                              for patient_name, status in patients:
                                  patient_cards.append(
                                      f'<div style="background: {priority_color}; color: white; padding: 4px 6px; margin: 2px 0; border-radius: 3px; font-size: 10px;">'
                                      f'<strong>{patient_name}</strong><br>📋 {status}'
                                      f'</div>'
                                  )
                              priority_sections.append(
                                  f'<div style="margin: 4px 0;">'
                                  f'<div style="background: {priority_color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold; margin-bottom: 2px;">'
                                  f'{priority.upper()} PRIORITY ({len(patients)})'
                                  f'</div>'
                                  f'{"".join(patient_cards)}'
                                  f'</div>'
                              )
                     
                     st.markdown(f"""
                     <div style="background: #e8f5e8; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #4caf50; min-height: 120px;">
                         <h5 style="color: #2e7d32; margin: 0 0 8px 0;">👨‍⚕️ {doctor}</h5>
                         <div style="max-height: 200px; overflow-y: auto;">
                             {''.join(priority_sections)}
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
                 else:
                     st.markdown(f"""
                     <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #cccccc; min-height: 120px; display: flex; align-items: center; justify-content: center;">
                         <div style="text-align: center;">
                             <h5 style="color: #666; margin: 0;">👨‍⚕️ {doctor}</h5>
                             <p style="color: #999; font-size: 12px; margin: 5px 0;">✅ Available</p>
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
    
    with col4:
         st.markdown("#### 🔬 Equipment")
         
         # MRI Machines
         st.markdown("**🔬 MRI Machines**")
         mri_machines = ["MRI-1", "MRI-2"]
         
         for mri in mri_machines:
            # Get patients using this MRI
            mri_patients = resource_status.get(mri, [])
            
            with st.container():
                # Get patient details for this MRI
                mri_patient_cards: List[str] = []
                for p in mri_patients:
                    if p in active_patients:
                        patient_info = active_patients[p]
                        priority = patient_info.get('priority', 'green')
                        status = patient_info.get('status', 'Unknown')
                        priority_color = get_priority_color_hex(priority)
                        mri_patient_cards.append(
                            f'<div style="background: {priority_color}; color: white; padding: 4px 6px; margin: 2px 0; border-radius: 3px; font-size: 10px;">'
                            f'<strong>{p}</strong><br>📋 {status}'
                            f'</div>'
                        )
                
                if mri_patient_cards:
                    st.markdown(f"""
                    <div style="background: #f3e5f5; padding: 8px; border-radius: 6px; margin: 3px 0; border: 1px solid #9c27b0; min-height: 60px;">
                        <h6 style="color: #7b1fa2; margin: 0 0 4px 0; font-size: 12px;">🔬 {mri}</h6>
                        <div style="max-height: 100px; overflow-y: auto;">
                            {''.join(mri_patient_cards)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 8px; border-radius: 6px; margin: 3px 0; border: 1px solid #cccccc; min-height: 60px; display: flex; align-items: center; justify-content: center;">
                        <div style="text-align: center;">
                            <h6 style="color: #666; margin: 0; font-size: 12px;">🔬 {mri}</h6>
                            <p style="color: #999; font-size: 10px; margin: 2px 0;">Available</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
         # Ultrasonic Machines
         st.markdown("**🔊 Ultrasonic Machines**")
         ultrasonic_machines = ["Ultrasonic-1", "Ultrasonic-2"]
         
         for ultrasonic in ultrasonic_machines:
             # Get patients using this Ultrasonic
             ultrasonic_patients = resource_status.get(ultrasonic, [])
             
             with st.container():
                 # Get patient details for this Ultrasonic
                 ultrasonic_patient_cards: List[str] = []
                 for p in ultrasonic_patients:
                     if p in active_patients:
                         patient_info = active_patients[p]
                         priority = patient_info.get('priority', 'green')
                         status = patient_info.get('status', 'Unknown')
                         priority_color = get_priority_color_hex(priority)
                         ultrasonic_patient_cards.append(
                             f'<div style="background: {priority_color}; color: white; padding: 4px 6px; margin: 2px 0; border-radius: 3px; font-size: 10px;">'
                             f'<strong>{p}</strong><br>📋 {status}'
                             f'</div>'
                         )
                 
                 if ultrasonic_patient_cards:
                     st.markdown(f"""
                     <div style="background: #e8f5e8; padding: 8px; border-radius: 6px; margin: 3px 0; border: 1px solid #4caf50; min-height: 60px;">
                         <h6 style="color: #2e7d32; margin: 0 0 4px 0; font-size: 12px;">🔊 {ultrasonic}</h6>
                         <div style="max-height: 100px; overflow-y: auto;">
                             {''.join(ultrasonic_patient_cards)}
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
                 else:
                     st.markdown(f"""
                     <div style="background: #f5f5f5; padding: 8px; border-radius: 6px; margin: 3px 0; border: 1px solid #cccccc; min-height: 60px; display: flex; align-items: center; justify-content: center;">
                         <div style="text-align: center;">
                             <h6 style="color: #666; margin: 0; font-size: 12px;">🔊 {ultrasonic}</h6>
                             <p style="color: #999; font-size: 10px; margin: 2px 0;">Available</p>
                         </div>
                     </div>
                     """, unsafe_allow_html=True)
    
    with col5:
         st.markdown("#### 🛏️ Beds")
         beds = ["ICU-1", "Ward-A1", "Ward-A2"]
         
         for bed in beds:
            # Get patients in this bed
            bed_patients = resource_status.get(bed, [])
            
            with st.container():
                # Get patient details for this bed
                bed_patient_cards: List[str] = []
                for p in bed_patients:
                    if p in active_patients:
                        patient_info = active_patients[p]
                        priority = patient_info.get('priority', 'green')
                        status = patient_info.get('status', 'Unknown')
                        priority_color = get_priority_color_hex(priority)
                        bed_patient_cards.append(
                            f'<div style="background: {priority_color}; color: white; padding: 6px; margin: 3px 0; border-radius: 4px; font-size: 11px;">'
                            f'<strong>{p}</strong><br>'
                            f'🚨 {priority.upper() if priority else "UNKNOWN"}<br>'
                            f'📋 {status}'
                            f'</div>'
                        )
                
                if bed_patient_cards:
                    st.markdown(f"""
                    <div style="background: #fff3e0; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #ff9800; min-height: 120px;">
                        <h5 style="color: #f57c00; margin: 0 0 8px 0;">🛏️ {bed}</h5>
                        <div style="max-height: 200px; overflow-y: auto;">
                            {''.join(bed_patient_cards)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #cccccc; min-height: 120px; display: flex; align-items: center; justify-content: center;">
                        <div style="text-align: center;">
                            <h5 style="color: #666; margin: 0;">🛏️ {bed}</h5>
                            <p style="color: #999; font-size: 12px; margin: 5px 0;">✅ Available</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col6:
          st.markdown("#### ✅ Processed Patients")
          
          with st.container():
             if processed_patients and len(processed_patients) > 0:
                 # Show most recent processed patients (limit to last 10)
                 recent_processed: List[Dict[str, Any]] = processed_patients[-10:] if len(processed_patients) > 10 else processed_patients
                 
                 processed_cards: List[str] = []
                 for patient in reversed(recent_processed):  # Show most recent first
                     priority_color = get_priority_color_hex(patient.get('priority', 'green'))
                     priority_str = patient.get('priority', 'unknown')
                     processed_cards.append(
                         f'<div style="background: {priority_color}; color: white; padding: 6px; margin: 3px 0; border-radius: 4px; font-size: 11px; opacity: 0.8;">'
                         f'<strong>{patient.get("name", "Unknown")}</strong><br>'
                         f'🚨 {priority_str.upper() if priority_str else "UNKNOWN"}<br>'
                         f'✅ {patient.get("final_status", "Unknown")}<br>'
                         f'⏱️ {patient.get("discharge_time", "Unknown")}<br>'
                         f'📊 Total: {patient.get("total_time", "Unknown")} min'
                         f'</div>'
                     )
                 
                 st.markdown(f"""
                 <div style="background: #f0f0f0; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #757575; min-height: 120px;">
                     <h5 style="color: #424242; margin: 0 0 8px 0;">✅ Processed Patients ({len(processed_patients)})</h5>
                     <div style="max-height: 200px; overflow-y: auto;">
                         {''.join(processed_cards)}
                     </div>
                 </div>
                 """, unsafe_allow_html=True)
             else:
                 st.markdown("""
                 <div style="background: #f5f5f5; padding: 12px; border-radius: 8px; margin: 5px 0; border: 2px solid #cccccc; min-height: 120px; display: flex; align-items: center; justify-content: center;">
                     <div style="text-align: center;">
                         <h5 style="color: #666; margin: 0;">✅ Processed Patients</h5>
                         <p style="color: #999; font-size: 12px; margin: 5px 0;">No patients processed yet</p>
                     </div>
                 </div>
                 """, unsafe_allow_html=True)
 
def get_priority_color_hex(priority: str) -> str:
    """Get hex color for priority"""
    colors = {
        "red": "#f44336",
        "orange": "#ff9800", 
        "yellow": "#ffeb3b",
        "green": "#4caf50",
        "blue": "#2196f3"
    }
    return colors.get(priority, "#4caf50")

def display_live_events(events: List[Dict[str, Any]], start_time: str, speed_multiplier: float = 1.0, simulation_data: Optional[Dict[str, Any]] = None):
    """Display events in real-time simulation with visual hospital layout"""
    st.subheader("🔴 Live Hospital Simulation")
    
    # Display hospital layout (will be updated in the loop)
    layout_container = st.empty()
    
    # Create placeholders for dynamic content
    st.subheader("📋 Current Events")
    event_container = st.empty()
    
    progress_bar = st.progress(0)
    time_display = st.empty()
    
    if not events:
        st.warning("No events to display")
        return
    
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda x: x['timestamp'])
    total_duration = sorted_events[-1]['timestamp']
    
    # Track active patients, resources, and processed patients
    active_patients: Dict[str, Any] = {}
    processed_patients: List[Dict[str, Any]] = []
    resource_status: Dict[str, List[str]] = {
        "Dr. Emergency": [],
        "Dr. Heart": [],
        "Dr. General": [],
        "ICU-1": [],
        "Ward-A1": [],
        "Ward-A2": [],
        "MRI-1": [],
        "MRI-2": [],
        "Ultrasonic-1": [],
        "Ultrasonic-2": []
    }
    
    # Display events with timing
    for i, event in enumerate(sorted_events):
        # Update progress
        progress = (event['timestamp'] / total_duration) if total_duration > 0 else 0
        progress_bar.progress(progress)
        
        # Update time display
        event_time = format_event_time(event['timestamp'], start_time)
        time_display.markdown(f"**🕐 Simulation Time: {event_time} (Minute {event['timestamp']:.1f})**")
        
        # Update patient and resource tracking
        patient_name = event['patient_name']
        event_type = event['event_type']
        priority = event.get('priority', 'green')
        resource_name = event.get('resource_name')
        
        # Update active patients based on event
        if event_type == 'PATIENT_ARRIVAL':
            active_patients[patient_name] = {
                'priority': 'pending',  # Set to pending until triage is complete
                'status': 'Arrived',
                'location': 'Entrance',
                'symptoms': event.get('details', {}).get('symptoms', [])
            }
        elif event_type == 'TRIAGE_COMPLETE':
            if patient_name in active_patients:
                active_patients[patient_name]['status'] = 'Triaged'
                active_patients[patient_name]['priority'] = priority  # This should now properly set the triage priority
        elif event_type == 'QUEUE_JOIN' and resource_name:
            if patient_name in active_patients:
                active_patients[patient_name]['status'] = f'Waiting for {resource_name}'
                active_patients[patient_name]['location'] = f'{resource_name} Queue'
        elif event_type == 'CONSULTATION_START' and resource_name:
            if patient_name in active_patients:
                active_patients[patient_name]['status'] = f'With {resource_name}'
                active_patients[patient_name]['location'] = resource_name
                if resource_name in resource_status:
                    resource_status[resource_name].append(patient_name)
        elif event_type == 'CONSULTATION_END' and resource_name:
            if resource_name in resource_status and patient_name in resource_status[resource_name]:
                resource_status[resource_name].remove(patient_name)
        elif event_type == 'BED_ASSIGNMENT' and resource_name:
            if patient_name in active_patients:
                active_patients[patient_name]['status'] = f'In {resource_name}'
                active_patients[patient_name]['location'] = resource_name
                if resource_name in resource_status:
                    resource_status[resource_name].append(patient_name)
        elif event_type == 'PATIENT_DISCHARGE':
            if patient_name in active_patients:
                # Move to processed patients before removing from active
                patient_info = active_patients[patient_name]
                processed_patients.append({
                    'name': patient_name,
                    'priority': patient_info.get('priority', 'green'),
                    'final_status': 'Discharged',
                    'total_time': event.get('details', {}).get('total_time_in_hospital', 'Unknown'),
                    'discharge_time': format_event_time(event['timestamp'], start_time)
                })
                del active_patients[patient_name]
            # Remove from all resources
            for resource in resource_status:
                if patient_name in resource_status[resource]:
                    resource_status[resource].remove(patient_name)
        
        # Display current event
        with event_container.container():
            # Special handling for routing decisions
            if event_type == 'ROUTING_DECISION':
                details = event.get('details', {})
                assign_doctor = details.get('assign_doctor', False)
                assign_bed = details.get('assign_bed', False)
                
                st.markdown(f"""
                <div class="event-card" style="background: #fff3e0; border-left: 4px solid #ff9800;">
                    <h4>🕐 {event_time} - 🤖 Routing Agent Decision</h4>
                    <p><strong>👤 Patient:</strong> {patient_name}</p>
                    <p><strong>🚨 Priority:</strong> {priority.upper() if priority else 'Unknown'}</p>
                    <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                        <h5 style="margin: 0 0 8px 0; color: #333;">🤖 Agent Decisions:</h5>
                        <p style="margin: 5px 0;">👨‍⚕️ <strong>Assign to Doctor:</strong> <span style="color: {'green' if assign_doctor else 'red'}; font-weight: bold;">{'✅ YES' if assign_doctor else '❌ NO'}</span></p>
                        <p style="margin: 5px 0;">🛏️ <strong>Assign Urgent Bed:</strong> <span style="color: {'green' if assign_bed else 'red'}; font-weight: bold;">{'✅ YES' if assign_bed else '❌ NO'}</span></p>
                        <p style="margin: 5px 0; font-size: 12px; color: #666;">💡 <em>Routing logic: {'High priority patients get both doctor and bed assignments' if assign_bed else 'Standard routing to available doctor'}</em></p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="event-card {get_priority_color(priority)}">
                    <h4>🕐 {event_time} - {event_type.replace('_', ' ').title()}</h4>
                    <p><strong>👤 Patient:</strong> {patient_name}</p>
                    {f"<p><strong>📍 Resource:</strong> {resource_name}</p>" if resource_name else ""}
                    {f"<p><strong>🚨 Priority:</strong> {priority.upper()}</p>" if priority else ""}
                </div>
                """, unsafe_allow_html=True)
        
        # Update hospital layout with current patient positions
        with layout_container.container():
            display_hospital_layout(active_patients, resource_status, processed_patients, simulation_data, event)
        
        # Wait based on speed multiplier
        if i < len(sorted_events) - 1:
            next_event_time = sorted_events[i + 1]['timestamp']
            wait_time = (next_event_time - event['timestamp']) / speed_multiplier
            time.sleep(min(wait_time, 2.0))  # Cap wait time at 2 seconds

def main():
    st.title("🏥 Hospital Simulation Viewer")
    st.markdown("Real-time visualization of hospital patient flow and operations")
    
    # Sidebar for file selection and controls
    st.sidebar.title("🎛️ Controls")
    
    # File selection
    backend_dir = 'backend'
    if not os.path.exists(backend_dir):
        st.error("Backend directory not found")
        return
    
    json_files = [f for f in os.listdir(backend_dir) if f.endswith('.json') and 'hospital_simulation' in f]
    
    if not json_files:
        st.error("No hospital simulation JSON files found in the current directory.")
        st.info("Please run the hospital simulation first to generate data files.")
        return
    
    # Sort files by modification time to get the most recent first
    json_files_with_time = [(f, os.path.getmtime(os.path.join(backend_dir, f))) for f in json_files]
    json_files_sorted = [f[0] for f in sorted(json_files_with_time, key=lambda x: x[1], reverse=True)]
    
    selected_file = st.sidebar.selectbox(
        "📁 Select Simulation File",
        json_files_sorted,
        index=0  # Default to most recent (first in sorted list)
    )
    
    # Show file timestamp for user reference
    if json_files_sorted:
        file_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(backend_dir, selected_file)))
        st.sidebar.caption(f"📅 Created: {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if selected_file == json_files_sorted[0]:
            st.sidebar.success("✅ Latest simulation file selected")
    
    # Load simulation data
    simulation_data = load_simulation_data(os.path.join(backend_dir, selected_file))
    
    if not simulation_data:
        return
    
    # Display simulation info
    st.sidebar.markdown("### 📊 Simulation Info")
    sim_info = simulation_data['simulation_info']
    st.sidebar.markdown(f"""
    - **Hospital:** {sim_info['hospital_name']}
    - **Duration:** {sim_info['duration_minutes']} minutes
    - **Total Events:** {sim_info['total_events']}
    - **Start Time:** {sim_info['start_time'][:19]}
    """)
    
    # View mode selection
    view_mode = st.sidebar.radio(
        "🎭 View Mode",
        ["Live Simulation", "Patient Journey", "Hospital Status", "Event Timeline"]
    )
    
    events = simulation_data['events']
    
    if view_mode == "Live Simulation":
        speed = st.sidebar.slider("⚡ Playback Speed", 0.1, 5.0, 1.0, 0.1)
        
        if st.sidebar.button("▶️ Start Live Simulation"):
            display_live_events(events, sim_info['start_time'], speed, simulation_data)
    
    elif view_mode == "Patient Journey":
        # Get unique patient names
        patient_names = list(set([e['patient_name'] for e in events if e['patient_name'] != 'SYSTEM']))
        
        selected_patient = st.sidebar.selectbox(
            "👤 Select Patient",
            patient_names
        )
        
        if selected_patient:
            display_patient_journey(events, selected_patient)
    
    elif view_mode == "Hospital Status":
        display_hospital_status(events)
    
    elif view_mode == "Event Timeline":
        st.subheader("📅 Complete Event Timeline")
        
        # Filter options
        event_types = list(set([e['event_type'] for e in events]))
        selected_types = st.multiselect(
            "Filter by Event Type",
            event_types,
            default=event_types
        )
        
        # Display filtered events
        filtered_events = [e for e in events if e['event_type'] in selected_types]
        
        for event in filtered_events:
            event_time = format_event_time(event['timestamp'], sim_info['start_time'])
            
            with st.expander(f"{event_time} - {event['event_type']} - {event['patient_name']}"):
                st.json(event)

if __name__ == "__main__":
    main()