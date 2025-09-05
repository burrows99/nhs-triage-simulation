import heapq
from typing import Tuple
from ..models.hospital.hospital import Hospital
from ..models.entities.patient import Patient
from ..models.entities.resources import Doctor, MRI, Bed
from ..services.plotting_service import PlottingService
from ..services.statistics_service import StatisticsService


class HospitalSimulationEngine:
    """Discrete event simulation engine for hospital operations."""
    
    def __init__(self, num_doctors: int, num_mri: int = 1, num_beds: int = 1, simulation_time: int = 50, seed: int = 42):
        """Initialize the simulation engine with specified resources."""
        self.simulation_time = simulation_time
        self.hospital = Hospital(entity_id=0, name="Sim Hospital")

        # Initialize doctors
        for i in range(num_doctors):
            self.hospital.add_resource(Doctor(entity_id=i, name=f"Dr_{i}"))
        
        # Initialize MRI machines
        for i in range(num_mri):
            self.hospital.add_resource(MRI(entity_id=100 + i, name=f"MRI_{i+1}"))
        
        # Initialize beds
        for i in range(num_beds):
            self.hospital.add_resource(Bed(entity_id=200 + i, name=f"Bed_{i+1}"))

        # Initialize statistics service for patient generation
        self.stats_service = StatisticsService(mu=0.0, sigma=1.0, seed=seed)
        self.patient_stream = self.stats_service.generate_patient_stream("SimPatient")

        # Pending arrivals: min-heap based on arrival_time
        self.pending_patients: list[Tuple[int, Patient]] = []

    def run(self):
        """Run the simulation over the defined number of steps."""
        for step in range(1, self.simulation_time + 1):
            # Add new arrivals for this step
            while True:
                peek_patient = next(self.patient_stream)
                if peek_patient.arrival_time is None or peek_patient.arrival_time > step:
                    # Patient hasn't arrived yet, push back to heap
                    arrival_time = peek_patient.arrival_time or step + 1
                    heapq.heappush(self.pending_patients, (arrival_time, peek_patient))
                    break
                self.hospital.admit_patient(peek_patient)  # type: ignore

            # Admit any pending patients whose time has come
            while self.pending_patients and self.pending_patients[0][0] <= step:
                _, patient = heapq.heappop(self.pending_patients)
                self.hospital.admit_patient(patient)  # type: ignore

            # Allocate resources for this step
            self.hospital.allocate_resources()  # type: ignore

            # Release patients whose service is complete
            for reslist in self.hospital.resources.values():
                for res in reslist:
                    if res.current_patient and res.current_patient.finish_service_time and res.current_patient.finish_service_time <= step:
                        self.hospital.release_patient(res)  # type: ignore

        # Initialize plotting service for snapshots after simulation
        self.hospital.plotting_service = PlottingService(self.hospital.history)