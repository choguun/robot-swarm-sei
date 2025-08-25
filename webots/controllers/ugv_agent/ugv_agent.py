#!/Users/choguun/.pyenv/versions/3.10.17/bin/python3.10
"""
UGV Agent Controller for Robot Swarm Coordination
Handles autonomous bidding, navigation, and proof capture
"""

import sys
import os
import json
import time
import hashlib
import math
from typing import Dict, List, Tuple, Optional

# Webots imports
from controller import Robot, GPS, Camera, Compass, InertialUnit, Emitter, Receiver

# Swarm Framework imports
try:
    from swarms import Agent, MixtureOfAgents, SwarmRouter, SwarmType
    SWARM_FRAMEWORK_AVAILABLE = True
    print("🌐 Swarms Framework loaded - Multi-agent orchestration enabled")
except ImportError as e:
    print(f"⚠️  Swarms Framework not available: {e}")
    print("   Falling back to individual agent mode")
    SWARM_FRAMEWORK_AVAILABLE = False

# Environment configuration
try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    env_path = '/Users/choguun/Documents/workspaces/hackathon/robot-swarm-sei/webots/controllers/.env'
    load_dotenv(env_path)
    DOTENV_AVAILABLE = True
    print("🔐 Environment variables loaded from .env")
except ImportError:
    print("⚠️  python-dotenv not available, using fallback configuration")
    DOTENV_AVAILABLE = False

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
    """Swarm-Enhanced UGV agent for disaster response tasks"""
    
    def __init__(self, enable_swarm_mode=True):
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
        
        # Motor-based position tracking for E-puck (no GPS)
        self.estimated_x = 0.0
        self.estimated_y = 0.0
        self.estimated_heading = 0.0  # Robot orientation in radians
        self.wheel_radius = 0.0205  # E-puck wheel radius in meters
        self.wheel_distance = 0.052  # Distance between wheels in meters
        self.previous_left_position = 0.0
        self.previous_right_position = 0.0
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
        
        # Initialize Swarm Intelligence
        self.swarm_mode = enable_swarm_mode and SWARM_FRAMEWORK_AVAILABLE
        if self.swarm_mode:
            self._init_swarm_intelligence()
            print(f"[{self.robot_id}] 🌐 SWARM MODE ENABLED - Multi-agent coordination active")
        else:
            self.swarm_agents = {}
            self.swarm_router = None
            self.peer_agents = []
            self.swarm_communication_queue = []
            self.collaboration_history = []
            print(f"[{self.robot_id}] Operating in individual agent mode")
        
        print(f"   • Navigation Speed: {self.capabilities['navigation_speed']}")
        print(f"   • AI Mode: {'🧠 ENABLED' if self.ai_enabled else '📊 Rule-based'}")
        print(f"   • Swarm Mode: {'🌐 ACTIVE' if self.swarm_mode else '🤖 Individual'}")
    
    def _init_capabilities(self) -> Dict[str, float]:
        """Initialize robot capabilities based on robot name"""
        base_capabilities = {
            'navigation_speed': 1.0,
            'payload_capacity': 10.0,
            'battery_efficiency': 1.0,
            'terrain_adaptability': 0.8,
            'sensor_quality': 0.7
        }
        
        # Customize based on robot ID and load wallet keys from environment
        if 'alpha' in self.robot_id:
            base_capabilities['navigation_speed'] = 1.2
            base_capabilities['terrain_adaptability'] = 0.9
            # Load wallet private key from environment
            self.private_key = os.getenv('UGV_ALPHA_PRIVATE_KEY', 
                                        '0x9a79353680bed8b0a61336c90df9efec03a78195b289618fc2be777d007f46c1')
        elif 'beta' in self.robot_id:
            base_capabilities['payload_capacity'] = 15.0
            base_capabilities['sensor_quality'] = 0.9
            # Load wallet private key from environment
            self.private_key = os.getenv('UGV_BETA_PRIVATE_KEY',
                                        '0xc94afabc1cc1fbd6b3ca7079165027406a8fc6e478f74392e17bc1afc2bcd283')
        elif 'gamma' in self.robot_id:
            base_capabilities['battery_efficiency'] = 1.3
            # Load wallet private key from environment
            self.private_key = os.getenv('UGV_GAMMA_PRIVATE_KEY',
                                        '0xd3d6ec92bb10b4ec75a659bf9b464f20bf24dc21a3de2ba2c89ec2af02241686')
            base_capabilities['navigation_speed'] = 0.8
        else:
            # Default to alpha key if no specific robot match
            self.private_key = os.getenv('UGV_ALPHA_PRIVATE_KEY',
                                        '0x9a79353680bed8b0a61336c90df9efec03a78195b289618fc2be777d007f46c1')
            base_capabilities['navigation_speed'] = 0.8
            
        # Calculate wallet address from private key
        try:
            from eth_account import Account
            account = Account.from_key(self.private_key)
            self.wallet_address = account.address
            print(f"[{self.robot_id}] 💳 Wallet Address: {self.wallet_address}")
        except (ImportError, Exception) as e:
            # Real wallet addresses derived from the private keys
            wallet_mapping = {
                "0x9a79353680bed8b0a61336c90df9efec03a78195b289618fc2be777d007f46c1": "0x37E01bF3888F200d3a17936Bc9458c7656679179",  # ugv_alpha
                "0xc94afabc1cc1fbd6b3ca7079165027406a8fc6e478f74392e17bc1afc2bcd283": "0x3BD91974F74dF7F014EAC3747e50819375667881",  # ugv_beta
                "0xd3d6ec92bb10b4ec75a659bf9b464f20bf24dc21a3de2ba2c89ec2af02241686": "0xAEdfb15F457bf3cfe9453af8514Dd9AfA0CF9196"   # ugv_gamma
            }
            self.wallet_address = wallet_mapping.get(self.private_key, "0x0000000000000000000000000000000000000000")
            print(f"[{self.robot_id}] 💳 Wallet Address: {self.wallet_address} (fallback)")
            
        return base_capabilities
    
    def _init_swarm_intelligence(self):
        """Initialize swarm intelligence components"""
        if not SWARM_FRAMEWORK_AVAILABLE:
            return
        
        try:
            # Create specialized swarm agents for different decision-making aspects
            self.swarm_agents = {
                'bidding_strategist': Agent(
                    agent_name=f"BiddingStrategist-{self.robot_id}",
                    system_prompt=f"You are a bidding strategist for robot {self.robot_id}. "
                                 f"Analyze market conditions, competitor behavior, and task requirements "
                                 f"to recommend optimal bidding strategies. Consider robot capabilities: {self.capabilities}",
                    model_name="gpt-4o-mini",
                    max_loops=1
                ),
                'navigation_planner': Agent(
                    agent_name=f"NavigationPlanner-{self.robot_id}",
                    system_prompt=f"You are a navigation and path planning specialist for robot {self.robot_id}. "
                                 f"Optimize routes, coordinate with other robots to avoid conflicts, "
                                 f"and suggest efficient task execution strategies.",
                    model_name="gpt-4o-mini", 
                    max_loops=1
                ),
                'collaboration_coordinator': Agent(
                    agent_name=f"CollaborationCoordinator-{self.robot_id}",
                    system_prompt=f"You are a collaboration coordinator for robot {self.robot_id}. "
                                 f"Facilitate communication between robots, negotiate task sharing, "
                                 f"and optimize collective performance of the robot swarm.",
                    model_name="gpt-4o-mini",
                    max_loops=1
                )
            }
            
            # Initialize swarm orchestration router
            agent_list = list(self.swarm_agents.values())
            self.swarm_router = SwarmRouter(
                swarm_type=SwarmType.MixtureOfAgents,
                agents=agent_list,
                aggregator_agent=Agent(
                    agent_name=f"SwarmAggregator-{self.robot_id}",
                    system_prompt=f"Synthesize recommendations from bidding, navigation, and collaboration "
                                 f"specialists to make final decisions for robot {self.robot_id}.",
                    model_name="gpt-4o-mini"
                )
            )
            
            # Peer communication for inter-robot coordination
            self.peer_agents = []
            self.swarm_communication_queue = []
            self.collaboration_history = []
            
            print(f"[{self.robot_id}] 🌐 Swarm Intelligence initialized with {len(self.swarm_agents)} specialized agents")
            
        except Exception as e:
            print(f"[{self.robot_id}] ⚠️  Swarm initialization failed: {e}")
            print(f"[{self.robot_id}] Falling back to individual agent mode")
            self.swarm_mode = False
            self.swarm_agents = {}
            self.swarm_router = None
            self.peer_agents = []
            self.swarm_communication_queue = []
            self.collaboration_history = []
    
    def _init_devices(self):
        """Initialize robot sensors and communication devices"""
        # Motor control
        self.left_motor = self.robot.getDevice('left wheel motor')
        self.right_motor = self.robot.getDevice('right wheel motor')
        
        # Debug motor initialization  
        if self.left_motor and self.right_motor:
            print(f"[{self.robot_id}] ✅ Motors found and initialized")
            print(f"[{self.robot_id}] 🔧 Timestep: {self.timestep}ms")
            
            # CRITICAL FIX: Ensure proper motor setup for E-puck
            # Force velocity mode explicitly
            self.left_motor.setPosition(float('inf'))
            self.right_motor.setPosition(float('inf'))
            
            # Enable position sensors for odometry
            if self.left_motor.getPositionSensor():
                self.left_motor.getPositionSensor().enable(self.timestep)
            if self.right_motor.getPositionSensor():
                self.right_motor.getPositionSensor().enable(self.timestep)
            
            # Start with zero velocity and confirm
            self.left_motor.setVelocity(0.0)
            self.right_motor.setVelocity(0.0)
            
            print(f"[{self.robot_id}] 🔧 Motors configured for velocity control")
            print(f"[{self.robot_id}] 📍 Position sensors enabled for odometry")
            
            # Add immediate movement test
            print(f"[{self.robot_id}] 🧪 IMMEDIATE MOVEMENT TEST")
            self.left_motor.setVelocity(3.14)  # Half of max E-puck speed
            self.right_motor.setVelocity(3.14)
            
            # Check motor limits and capabilities
            try:
                print(f"[{self.robot_id}] 🔬 Motor max velocity: {self.left_motor.getMaxVelocity()}")
                print(f"[{self.robot_id}] 🔬 Basic time step: {self.robot.getBasicTimeStep()}")
                print(f"[{self.robot_id}] 🔬 Robot model: {self.robot.getModel()}")
                
                # Force a physics step to see if motor commands take effect
                for i in range(3):
                    self.robot.step(self.timestep)
                    
                # Check if velocity was set
                print(f"[{self.robot_id}] 🔍 Current motor velocities - L: {self.left_motor.getVelocity():.3f}, R: {self.right_motor.getVelocity():.3f}")
                
            except Exception as e:
                print(f"[{self.robot_id}] ⚠️ Motor diagnostics failed: {e}")
                
        else:
            print(f"[{self.robot_id}] ❌ Motors not found! Left: {self.left_motor}, Right: {self.right_motor}")
        
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
            if sensor:
                sensor.enable(self.timestep)
                self.proximity_sensors.append(sensor)
            else:
                print(f"[{self.robot_id}] Warning: Proximity sensor ps{i} not available")
                # Add None placeholder to maintain indexing
                self.proximity_sensors.append(None)
    
    def update_position(self):
        """Update current position using motor odometry (E-puck method)"""
        # First try GPS if available
        if self.gps and self.gps.getValues():
            gps_values = self.gps.getValues()
            if len(gps_values) >= 3 and any(abs(v) > 0.001 for v in gps_values):
                self.position = list(gps_values)
                # Update estimated position to match GPS
                self.estimated_x = self.position[0] 
                self.estimated_y = self.position[1]
                return
        
        # Use motor-based odometry for E-puck
        if self.left_motor and self.right_motor:
            try:
                # Get current motor positions (in radians)
                left_pos = self.left_motor.getPositionSensor().getValue() if self.left_motor.getPositionSensor() else 0
                right_pos = self.right_motor.getPositionSensor().getValue() if self.right_motor.getPositionSensor() else 0
                
                # Calculate distance traveled by each wheel
                left_distance = (left_pos - self.previous_left_position) * self.wheel_radius
                right_distance = (right_pos - self.previous_right_position) * self.wheel_radius
                
                # Calculate robot movement
                distance = (left_distance + right_distance) / 2.0
                angle_change = (right_distance - left_distance) / self.wheel_distance
                
                # Update heading
                self.estimated_heading += angle_change
                
                # Update position
                self.estimated_x += distance * math.cos(self.estimated_heading)
                self.estimated_y += distance * math.sin(self.estimated_heading)
                
                # Update stored position
                self.position = [self.estimated_x, self.estimated_y, 0.05]
                
                # Store current positions for next calculation
                self.previous_left_position = left_pos
                self.previous_right_position = right_pos
                
            except:
                # Fallback to estimated position tracking
                pass
        
        # Initialize position if not set
        if not hasattr(self, 'position') or not self.position:
            initial_positions = {
                'ugv_alpha': [-0.5, -0.5, 0.05],
                'ugv_beta': [0.5, -0.5, 0.05], 
                'ugv_gamma': [0, -2, 0.05]
            }
            self.position = initial_positions.get(self.robot_id, [0, 0, 0.05])
            self.estimated_x = self.position[0]
            self.estimated_y = self.position[1]
    
    def calculate_bid(self, task: Dict) -> Dict:
        """Swarm-Enhanced bid calculation with multi-agent consensus"""
        
        if self.swarm_mode and hasattr(self, 'swarm_router') and self.swarm_router:
            # 🌐 Use Swarm Intelligence for collaborative bidding
            return self._swarm_calculate_bid(task)
        elif self.ai_enabled and self.ai_brain:
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
        print(f"   • 💳 Wallet: {self.wallet_address}")
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
    
    def _swarm_calculate_bid(self, task: Dict) -> Dict:
        """Swarm-based collaborative bidding using multi-agent consensus"""
        if not self.swarm_mode or not self.swarm_router:
            return self._rule_based_calculate_bid(task)
        
        try:
            # Prepare context for swarm agents
            task_context = f"""
            TASK ANALYSIS REQUEST:
            - Task ID: {task.get('taskId', 'unknown')}
            - Task Type: {task.get('type', 'scan')}
            - Task Location: {task.get('location', [0, 0])}
            - Task Priority: {task.get('priority', 1.0)}
            - Estimated Reward: {task.get('budget', 200)} SEI
            
            ROBOT STATUS:
            - Robot ID: {self.robot_id}
            - Current Position: {self.position}
            - Battery Level: {self.battery_level}%
            - Reputation Score: {self.reputation_score}
            - Capabilities: {self.capabilities}
            
            MARKET INTELLIGENCE:
            - Competition Level: Medium
            - Recent Win Rate: 30%
            - Average Winning Bid: 180 SEI
            
            Please provide specific recommendations for bidding strategy, navigation planning, 
            and collaboration opportunities. Be concise and actionable.
            """
            
            # Get swarm consensus using MixtureOfAgents
            swarm_response = self.swarm_router.run(task_context)
            
            # Parse swarm recommendations
            bid_recommendations = self._parse_swarm_response(swarm_response, task)
            
            # Calculate base metrics for validation
            task_location = task.get('location', [0, 0])
            distance = math.sqrt(
                (task_location[0] - self.position[0])**2 + 
                (task_location[1] - self.position[1])**2
            )
            
            base_time = distance / self.capabilities['navigation_speed']
            task_execution_time = self._estimate_task_time(task.get('type', 'scan'))
            total_time = base_time + task_execution_time
            
            energy_cost = self._calculate_energy_cost(distance, task.get('type', 'scan'))
            capability_match = self._calculate_capability_match(task)
            
            # Apply swarm intelligence modifications - DEMO PRICING (60% reduction)
            swarm_bid_amount = bid_recommendations.get('recommended_bid', 0.03)  # Reduced from 0.08 to 0.03 (62% reduction)
            swarm_confidence = bid_recommendations.get('confidence', 0.7)
            collaboration_factor = bid_recommendations.get('collaboration_bonus', 1.0)
            
            # Adjust bid based on swarm consensus (keep as float for precision)
            final_bid = round(swarm_bid_amount * collaboration_factor, 4)  # 4 decimal places
            
            print(f"[{self.robot_id}] 🌐 SWARM BID: {final_bid} SEI")
            print(f"   • 💳 Wallet: {self.wallet_address}")
            print(f"   • Swarm Consensus: {swarm_confidence:.2%} confidence")
            print(f"   • Collaboration Factor: {collaboration_factor:.2f}x")
            print(f"   • Strategy: {bid_recommendations.get('strategy', 'competitive')}")
            
            return {
                'robotId': self.robot_id,
                'taskId': task['taskId'],
                'bidAmount': final_bid,
                'estimatedTime': int(total_time),
                'capabilityMatch': capability_match,
                'energyCost': energy_cost,
                'reputation': self.reputation_score,
                'batteryLevel': self.battery_level,
                'swarm_metadata': {
                    'decision_method': 'swarm_consensus',
                    'confidence': swarm_confidence,
                    'collaboration_factor': collaboration_factor,
                    'strategy': bid_recommendations.get('strategy', 'competitive'),
                    'swarm_agents_used': list(self.swarm_agents.keys()),
                    'consensus_strength': bid_recommendations.get('consensus_strength', 0.8)
                }
            }
            
        except Exception as e:
            print(f"[{self.robot_id}] ⚠️  Swarm bidding error: {e}, falling back to rule-based")
            return self._rule_based_calculate_bid(task)
    
    def _parse_swarm_response(self, swarm_response: str, task: Dict) -> Dict:
        """Parse and extract actionable recommendations from swarm response"""
        # Default recommendations
        recommendations = {
            'recommended_bid': 150,
            'confidence': 0.7,
            'collaboration_bonus': 1.0,
            'strategy': 'competitive',
            'consensus_strength': 0.8
        }
        
        try:
            # Simple keyword-based parsing (in production, use more sophisticated NLP)
            response_lower = swarm_response.lower()
            
            # Extract bid amount recommendations
            import re
            bid_matches = re.findall(r'bid[:\\s]*(\d+)', response_lower)
            if bid_matches:
                recommendations['recommended_bid'] = int(bid_matches[-1])
            
            # Determine strategy based on keywords
            if 'aggressive' in response_lower or 'competitive' in response_lower:
                recommendations['strategy'] = 'aggressive'
                recommendations['collaboration_bonus'] = 0.9  # Slightly lower for competitive bidding
            elif 'collaborative' in response_lower or 'cooperate' in response_lower:
                recommendations['strategy'] = 'collaborative'
                recommendations['collaboration_bonus'] = 1.1  # Bonus for collaboration
            elif 'conservative' in response_lower:
                recommendations['strategy'] = 'conservative'
                recommendations['collaboration_bonus'] = 1.0
                
            # Extract confidence indicators
            if 'high confidence' in response_lower or 'very confident' in response_lower:
                recommendations['confidence'] = 0.9
            elif 'low confidence' in response_lower or 'uncertain' in response_lower:
                recommendations['confidence'] = 0.5
            
        except Exception as e:
            print(f"[{self.robot_id}] Warning: Failed to parse swarm response: {e}")
        
        return recommendations
    
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
        
        # Base bid calculation - DEMO PRICING (60% reduction)
        base_cost = 0.02  # Reduced from 0.05 to 0.02 SEI (60% reduction)
        distance_factor = 1 + (distance * 0.0005)  # Reduced from 0.001 to 0.0005 (50% reduction)
        time_factor = 1 + (total_time * 0.00005)  # Reduced from 0.0001 to 0.00005 (50% reduction)  
        energy_factor = 1 + (energy_cost * 0.00005)  # Reduced from 0.0001 to 0.00005 (50% reduction)
        
        # Apply capability bonus/penalty
        capability_factor = 0.8 + (capability_match * 0.2)  # More stable range
        
        # Reputation modifier (better reputation = more competitive bids)
        reputation_factor = 1.5 - (self.reputation_score * 0.5)  # Reduced impact
        
        # Final bid amount (keep as float for precision under 0.1 SEI)
        bid_amount = round(base_cost * distance_factor * time_factor * 
                          energy_factor * capability_factor * reputation_factor, 4)
        
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
            'average_winning_bid': 0.03, # Average winning bid amount (demo pricing - 62% reduction)
            'market_volatility': 0.4,  # How much bid prices fluctuate
            'competitors': {
                # Simulated competitor data for AI analysis
                'ugv_alpha': {'recent_bids': [0.025, 0.035, 0.03], 'wins': 2, 'total_auctions': 5},
                'ugv_beta': {'recent_bids': [0.04, 0.045, 0.042], 'wins': 3, 'total_auctions': 6},  
                'ugv_gamma': {'recent_bids': [0.02, 0.03, 0.025], 'wins': 1, 'total_auctions': 4}
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
            print(f"[{self.robot_id}] 📋 Assigned task {assignment_data['taskId']}")
            print(f"[{self.robot_id}] 🗺️ Received {len(self.waypoints)} waypoints:")
            for i, wp in enumerate(self.waypoints):
                print(f"[{self.robot_id}]   Waypoint {i+1}: ({wp[0]:.2f}, {wp[1]:.2f})")
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
        
        # Debug output for navigation
        if hasattr(self, '_nav_debug_counter'):
            self._nav_debug_counter += 1
        else:
            self._nav_debug_counter = 0
        
        if self._nav_debug_counter % 50 == 0:  # Debug every 50 steps
            print(f"[{self.robot_id}] NAV DEBUG: Target=({target_x:.2f}, {target_y:.2f}), Current=({self.position[0]:.2f}, {self.position[1]:.2f}), Distance={distance:.2f}")
        
        # Check if reached waypoint
        if distance < 0.5:
            print(f"[{self.robot_id}] 🎯 Reached waypoint: ({target_x:.2f}, {target_y:.2f})")
            return True
        
        # FORCE SIMPLE NAVIGATION - compass navigation has issues
        if True:  # Always use simple navigation
            print(f"[{self.robot_id}] 🔧 FORCE Simple navigation mode")
            # Simple navigation without compass - FIXED SPEEDS
            if abs(dx) > 0.1 or abs(dy) > 0.1:
                # Move towards target with effective speeds (physics test showed 6.0 works)
                left_speed = 6.0  # Start at max effective speed
                right_speed = 6.0
                
                # Simple turning based on position difference
                if abs(dx) > abs(dy):  # Turn based on X difference
                    if dx > 0:  # Move right
                        left_speed = 6.0
                        right_speed = 2.0
                        print(f"[{self.robot_id}] 🔄 Turning RIGHT: target X={dx:.2f}")
                    else:  # Move left
                        left_speed = 2.0
                        right_speed = 6.0
                        print(f"[{self.robot_id}] 🔄 Turning LEFT: target X={dx:.2f}")
                else:  # Move forward/backward primarily
                    if dy > 0:  # Move forward
                        left_speed = 6.0
                        right_speed = 6.0
                        print(f"[{self.robot_id}] ⬆️ Moving FORWARD: target Y={dy:.2f}")
                    else:  # Move backward (reverse)
                        left_speed = -6.0
                        right_speed = -6.0
                        print(f"[{self.robot_id}] ⬇️ Moving BACKWARD: target Y={dy:.2f}")
                
                # FORCE SET MOTOR VELOCITIES
                self.left_motor.setVelocity(left_speed)
                self.right_motor.setVelocity(right_speed)
                
                # **CRITICAL FIX**: Update position immediately after setting motors
                self.update_position()
                
                if self._nav_debug_counter % 20 == 0:  # More frequent debug
                    print(f"[{self.robot_id}] 🚀 MOTORS SET: L={left_speed:.1f}, R={right_speed:.1f}")
                    print(f"[{self.robot_id}] 📍 Target: ({target_x:.2f}, {target_y:.2f}), Current: ({self.position[0]:.6f}, {self.position[1]:.6f})")
                    
                # Show position change every few steps
                if self._nav_debug_counter % 10 == 0:
                    print(f"[{self.robot_id}] 📍 REAL POSITION: ({self.position[0]:.10f}, {self.position[1]:.10f})")
            return False
            
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
        
        # Obstacle avoidance (temporarily disabled for testing)
        obstacle_detected, avoidance_angle = self._detect_obstacles()
        
        # TEMPORARY: Disable obstacle avoidance to test basic movement
        if False and obstacle_detected:  # Disabled
            # Adjust heading for obstacle avoidance
            target_heading += avoidance_angle
            if self._nav_debug_counter % 50 == 0:
                print(f"[{self.robot_id}] Obstacle detected, adjusting by {avoidance_angle:.2f}")
        
        # Simple proportional control - FIXED BASE SPEED
        max_speed = 6.28  # E-puck max wheel speed
        base_speed = 5.0  # Increased from 3.0 based on physics test results
        turn_speed = heading_error * 1.5  # Reduced turn sensitivity
        
        left_speed = base_speed - turn_speed
        right_speed = base_speed + turn_speed
        
        # Limit speeds
        left_speed = max(-max_speed, min(max_speed, left_speed))
        right_speed = max(-max_speed, min(max_speed, right_speed))
        
        # Set motor velocities
        if self.left_motor and self.right_motor:
            self.left_motor.setVelocity(left_speed)
            self.right_motor.setVelocity(right_speed)
            
            # Debug motor commands occasionally
            if self._nav_debug_counter % 100 == 0:
                print(f"[{self.robot_id}] 🔧 Motor velocities set: L={left_speed:.2f}, R={right_speed:.2f}")
        else:
            if self._nav_debug_counter % 100 == 0:
                print(f"[{self.robot_id}] ❌ Cannot set motor velocities - motors not available")
        
        # Debug navigation
        if self._nav_debug_counter % 50 == 0:
            print(f"[{self.robot_id}] MOTORS: L={left_speed:.2f}, R={right_speed:.2f}, HeadingErr={heading_error:.2f}")
        
        return False
    
    def _detect_obstacles(self) -> Tuple[bool, float]:
        """Detect obstacles using proximity sensors"""
        # Safely get sensor values, handling None sensors
        sensor_values = []
        for sensor in self.proximity_sensors:
            if sensor:
                sensor_values.append(sensor.getValue())
            else:
                sensor_values.append(0)  # Default to no obstacle
        
        # Threshold for obstacle detection (E-puck sensors range 0-4095)
        # High threshold to prevent false detections in open space
        obstacle_threshold = 2000
        
        # Check front sensors (0, 1, 6, 7) if they exist
        front_indices = [0, 1, 6, 7]
        front_sensors = []
        
        for i in front_indices:
            if i < len(sensor_values):
                front_sensors.append(sensor_values[i])
            else:
                front_sensors.append(0)
        
        if any(value > obstacle_threshold for value in front_sensors):
            # Simple avoidance: turn away from strongest signal
            max_value = max(front_sensors)
            max_index = front_sensors.index(max_value)
            
            # Debug output for actual obstacles
            if hasattr(self, '_obstacle_debug_counter'):
                self._obstacle_debug_counter += 1
            else:
                self._obstacle_debug_counter = 0
            
            if self._obstacle_debug_counter % 20 == 0:  # Debug every 20 detections
                print(f"[{self.robot_id}] Real obstacle detected! Max sensor: {max_value:.1f} (threshold: {obstacle_threshold})")
                print(f"[{self.robot_id}] All front sensors: {[f'{v:.1f}' for v in front_sensors]}")
            
            # Avoidance angles (reduced for smoother movement)
            avoidance_angles = [0.2, 0.15, -0.15, -0.2]
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
        debug_counter = 0
        
        # Startup sequence - let physics settle
        print(f"[{self.robot_id}] 🚀 Starting physics initialization sequence...")
        for i in range(3):
            self.robot.step(self.timestep)
            print(f"[{self.robot_id}] 🚀 Physics step {i+1}/3")
        
        while self.robot.step(self.timestep) != -1:
            # Update sensor readings
            self.update_position()
            
            # Process incoming messages
            self.receive_messages()
            
            # Process swarm communications
            if self.swarm_mode:
                self.process_swarm_communications()
            
            # Update battery level (simulation)
            self.battery_level = max(0, self.battery_level - 0.001)
            
            # Debug output every 100 steps (about 10 seconds at 64ms timestep)
            debug_counter += 1
            if debug_counter % 100 == 0:
                print(f"[{self.robot_id}] Status: Pos={self.position}, Task={bool(self.current_task)}, Waypoints={len(self.waypoints) if self.waypoints else 0}")
            
            # Execute current task
            if self.current_task and self.waypoints:
                if current_waypoint_index < len(self.waypoints):
                    waypoint = self.waypoints[current_waypoint_index]
                    
                    # Debug waypoint info every 100 steps
                    if debug_counter % 100 == 0:
                        print(f"[{self.robot_id}] TASK DEBUG: Navigating to waypoint {current_waypoint_index + 1}/{len(self.waypoints)}: ({waypoint[0]:.2f}, {waypoint[1]:.2f})")
                    
                    if self.navigate_to_waypoint(waypoint):
                        print(f"[{self.robot_id}] ✅ Reached waypoint {current_waypoint_index + 1}/{len(self.waypoints)}")
                        
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
        """Enhanced learning from auction outcomes with swarm intelligence"""
        # Traditional AI learning
        if self.ai_enabled and self.ai_brain:
            market_info = self._gather_market_intelligence()
            if winner_info:
                market_info['winning_bid'] = winner_info.get('bidAmount', 0)
                market_info['winner_id'] = winner_info.get('robotId', 'unknown')
            
            self.ai_brain.learn_from_auction_result(
                task=task, 
                bid_amount=bid_info['bidAmount'], 
                won=won, 
                market_info=market_info
            )
        
        # Swarm-based collaborative learning
        if self.swarm_mode:
            self._swarm_learn_from_auction(task, bid_info, won, winner_info)
        
        # Update reputation
        if won:
            self.reputation_score = min(1.0, self.reputation_score + 0.01)
        else:
            self.reputation_score = max(0.1, self.reputation_score - 0.005)
    
    def _swarm_learn_from_auction(self, task: Dict, bid_info: Dict, won: bool, winner_info: Dict = None):
        """Swarm-based collaborative learning from auction outcomes"""
        try:
            # Ensure collaboration_history exists
            if not hasattr(self, 'collaboration_history'):
                self.collaboration_history = []
            
            # Record auction outcome for swarm learning
            auction_record = {
                'task': task,
                'our_bid': bid_info,
                'won': won,
                'winner': winner_info,
                'timestamp': time.time(),
                'market_conditions': self._gather_market_intelligence()
            }
            
            self.collaboration_history.append(auction_record)
            
            # Keep only recent history (last 50 auctions)
            if len(self.collaboration_history) > 50:
                self.collaboration_history = self.collaboration_history[-50:]
            
            # Share learning with swarm if we have peer agents
            if self.peer_agents:
                self._share_auction_intelligence(auction_record)
            
            print(f"[{self.robot_id}] 🌐 Swarm Learning: {'WIN' if won else 'LOSS'} recorded for collective intelligence")
            
        except Exception as e:
            print(f"[{self.robot_id}] Warning: Swarm learning error: {e}")
    
    def _share_auction_intelligence(self, auction_record: Dict):
        """Share auction intelligence with peer robots"""
        intelligence_message = {
            'type': 'swarm_intelligence',
            'data': {
                'robot_id': self.robot_id,
                'auction_outcome': auction_record,
                'market_insights': self._extract_market_insights(),
                'collaboration_score': self.reputation_score
            },
            'timestamp': time.time(),
            'sender': self.robot_id
        }
        
        # Add to communication queue (in production, would send via network)
        self.swarm_communication_queue.append(intelligence_message)
        
        # Simulate broadcasting to peer robots
        if hasattr(self, 'emitter') and self.emitter:
            self.emitter.send(json.dumps(intelligence_message))
    
    def _extract_market_insights(self) -> Dict:
        """Extract actionable market insights from collaboration history"""
        if not self.collaboration_history:
            return {'insights': 'insufficient_data'}
        
        recent_auctions = self.collaboration_history[-10:]  # Last 10 auctions
        
        # Analyze winning patterns
        wins = [record for record in recent_auctions if record['won']]
        losses = [record for record in recent_auctions if not record['won']]
        
        insights = {
            'recent_win_rate': len(wins) / len(recent_auctions) if recent_auctions else 0,
            'average_winning_bid': sum([w['our_bid']['bidAmount'] for w in wins]) / len(wins) if wins else 0,
            'competitive_pressure': len(losses) / len(recent_auctions) if recent_auctions else 0.5,
            'optimal_bid_range': self._calculate_optimal_bid_range(recent_auctions),
            'collaboration_opportunities': self._identify_collaboration_opportunities()
        }
        
        return insights
    
    def _calculate_optimal_bid_range(self, auction_history: List[Dict]) -> Dict:
        """Calculate optimal bidding range based on auction history"""
        if not auction_history:
            return {'min': 100, 'max': 200, 'optimal': 150}
        
        winning_bids = [record['our_bid']['bidAmount'] for record in auction_history if record['won']]
        losing_bids = [record['our_bid']['bidAmount'] for record in auction_history if not record['won']]
        
        if winning_bids:
            optimal_bid = sum(winning_bids) / len(winning_bids)
            min_winning = min(winning_bids)
            max_winning = max(winning_bids)
        else:
            optimal_bid = 150
            min_winning = 100
            max_winning = 200
        
        return {
            'min': max(50, int(min_winning * 0.9)),
            'max': min(300, int(max_winning * 1.1)),
            'optimal': int(optimal_bid)
        }
    
    def _identify_collaboration_opportunities(self) -> List[str]:
        """Identify opportunities for robot-to-robot collaboration"""
        opportunities = []
        
        # Analyze recent performance patterns
        if hasattr(self, 'collaboration_history') and len(self.collaboration_history) > 5:
            recent_performance = self.collaboration_history[-5:]
            win_rate = sum([1 for r in recent_performance if r['won']]) / len(recent_performance)
            
            if win_rate < 0.3:
                opportunities.extend(['seek_mentorship', 'form_bidding_coalition'])
            elif win_rate > 0.7:
                opportunities.extend(['mentor_other_robots', 'lead_task_coordination'])
            else:
                opportunities.append('peer_collaboration')
        
        # Check for complementary capabilities
        if self.capabilities['navigation_speed'] > 1.0:
            opportunities.append('navigation_leadership')
        if self.capabilities['sensor_quality'] > 0.8:
            opportunities.append('reconnaissance_specialist')
        
        return opportunities
    
    def initiate_swarm_collaboration(self, collaboration_type: str, target_robots: List[str] = None):
        """Initiate collaboration with other robots in the swarm"""
        if not self.swarm_mode:
            print(f"[{self.robot_id}] Swarm mode not enabled, cannot initiate collaboration")
            return
        
        collaboration_request = {
            'type': 'collaboration_request',
            'data': {
                'collaboration_type': collaboration_type,
                'initiator': self.robot_id,
                'target_robots': target_robots or [],
                'capabilities_offered': self.capabilities,
                'reputation_score': self.reputation_score,
                'proposed_benefits': self._calculate_collaboration_benefits(collaboration_type)
            },
            'timestamp': time.time(),
            'sender': self.robot_id
        }
        
        # Broadcast collaboration request
        if hasattr(self, 'emitter') and self.emitter:
            self.emitter.send(json.dumps(collaboration_request))
        
        print(f"[{self.robot_id}] 🤝 Initiated {collaboration_type} collaboration request")
    
    def _calculate_collaboration_benefits(self, collaboration_type: str) -> Dict:
        """Calculate potential benefits of proposed collaboration"""
        benefits = {
            'efficiency_gain': 0.1,  # 10% efficiency improvement
            'cost_reduction': 0.05,  # 5% cost reduction
            'success_rate_improvement': 0.15  # 15% better success rate
        }
        
        # Customize benefits based on collaboration type
        if collaboration_type == 'bidding_coalition':
            benefits.update({
                'market_power_increase': 0.2,
                'information_sharing': 0.25,
                'risk_reduction': 0.15
            })
        elif collaboration_type == 'task_coordination':
            benefits.update({
                'parallel_execution': 0.3,
                'resource_optimization': 0.2,
                'quality_improvement': 0.1
            })
        elif collaboration_type == 'knowledge_sharing':
            benefits.update({
                'learning_acceleration': 0.4,
                'strategy_diversification': 0.3,
                'collective_intelligence': 0.35
            })
        
        return benefits
    
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
        
        # Gather sensor data - safely handle None sensors
        proximity_values = []
        for sensor in self.proximity_sensors:
            if sensor:
                proximity_values.append(sensor.getValue())
            else:
                proximity_values.append(0)  # Default value for missing sensors
        
        sensor_data = {
            'proximity_sensors': proximity_values,
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
    
    def process_swarm_communications(self):
        """Process incoming swarm intelligence communications"""
        if not self.swarm_mode:
            return
        
        # Ensure communication queue exists
        if not hasattr(self, 'swarm_communication_queue'):
            self.swarm_communication_queue = []
        
        # Process messages from communication queue
        while self.swarm_communication_queue:
            message = self.swarm_communication_queue.pop(0)
            self._handle_swarm_message(message)
    
    def _handle_swarm_message(self, message: Dict):
        """Handle incoming swarm intelligence messages"""
        message_type = message.get('type')
        sender = message.get('sender')
        
        if sender == self.robot_id:  # Don't process our own messages
            return
        
        try:
            if message_type == 'swarm_intelligence':
                self._process_swarm_intelligence(message['data'], sender)
            elif message_type == 'collaboration_request':
                self._process_collaboration_request(message['data'], sender)
                
        except Exception as e:
            print(f"[{self.robot_id}] Error handling swarm message from {sender}: {e}")
    
    def _process_swarm_intelligence(self, data: Dict, sender: str):
        """Process shared intelligence from peer robots"""
        auction_outcome = data.get('auction_outcome', {})
        
        # Learn from peer's experience
        if auction_outcome and self.swarm_mode:
            peer_bid_amount = auction_outcome.get('our_bid', {}).get('bidAmount', 0)
            peer_won = auction_outcome.get('won', False)
            
            # Update competitive intelligence
            if not hasattr(self, 'competitive_intelligence'):
                self.competitive_intelligence = {}
            
            if sender not in self.competitive_intelligence:
                self.competitive_intelligence[sender] = {
                    'recent_bids': [],
                    'win_rate': 0.5
                }
            
            self.competitive_intelligence[sender]['recent_bids'].append({
                'bid': peer_bid_amount,
                'won': peer_won,
                'timestamp': time.time()
            })
            
            # Keep only recent data
            if len(self.competitive_intelligence[sender]['recent_bids']) > 10:
                self.competitive_intelligence[sender]['recent_bids'] = \
                    self.competitive_intelligence[sender]['recent_bids'][-10:]
        
        print(f"[{self.robot_id}] 🌐 Processed swarm intelligence from {sender}")
    
    def get_swarm_status_report(self) -> Dict:
        """Get comprehensive swarm system status"""
        if not self.swarm_mode:
            return {'swarm_enabled': False}
        
        return {
            'swarm_enabled': True,
            'swarm_agents_count': len(self.swarm_agents),
            'collaboration_history_size': len(getattr(self, 'collaboration_history', [])),
            'competitive_intelligence_size': len(getattr(self, 'competitive_intelligence', {})),
            'communication_queue_size': len(self.swarm_communication_queue),
            'swarm_router_active': self.swarm_router is not None,
            'market_insights': self._extract_market_insights() if hasattr(self, 'collaboration_history') else {}
        }

if __name__ == "__main__":
    agent = UGVAgent()
    agent.run()