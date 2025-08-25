// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./RobotMarketplace.sol";

/**
 * @title TaskAuction
 * @dev Handles autonomous task auctions, bidding, escrow, and payments
 * @notice Built exclusively for Sei Network - Sub-400ms finality enables real-time auctions
 */
contract TaskAuction is AccessControl, ReentrancyGuard, Pausable {
    
    bytes32 public constant SUPERVISOR_ROLE = keccak256("SUPERVISOR_ROLE");
    bytes32 public constant ATTESTOR_ROLE = keccak256("ATTESTOR_ROLE");
    
    enum TaskState {
        CREATED,
        AUCTION_OPEN,
        AUCTION_CLOSED,
        ASSIGNED,
        PROOF_SUBMITTED,
        VERIFIED,
        COMPLETED,
        FAILED,
        EXPIRED
    }
    
    struct Task {
        uint256 taskId;
        uint256 missionId;
        address sponsor;
        string taskType;
        string description;
        uint256[2] location;  // [x, y] coordinates
        uint256[] requiredCapabilities;
        uint256 budget;
        uint256 deadline;
        uint256 auctionEndTime;
        TaskState state;
        address assignedRobot;
        uint256 escrowAmount;
        uint256 createdTime;
    }
    
    struct Bid {
        address robot;
        uint256 amount;
        uint256 estimatedTime;
        uint256 capabilityMatch;
        uint256 reputation;
        uint256 timestamp;
        bool isValid;
    }
    
    // Core storage
    mapping(uint256 => Task) public tasks;
    mapping(uint256 => Bid[]) public taskBids;
    mapping(uint256 => mapping(address => bool)) public hasBid;
    mapping(address => uint256) public escrowBalances;
    
    uint256 public nextTaskId = 1;
    uint256 public constant AUCTION_DURATION = 30; // 30 seconds for real-time demo
    uint256 public constant TASK_TIMEOUT = 300;    // 5 minutes maximum task duration
    
    RobotMarketplace public robotMarketplace;
    
    // Events
    event TaskCreated(
        uint256 indexed taskId,
        uint256 indexed missionId,
        address indexed sponsor,
        string taskType,
        uint256[2] location,
        uint256 budget,
        uint256 deadline
    );
    
    event AuctionOpened(
        uint256 indexed taskId,
        uint256 auctionEndTime,
        uint256[] requiredCapabilities
    );
    
    event BidPlaced(
        uint256 indexed taskId,
        address indexed robot,
        uint256 bidAmount,
        uint256 estimatedTime,
        uint256 capabilityMatch,
        uint256 timestamp
    );
    
    event WinnerSelected(
        uint256 indexed taskId,
        address indexed winner,
        uint256 winningBid,
        uint256 selectionTime
    );
    
    event TaskAssigned(
        uint256 indexed taskId,
        address indexed robot,
        uint256 escrowAmount,
        uint256 deadline
    );
    
    event EscrowReleased(
        uint256 indexed taskId,
        address indexed robot,
        uint256 amount,
        string reason
    );
    
    event TaskCompleted(
        uint256 indexed taskId,
        address indexed robot,
        uint256 completionTime,
        uint256 payout
    );
    
    event TaskFailed(
        uint256 indexed taskId,
        address indexed robot,
        string reason,
        uint256 penalty
    );
    
    constructor(address _robotMarketplace) {
        require(_robotMarketplace != address(0), "Invalid marketplace address");
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SUPERVISOR_ROLE, msg.sender);
        _grantRole(ATTESTOR_ROLE, msg.sender);
        
        robotMarketplace = RobotMarketplace(_robotMarketplace);
    }
    
    /**
     * @dev Create a new task and open auction
     * @param missionId Parent mission identifier
     * @param taskType Type of task (scan, delivery, etc.)
     * @param description Task description
     * @param location Task location coordinates
     * @param requiredCapabilities Minimum capability requirements
     * @param budget Maximum budget for task
     */
    function createTask(
        uint256 missionId,
        string calldata taskType,
        string calldata description,
        uint256[2] calldata location,
        uint256[] calldata requiredCapabilities,
        uint256 budget
    ) external payable onlyRole(SUPERVISOR_ROLE) nonReentrant whenNotPaused returns (uint256) {
        require(msg.value >= budget, "Insufficient funds for budget");
        require(bytes(taskType).length > 0, "Task type required");
        require(budget > 0, "Budget must be positive");
        
        uint256 taskId = nextTaskId++;
        uint256 deadline = block.timestamp + TASK_TIMEOUT;
        uint256 auctionEndTime = block.timestamp + AUCTION_DURATION;
        
        tasks[taskId] = Task({
            taskId: taskId,
            missionId: missionId,
            sponsor: msg.sender,
            taskType: taskType,
            description: description,
            location: location,
            requiredCapabilities: requiredCapabilities,
            budget: budget,
            deadline: deadline,
            auctionEndTime: auctionEndTime,
            state: TaskState.AUCTION_OPEN,
            assignedRobot: address(0),
            escrowAmount: 0,
            createdTime: block.timestamp
        });
        
        // Store excess funds for later refund
        if (msg.value > budget) {
            escrowBalances[msg.sender] += msg.value - budget;
        }
        
        emit TaskCreated(taskId, missionId, msg.sender, taskType, location, budget, deadline);
        emit AuctionOpened(taskId, auctionEndTime, requiredCapabilities);
        
        return taskId;
    }
    
    /**
     * @dev Place bid for a task
     * @param taskId Task to bid on
     * @param estimatedTime Estimated completion time in seconds
     */
    function placeBid(
        uint256 taskId,
        uint256 estimatedTime
    ) external nonReentrant whenNotPaused {
        Task storage task = tasks[taskId];
        require(task.taskId != 0, "Task does not exist");
        require(task.state == TaskState.AUCTION_OPEN, "Auction not open");
        require(block.timestamp < task.auctionEndTime, "Auction ended");
        require(!hasBid[taskId][msg.sender], "Already placed bid");
        
        // Verify robot is registered and active
        (string memory robotId, uint256 reputation, bool isActive,,,) = robotMarketplace.getRobotStats(msg.sender);
        require(isActive, "Robot not active");
        require(bytes(robotId).length > 0, "Robot not registered");
        
        // Calculate capability match
        uint256 capabilityMatch = robotMarketplace.calculateCapabilityMatch(
            msg.sender,
            task.requiredCapabilities
        );
        require(capabilityMatch >= 300, "Insufficient capabilities"); // Minimum 30% match
        
        // Calculate bid amount based on robot's algorithm
        uint256 bidAmount = _calculateRobotBidAmount(taskId, msg.sender, estimatedTime, capabilityMatch);
        require(bidAmount <= task.budget, "Bid exceeds budget");
        
        // Store bid
        taskBids[taskId].push(Bid({
            robot: msg.sender,
            amount: bidAmount,
            estimatedTime: estimatedTime,
            capabilityMatch: capabilityMatch,
            reputation: reputation,
            timestamp: block.timestamp,
            isValid: true
        }));
        
        hasBid[taskId][msg.sender] = true;
        
        emit BidPlaced(taskId, msg.sender, bidAmount, estimatedTime, capabilityMatch, block.timestamp);
    }
    
    /**
     * @dev Calculate robot's bid amount using standardized algorithm
     */
    function _calculateRobotBidAmount(
        uint256 taskId,
        address robot,
        uint256 estimatedTime,
        uint256 capabilityMatch
    ) internal view returns (uint256) {
        Task memory task = tasks[taskId];
        (, uint256 reputation,,,, uint256 successRate) = robotMarketplace.getRobotStats(robot);
        
        // Base cost calculation
        uint256 baseCost = task.budget / 4;  // Start at 25% of budget
        
        // Time factor (longer tasks cost more)
        uint256 timeFactor = 1000 + (estimatedTime * 2); // 1.0 + time penalty
        
        // Capability bonus (better match = lower cost)
        uint256 capabilityFactor = 1500 - (capabilityMatch / 2); // 1.5 - capability bonus
        
        // Reputation factor (higher reputation = more competitive)
        uint256 reputationFactor = 2000 - reputation; // Better reputation = lower bids
        
        // Success rate factor
        uint256 successFactor = 1000 + (1000 - successRate); // Higher success = lower bids
        
        // Calculate final bid
        uint256 bidAmount = (baseCost * timeFactor * capabilityFactor * reputationFactor * successFactor) 
                           / (1000 * 1000 * 1000 * 1000);
        
        // Ensure within reasonable bounds
        uint256 minBid = task.budget / 10;  // Minimum 10% of budget
        uint256 maxBid = (task.budget * 90) / 100;  // Maximum 90% of budget
        
        if (bidAmount < minBid) bidAmount = minBid;
        if (bidAmount > maxBid) bidAmount = maxBid;
        
        return bidAmount;
    }
    
    /**
     * @dev Close auction and select winner
     * @param taskId Task to close auction for
     */
    function closeAuction(uint256 taskId) external onlyRole(SUPERVISOR_ROLE) nonReentrant {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.AUCTION_OPEN, "Auction not open");
        require(block.timestamp >= task.auctionEndTime, "Auction still active");
        
        Bid[] memory bids = taskBids[taskId];
        require(bids.length > 0, "No bids received");
        
        // Select winner using multi-criteria algorithm
        address winner = _selectAuctionWinner(taskId);
        require(winner != address(0), "No suitable winner found");
        
        // Update task state
        task.state = TaskState.ASSIGNED;
        task.assignedRobot = winner;
        
        // Find winning bid amount
        uint256 winningBid = 0;
        for (uint256 i = 0; i < bids.length; i++) {
            if (bids[i].robot == winner) {
                winningBid = bids[i].amount;
                break;
            }
        }
        
        // Escrow payment
        task.escrowAmount = winningBid;
        
        emit WinnerSelected(taskId, winner, winningBid, block.timestamp);
        emit TaskAssigned(taskId, winner, winningBid, task.deadline);
    }
    
    /**
     * @dev Select auction winner using multi-criteria decision algorithm
     */
    function _selectAuctionWinner(uint256 taskId) internal view returns (address) {
        Bid[] memory bids = taskBids[taskId];
        
        uint256 bestScore = 0;
        address bestRobot = address(0);
        
        for (uint256 i = 0; i < bids.length; i++) {
            if (!bids[i].isValid) continue;
            
            // Multi-criteria scoring:
            // 40% - Bid amount (lower is better)
            // 30% - Capability match (higher is better) 
            // 20% - Reputation (higher is better)
            // 10% - Estimated time (lower is better)
            
            uint256 bidScore = (10000 - (bids[i].amount * 10000 / tasks[taskId].budget)) * 40 / 100;
            uint256 capabilityScore = bids[i].capabilityMatch * 30 / 100;
            uint256 reputationScore = bids[i].reputation * 20 / 100;
            uint256 timeScore = (3600 - bids[i].estimatedTime) * 10 / 3600 / 100;
            
            uint256 totalScore = bidScore + capabilityScore + reputationScore + timeScore;
            
            if (totalScore > bestScore) {
                bestScore = totalScore;
                bestRobot = bids[i].robot;
            }
        }
        
        return bestRobot;
    }
    
    /**
     * @dev Submit task completion proof (called by attestation system)
     * @param taskId Completed task
     * @param robot Robot that completed task
     * @param success Whether task was successful
     * @param proofHash Hash of completion proof
     */
    function submitTaskCompletion(
        uint256 taskId,
        address robot,
        bool success,
        bytes32 proofHash
    ) external onlyRole(ATTESTOR_ROLE) nonReentrant {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.ASSIGNED, "Task not in assigned state");
        require(task.assignedRobot == robot, "Robot not assigned to task");
        
        if (success) {
            // Task completed successfully
            task.state = TaskState.COMPLETED;
            
            // Release escrow to robot
            uint256 payout = task.escrowAmount;
            
            // Transfer payment
            payable(robot).transfer(payout);
            
            // Update robot reputation
            robotMarketplace.recordTaskCompletion(robot, true);
            
            emit TaskCompleted(taskId, robot, block.timestamp, payout);
            emit EscrowReleased(taskId, robot, payout, "Task completed successfully");
            
        } else {
            // Task failed
            task.state = TaskState.FAILED;
            
            // Refund escrowed amount to sponsor
            escrowBalances[task.sponsor] += task.escrowAmount;
            
            // Penalize robot reputation
            robotMarketplace.recordTaskCompletion(robot, false);
            
            emit TaskFailed(taskId, robot, "Task completion verification failed", 0);
        }
    }
    
    /**
     * @dev Handle task timeout (automatic failure)
     * @param taskId Task that timed out
     */
    function handleTaskTimeout(uint256 taskId) external onlyRole(SUPERVISOR_ROLE) nonReentrant {
        Task storage task = tasks[taskId];
        require(task.state == TaskState.ASSIGNED, "Task not assigned");
        require(block.timestamp > task.deadline, "Task not yet expired");
        
        task.state = TaskState.EXPIRED;
        
        // Refund to sponsor
        escrowBalances[task.sponsor] += task.escrowAmount;
        
        // Penalize robot for timeout
        robotMarketplace.recordTaskCompletion(task.assignedRobot, false);
        
        emit TaskFailed(taskId, task.assignedRobot, "Task expired - timeout", task.escrowAmount);
    }
    
    /**
     * @dev Withdraw escrowed funds
     */
    function withdrawEscrow() external nonReentrant {
        uint256 amount = escrowBalances[msg.sender];
        require(amount > 0, "No funds to withdraw");
        
        escrowBalances[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
    }
    
    /**
     * @dev Get all bids for a task
     * @param taskId Task to get bids for
     */
    function getTaskBids(uint256 taskId) external view returns (Bid[] memory) {
        return taskBids[taskId];
    }
    
    /**
     * @dev Get task details
     * @param taskId Task to get details for
     */
    function getTaskDetails(uint256 taskId) external view returns (
        string memory taskType,
        string memory description,
        uint256[2] memory location,
        uint256 budget,
        TaskState state,
        address assignedRobot,
        uint256 deadline,
        uint256 bidCount
    ) {
        Task memory task = tasks[taskId];
        require(task.taskId != 0, "Task does not exist");
        
        return (
            task.taskType,
            task.description,
            task.location,
            task.budget,
            task.state,
            task.assignedRobot,
            task.deadline,
            taskBids[taskId].length
        );
    }
    
    /**
     * @dev Get active tasks (auction open or assigned)
     */
    function getActiveTasks() external view returns (uint256[] memory) {
        uint256 activeCount = 0;
        
        // Count active tasks
        for (uint256 i = 1; i < nextTaskId; i++) {
            TaskState state = tasks[i].state;
            if (state == TaskState.AUCTION_OPEN || state == TaskState.ASSIGNED) {
                activeCount++;
            }
        }
        
        // Create array of active task IDs
        uint256[] memory activeTasks = new uint256[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 1; i < nextTaskId; i++) {
            TaskState state = tasks[i].state;
            if (state == TaskState.AUCTION_OPEN || state == TaskState.ASSIGNED) {
                activeTasks[index] = i;
                index++;
            }
        }
        
        return activeTasks;
    }
    
    /**
     * @dev Emergency pause
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @dev Unpause
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
    
    /**
     * @dev Emergency withdraw (admin only)
     */
    function emergencyWithdraw() external onlyRole(DEFAULT_ADMIN_ROLE) {
        payable(msg.sender).transfer(address(this).balance);
    }
}