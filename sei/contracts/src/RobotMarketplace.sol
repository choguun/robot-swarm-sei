// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title RobotMarketplace
 * @dev Manages robot registration, capabilities, and reputation for autonomous marketplace
 * @notice Built exclusively for Sei Network - Hackathon Submission
 */
contract RobotMarketplace is AccessControl, ReentrancyGuard, Pausable {
    
    bytes32 public constant SUPERVISOR_ROLE = keccak256("SUPERVISOR_ROLE");
    bytes32 public constant ATTESTOR_ROLE = keccak256("ATTESTOR_ROLE");
    
    struct Robot {
        address owner;
        string robotId;
        uint256[] capabilities;  // [speed, payload, battery, terrain, sensor]
        uint256 reputation;      // Reputation score (0-1000, scaled)
        bool isActive;
        uint256 totalTasksCompleted;
        uint256 totalTasksFailed;
        uint256 registrationTime;
        uint256 lastActiveTime;
    }
    
    struct Capability {
        string name;
        string description;
        uint256 minValue;
        uint256 maxValue;
    }
    
    // Robot management
    mapping(address => Robot) public robots;
    mapping(string => address) public robotIdToAddress;
    address[] public robotAddresses;
    
    // Capability definitions
    Capability[] public capabilityTypes;
    
    // Events
    event RobotRegistered(
        address indexed owner,
        string robotId,
        uint256[] capabilities,
        uint256 timestamp
    );
    
    event RobotUpdated(
        address indexed robot,
        uint256[] newCapabilities,
        uint256 timestamp
    );
    
    event ReputationUpdated(
        address indexed robot,
        uint256 oldReputation,
        uint256 newReputation,
        string reason
    );
    
    event RobotActivated(address indexed robot, uint256 timestamp);
    event RobotDeactivated(address indexed robot, uint256 timestamp);
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SUPERVISOR_ROLE, msg.sender);
        _grantRole(ATTESTOR_ROLE, msg.sender);
        
        _initializeCapabilities();
    }
    
    /**
     * @dev Initialize standard capability types for disaster response robots
     */
    function _initializeCapabilities() internal {
        capabilityTypes.push(Capability({
            name: "navigation_speed",
            description: "Robot movement speed (m/s * 100)",
            minValue: 50,   // 0.5 m/s
            maxValue: 200   // 2.0 m/s
        }));
        
        capabilityTypes.push(Capability({
            name: "payload_capacity", 
            description: "Carrying capacity (kg * 10)",
            minValue: 50,   // 5 kg
            maxValue: 200   // 20 kg
        }));
        
        capabilityTypes.push(Capability({
            name: "battery_efficiency",
            description: "Battery efficiency rating (0-100)",
            minValue: 60,
            maxValue: 100
        }));
        
        capabilityTypes.push(Capability({
            name: "terrain_adaptability",
            description: "Terrain handling capability (0-100)",
            minValue: 50,
            maxValue: 100
        }));
        
        capabilityTypes.push(Capability({
            name: "sensor_quality",
            description: "Sensor accuracy and range (0-100)",
            minValue: 40,
            maxValue: 100
        }));
    }
    
    /**
     * @dev Register a new robot in the marketplace
     * @param robotId Unique identifier for the robot
     * @param capabilities Array of capability values
     */
    function registerRobot(
        string calldata robotId,
        uint256[] calldata capabilities
    ) external nonReentrant whenNotPaused {
        require(bytes(robotId).length > 0, "Robot ID cannot be empty");
        require(robotIdToAddress[robotId] == address(0), "Robot ID already exists");
        require(robots[msg.sender].owner == address(0), "Address already has registered robot");
        require(capabilities.length == capabilityTypes.length, "Invalid capabilities length");
        
        // Validate capability values
        for (uint256 i = 0; i < capabilities.length; i++) {
            require(
                capabilities[i] >= capabilityTypes[i].minValue &&
                capabilities[i] <= capabilityTypes[i].maxValue,
                "Capability value out of range"
            );
        }
        
        // Create robot record
        robots[msg.sender] = Robot({
            owner: msg.sender,
            robotId: robotId,
            capabilities: capabilities,
            reputation: 500,  // Start with neutral reputation (50%)
            isActive: true,
            totalTasksCompleted: 0,
            totalTasksFailed: 0,
            registrationTime: block.timestamp,
            lastActiveTime: block.timestamp
        });
        
        robotIdToAddress[robotId] = msg.sender;
        robotAddresses.push(msg.sender);
        
        emit RobotRegistered(msg.sender, robotId, capabilities, block.timestamp);
    }
    
    /**
     * @dev Update robot capabilities
     * @param capabilities New capability values
     */
    function updateCapabilities(
        uint256[] calldata capabilities
    ) external nonReentrant whenNotPaused {
        require(robots[msg.sender].owner != address(0), "Robot not registered");
        require(capabilities.length == capabilityTypes.length, "Invalid capabilities length");
        
        // Validate capability values
        for (uint256 i = 0; i < capabilities.length; i++) {
            require(
                capabilities[i] >= capabilityTypes[i].minValue &&
                capabilities[i] <= capabilityTypes[i].maxValue,
                "Capability value out of range"
            );
        }
        
        robots[msg.sender].capabilities = capabilities;
        robots[msg.sender].lastActiveTime = block.timestamp;
        
        emit RobotUpdated(msg.sender, capabilities, block.timestamp);
    }
    
    /**
     * @dev Update robot reputation (only by authorized roles)
     * @param robot Robot address
     * @param newReputation New reputation score
     * @param reason Reason for reputation change
     */
    function updateReputation(
        address robot,
        uint256 newReputation,
        string calldata reason
    ) external onlyRole(SUPERVISOR_ROLE) nonReentrant {
        require(robots[robot].owner != address(0), "Robot not registered");
        require(newReputation <= 1000, "Reputation cannot exceed 1000");
        
        uint256 oldReputation = robots[robot].reputation;
        robots[robot].reputation = newReputation;
        robots[robot].lastActiveTime = block.timestamp;
        
        emit ReputationUpdated(robot, oldReputation, newReputation, reason);
    }
    
    /**
     * @dev Record task completion for reputation management
     * @param robot Robot address
     * @param success Whether task was successful
     */
    function recordTaskCompletion(
        address robot,
        bool success
    ) external onlyRole(SUPERVISOR_ROLE) nonReentrant {
        require(robots[robot].owner != address(0), "Robot not registered");
        
        Robot storage r = robots[robot];
        
        if (success) {
            r.totalTasksCompleted++;
            // Increase reputation for successful tasks (max 1000)
            uint256 reputationIncrease = 10; // Base increase
            if (r.reputation < 800) reputationIncrease = 20; // Bonus for lower reputation
            r.reputation = r.reputation + reputationIncrease > 1000 ? 1000 : r.reputation + reputationIncrease;
            
            emit ReputationUpdated(robot, r.reputation - reputationIncrease, r.reputation, "Task completed successfully");
        } else {
            r.totalTasksFailed++;
            // Decrease reputation for failed tasks (min 0)
            uint256 reputationDecrease = 50;
            r.reputation = r.reputation > reputationDecrease ? r.reputation - reputationDecrease : 0;
            
            emit ReputationUpdated(robot, r.reputation + reputationDecrease, r.reputation, "Task failed");
        }
        
        r.lastActiveTime = block.timestamp;
    }
    
    /**
     * @dev Activate robot for marketplace participation
     */
    function activateRobot() external nonReentrant {
        require(robots[msg.sender].owner != address(0), "Robot not registered");
        require(!robots[msg.sender].isActive, "Robot already active");
        
        robots[msg.sender].isActive = true;
        robots[msg.sender].lastActiveTime = block.timestamp;
        
        emit RobotActivated(msg.sender, block.timestamp);
    }
    
    /**
     * @dev Deactivate robot from marketplace participation
     */
    function deactivateRobot() external nonReentrant {
        require(robots[msg.sender].owner != address(0), "Robot not registered");
        require(robots[msg.sender].isActive, "Robot already inactive");
        
        robots[msg.sender].isActive = false;
        
        emit RobotDeactivated(msg.sender, block.timestamp);
    }
    
    /**
     * @dev Get active robots for task assignment
     * @return Array of active robot addresses
     */
    function getActiveRobots() external view returns (address[] memory) {
        uint256 activeCount = 0;
        
        // Count active robots
        for (uint256 i = 0; i < robotAddresses.length; i++) {
            if (robots[robotAddresses[i]].isActive) {
                activeCount++;
            }
        }
        
        // Create array of active robots
        address[] memory activeRobots = new address[](activeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < robotAddresses.length; i++) {
            if (robots[robotAddresses[i]].isActive) {
                activeRobots[index] = robotAddresses[i];
                index++;
            }
        }
        
        return activeRobots;
    }
    
    /**
     * @dev Get robot capabilities
     * @param robot Robot address
     * @return Array of capability values
     */
    function getRobotCapabilities(address robot) external view returns (uint256[] memory) {
        require(robots[robot].owner != address(0), "Robot not registered");
        return robots[robot].capabilities;
    }
    
    /**
     * @dev Calculate capability match score for task
     * @param robot Robot address
     * @param requiredCapabilities Required capability minimums
     * @return Match score (0-1000)
     */
    function calculateCapabilityMatch(
        address robot,
        uint256[] calldata requiredCapabilities
    ) external view returns (uint256) {
        require(robots[robot].owner != address(0), "Robot not registered");
        require(requiredCapabilities.length == capabilityTypes.length, "Invalid requirements length");
        
        uint256[] memory robotCaps = robots[robot].capabilities;
        uint256 totalScore = 0;
        
        for (uint256 i = 0; i < robotCaps.length; i++) {
            if (robotCaps[i] >= requiredCapabilities[i]) {
                // Robot meets or exceeds requirement
                uint256 capabilityRange = capabilityTypes[i].maxValue - capabilityTypes[i].minValue;
                uint256 robotScore = ((robotCaps[i] - capabilityTypes[i].minValue) * 1000) / capabilityRange;
                totalScore += robotScore;
            } else {
                // Robot doesn't meet requirement - partial credit
                uint256 partialScore = (robotCaps[i] * 500) / requiredCapabilities[i];
                totalScore += partialScore;
            }
        }
        
        return totalScore / robotCaps.length; // Average score
    }
    
    /**
     * @dev Get robot statistics
     * @param robot Robot address
     */
    function getRobotStats(address robot) external view returns (
        string memory robotId,
        uint256 reputation,
        bool isActive,
        uint256 totalTasksCompleted,
        uint256 totalTasksFailed,
        uint256 successRate
    ) {
        require(robots[robot].owner != address(0), "Robot not registered");
        
        Robot memory r = robots[robot];
        uint256 totalTasks = r.totalTasksCompleted + r.totalTasksFailed;
        uint256 successRateCalc = totalTasks > 0 ? (r.totalTasksCompleted * 1000) / totalTasks : 0;
        
        return (
            r.robotId,
            r.reputation,
            r.isActive,
            r.totalTasksCompleted,
            r.totalTasksFailed,
            successRateCalc
        );
    }
    
    /**
     * @dev Get capability type information
     * @param index Capability type index
     */
    function getCapabilityType(uint256 index) external view returns (
        string memory name,
        string memory description,
        uint256 minValue,
        uint256 maxValue
    ) {
        require(index < capabilityTypes.length, "Invalid capability index");
        
        Capability memory cap = capabilityTypes[index];
        return (cap.name, cap.description, cap.minValue, cap.maxValue);
    }
    
    /**
     * @dev Get total number of registered robots
     */
    function getTotalRobots() external view returns (uint256) {
        return robotAddresses.length;
    }
    
    /**
     * @dev Emergency pause function
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @dev Unpause function
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
}