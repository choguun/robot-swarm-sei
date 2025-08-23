#!/Users/choguun/.pyenv/versions/3.10.17/bin/python3.10
"""
UGV Agent Controller for Robot Swarm Coordination
Handles autonomous bidding, navigation, and proof capture
"""

import sys
import json
import time
import hashlib
import math
from typing import Dict, List, Tuple, Optional

# Webots imports
from controller import Robot, GPS, Camera, Compass, InertialUnit, Emitter, Receiver

# AI Brain import
try:
    from ai_brain import AIBrain
    AI_BRAIN_AVAILABLE = True
    print("🧠 AI Brain module loaded - Advanced ML capabilities enabled")
except ImportError as e:
    print(f"⚠️  AI Brain not available: {e}")
    print("   Falling back to rule-based decision making")
    AI_BRAIN_AVAILABLE = False

class UGVAgent:
    """Autonomous UGV agent for disaster response tasks"""
    
    def __init__(self):
        # Initialize robot
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Robot identification
        self.robot_id = self.robot.getName()
        self.capabilities = self._init_capabilities()
        
        # Initialize devices
        self._init_devices()
        
        # State management
        self.current_task = None
        self.reputation_score = 0.9  # Initial reputation
        self.battery_level = 100.0
        self.position = [0.0, 0.0, 0.0]
        self.waypoints = []
        self.captured_proofs = []
        
        # Communication
        self.bids_sent = {}
        self.task_assignments = {}
        
        # Initialize AI Brain
        if AI_BRAIN_AVAILABLE:
            self.ai_brain = AIBrain(self.robot_id, self.capabilities)
            self.ai_enabled = True
            print(f"[{self.robot_id}] 🤖 AI-Enhanced Agent initialized with ML capabilities")
        else:
            self.ai_brain = None
            self.ai_enabled = False
            print(f"[{self.robot_id}] UGV Agent initialized with capabilities: {self.capabilities}")
        
        print(f"   • Navigation Speed: {self.capabilities['navigation_speed']}")
        print(f"   • AI Mode: {'🧠 ENABLED' if self.ai_enabled else '📊 Rule-based'}")
    
    def _init_capabilities(self) -> Dict[str, float]:
        """Initialize robot capabilities based on robot name"""
        base_capabilities = {
            'navigation_speed': 1.0,
            'payload_capacity': 10.0,
            'battery_efficiency': 1.0,
            'terrain_adaptability': 0.8,
            'sensor_quality': 0.7
        }
        
        # Customize based on robot ID
        if 'alpha' in self.robot_id:
            base_capabilities['navigation_speed'] = 1.2
            base_capabilities['terrain_adaptability'] = 0.9
        elif 'beta' in self.robot_id:
            base_capabilities['payload_capacity'] = 15.0
            base_capabilities['sensor_quality'] = 0.9
        elif 'gamma' in self.robot_id:
            base_capabilities['battery_efficiency'] = 1.3
            base_capabilities['navigation_speed'] = 0.8
            
        return base_capabilities
    
    def _init_devices(self):
        """Initialize robot sensors and communication devices"""
        # Motor control
        self.left_motor = self.robot.getDevice('left wheel motor')
        self.right_motor = self.robot.getDevice('right wheel motor')
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
        
        # Sensors
        self.gps = self.robot.getDevice('gps')
        if self.gps:
            self.gps.enable(self.timestep)
        else:
            print(f"[{self.robot_id}] Warning: GPS not available, using simulated position")
        
        self.camera = self.robot.getDevice('camera')
        if self.camera:
            self.camera.enable(self.timestep)
        else:
            print(f"[{self.robot_id}] Warning: Camera not available")
        
        self.compass = self.robot.getDevice('compass')
        if self.compass:
            self.compass.enable(self.timestep)
        else:
            print(f"[{self.robot_id}] Warning: Compass not available")
        
        # Communication
        self.emitter = self.robot.getDevice('emitter')
        self.receiver = self.robot.getDevice('receiver')
        if self.receiver:
            self.receiver.enable(self.timestep)
        else:
            print(f"[{self.robot_id}] Warning: Receiver not available")
        
        # Proximity sensors for obstacle avoidance
        self.proximity_sensors = []
        for i in range(8):
            sensor = self.robot.getDevice(f'ps{i}')
            sensor.enable(self.timestep)
            self.proximity_sensors.append(sensor)
    
    def update_position(self):
        """Update current position from GPS or use simulated position"""
        if self.gps and self.gps.getValues():
            self.position = list(self.gps.getValues())
        else:
            # Use simulated position based on robot name for demo
            positions = {
                'ugv_alpha': [-2, -2, 0],
                'ugv_beta': [2, -2, 0], 
                'ugv_gamma': [0, -8, 0]
            }
            if self.robot_id in positions:
                self.position = positions[self.robot_id]
    
    def calculate_bid(self, task: Dict) -> Dict:
        """AI-Enhanced bid calculation with machine learning"""
        
        if self.ai_enabled and self.ai_brain:
            # 🧠 Use AI Brain for intelligent bidding
            return self._ai_calculate_bid(task)
        else:
            # 📊 Fall back to rule-based bidding
            return self._rule_based_calculate_bid(task)
    
    def _ai_calculate_bid(self, task: Dict) -> Dict:
        """AI-powered intelligent bidding with machine learning"""
        # Gather market intelligence
        market_info = self._gather_market_intelligence()
        
        # Current robot status for AI decision
        robot_status = {
            'battery_level': self.battery_level,
            'current_position': self.position,
            'active_tasks': len(self.task_assignments),
            'recent_performance': self.reputation_score
        }
        
        # Use AI brain to make intelligent bid decision
        ai_decision = self.ai_brain.make_intelligent_bid(task, market_info, robot_status)
        
        # Extract traditional metrics for compatibility
        task_location = task.get('location', [0, 0])
        distance = math.sqrt(
            (task_location[0] - self.position[0])**2 + 
            (task_location[1] - self.position[1])**2
        )
        
        # Estimate time using AI-enhanced method
        base_time = distance / self.capabilities['navigation_speed']
        task_execution_time = self._estimate_task_time(task.get('type', 'scan'))
        total_time = base_time + task_execution_time
        
        # Calculate energy and capability match
        energy_cost = self._calculate_energy_cost(distance, task.get('type', 'scan'))
        capability_match = self._calculate_capability_match(task)
        
        print(f"[{self.robot_id}] 🧠 AI BID: {ai_decision['bid_amount']} SEI")
        print(f"   • Confidence: {ai_decision['confidence']:.2%}")
        print(f"   • RL Factor: {ai_decision['ai_reasoning']['rl_adjustment']:.2f}x")
        print(f"   • Win Rate: {ai_decision['learning_metadata']['win_rate']:.2%}")
        print(f"   • Experience: {ai_decision['learning_metadata']['experience_count']} samples")
        
        return {
            'robotId': self.robot_id,
            'taskId': task['taskId'],
            'bidAmount': ai_decision['bid_amount'],
            'estimatedTime': int(total_time),
            'capabilityMatch': capability_match,
            'energyCost': energy_cost,
            'reputation': self.reputation_score,
            'batteryLevel': self.battery_level,
            # AI-specific metadata
            'ai_metadata': {
                'confidence': ai_decision['confidence'],
                'decision_method': 'reinforcement_learning',
                'learning_progress': self.ai_brain.learning_progress,
                'model_versions': self.ai_brain.ai_model_versions,
                'reasoning': ai_decision['ai_reasoning']
            }
        }
    
    def _rule_based_calculate_bid(self, task: Dict) -> Dict:
        """Traditional rule-based bidding (fallback)"""
        # Extract task parameters
        task_location = task.get('location', [0, 0])
        task_type = task.get('type', 'scan')
        task_priority = task.get('priority', 1.0)
        
        # Calculate distance to task
        distance = math.sqrt(
            (task_location[0] - self.position[0])**2 + 
            (task_location[1] - self.position[1])**2
        )
        
        # Estimate time to complete
        base_time = distance / self.capabilities['navigation_speed']
        task_execution_time = self._estimate_task_time(task_type)
        total_time = base_time + task_execution_time
        
        # Calculate energy cost
        energy_cost = self._calculate_energy_cost(distance, task_type)
        
        # Capability match score
        capability_match = self._calculate_capability_match(task)
        
        # Base bid calculation
        base_cost = 50  # Base cost in Sei tokens
        distance_factor = 1 + (distance * 0.1)
        time_factor = 1 + (total_time * 0.01)
        energy_factor = 1 + (energy_cost * 0.02)
        
        # Apply capability bonus/penalty
        capability_factor = 0.5 + (capability_match * 0.5)
        
        # Reputation modifier (better reputation = more competitive bids)
        reputation_factor = 2 - self.reputation_score
        
        # Final bid amount
        bid_amount = int(base_cost * distance_factor * time_factor * 
                        energy_factor * capability_factor * reputation_factor)
        
        return {
            'robotId': self.robot_id,
            'taskId': task['taskId'],
            'bidAmount': bid_amount,
            'estimatedTime': int(total_time),
            'capabilityMatch': capability_match,
            'energyCost': energy_cost,
            'reputation': self.reputation_score,
            'batteryLevel': self.battery_level,
            'ai_metadata': {
                'decision_method': 'rule_based_fallback'
            }
        }
    
    def _gather_market_intelligence(self) -> Dict:
        """Gather market intelligence for AI decision making"""
        # Simulate market data gathering (in production, this would query blockchain/coordinator)
        return {
            'competition_level': 0.7,  # How many robots are likely bidding
            'recent_win_rate': 0.3,    # Recent auction success rate
            'average_winning_bid': 180, # Average winning bid amount
            'market_volatility': 0.4,  # How much bid prices fluctuate
            'competitors': {
                # Simulated competitor data for AI analysis
                'ugv_alpha': {'recent_bids': [120, 150, 140], 'wins': 2, 'total_auctions': 5},
                'ugv_beta': {'recent_bids': [180, 200, 190], 'wins': 3, 'total_auctions': 6},
                'ugv_gamma': {'recent_bids': [100, 130, 120], 'wins': 1, 'total_auctions': 4}
            }
        }
    
    def _estimate_task_time(self, task_type: str) -> float:
        """Estimate time to complete specific task type"""
        task_times = {
            'scan': 30,
            'debris_clear': 60,
            'delivery': 45,
            'reconnaissance': 40
        }
        return task_times.get(task_type, 30)
    
    def _calculate_energy_cost(self, distance: float, task_type: str) -> float:
        """Calculate expected energy consumption"""
        base_energy = distance * 2 / self.capabilities['battery_efficiency']
        
        task_energy = {
            'scan': 5,
            'debris_clear': 15,
            'delivery': 10,
            'reconnaissance': 8
        }
        
        return base_energy + task_energy.get(task_type, 5)
    
    def _calculate_capability_match(self, task: Dict) -> float:
        """Calculate how well robot capabilities match task requirements"""
        task_type = task.get('type', 'scan')
        
        # Weight different capabilities based on task type
        if task_type == 'scan':
            return (self.capabilities['sensor_quality'] * 0.6 + 
                   self.capabilities['navigation_speed'] * 0.4)
        elif task_type == 'debris_clear':
            return (self.capabilities['payload_capacity'] * 0.1 * 0.7 + 
                   self.capabilities['terrain_adaptability'] * 0.3)
        elif task_type == 'delivery':
            return (self.capabilities['navigation_speed'] * 0.5 + 
                   self.capabilities['battery_efficiency'] * 0.3 +
                   self.capabilities['payload_capacity'] * 0.1 * 0.2)
        else:
            return sum(self.capabilities.values()) / len(self.capabilities)
    
    def send_bid(self, bid: Dict):
        """Send bid to supervisor"""
        message = {
            'type': 'bid',
            'data': bid,
            'timestamp': time.time(),
            'sender': self.robot_id
        }
        
        self.emitter.send(json.dumps(message))
        self.bids_sent[bid['taskId']] = bid
        
        print(f"[{self.robot_id}] Sent bid: {bid['bidAmount']} for task {bid['taskId']}")
    
    def receive_messages(self):
        """Process incoming messages from supervisor"""
        while self.receiver.getQueueLength() > 0:
            try:
                message_str = self.receiver.getString()
                message = json.loads(message_str)
                self.receiver.nextPacket()
                
                if message['type'] == 'task_auction':
                    self._handle_task_auction(message['data'])
                elif message['type'] == 'task_assignment':
                    self._handle_task_assignment(message['data'])
                elif message['type'] == 'task_timeout':
                    self._handle_task_timeout(message['data'])
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[{self.robot_id}] Error processing message: {e}")
                self.receiver.nextPacket()
    
    def _handle_task_auction(self, task_data: Dict):
        """Handle new task auction"""
        if not self._should_bid_for_task(task_data):
            return
            
        bid = self.calculate_bid(task_data)
        self.send_bid(bid)
    
    def _handle_task_assignment(self, assignment_data: Dict):
        """Handle task assignment"""
        if assignment_data['robotId'] == self.robot_id:
            self.current_task = assignment_data
            self.waypoints = assignment_data.get('waypoints', [])
            print(f"[{self.robot_id}] Assigned task {assignment_data['taskId']}")
            self._start_task_execution()
    
    def _handle_task_timeout(self, timeout_data: Dict):
        """Handle task timeout notification"""
        task_id = timeout_data.get('taskId')
        if self.current_task and self.current_task.get('taskId') == task_id:
            print(f"[{self.robot_id}] Task {task_id} timed out")
            self.current_task = None
            self.waypoints = []
            self._stop_movement()
    
    def _should_bid_for_task(self, task: Dict) -> bool:
        """Determine if robot should bid for task"""
        # Don't bid if already busy
        if self.current_task:
            return False
            
        # Don't bid if battery too low
        if self.battery_level < 20:
            return False
            
        # Check if task is within capabilities
        capability_match = self._calculate_capability_match(task)
        return capability_match > 0.3
    
    def _start_task_execution(self):
        """Begin executing assigned task"""
        if not self.waypoints:
            print(f"[{self.robot_id}] No waypoints provided for task")
            return
            
        print(f"[{self.robot_id}] Starting task execution with {len(self.waypoints)} waypoints")
        self.captured_proofs = []
    
    def navigate_to_waypoint(self, waypoint: List[float]) -> bool:
        """Navigate to specific waypoint"""
        target_x, target_y = waypoint[0], waypoint[1]
        
        # Calculate direction to target
        dx = target_x - self.position[0]
        dy = target_y - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if reached waypoint
        if distance < 0.5:
            return True
            
        # Get current heading from compass
        compass_values = self.compass.getValues()
        current_heading = math.atan2(compass_values[0], compass_values[2])
        
        # Calculate target heading
        target_heading = math.atan2(dy, dx)
        heading_error = target_heading - current_heading
        
        # Normalize heading error
        while heading_error > math.pi:
            heading_error -= 2 * math.pi
        while heading_error < -math.pi:
            heading_error += 2 * math.pi
        
        # Obstacle avoidance
        obstacle_detected, avoidance_angle = self._detect_obstacles()
        
        if obstacle_detected:
            # Adjust heading for obstacle avoidance
            target_heading += avoidance_angle
        
        # Simple proportional control
        max_speed = 6.28  # E-puck max wheel speed
        base_speed = 3.0
        turn_speed = heading_error * 2.0
        
        left_speed = base_speed - turn_speed
        right_speed = base_speed + turn_speed
        
        # Limit speeds
        left_speed = max(-max_speed, min(max_speed, left_speed))
        right_speed = max(-max_speed, min(max_speed, right_speed))
        
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
        
        return False
    
    def _detect_obstacles(self) -> Tuple[bool, float]:
        """Detect obstacles using proximity sensors"""
        sensor_values = [sensor.getValue() for sensor in self.proximity_sensors]
        
        # Threshold for obstacle detection
        obstacle_threshold = 80
        
        # Check front sensors (0, 1, 6, 7)
        front_sensors = [sensor_values[0], sensor_values[1], sensor_values[6], sensor_values[7]]
        
        if any(value > obstacle_threshold for value in front_sensors):
            # Simple avoidance: turn away from strongest signal
            max_value = max(front_sensors)
            max_index = front_sensors.index(max_value)
            
            # Avoidance angles
            avoidance_angles = [0.5, 0.3, -0.3, -0.5]
            return True, avoidance_angles[max_index]
        
        return False, 0.0
    
    def capture_proof(self) -> Dict:
        """Capture proof at current location"""
        # Save camera image
        timestamp = int(time.time() * 1000)
        image_filename = f"proof_{self.robot_id}_{timestamp}.png"
        
        # Get camera image
        self.camera.saveImage(image_filename, 100)
        
        # Calculate image hash (simulation)
        image_hash = hashlib.sha256(f"{image_filename}_{timestamp}".encode()).hexdigest()
        
        # Create waypoint record
        waypoint_data = {
            'position': self.position.copy(),
            'timestamp': timestamp,
            'image_hash': image_hash,
            'image_file': image_filename
        }
        
        # Calculate waypoint hash
        waypoint_str = json.dumps(waypoint_data, sort_keys=True)
        waypoint_hash = hashlib.sha256(waypoint_str.encode()).hexdigest()
        
        proof = {
            'waypoint_hash': waypoint_hash,
            'image_hash': image_hash,
            'position': self.position.copy(),
            'timestamp': timestamp
        }
        
        self.captured_proofs.append(proof)
        print(f"[{self.robot_id}] Captured proof at {self.position}")
        
        return proof
    
    def submit_task_completion(self):
        """Submit completed task with proofs"""
        if not self.current_task:
            return
            
        # Create proof bundle
        waypoint_hashes = [proof['waypoint_hash'] for proof in self.captured_proofs]
        image_hashes = [proof['image_hash'] for proof in self.captured_proofs]
        
        # Calculate combined proof hash
        proof_data = {
            'taskId': self.current_task['taskId'],
            'robotId': self.robot_id,
            'waypoint_hashes': waypoint_hashes,
            'image_hashes': image_hashes,
            'start_time': self.current_task.get('start_time'),
            'completion_time': time.time()
        }
        
        proof_str = json.dumps(proof_data, sort_keys=True)
        proof_bundle_hash = hashlib.sha256(proof_str.encode()).hexdigest()
        
        completion_message = {
            'type': 'task_completion',
            'data': {
                'taskId': self.current_task['taskId'],
                'robotId': self.robot_id,
                'proofBundleHash': proof_bundle_hash,
                'waypointHashes': waypoint_hashes,
                'imageHashes': image_hashes,
                'completionTime': time.time()
            },
            'timestamp': time.time(),
            'sender': self.robot_id
        }
        
        self.emitter.send(json.dumps(completion_message))
        print(f"[{self.robot_id}] Submitted task completion for task {self.current_task['taskId']}")
        
        # Update reputation based on timely completion
        self._update_reputation(True)
        
        # Reset task state
        self.current_task = None
        self.waypoints = []
        self._stop_movement()
    
    def _update_reputation(self, success: bool):
        """Update reputation score based on task outcome"""
        if success:
            self.reputation_score = min(1.0, self.reputation_score + 0.05)
        else:
            self.reputation_score = max(0.1, self.reputation_score - 0.1)
    
    def _stop_movement(self):
        """Stop robot movement"""
        self.left_motor.setVelocity(0.0)
        self.right_motor.setVelocity(0.0)
    
    def run(self):
        """Main robot control loop"""
        print(f"[{self.robot_id}] Starting main control loop")
        
        current_waypoint_index = 0
        proof_capture_timer = 0
        
        while self.robot.step(self.timestep) != -1:
            # Update sensor readings
            self.update_position()
            
            # Process incoming messages
            self.receive_messages()
            
            # Update battery level (simulation)
            self.battery_level = max(0, self.battery_level - 0.001)
            
            # Execute current task
            if self.current_task and self.waypoints:
                if current_waypoint_index < len(self.waypoints):
                    waypoint = self.waypoints[current_waypoint_index]
                    
                    if self.navigate_to_waypoint(waypoint):
                        print(f"[{self.robot_id}] Reached waypoint {current_waypoint_index + 1}/{len(self.waypoints)}")
                        
                        # Capture proof at waypoint
                        self.capture_proof()
                        current_waypoint_index += 1
                        
                        # Small delay for proof capture
                        proof_capture_timer = 10
                
                elif proof_capture_timer > 0:
                    proof_capture_timer -= 1
                    self._stop_movement()
                    
                else:
                    # All waypoints completed
                    self.submit_task_completion()
                    current_waypoint_index = 0
    
    def learn_from_auction_result(self, task: Dict, bid_info: Dict, won: bool, winner_info: Dict = None):
        """AI learning from auction outcomes"""
        if not self.ai_enabled or not self.ai_brain:
            return
        
        # Prepare market information for learning
        market_info = self._gather_market_intelligence()
        if winner_info:
            market_info['winning_bid'] = winner_info.get('bidAmount', 0)
            market_info['winner_id'] = winner_info.get('robotId', 'unknown')
        
        # Let AI brain learn from this experience
        self.ai_brain.learn_from_auction_result(
            task=task, 
            bid_amount=bid_info['bidAmount'], 
            won=won, 
            market_info=market_info
        )
        
        # Update our own performance tracking
        if won:
            self.reputation_score = min(1.0, self.reputation_score + 0.01)
        else:
            # Small penalty for losing, but not too harsh to encourage exploration
            self.reputation_score = max(0.1, self.reputation_score - 0.005)
    
    def ai_analyze_environment(self) -> Dict:
        """AI-powered environment analysis using computer vision"""
        if not self.ai_enabled or not self.ai_brain:
            return {'error': 'AI not available'}
        
        # Get camera image data
        image_data = b''  # Placeholder - in real Webots this would be camera.getImage()
        if hasattr(self, 'camera') and self.camera:
            try:
                # Simulate camera data capture
                timestamp = str(int(time.time() * 1000))
                image_data = f"simulated_image_data_{self.robot_id}_{timestamp}".encode()
            except Exception as e:
                print(f"[{self.robot_id}] Camera error: {e}")
        
        # Gather sensor data
        sensor_data = {
            'proximity_sensors': [sensor.getValue() for sensor in self.proximity_sensors],
            'battery_level': self.battery_level,
            'position': self.position,
            'timestamp': time.time()
        }
        
        # Use AI brain for environmental analysis
        try:
            environment_analysis = self.ai_brain.process_task_environment(image_data, sensor_data)
            
            print(f"[{self.robot_id}] 👁️  AI Vision Analysis:")
            print(f"   • Objects Detected: {len(environment_analysis.get('objects_detected', []))}")
            print(f"   • Navigation Safety: {environment_analysis.get('navigation_safety', 0.8):.2%}")
            print(f"   • Scene Complexity: {environment_analysis.get('scene_complexity', 0.3):.2f}")
            
            return environment_analysis
            
        except Exception as e:
            print(f"[{self.robot_id}] ⚠️  AI analysis error: {e}")
            return {'error': str(e)}
    
    def get_ai_status_report(self) -> Dict:
        """Get comprehensive AI system status for monitoring"""
        if not self.ai_enabled or not self.ai_brain:
            return {
                'ai_enabled': False,
                'decision_method': 'rule_based',
                'learning_progress': 0.0
            }
        
        ai_status = self.ai_brain.get_ai_status_report()
        ai_status.update({
            'robot_id': self.robot_id,
            'current_reputation': self.reputation_score,
            'battery_level': self.battery_level,
            'active_tasks': len(self.task_assignments),
            'capabilities': self.capabilities,
            'system_uptime': time.time() - getattr(self, 'start_time', time.time())
        })
        
        return ai_status
    
    def adapt_ai_strategy(self, performance_feedback: Dict):
        """Adapt AI strategy based on performance feedback"""
        if not self.ai_enabled or not self.ai_brain:
            return
        
        # Update learning parameters based on performance
        recent_win_rate = performance_feedback.get('win_rate', 0.3)
        
        # If performing poorly, increase exploration
        if recent_win_rate < 0.2:
            if hasattr(self.ai_brain.rl_agent, 'epsilon'):
                self.ai_brain.rl_agent.epsilon = min(0.5, self.ai_brain.rl_agent.epsilon + 0.05)
                print(f"[{self.robot_id}] 🔄 Increasing exploration (ε={self.ai_brain.rl_agent.epsilon:.3f})")
        
        # If performing well, focus more on exploitation
        elif recent_win_rate > 0.6:
            if hasattr(self.ai_brain.rl_agent, 'epsilon'):
                self.ai_brain.rl_agent.epsilon = max(0.05, self.ai_brain.rl_agent.epsilon - 0.02)
                print(f"[{self.robot_id}] 🎯 Reducing exploration (ε={self.ai_brain.rl_agent.epsilon:.3f})")
        
        # Update swarm coordination strategy
        if hasattr(self.ai_brain, 'swarm_intelligence'):
            cooperation_feedback = performance_feedback.get('cooperation_success', 0.5)
            current_cooperation = self.ai_brain.swarm_intelligence.collaborative_strategies['collaboration_willingness']
            
            # Adjust cooperation strategy based on feedback
            if cooperation_feedback > 0.7:
                new_cooperation = min(1.0, current_cooperation + 0.05)
                self.ai_brain.swarm_intelligence.collaborative_strategies['collaboration_willingness'] = new_cooperation
                print(f"[{self.robot_id}] 🤝 Increasing cooperation willingness ({new_cooperation:.2f})")

if __name__ == "__main__":
    agent = UGVAgent()
    agent.run()