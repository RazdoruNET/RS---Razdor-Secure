"""
🛰️ ORPHEUS-1 Quantum Communication Module
TOP SECRET // SCI // NOFORN // ORCON
"""

import numpy as np
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config.quantum_config import QuantumConfig
from security.quantum_encryption import QuantumEncryption


class QuantumState(Enum):
    """Quantum communication states"""
    IDLE = "idle"
    ENTANGLING = "entangling"
    TELEPORTING = "teleporting"
    MEASURING = "measuring"
    DECOHERENT = "decoherent"


@dataclass
class QuantumChannel:
    """Quantum communication channel"""
    channel_id: str
    frequency: float
    bandwidth: float
    entanglement_rate: float
    fidelity: float
    noise_level: float
    active: bool = True


@dataclass
class EntangledPair:
    """Quantum entangled particle pair"""
    pair_id: str
    created_time: float
    fidelity: float
    measurement_basis: str
    alice_state: Optional[np.ndarray] = None
    bob_state: Optional[np.ndarray] = None


class QuantumCommunication:
    """Quantum communication system for ORPHEUS-1"""
    
    def __init__(self, config: QuantumConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize quantum parameters
        self.qubit_count = config.processor["qubits"]
        self.coherence_time = config.processor["coherence_time"]
        self.gate_fidelity = config.processor["gate_fidelity"]
        
        # Communication parameters
        self.entanglement_rate = config.communication["entanglement_rate"]
        self.teleportation_fidelity = config.communication["teleportation_fidelity"]
        self.key_generation_rate = config.communication["key_generation_rate"]
        
        # Initialize components
        self.encryption = QuantumEncryption(config.communication)
        
        # Quantum state management
        self.current_state = QuantumState.IDLE
        self.entangled_pairs: List[EntangledPair] = []
        self.quantum_channels: Dict[str, QuantumChannel] = {}
        
        # Performance metrics
        self.metrics = {
            "total_entanglements": 0,
            "successful_teleportations": 0,
            "failed_teleportations": 0,
            "average_fidelity": 0.0,
            "key_bits_generated": 0,
            "channel_utilization": 0.0
        }
        
        # Initialize channels
        self._initialize_channels()
        
        self.logger.info("🔗 Quantum Communication System Initialized")
    
    def _initialize_channels(self):
        """Initialize quantum communication channels"""
        # Primary quantum channel
        self.quantum_channels["primary"] = QuantumChannel(
            channel_id="primary",
            frequency=1550e-9,  # 1550 nm
            bandwidth=1e12,     # 1 THz
            entanglement_rate=self.entanglement_rate,
            fidelity=0.999,
            noise_level=1e-6
        )
        
        # Backup quantum channel
        self.quantum_channels["backup"] = QuantumChannel(
            channel_id="backup",
            frequency=1310e-9,  # 1310 nm
            bandwidth=5e11,      # 500 GHz
            entanglement_rate=self.entanglement_rate * 0.5,
            fidelity=0.995,
            noise_level=2e-6
        )
        
        # Emergency channel
        self.quantum_channels["emergency"] = QuantumChannel(
            channel_id="emergency",
            frequency=1064e-9,  # 1064 nm
            bandwidth=1e11,      # 100 GHz
            entanglement_rate=self.entanglement_rate * 0.2,
            fidelity=0.990,
            noise_level=5e-6
        )
    
    def create_entangled_pairs(self, count: int = 100) -> List[EntangledPair]:
        """Create quantum entangled particle pairs"""
        self.current_state = QuantumState.ENTANGLING
        pairs = []
        
        try:
            for i in range(count):
                pair_id = f"pair_{int(time.time())}_{i}"
                
                # Create Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2
                alice_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
                bob_state = alice_state.copy()
                
                # Add quantum noise
                noise_amplitude = np.random.normal(0, 0.001, 4)
                alice_state += noise_amplitude * (1 + 1j)
                bob_state += noise_amplitude * (1 - 1j)
                
                # Normalize states
                alice_state = alice_state / np.linalg.norm(alice_state)
                bob_state = bob_state / np.linalg.norm(bob_state)
                
                # Calculate fidelity
                fidelity = np.abs(np.vdot(alice_state, bob_state))**2
                
                pair = EntangledPair(
                    pair_id=pair_id,
                    created_time=time.time(),
                    fidelity=fidelity,
                    measurement_basis="computational",
                    alice_state=alice_state,
                    bob_state=bob_state
                )
                
                pairs.append(pair)
                self.entangled_pairs.append(pair)
                
                # Update metrics
                self.metrics["total_entanglements"] += 1
                self.metrics["average_fidelity"] = (
                    (self.metrics["average_fidelity"] * (len(self.entangled_pairs) - 1) + fidelity) /
                    len(self.entangled_pairs)
                )
            
            self.logger.info(f"✅ Created {count} entangled pairs")
            return pairs
            
        except Exception as e:
            self.logger.error(f"❌ Entanglement creation failed: {e}")
            self.current_state = QuantumState.IDLE
            return []
    
    def teleport_quantum_state(self, state: np.ndarray, target_channel: str = "primary") -> bool:
        """Teleport quantum state to target"""
        if target_channel not in self.quantum_channels:
            self.logger.error(f"❌ Unknown channel: {target_channel}")
            return False
        
        channel = self.quantum_channels[target_channel]
        if not channel.active:
            self.logger.error(f"❌ Channel {target_channel} not active")
            return False
        
        # Find available entangled pair
        available_pair = self._find_available_pair()
        if not available_pair:
            self.logger.warning("⚠️ No available entangled pairs")
            return False
        
        self.current_state = QuantumState.TELEPORTING
        
        try:
            # Quantum teleportation protocol
            success = self._perform_teleportation(state, available_pair, channel)
            
            if success:
                self.metrics["successful_teleportations"] += 1
                self.logger.info(f"✅ Quantum state teleported via {target_channel}")
            else:
                self.metrics["failed_teleportations"] += 1
                self.logger.error(f"❌ Quantum state teleportation failed")
            
            self.current_state = QuantumState.IDLE
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Teleportation error: {e}")
            self.current_state = QuantumState.IDLE
            return False
    
    def _find_available_pair(self) -> Optional[EntangledPair]:
        """Find available entangled pair"""
        current_time = time.time()
        
        for pair in self.entangled_pairs:
            # Check if pair is still coherent
            age = current_time - pair.created_time
            if age < self.coherence_time and pair.fidelity > 0.95:
                return pair
        
        return None
    
    def _perform_teleportation(self, state: np.ndarray, pair: EntangledPair, channel: QuantumChannel) -> bool:
        """Perform quantum teleportation"""
        try:
            # Bell state measurement
            bell_state = self._bell_state_measurement(state, pair.alice_state)
            
            # Classical communication of measurement results
            classical_bits = self._encode_measurement_results(bell_state)
            
            # Apply correction operations on Bob's qubit
            corrected_state = self._apply_correction_operations(pair.bob_state, classical_bits)
            
            # Verify teleportation fidelity
            fidelity = np.abs(np.vdot(state, corrected_state))**2
            
            # Account for channel noise
            channel_fidelity = channel.fidelity * (1 - channel.noise_level)
            total_fidelity = fidelity * channel_fidelity
            
            # Remove used pair
            self.entangled_pairs.remove(pair)
            
            return total_fidelity > 0.9
            
        except Exception as e:
            self.logger.error(f"❌ Teleportation protocol error: {e}")
            return False
    
    def _bell_state_measurement(self, state: np.ndarray, alice_state: np.ndarray) -> int:
        """Perform Bell state measurement"""
        # Simplified Bell state measurement
        # In reality, this would involve complex quantum operations
        
        # Create combined state
        combined_state = np.kron(state, alice_state)
        
        # Bell basis transformation matrix
        bell_transform = (1/np.sqrt(2)) * np.array([
            [1, 0, 0, 1, 0, 1, 1, 0, 0, 1, -1, 0, 1, 0, 0, -1],
            [1, 0, 0, -1, 0, -1, 1, 0, 0, -1, -1, 0, 1, 0, 0, 1],
            [1, 0, 0, 1, 0, -1, -1, 0, 0, -1, 1, 0, -1, 0, 0, 1],
            [1, 0, 0, -1, 0, 1, -1, 0, 0, 1, 1, 0, -1, 0, 0, -1]
        ])
        
        # Transform to Bell basis
        bell_basis = bell_transform @ combined_state
        
        # Measurement (simplified - probabilistic)
        probabilities = np.abs(bell_basis)**2
        measurement = np.random.choice(4, p=probabilities)
        
        return measurement
    
    def _encode_measurement_results(self, bell_state: int) -> List[int]:
        """Encode Bell state measurement results"""
        # 2 classical bits for Bell state
        return [(bell_state >> 1) & 1, bell_state & 1]
    
    def _apply_correction_operations(self, bob_state: np.ndarray, classical_bits: List[int]) -> np.ndarray:
        """Apply Pauli corrections based on classical bits"""
        # Pauli matrices
        I = np.array([[1, 0], [0, 1]], dtype=complex)
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        
        # Determine correction operation
        if classical_bits == [0, 0]:
            correction = I
        elif classical_bits == [0, 1]:
            correction = X
        elif classical_bits == [1, 0]:
            correction = Z
        else:  # [1, 1]
            correction = Y
        
        # Apply correction (simplified for 2-qubit state)
        corrected_state = np.kron(correction, I) @ bob_state
        
        return corrected_state
    
    def generate_quantum_key(self, key_length: int = 256) -> Optional[bytes]:
        """Generate quantum cryptographic key"""
        try:
            # Generate entangled pairs for key generation
            pairs = self.create_entangled_pairs(key_length // 8)
            
            if len(pairs) < (key_length // 8):
                self.logger.warning("⚠️ Insufficient entangled pairs for key generation")
                return None
            
            key_bits = []
            
            for pair in pairs:
                # Random basis selection
                alice_basis = np.random.choice(['Z', 'X'])
                bob_basis = np.random.choice(['Z', 'X'])
                
                # Measurement in selected basis
                if alice_basis == bob_basis:
                    # Same basis - use for key
                    measurement = self._measure_in_basis(pair.alice_state, alice_basis)
                    key_bits.append(measurement)
                    
                    # Remove used pair
                    self.entangled_pairs.remove(pair)
                else:
                    # Different basis - discard (but keep for future use)
                    pass
            
            # Convert bits to bytes
            if len(key_bits) >= key_length:
                key_bytes = bytes([int(''.join(map(str, key_bits[i:i+8])), 2) 
                                 for i in range(0, key_length, 8)])
                
                self.metrics["key_bits_generated"] += key_length
                self.logger.info(f"✅ Generated {key_length}-bit quantum key")
                
                return key_bytes
            else:
                self.logger.warning(f"⚠️ Only generated {len(key_bits)} bits, need {key_length}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Key generation failed: {e}")
            return None
    
    def _measure_in_basis(self, state: np.ndarray, basis: str) -> int:
        """Measure qubit in specified basis"""
        if basis == 'Z':
            # Computational basis
            probabilities = np.abs(state)**2
        else:  # 'X'
            # Hadamard basis
            H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
            transformed_state = H @ state[:2]  # Simplified for first qubit
            probabilities = np.abs(transformed_state)**2
        
        # Probabilistic measurement
        measurement = np.random.choice(2, p=probabilities[:2])
        return measurement
    
    def establish_quantum_link(self, target_id: str, channel: str = "primary") -> bool:
        """Establish quantum communication link"""
        if channel not in self.quantum_channels:
            self.logger.error(f"❌ Unknown channel: {channel}")
            return False
        
        self.logger.info(f"🔗 Establishing quantum link to {target_id} via {channel}")
        
        try:
            # Create entangled pairs for link
            pairs = self.create_entangled_pairs(50)
            
            if not pairs:
                self.logger.error("❌ Failed to create entangled pairs")
                return False
            
            # Test link quality
            test_state = np.array([1, 0], dtype=complex)  # |0⟩ state
            success = self.teleport_quantum_state(test_state, channel)
            
            if success:
                self.logger.info(f"✅ Quantum link established with {target_id}")
                return True
            else:
                self.logger.error(f"❌ Quantum link test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Link establishment failed: {e}")
            return False
    
    def get_channel_status(self, channel_id: str) -> Dict[str, Any]:
        """Get channel status"""
        if channel_id not in self.quantum_channels:
            return {"error": f"Unknown channel: {channel_id}"}
        
        channel = self.quantum_channels[channel_id]
        
        return {
            "channel_id": channel.channel_id,
            "frequency": channel.frequency,
            "bandwidth": channel.bandwidth,
            "entanglement_rate": channel.entanglement_rate,
            "fidelity": channel.fidelity,
            "noise_level": channel.noise_level,
            "active": channel.active,
            "utilization": self._calculate_channel_utilization(channel)
        }
    
    def _calculate_channel_utilization(self, channel: QuantumChannel) -> float:
        """Calculate channel utilization"""
        # Simplified utilization calculation
        max_pairs_per_second = channel.entanglement_rate
        current_pairs = len([p for p in self.entangled_pairs 
                          if time.time() - p.created_time < self.coherence_time])
        
        utilization = min(current_pairs / (max_pairs_per_second * self.coherence_time), 1.0)
        return utilization
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        total_pairs = len(self.entangled_pairs)
        coherent_pairs = len([p for p in self.entangled_pairs 
                             if time.time() - p.created_time < self.coherence_time])
        
        return {
            "current_state": self.current_state.value,
            "total_entangled_pairs": total_pairs,
            "coherent_pairs": coherent_pairs,
            "average_fidelity": self.metrics["average_fidelity"],
            "successful_teleportations": self.metrics["successful_teleportations"],
            "failed_teleportations": self.metrics["failed_teleportations"],
            "teleportation_success_rate": (
                self.metrics["successful_teleportations"] / 
                max(1, self.metrics["successful_teleportations"] + self.metrics["failed_teleportations"])
            ),
            "key_bits_generated": self.metrics["key_bits_generated"],
            "channel_status": {cid: self.get_channel_status(cid) for cid in self.quantum_channels},
            "timestamp": time.time()
        }
    
    def cleanup_decoherent_pairs(self):
        """Remove decoherent entangled pairs"""
        current_time = time.time()
        initial_count = len(self.entangled_pairs)
        
        self.entangled_pairs = [
            pair for pair in self.entangled_pairs 
            if (current_time - pair.created_time) < self.coherence_time
        ]
        
        removed_count = initial_count - len(self.entangled_pairs)
        if removed_count > 0:
            self.logger.info(f"🧹 Cleaned up {removed_count} decoherent pairs")
    
    def shutdown(self):
        """Shutdown quantum communication system"""
        self.logger.info("🔌 Shutting down Quantum Communication System")
        
        # Clear all entangled pairs
        self.entangled_pairs.clear()
        
        # Deactivate channels
        for channel in self.quantum_channels.values():
            channel.active = False
        
        # Reset state
        self.current_state = QuantumState.IDLE
        
        self.logger.info("✅ Quantum Communication System shutdown complete")
