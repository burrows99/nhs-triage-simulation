from dataclasses import dataclass, field
from typing import List

@dataclass
class Symptoms:
    symptoms: List[str] = field(default_factory=list)
    
    def add(self, symptom: str):
        """Add a new symptom"""
        if symptom not in self.symptoms:
            self.symptoms.append(symptom)
    
    def remove(self, symptom: str):
        """Remove a symptom"""
        if symptom in self.symptoms:
            self.symptoms.remove(symptom)
    
    def __len__(self):
        return len(self.symptoms)
    
    def __contains__(self, symptom: str):
        return symptom in self.symptoms
    
    def __iter__(self):
        return iter(self.symptoms)