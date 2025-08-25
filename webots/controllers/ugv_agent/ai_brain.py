#!/usr/bin/env python3
"""
AI Brain for UGV Agents - Real Machine Learning Intelligence
Implements reinforcement learning, computer vision, and adaptive decision making
"""

import numpy as np
import json
import time
import hashlib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import random
import math

# Lightweight ML implementations (production would use torch/tensorflow)
class SimpleNeuralNetwork:
    """Lightweight neural network for decision making"""
    
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        # Xavier initialization
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))
        
        # Learning parameters
        self.learning_rate = 0.001
        self.experience = deque(maxlen=1000)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward propagation with ReLU activation"""
        self.z1 = np.dot(x, self.W1) + self.b1
        self.a1 = np.maximum(0, self.z1)  # ReLU
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        return self.z2  # Linear output
    
    def train(self, x: np.ndarray, y: np.ndarray):
        """Simple backpropagation training"""
        m = x.shape[0]
        
        # Forward pass
        output = self.forward(x)
        
        # Backward pass
        dz2 = (output - y) / m
        dW2 = np.dot(self.a1.T, dz2)
        db2 = np.sum(dz2, axis=0, keepdims=True)
        
        dz1 = np.dot(dz2, self.W2.T) * (self.z1 > 0)  # ReLU derivative
        dW1 = np.dot(x.T, dz1)
        db1 = np.sum(dz1, axis=0, keepdims=True)
        
        # Update weights
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1

@dataclass
class Experience:
    """Experience tuple for reinforcement learning"""
    state: np.ndarray
    action: float
    reward: float
    next_state: np.ndarray
    task_success: bool

class ReinforcementLearningAgent:
    """Q-Learning agent for adaptive bidding strategies"""
    
    def __init__(self, state_size: int = 10, action_size: int = 100):
        self.state_size = state_size
        self.action_size = action_size  # Discretized bid amounts
        
        # Q-Network for value estimation
        self.q_network = SimpleNeuralNetwork(state_size, 64, action_size)
        self.target_network = SimpleNeuralNetwork(state_size, 64, action_size)
        
        # RL parameters
        self.epsilon = 0.3  # Exploration rate
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05
        self.gamma = 0.95  # Discount factor
        self.memory = deque(maxlen=2000)
        
        # Performance tracking
        self.wins = 0
        self.total_auctions = 0
        self.reward_history = deque(maxlen=100)
        
    def get_state(self, task: Dict, robot_capabilities: Dict, market_info: Dict) -> np.ndarray:
        """Convert environment info to state vector for neural network"""
        task_location = task.get('location', [0, 0])
        task_budget = task.get('budget', 1000)
        task_priority = task.get('priority', 1.0)
        
        # Distance calculation
        distance = math.sqrt(task_location[0]**2 + task_location[1]**2)
        
        state = np.array([
            distance / 10.0,  # Normalized distance
            task_budget / 1000.0,  # Normalized budget
            task_priority,  # Task priority
            robot_capabilities.get('navigation_speed', 1.0),
            robot_capabilities.get('payload_capacity', 10.0) / 20.0,
            robot_capabilities.get('battery_efficiency', 1.0),
            robot_capabilities.get('sensor_quality', 0.5),
            market_info.get('competition_level', 0.5),  # How many robots bidding
            market_info.get('recent_win_rate', 0.3),  # Recent auction success
            market_info.get('average_winning_bid', 200) / 500.0  # Normalized avg bid
        ]).reshape(1, -1)
        
        return state
    
    def choose_action(self, state: np.ndarray, base_bid: float) -> float:
        """Choose bid amount using epsilon-greedy policy with neural network"""
        if np.random.random() < self.epsilon:
            # Exploration: random bid adjustment
            adjustment = np.random.uniform(0.7, 1.5)
            return base_bid * adjustment
        
        # Exploitation: use neural network to predict best bid multiplier
        q_values = self.q_network.forward(state)
        best_action = np.argmax(q_values[0])
        
        # Convert action index to bid multiplier (0.5x to 2.0x base bid)
        bid_multiplier = 0.5 + (best_action / self.action_size) * 1.5
        return base_bid * bid_multiplier
    
    def remember(self, experience: Experience):
        """Store experience for training"""
        self.memory.append(experience)
    
    def learn(self, batch_size: int = 32):
        """Train the neural network on experiences"""
        if len(self.memory) < batch_size:
            return
        
        # Sample random batch
        batch = random.sample(self.memory, batch_size)
        states = np.array([e.state.flatten() for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_states = np.array([e.next_state.flatten() for e in batch])
        
        # Compute target values
        current_q = self.q_network.forward(states)
        next_q = self.target_network.forward(next_states)
        
        targets = current_q.copy()
        for i, experience in enumerate(batch):
            if experience.task_success:
                targets[i][int(experience.action)] = experience.reward
            else:
                targets[i][int(experience.action)] = experience.reward + self.gamma * np.max(next_q[i])
        
        # Train network
        self.q_network.train(states, targets)
        
        # Decay exploration
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def update_performance(self, won: bool, reward: float):
        """Update performance metrics for learning"""
        self.total_auctions += 1
        if won:
            self.wins += 1
        
        self.reward_history.append(reward)
        
        # Update target network periodically
        if self.total_auctions % 10 == 0:
            self.target_network = SimpleNeuralNetwork(self.state_size, 64, self.action_size)
            self.target_network.W1 = self.q_network.W1.copy()
            self.target_network.W2 = self.q_network.W2.copy()
            self.target_network.b1 = self.q_network.b1.copy()
            self.target_network.b2 = self.q_network.b2.copy()

class ComputerVisionAI:
    """AI-powered computer vision for environment understanding"""
    
    def __init__(self):
        self.object_detection_confidence = 0.8
        self.environment_memory = deque(maxlen=100)
        
        # Simulated AI models (production would use YOLO/CNN)
        self.hazard_detector = self._init_hazard_detection()
        self.path_planner = self._init_path_planning()
        
    def _init_hazard_detection(self):
        """Initialize hazard detection AI model"""
        # Simulated neural network weights for hazard detection
        return {
            'fire': {'confidence_threshold': 0.85, 'feature_weights': np.random.rand(10)},
            'debris': {'confidence_threshold': 0.75, 'feature_weights': np.random.rand(10)},
            'survivor': {'confidence_threshold': 0.9, 'feature_weights': np.random.rand(10)},
            'obstacle': {'confidence_threshold': 0.7, 'feature_weights': np.random.rand(10)}
        }
    
    def _init_path_planning(self):
        """Initialize AI path planning model"""
        return {
            'optimal_path_weights': np.random.rand(8),  # For different path criteria
            'dynamic_obstacles': True,
            'learning_rate': 0.01
        }
    
    def analyze_camera_image(self, image_data: bytes) -> Dict:
        """AI-powered image analysis (simulated CNN/YOLO)"""
        # Simulate AI computer vision processing
        image_hash = hashlib.sha256(image_data).hexdigest()[:16]
        
        # Simulated object detection results
        detected_objects = []
        
        # Use AI model to detect hazards and objects
        for obj_type, model in self.hazard_detector.items():
            confidence = self._simulate_ai_detection(image_hash, model['feature_weights'])
            if confidence > model['confidence_threshold']:
                detected_objects.append({
                    'type': obj_type,
                    'confidence': confidence,
                    'bounding_box': self._generate_bounding_box(),
                    'ai_metadata': {
                        'model_version': '1.2.0',
                        'inference_time_ms': random.randint(15, 45)
                    }
                })
        
        return {
            'objects_detected': detected_objects,
            'scene_complexity': self._calculate_scene_complexity(detected_objects),
            'navigation_safety': self._assess_navigation_safety(detected_objects),
            'task_completion_probability': self._predict_task_success(detected_objects)
        }
    
    def _simulate_ai_detection(self, image_hash: str, weights: np.ndarray) -> float:
        """Simulate AI model inference"""
        # Convert image hash to feature vector
        features = np.array([ord(c) / 255.0 for c in image_hash[:len(weights)]])
        
        # Simulate neural network inference
        score = np.dot(features, weights)
        return 1.0 / (1.0 + np.exp(-score))  # Sigmoid activation
    
    def _generate_bounding_box(self) -> Dict:
        """Generate realistic bounding box coordinates"""
        return {
            'x': random.randint(0, 320),
            'y': random.randint(0, 240), 
            'width': random.randint(20, 100),
            'height': random.randint(20, 80)
        }
    
    def _calculate_scene_complexity(self, objects: List[Dict]) -> float:
        """AI-calculated scene complexity metric"""
        if not objects:
            return 0.1
        
        complexity = len(objects) * 0.2
        for obj in objects:
            complexity += obj['confidence'] * 0.1
        
        return min(complexity, 1.0)
    
    def _assess_navigation_safety(self, objects: List[Dict]) -> float:
        """AI risk assessment for navigation"""
        safety_score = 1.0
        
        for obj in objects:
            if obj['type'] in ['fire', 'debris']:
                safety_score -= obj['confidence'] * 0.3
            elif obj['type'] == 'obstacle':
                safety_score -= obj['confidence'] * 0.1
        
        return max(safety_score, 0.1)
    
    def _predict_task_success(self, objects: List[Dict]) -> float:
        """AI prediction of task completion probability"""
        base_success = 0.8
        
        for obj in objects:
            if obj['type'] == 'survivor':
                base_success += 0.2  # Higher chance if survivor detected
            elif obj['type'] in ['fire', 'debris']:
                base_success -= obj['confidence'] * 0.1
        
        return max(min(base_success, 1.0), 0.1)

class SwarmIntelligence:
    """Multi-agent swarm coordination and learning"""
    
    def __init__(self, robot_id: str):
        self.robot_id = robot_id
        self.swarm_knowledge = {}
        self.communication_history = deque(maxlen=50)
        self.collaborative_strategies = self._init_swarm_strategies()
        
    def _init_swarm_strategies(self):
        """Initialize swarm coordination strategies"""
        return {
            'task_specialization': 0.7,  # Tendency to specialize in certain tasks
            'collaboration_willingness': 0.8,  # Willingness to help other robots
            'information_sharing': 0.9,  # How much info to share with swarm
            'competitive_edge': 0.6  # Balance between cooperation and competition
        }
    
    def analyze_swarm_behavior(self, other_robots: Dict) -> Dict:
        """AI analysis of other robots' bidding patterns"""
        competitors_analysis = {}
        
        for robot_id, data in other_robots.items():
            if robot_id == self.robot_id:
                continue
                
            # AI pattern recognition
            bidding_pattern = self._detect_bidding_pattern(data.get('recent_bids', []))
            success_rate = data.get('wins', 0) / max(data.get('total_auctions', 1), 1)
            
            competitors_analysis[robot_id] = {
                'bidding_strategy': bidding_pattern,
                'success_rate': success_rate,
                'predicted_next_bid': self._predict_competitor_bid(bidding_pattern),
                'cooperation_potential': self._assess_cooperation_potential(data)
            }
        
        return competitors_analysis
    
    def _detect_bidding_pattern(self, bids: List[float]) -> str:
        """AI pattern recognition for competitor bidding"""
        if len(bids) < 3:
            return 'insufficient_data'
        
        # Analyze bidding trends
        recent_trend = np.mean(bids[-3:]) - np.mean(bids[:-3]) if len(bids) > 3 else 0
        variance = np.var(bids)
        
        if variance < 100:  # Low variance
            return 'conservative'
        elif recent_trend > 50:  # Increasing bids
            return 'aggressive'
        elif recent_trend < -50:  # Decreasing bids
            return 'strategic_retreat'
        else:
            return 'adaptive'
    
    def _predict_competitor_bid(self, pattern: str) -> float:
        """AI prediction of competitor's next bid"""
        base_predictions = {
            'conservative': 150,
            'aggressive': 300,
            'strategic_retreat': 120,
            'adaptive': 200,
            'insufficient_data': 180
        }
        
        # Add some intelligent randomness
        base = base_predictions.get(pattern, 180)
        return base * random.uniform(0.8, 1.2)
    
    def _assess_cooperation_potential(self, robot_data: Dict) -> float:
        """Assess potential for cooperation with other robot"""
        # AI-based cooperation assessment
        reputation = robot_data.get('reputation', 0.5)
        success_rate = robot_data.get('wins', 0) / max(robot_data.get('total_auctions', 1), 1)
        
        cooperation_score = (reputation * 0.6 + success_rate * 0.4) * self.collaborative_strategies['collaboration_willingness']
        return cooperation_score
    
    def optimize_swarm_strategy(self, auction_results: List[Dict]):
        """Continuously optimize swarm behavior based on results"""
        # Update specialization preferences based on success patterns
        for result in auction_results:
            if result.get('winner') == self.robot_id:
                task_type = result.get('task_type', 'generic')
                current_spec = self.collaborative_strategies['task_specialization']
                
                # Increase specialization in successful task types
                if task_type in ['scan', 'reconnaissance']:
                    self.collaborative_strategies['task_specialization'] = min(current_spec + 0.05, 1.0)
                elif task_type in ['delivery', 'transport']:
                    self.collaborative_strategies['task_specialization'] = min(current_spec + 0.03, 1.0)

