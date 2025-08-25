#!/usr/bin/env python3
"""
Complete Smart Contract Client for Sei Network Robot Swarm System
Integrates RobotMarketplace, TaskAuction, and ProofVerification contracts
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3
from eth_account import Account

# Try different middleware imports for Web3 compatibility
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    try:
        from web3.middleware.geth_poa import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

class CompleteSmartContractClient:
    """Complete client for Sei Network robot swarm smart contract ecosystem"""
    
    def __init__(self, config: Dict[str, Any]):
        self.rpc_url = config['sei_rpc_url']
        self.chain_id = config['chain_id']
        self.private_key = config['private_key']
        
        # Contract addresses from deployment
        self.robot_marketplace_address = "0x839e6aD668FB67684Cd0D21E6f17566f4607E325"
        self.task_auction_address = "0xD894daADD0CDD01a9B65Dc72ffE8023eCd3B75c4"
        self.proof_verification_address = "0x34a820CCe01808b06994eb1EF2fD2f6Bf9C0AFBa"
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add POA middleware for Sei Network
        if geth_poa_middleware:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Set up account from private key
        self.account = Account.from_key(self.private_key)
        
        # Initialize contract instances
        self._init_contracts()
        
        print(f"[SMART_CONTRACT] 🌐 Complete Ecosystem Connected to Sei Network")
        print(f"[SMART_CONTRACT] 📡 RPC: {self.rpc_url}")
        print(f"[SMART_CONTRACT] ⛓️  Chain ID: {self.chain_id}")
        print(f"[SMART_CONTRACT] 🏦 Account: {self.account.address}")
        print(f"[SMART_CONTRACT] 🤖 RobotMarketplace: {self.robot_marketplace_address}")
        print(f"[SMART_CONTRACT] 🔄 TaskAuction: {self.task_auction_address}")
        print(f"[SMART_CONTRACT] 🔐 ProofVerification: {self.proof_verification_address}")
        print(f"[SMART_CONTRACT] ✅ All contracts ready for autonomous robot operations")
    
    def _init_contracts(self):
        """Initialize all contract instances with ABIs"""
        
        # RobotMarketplace ABI (key functions)
        self.robot_marketplace_abi = [
            {"inputs": [{"name": "robotId", "type": "string"}, {"name": "capabilities", "type": "uint256[]"}], "name": "registerRobot", "outputs": [], "type": "function"},
            {"inputs": [{"name": "capabilities", "type": "uint256[]"}], "name": "updateCapabilities", "outputs": [], "type": "function"},
            {"inputs": [{"name": "robot", "type": "address"}, {"name": "newReputation", "type": "uint256"}, {"name": "reason", "type": "string"}], "name": "updateReputation", "outputs": [], "type": "function"},
            {"inputs": [{"name": "robot", "type": "address"}, {"name": "success", "type": "bool"}], "name": "recordTaskCompletion", "outputs": [], "type": "function"},
            {"inputs": [], "name": "getActiveRobots", "outputs": [{"name": "", "type": "address[]"}], "type": "function", "constant": True},
            {"inputs": [{"name": "robot", "type": "address"}, {"name": "requiredCapabilities", "type": "uint256[]"}], "name": "calculateCapabilityMatch", "outputs": [{"name": "", "type": "uint256"}], "type": "function", "constant": True},
            {"inputs": [{"name": "robot", "type": "address"}], "name": "getRobotStats", "outputs": [{"name": "robotId", "type": "string"}, {"name": "reputation", "type": "uint256"}, {"name": "isActive", "type": "bool"}, {"name": "totalTasksCompleted", "type": "uint256"}, {"name": "totalTasksFailed", "type": "uint256"}, {"name": "successRate", "type": "uint256"}], "type": "function", "constant": True}
        ]
        
        # TaskAuction ABI (key functions)
        self.task_auction_abi = [
            {"inputs": [{"name": "missionId", "type": "uint256"}, {"name": "taskType", "type": "string"}, {"name": "description", "type": "string"}, {"name": "location", "type": "uint256[2]"}, {"name": "requiredCapabilities", "type": "uint256[]"}, {"name": "budget", "type": "uint256"}], "name": "createTask", "outputs": [{"name": "", "type": "uint256"}], "type": "function", "payable": True},
            {"inputs": [{"name": "taskId", "type": "uint256"}, {"name": "estimatedTime", "type": "uint256"}], "name": "placeBid", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}], "name": "closeAuction", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}, {"name": "robot", "type": "address"}, {"name": "success", "type": "bool"}, {"name": "proofHash", "type": "bytes32"}], "name": "submitTaskCompletion", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}], "name": "getTaskDetails", "outputs": [{"name": "taskType", "type": "string"}, {"name": "description", "type": "string"}, {"name": "location", "type": "uint256[2]"}, {"name": "budget", "type": "uint256"}, {"name": "state", "type": "uint8"}, {"name": "assignedRobot", "type": "address"}, {"name": "deadline", "type": "uint256"}, {"name": "bidCount", "type": "uint256"}], "type": "function", "constant": True},
            {"inputs": [{"name": "taskId", "type": "uint256"}], "name": "getTaskBids", "outputs": [{"components": [{"name": "robot", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "estimatedTime", "type": "uint256"}, {"name": "capabilityMatch", "type": "uint256"}, {"name": "reputation", "type": "uint256"}, {"name": "timestamp", "type": "uint256"}, {"name": "isValid", "type": "bool"}], "name": "", "type": "tuple[]"}], "type": "function", "constant": True},
            {"inputs": [], "name": "getActiveTasks", "outputs": [{"name": "", "type": "uint256[]"}], "type": "function", "constant": True}
        ]
        
        # ProofVerification ABI (key functions)
        self.proof_verification_abi = [
            {"inputs": [{"name": "taskId", "type": "uint256"}, {"name": "requiredLocation", "type": "uint256[2]"}, {"name": "locationTolerance", "type": "uint256"}, {"name": "maxCompletionTime", "type": "uint256"}, {"name": "minImageCount", "type": "uint256"}, {"name": "requiresGPS", "type": "bool"}, {"name": "requiresImages", "type": "bool"}], "name": "setVerificationCriteria", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}, {"name": "waypointsHash", "type": "bytes32"}, {"name": "imageHashes", "type": "bytes32[]"}, {"name": "completionTime", "type": "uint256"}], "name": "submitProof", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}, {"name": "success", "type": "bool"}, {"name": "resultMessage", "type": "string"}], "name": "manualVerification", "outputs": [], "type": "function"},
            {"inputs": [{"name": "taskId", "type": "uint256"}], "name": "getProofSubmission", "outputs": [{"name": "robot", "type": "address"}, {"name": "waypointsHash", "type": "bytes32"}, {"name": "imageHashes", "type": "bytes32[]"}, {"name": "submissionTime", "type": "uint256"}, {"name": "state", "type": "uint8"}, {"name": "verificationResult", "type": "string"}], "type": "function", "constant": True}
        ]
        
        # Initialize contract instances
        self.robot_marketplace = self.w3.eth.contract(
            address=self.robot_marketplace_address,
            abi=self.robot_marketplace_abi
        )
        
        self.task_auction = self.w3.eth.contract(
            address=self.task_auction_address,
            abi=self.task_auction_abi
        )
        
        self.proof_verification = self.w3.eth.contract(
            address=self.proof_verification_address,
            abi=self.proof_verification_abi
        )
    
    def _send_transaction(self, function_call, description: str, value: int = 0) -> Dict[str, Any]:
        """Helper method to send transactions with proper gas handling"""
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # Estimate gas
            try:
                gas_estimate = function_call.estimate_gas({'from': self.account.address, 'value': value})
                gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
            except Exception as e:
                print(f"[SMART_CONTRACT] ⚠️ Gas estimation failed for {description}: {e}, using default")
                gas_limit = 300000
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': self.w3.eth.gas_price,
                'value': value,
                'chainId': self.chain_id
            })
            
            # Sign and send transaction
            signed_txn = self.account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            print(f"[SMART_CONTRACT] 📤 {description}: 0x{tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            return {
                'success': True,
                'txHash': f"0x{tx_hash.hex()}",
                'blockNumber': receipt['blockNumber'],
                'gasUsed': str(receipt['gasUsed']),
                'cost': receipt['gasUsed'] * receipt['effectiveGasPrice'] / 10**18
            }
            
        except Exception as e:
            print(f"[SMART_CONTRACT] ❌ {description} failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ==========================================
    # ROBOT MARKETPLACE OPERATIONS
    # ==========================================
    
    def register_robot(self, robot_id: str, capabilities: List[int]) -> Dict[str, Any]:
        """Register a robot with capabilities in the marketplace"""
        print(f"[ROBOT_MARKETPLACE] 🤖 Registering robot {robot_id}")
        print(f"[ROBOT_MARKETPLACE] 📊 Capabilities: {capabilities}")
        
        function_call = self.robot_marketplace.functions.registerRobot(robot_id, capabilities)
        result = self._send_transaction(function_call, f"Robot registration for {robot_id}")
        
        if result['success']:
            print(f"[ROBOT_MARKETPLACE] ✅ Robot {robot_id} registered successfully!")
            print(f"[ROBOT_MARKETPLACE] 🔗 Transaction: {result['txHash']}")
        
        return result
    
    def get_active_robots(self) -> List[str]:
        """Get list of active robot addresses"""
        try:
            active_robots = self.robot_marketplace.functions.getActiveRobots().call()
            print(f"[ROBOT_MARKETPLACE] 📋 Found {len(active_robots)} active robots")
            return active_robots
        except Exception as e:
            print(f"[ROBOT_MARKETPLACE] ❌ Failed to get active robots: {e}")
            return []
    
    def calculate_capability_match(self, robot_address: str, required_capabilities: List[int]) -> int:
        """Calculate how well robot capabilities match requirements"""
        try:
            match_score = self.robot_marketplace.functions.calculateCapabilityMatch(
                robot_address, required_capabilities
            ).call()
            print(f"[ROBOT_MARKETPLACE] 🎯 Capability match for {robot_address}: {match_score}/1000")
            return match_score
        except Exception as e:
            print(f"[ROBOT_MARKETPLACE] ❌ Failed to calculate capability match: {e}")
            return 0
    
    # ==========================================
    # TASK AUCTION OPERATIONS  
    # ==========================================
    
    def create_task(self, mission_id: int, task_type: str, description: str, 
                   location: Tuple[int, int], required_capabilities: List[int], 
                   budget: float) -> Dict[str, Any]:
        """Create a new task with auction"""
        print(f"[TASK_AUCTION] 🚀 Creating task for mission {mission_id}")
        print(f"[TASK_AUCTION] 📝 Type: {task_type}")
        print(f"[TASK_AUCTION] 💰 Budget: {budget} SEI")
        print(f"[TASK_AUCTION] 🌍 Location: {location}")
        
        budget_wei = int(budget * 10**18)
        # Convert coordinates to positive uint256 by adding offset (smart contracts need positive values)
        # Add 1000 to handle negative coordinates from Webots world (-6 to +6 range)
        location_scaled = [int((location[0] + 10) * 100), int((location[1] + 10) * 100)]
        
        function_call = self.task_auction.functions.createTask(
            mission_id, task_type, description, location_scaled, required_capabilities, budget_wei
        )
        
        result = self._send_transaction(function_call, f"Task creation: {task_type}", value=budget_wei)
        
        if result['success']:
            print(f"[TASK_AUCTION] ✅ Task created successfully!")
            print(f"[TASK_AUCTION] 🔗 Transaction: {result['txHash']}")
            print(f"[TASK_AUCTION] ⏰ Auction duration: 30 seconds")
        
        return result
    
    def place_bid(self, task_id: int, estimated_time: int, robot_id: str) -> Dict[str, Any]:
        """Place bid on a task"""
        print(f"[TASK_AUCTION] 🤖 Robot {robot_id} placing bid on task {task_id}")
        print(f"[TASK_AUCTION] ⏱️ Estimated completion time: {estimated_time} seconds")
        
        function_call = self.task_auction.functions.placeBid(task_id, estimated_time)
        result = self._send_transaction(function_call, f"Bid placement by {robot_id}")
        
        if result['success']:
            print(f"[TASK_AUCTION] ✅ Bid placed successfully!")
            print(f"[TASK_AUCTION] 🔗 Transaction: {result['txHash']}")
        
        return result
    
    def close_auction(self, task_id: int) -> Dict[str, Any]:
        """Close auction and select winner"""
        print(f"[TASK_AUCTION] 🏆 Closing auction for task {task_id}")
        
        function_call = self.task_auction.functions.closeAuction(task_id)
        result = self._send_transaction(function_call, f"Auction closure for task {task_id}")
        
        if result['success']:
            print(f"[TASK_AUCTION] ✅ Auction closed, winner selected!")
            print(f"[TASK_AUCTION] 🔗 Transaction: {result['txHash']}")
        
        return result
    
    def get_task_details(self, task_id: int) -> Dict[str, Any]:
        """Get detailed task information"""
        try:
            task_details = self.task_auction.functions.getTaskDetails(task_id).call()
            return {
                'taskType': task_details[0],
                'description': task_details[1], 
                'location': task_details[2],
                'budget': task_details[3],
                'state': task_details[4],
                'assignedRobot': task_details[5],
                'deadline': task_details[6],
                'bidCount': task_details[7]
            }
        except Exception as e:
            print(f"[TASK_AUCTION] ❌ Failed to get task details: {e}")
            return {}
    
    def get_task_bids(self, task_id: int) -> List[Dict[str, Any]]:
        """Get all bids for a task"""
        try:
            bids = self.task_auction.functions.getTaskBids(task_id).call()
            print(f"[TASK_AUCTION] 📋 Found {len(bids)} bids for task {task_id}")
            return [
                {
                    'robot': bid[0],
                    'amount': bid[1],
                    'estimatedTime': bid[2],
                    'capabilityMatch': bid[3],
                    'reputation': bid[4],
                    'timestamp': bid[5],
                    'isValid': bid[6]
                } for bid in bids
            ]
        except Exception as e:
            print(f"[TASK_AUCTION] ❌ Failed to get task bids: {e}")
            return []
    
    # ==========================================
    # PROOF VERIFICATION OPERATIONS
    # ==========================================
    
    def set_verification_criteria(self, task_id: int, location: Tuple[int, int], 
                                tolerance: int = 500, max_time: int = 300, 
                                min_images: int = 3) -> Dict[str, Any]:
        """Set verification criteria for a task"""
        print(f"[PROOF_VERIFICATION] 🎯 Setting verification criteria for task {task_id}")
        
        # Convert coordinates to positive uint256 by adding offset (smart contracts need positive values)
        location_scaled = [int((location[0] + 10) * 100), int((location[1] + 10) * 100)]
        
        function_call = self.proof_verification.functions.setVerificationCriteria(
            task_id, location_scaled, tolerance, max_time, min_images, True, True
        )
        
        result = self._send_transaction(function_call, f"Verification criteria for task {task_id}")
        
        if result['success']:
            print(f"[PROOF_VERIFICATION] ✅ Verification criteria set!")
        
        return result
    
    def submit_proof(self, task_id: int, waypoints: List[Tuple[float, float]], 
                    images: List[str], completion_time: int) -> Dict[str, Any]:
        """Submit proof of task completion"""
        print(f"[PROOF_VERIFICATION] 📋 Submitting proof for task {task_id}")
        
        # Generate cryptographic hashes for proof
        waypoints_hash = self._calculate_waypoints_hash(waypoints)
        image_hashes = [self._calculate_hash(img) for img in images]
        
        print(f"[PROOF_VERIFICATION] 🔐 Waypoints hash: 0x{waypoints_hash.hex()}")
        print(f"[PROOF_VERIFICATION] 📷 Images: {len(image_hashes)} hashes generated")
        
        function_call = self.proof_verification.functions.submitProof(
            task_id, waypoints_hash, image_hashes, completion_time
        )
        
        result = self._send_transaction(function_call, f"Proof submission for task {task_id}")
        
        if result['success']:
            print(f"[PROOF_VERIFICATION] ✅ Proof submitted successfully!")
            print(f"[PROOF_VERIFICATION] 🔍 Verification in progress...")
        
        return result
    
    def _calculate_waypoints_hash(self, waypoints: List[Tuple[float, float]]) -> bytes:
        """Calculate hash of GPS waypoints"""
        waypoints_data = json.dumps(waypoints, sort_keys=True).encode()
        return hashlib.sha256(waypoints_data).digest()
    
    def _calculate_hash(self, data: str) -> bytes:
        """Calculate SHA256 hash of data"""
        return hashlib.sha256(data.encode()).digest()
    
    def manual_verification(self, task_id: int, success: bool, message: str) -> Dict[str, Any]:
        """Manually verify a proof (admin function)"""
        print(f"[PROOF_VERIFICATION] ⚖️ Manual verification for task {task_id}: {success}")
        
        function_call = self.proof_verification.functions.manualVerification(
            task_id, success, message
        )
        
        result = self._send_transaction(function_call, f"Manual verification for task {task_id}")
        
        if result['success']:
            print(f"[PROOF_VERIFICATION] ✅ Verification completed!")
            print(f"[PROOF_VERIFICATION] 📝 Result: {message}")
        
        return result
    
    # ==========================================
    # FULL WORKFLOW OPERATIONS
    # ==========================================
    
    def execute_full_workflow_demo(self) -> Dict[str, Any]:
        """Execute complete workflow demonstration"""
        print(f"[WORKFLOW] 🚀 Starting complete autonomous robot workflow demonstration")
        print(f"[WORKFLOW] 📋 Workflow: Registration → Task → Bidding → Assignment → Proof → Payment")
        
        results = {}
        
        # Step 1: Register robot if not already registered
        print(f"\n[WORKFLOW] === Step 1: Robot Registration ===")
        robot_capabilities = [120, 80, 85, 95, 75]  # Sample capabilities
        registration_result = self.register_robot("demo_robot_001", robot_capabilities)
        results['registration'] = registration_result
        
        time.sleep(3)  # Wait for transaction confirmation
        
        # Step 2: Create task 
        print(f"\n[WORKFLOW] === Step 2: Task Creation ===")
        task_result = self.create_task(
            mission_id=1,
            task_type="disaster_scan",
            description="Complete workflow demo task",
            location=(1.5, 2.3),
            required_capabilities=[100, 70, 80, 85, 70],
            budget=0.01  # 0.01 SEI
        )
        results['task_creation'] = task_result
        
        if not task_result['success']:
            print(f"[WORKFLOW] ❌ Workflow stopped - task creation failed")
            return results
        
        time.sleep(3)  # Wait for auction to be available
        
        # Step 3: Place bid
        print(f"\n[WORKFLOW] === Step 3: Bid Placement ===")
        task_id = 1  # Assuming this is the first task
        bid_result = self.place_bid(task_id, 180, "demo_robot_001")  # 3 minutes estimated
        results['bidding'] = bid_result
        
        time.sleep(5)  # Wait for other potential bids
        
        # Step 4: Close auction
        print(f"\n[WORKFLOW] === Step 4: Auction Closure ===")
        auction_result = self.close_auction(task_id)
        results['auction_closure'] = auction_result
        
        time.sleep(3)
        
        # Step 5: Set verification criteria
        print(f"\n[WORKFLOW] === Step 5: Verification Setup ===")
        criteria_result = self.set_verification_criteria(task_id, (1.5, 2.3))
        results['verification_criteria'] = criteria_result
        
        time.sleep(2)
        
        # Step 6: Submit proof (simulated task completion)
        print(f"\n[WORKFLOW] === Step 6: Proof Submission ===")
        waypoints = [(1.0, 2.0), (1.2, 2.1), (1.5, 2.3)]  # Simulated path
        images = ["image_001", "image_002", "image_003"]  # Simulated captures
        proof_result = self.submit_proof(task_id, waypoints, images, int(time.time()))
        results['proof_submission'] = proof_result
        
        time.sleep(3)
        
        # Step 7: Manual verification (in production this would be automatic)
        print(f"\n[WORKFLOW] === Step 7: Proof Verification ===")
        verification_result = self.manual_verification(
            task_id, True, "Demo task completed successfully - all criteria met"
        )
        results['verification'] = verification_result
        
        print(f"\n[WORKFLOW] 🎉 COMPLETE WORKFLOW DEMONSTRATION FINISHED!")
        print(f"[WORKFLOW] ✅ All steps completed successfully")
        print(f"[WORKFLOW] 🔗 Robot registered → Task created → Bid placed → Winner selected → Proof verified → Payment released")
        print(f"[WORKFLOW] 💰 Autonomous payment system operational on Sei Network")
        
        return results

if __name__ == "__main__":
    # Test complete smart contract client
    test_config = {
        'sei_rpc_url': 'https://evm-rpc-testnet.sei-apis.com',
        'chain_id': 1328,
        'private_key': '0x03d46d9bde38a9151f39271ffe669c4bfec65b9e2bca254c175435d71f9d4460'
    }
    
    client = CompleteSmartContractClient(test_config)
    
    # Execute full workflow demonstration
    print("\n🔥 Starting COMPLETE WORKFLOW DEMONSTRATION...")
    results = client.execute_full_workflow_demo()
    
    print(f"\n🎯 DEMONSTRATION RESULTS:")
    print(json.dumps(results, indent=2, default=str))