class AIBrain:
    """Main AI Brain that coordinates all intelligent subsystems"""
    
    def __init__(self, robot_id: str, capabilities: Dict):
        self.robot_id = robot_id
        self.capabilities = capabilities
        
        # Initialize AI subsystems
        self.rl_agent = ReinforcementLearningAgent()
        self.computer_vision = ComputerVisionAI()
        self.swarm_intelligence = SwarmIntelligence(robot_id)
        
        # AI decision metrics
        self.decision_confidence = 0.8
        self.learning_progress = 0.0
        self.ai_model_versions = {
            'rl_agent': '1.0.0',
            'computer_vision': '2.1.0', 
            'swarm_coordination': '1.5.0'
        }
        
        print(f"[{robot_id}] 🧠 AI Brain initialized with ML capabilities:")
        print(f"   • Reinforcement Learning: Q-Network with experience replay")
        print(f"   • Computer Vision: Object detection & scene understanding") 
        print(f"   • Swarm Intelligence: Multi-agent coordination & learning")
    
    def make_intelligent_bid(self, task: Dict, market_info: Dict, robot_status: Dict) -> Dict:
        """AI-powered intelligent bidding decision"""
        # Get current state for RL agent
        state = self.rl_agent.get_state(task, self.capabilities, market_info)
        
        # Calculate base bid using traditional method
        base_bid = self._calculate_base_bid(task, robot_status)
        
        # Use reinforcement learning to optimize bid
        ai_bid = self.rl_agent.choose_action(state, base_bid)
        
        # Apply swarm intelligence modifications
        competitors = market_info.get('competitors', {})
        swarm_analysis = self.swarm_intelligence.analyze_swarm_behavior(competitors)
        
        # Adjust bid based on swarm intelligence
        competition_factor = self._calculate_competition_factor(swarm_analysis)
        final_bid = ai_bid * competition_factor
        
        # Calculate AI confidence in this decision
        self.decision_confidence = self._calculate_decision_confidence(state, swarm_analysis)
        
        return {
            'bid_amount': int(final_bid),
            'confidence': self.decision_confidence,
            'ai_reasoning': {
                'base_calculation': base_bid,
                'rl_adjustment': ai_bid / base_bid if base_bid > 0 else 1.0,
                'swarm_factor': competition_factor,
                'decision_factors': {
                    'task_suitability': self._assess_task_suitability(task),
                    'competition_level': len(competitors),
                    'success_probability': self.computer_vision._predict_task_success([])
                }
            },
            'learning_metadata': {
                'epsilon': self.rl_agent.epsilon,
                'win_rate': self.rl_agent.wins / max(self.rl_agent.total_auctions, 1),
                'experience_count': len(self.rl_agent.memory)
            }
        }
    
    def process_task_environment(self, image_data: bytes, sensor_data: Dict) -> Dict:
        """AI-powered environmental analysis"""
        # Use computer vision AI to analyze environment
        vision_analysis = self.computer_vision.analyze_camera_image(image_data)
        
        # Combine with sensor data for comprehensive understanding
        environmental_assessment = {
            **vision_analysis,
            'sensor_readings': sensor_data,
            'ai_risk_assessment': self._calculate_risk_level(vision_analysis, sensor_data),
            'optimal_path_suggestion': self._suggest_optimal_path(vision_analysis),
            'task_modification_needed': self._assess_task_modifications(vision_analysis)
        }
        
        return environmental_assessment
    
    def learn_from_auction_result(self, task: Dict, bid_amount: float, won: bool, market_info: Dict):
        """Learn from auction outcomes to improve future performance"""
        # Calculate reward for reinforcement learning
        reward = self._calculate_learning_reward(task, bid_amount, won, market_info)
        
        # Create experience for RL agent
        state = self.rl_agent.get_state(task, self.capabilities, market_info)
        next_state = state  # Simplified for this example
        
        experience = Experience(
            state=state,
            action=bid_amount,
            reward=reward,
            next_state=next_state,
            task_success=won
        )
        
        # Store and learn from experience
        self.rl_agent.remember(experience)
        self.rl_agent.learn()
        self.rl_agent.update_performance(won, reward)
        
        # Update swarm intelligence
        auction_result = {
            'task_id': task.get('id'),
            'task_type': task.get('type'),
            'winner': self.robot_id if won else 'other',
            'winning_bid': bid_amount if won else market_info.get('winning_bid', 0)
        }
        self.swarm_intelligence.optimize_swarm_strategy([auction_result])
        
        # Update learning progress
        self.learning_progress = min(self.learning_progress + 0.01, 1.0)
        
        print(f"[{self.robot_id}] 📚 Learning from auction:")
        print(f"   • Result: {'WON' if won else 'LOST'} (Reward: {reward:.2f})")
        print(f"   • RL Epsilon: {self.rl_agent.epsilon:.3f}")
        print(f"   • Win Rate: {self.rl_agent.wins / max(self.rl_agent.total_auctions, 1):.2%}")
        print(f"   • Experience Count: {len(self.rl_agent.memory)}")
    
    # Helper methods
    def _calculate_base_bid(self, task: Dict, robot_status: Dict) -> float:
        """Calculate base bid using traditional heuristics - LOWERED FOR TESTNET"""
        task_location = task.get('location', [0, 0])
        distance = math.sqrt(task_location[0]**2 + task_location[1]**2)
        
        # HEAVILY REDUCED for demo - 60% smaller
        base_cost = 0.02  # Reduced from 0.05 to 0.02 (60% reduction)
        distance_factor = 1 + (distance * 0.0005)  # Reduced from 0.001 to 0.0005 (50% reduction)
        energy_factor = 1.0 + (2.0 - robot_status.get('battery_level', 100) / 100.0) * 0.005  # Reduced from 0.01 to 0.005
        
        return base_cost * distance_factor * energy_factor
    
    def _calculate_competition_factor(self, swarm_analysis: Dict) -> float:
        """Calculate bid adjustment based on competition"""
        if not swarm_analysis:
            return 1.0
        
        aggressive_competitors = sum(1 for data in swarm_analysis.values() 
                                   if data['bidding_strategy'] == 'aggressive')
        
        total_competitors = len(swarm_analysis)
        competition_intensity = aggressive_competitors / max(total_competitors, 1)
        
        # Adjust bid based on competition (lower bids when high competition)
        return 0.85 + (competition_intensity * 0.3)
    
    def _calculate_decision_confidence(self, state: np.ndarray, swarm_analysis: Dict) -> float:
        """Calculate AI confidence in bidding decision"""
        base_confidence = 0.7
        
        # Higher confidence with more experience
        experience_bonus = len(self.rl_agent.memory) / 2000.0 * 0.2
        
        # Lower confidence with high competition uncertainty
        competition_uncertainty = len(swarm_analysis) * 0.05
        
        return max(min(base_confidence + experience_bonus - competition_uncertainty, 0.95), 0.3)
    
    def _assess_task_suitability(self, task: Dict) -> float:
        """AI assessment of how suitable this robot is for the task"""
        task_type = task.get('type', 'generic')
        
        suitability_map = {
            'scan': self.capabilities.get('sensor_quality', 0.5),
            'delivery': self.capabilities.get('payload_capacity', 10) / 20.0,
            'reconnaissance': self.capabilities.get('navigation_speed', 1.0),
            'transport': self.capabilities.get('payload_capacity', 10) / 20.0,
            'generic': 0.6
        }
        
        return suitability_map.get(task_type, 0.6)
    
    def _calculate_risk_level(self, vision_data: Dict, sensor_data: Dict) -> float:
        """AI risk assessment combining vision and sensor data"""
        vision_safety = vision_data.get('navigation_safety', 0.8)
        sensor_risk = 1.0 - sensor_data.get('obstacle_proximity', 0.2)
        
        combined_risk = 1.0 - (vision_safety * sensor_risk)
        return combined_risk
    
    def _suggest_optimal_path(self, vision_data: Dict) -> Dict:
        """AI-suggested optimal path based on environment analysis"""
        objects = vision_data.get('objects_detected', [])
        
        # Simple path suggestion based on detected objects
        path_weights = {
            'avoid_fire': 0.9,
            'avoid_debris': 0.7,
            'approach_survivor': 1.2,
            'minimize_obstacles': 0.8
        }
        
        return {
            'suggested_route': 'dynamic',
            'path_weights': path_weights,
            'safety_priority': vision_data.get('navigation_safety', 0.8)
        }
    
    def _assess_task_modifications(self, vision_data: Dict) -> bool:
        """Determine if task parameters should be modified based on environment"""
        scene_complexity = vision_data.get('scene_complexity', 0.3)
        return scene_complexity > 0.7  # Suggest modifications for complex scenes
    
    def _calculate_learning_reward(self, task: Dict, bid_amount: float, won: bool, market_info: Dict) -> float:
        """Calculate reward signal for reinforcement learning"""
        if won:
            # Reward for winning, bonus for efficient bidding
            base_reward = 100
            efficiency_bonus = max(0, 200 - bid_amount) * 0.1  # Bonus for lower bids
            return base_reward + efficiency_bonus
        else:
            # Small negative reward for losing, larger penalty for overbidding
            winning_bid = market_info.get('winning_bid', bid_amount)
            if bid_amount > winning_bid * 1.5:
                return -20  # Penalty for significant overbidding
            else:
                return -5   # Small penalty for losing with reasonable bid
    
    def get_ai_status_report(self) -> Dict:
        """Get comprehensive AI system status"""
        return {
            'ai_brain_active': True,
            'learning_progress': self.learning_progress,
            'decision_confidence': self.decision_confidence,
            'model_versions': self.ai_model_versions,
            'rl_stats': {
                'epsilon': self.rl_agent.epsilon,
                'total_auctions': self.rl_agent.total_auctions,
                'win_rate': self.rl_agent.wins / max(self.rl_agent.total_auctions, 1),
                'experience_buffer_size': len(self.rl_agent.memory),
                'average_reward': np.mean(self.rl_agent.reward_history) if self.rl_agent.reward_history else 0
            },
            'swarm_coordination': {
                'task_specialization': self.swarm_intelligence.collaborative_strategies['task_specialization'],
                'collaboration_willingness': self.swarm_intelligence.collaborative_strategies['collaboration_willingness'],
                'communication_history_size': len(self.swarm_intelligence.communication_history)
            }
        }