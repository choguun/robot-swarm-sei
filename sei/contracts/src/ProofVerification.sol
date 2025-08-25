// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./TaskAuction.sol";

/**
 * @title ProofVerification
 * @dev Handles proof submission and verification with Rivalz ADCS oracle integration
 * @notice Built for Sei Network - Enables cryptographic proof verification for robot tasks
 */
contract ProofVerification is AccessControl, ReentrancyGuard {
    
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant ROBOT_ROLE = keccak256("ROBOT_ROLE");
    
    enum ProofState {
        SUBMITTED,
        VERIFYING,
        VERIFIED,
        REJECTED,
        EXPIRED
    }
    
    struct ProofSubmission {
        uint256 taskId;
        address robot;
        bytes32 waypointsHash;
        bytes32[] imageHashes;
        bytes32 proofBundleHash;
        uint256 submissionTime;
        uint256 completionTime;
        ProofState state;
        string verificationResult;
    }
    
    struct VerificationCriteria {
        uint256[2] requiredLocation;    // Target location for task
        uint256 locationTolerance;      // Acceptable distance from target (in meters * 100)
        uint256 maxCompletionTime;     // Maximum time allowed for task
        uint256 minImageCount;         // Minimum number of images required
        bool requiresGPSProof;         // Whether GPS waypoints are required
        bool requiresImageProof;       // Whether images are required
    }
    
    // Storage
    mapping(uint256 => ProofSubmission) public proofSubmissions;
    mapping(uint256 => VerificationCriteria) public taskCriteria;
    mapping(bytes32 => bool) public usedProofHashes;
    
    TaskAuction public taskAuction;
    
    // Oracle configuration
    address public rivalzOracleAddress;
    uint256 public verificationTimeout = 60; // 1 minute timeout for verification
    
    // Events
    event ProofSubmitted(
        uint256 indexed taskId,
        address indexed robot,
        bytes32 waypointsHash,
        bytes32[] imageHashes,
        bytes32 proofBundleHash,
        uint256 submissionTime
    );
    
    event ProofVerificationRequested(
        uint256 indexed taskId,
        address indexed oracle,
        bytes32 proofBundleHash,
        uint256 requestTime
    );
    
    event ProofVerified(
        uint256 indexed taskId,
        address indexed robot,
        bool success,
        string result,
        uint256 verificationTime
    );
    
    event VerificationFailed(
        uint256 indexed taskId,
        address indexed robot,
        string reason,
        uint256 verificationTime
    );
    
    event CriteriaUpdated(
        uint256 indexed taskId,
        uint256[2] requiredLocation,
        uint256 locationTolerance,
        uint256 maxCompletionTime
    );
    
    constructor(address _taskAuction) {
        require(_taskAuction != address(0), "Invalid task auction address");
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ORACLE_ROLE, msg.sender); // Admin can act as oracle initially
        
        taskAuction = TaskAuction(_taskAuction);
    }
    
    /**
     * @dev Set verification criteria for a task
     * @param taskId Task to set criteria for
     * @param requiredLocation Target location coordinates
     * @param locationTolerance Acceptable distance from target (meters * 100)
     * @param maxCompletionTime Maximum allowed task duration
     * @param minImageCount Minimum required images
     * @param requiresGPS Whether GPS proof is required
     * @param requiresImages Whether image proof is required
     */
    function setVerificationCriteria(
        uint256 taskId,
        uint256[2] calldata requiredLocation,
        uint256 locationTolerance,
        uint256 maxCompletionTime,
        uint256 minImageCount,
        bool requiresGPS,
        bool requiresImages
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        taskCriteria[taskId] = VerificationCriteria({
            requiredLocation: requiredLocation,
            locationTolerance: locationTolerance,
            maxCompletionTime: maxCompletionTime,
            minImageCount: minImageCount,
            requiresGPSProof: requiresGPS,
            requiresImageProof: requiresImages
        });
        
        emit CriteriaUpdated(taskId, requiredLocation, locationTolerance, maxCompletionTime);
    }
    
    /**
     * @dev Submit proof for task completion
     * @param taskId Task ID for completed task
     * @param waypointsHash Hash of GPS waypoint data
     * @param imageHashes Array of image hashes from task execution
     * @param completionTime Timestamp when task was completed
     */
    function submitProof(
        uint256 taskId,
        bytes32 waypointsHash,
        bytes32[] calldata imageHashes,
        uint256 completionTime
    ) external nonReentrant {
        // Verify caller is assigned robot for this task
        (, , , , , address assignedRobot, ,) = taskAuction.getTaskDetails(taskId);
        require(assignedRobot == msg.sender, "Not assigned robot");
        require(proofSubmissions[taskId].robot == address(0), "Proof already submitted");
        
        // Calculate proof bundle hash
        bytes32 proofBundleHash = _calculateProofBundleHash(
            taskId,
            msg.sender,
            waypointsHash,
            imageHashes,
            completionTime
        );
        
        require(!usedProofHashes[proofBundleHash], "Proof hash already used");
        usedProofHashes[proofBundleHash] = true;
        
        // Store proof submission
        proofSubmissions[taskId] = ProofSubmission({
            taskId: taskId,
            robot: msg.sender,
            waypointsHash: waypointsHash,
            imageHashes: imageHashes,
            proofBundleHash: proofBundleHash,
            submissionTime: block.timestamp,
            completionTime: completionTime,
            state: ProofState.SUBMITTED,
            verificationResult: ""
        });
        
        emit ProofSubmitted(
            taskId,
            msg.sender,
            waypointsHash,
            imageHashes,
            proofBundleHash,
            block.timestamp
        );
        
        // Automatically trigger verification
        _requestVerification(taskId);
    }
    
    /**
     * @dev Internal function to calculate proof bundle hash
     */
    function _calculateProofBundleHash(
        uint256 taskId,
        address robot,
        bytes32 waypointsHash,
        bytes32[] calldata imageHashes,
        uint256 completionTime
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(
            taskId,
            robot,
            waypointsHash,
            keccak256(abi.encodePacked(imageHashes)),
            completionTime
        ));
    }
    
    /**
     * @dev Request verification from oracle
     * @param taskId Task to verify
     */
    function _requestVerification(uint256 taskId) internal {
        ProofSubmission storage proof = proofSubmissions[taskId];
        proof.state = ProofState.VERIFYING;
        
        // In a real implementation, this would call Rivalz ADCS oracle
        // For hackathon demo, we'll use a simplified verification process
        
        if (rivalzOracleAddress != address(0)) {
            // External oracle integration would go here
            emit ProofVerificationRequested(
                taskId,
                rivalzOracleAddress,
                proof.proofBundleHash,
                block.timestamp
            );
        } else {
            // Use internal verification for demo
            _performInternalVerification(taskId);
        }
    }
    
    /**
     * @dev Perform internal verification (for demo purposes)
     * @param taskId Task to verify
     */
    function _performInternalVerification(uint256 taskId) internal {
        ProofSubmission storage proof = proofSubmissions[taskId];
        VerificationCriteria memory criteria = taskCriteria[taskId];
        
        bool isValid = true;
        string memory result = "Verification passed";
        
        // Basic validation checks
        if (criteria.requiresGPSProof && proof.waypointsHash == bytes32(0)) {
            isValid = false;
            result = "GPS waypoints required but not provided";
        }
        
        if (criteria.requiresImageProof && proof.imageHashes.length < criteria.minImageCount) {
            isValid = false;
            result = "Insufficient image proofs provided";
        }
        
        // Time validation
        uint256 taskDuration = proof.completionTime - proof.submissionTime + 300; // Add buffer
        if (taskDuration > criteria.maxCompletionTime) {
            isValid = false;
            result = "Task completed outside time limit";
        }
        
        _completeVerification(taskId, isValid, result);
    }
    
    /**
     * @dev Complete verification process (called by oracle or internal verification)
     * @param taskId Task being verified
     * @param success Whether verification passed
     * @param resultMessage Verification result message
     */
    function _completeVerification(
        uint256 taskId,
        bool success,
        string memory resultMessage
    ) internal {
        ProofSubmission storage proof = proofSubmissions[taskId];
        require(proof.state == ProofState.VERIFYING, "Invalid proof state");
        
        proof.state = success ? ProofState.VERIFIED : ProofState.REJECTED;
        proof.verificationResult = resultMessage;
        
        // Notify task auction contract of result
        taskAuction.submitTaskCompletion(
            taskId,
            proof.robot,
            success,
            proof.proofBundleHash
        );
        
        if (success) {
            emit ProofVerified(taskId, proof.robot, true, resultMessage, block.timestamp);
        } else {
            emit VerificationFailed(taskId, proof.robot, resultMessage, block.timestamp);
        }
    }
    
    /**
     * @dev Oracle callback for verification result (Rivalz ADCS integration)
     * @param taskId Task that was verified
     * @param success Verification result
     * @param resultData Additional verification data
     */
    function oracleVerificationCallback(
        uint256 taskId,
        bool success,
        bytes calldata resultData
    ) external onlyRole(ORACLE_ROLE) {
        ProofSubmission storage proof = proofSubmissions[taskId];
        require(proof.state == ProofState.VERIFYING, "Invalid proof state");
        
        string memory resultMessage = success ? "Oracle verification passed" : "Oracle verification failed";
        
        // Parse additional result data if needed
        if (resultData.length > 0) {
            resultMessage = string(resultData);
        }
        
        _completeVerification(taskId, success, resultMessage);
    }
    
    /**
     * @dev Handle verification timeout
     * @param taskId Task that timed out during verification
     */
    function handleVerificationTimeout(uint256 taskId) external onlyRole(DEFAULT_ADMIN_ROLE) {
        ProofSubmission storage proof = proofSubmissions[taskId];
        require(proof.state == ProofState.VERIFYING, "Invalid proof state");
        require(
            block.timestamp > proof.submissionTime + verificationTimeout,
            "Verification not yet timed out"
        );
        
        proof.state = ProofState.EXPIRED;
        proof.verificationResult = "Verification timed out";
        
        // Treat timeout as failure
        taskAuction.submitTaskCompletion(
            taskId,
            proof.robot,
            false,
            proof.proofBundleHash
        );
        
        emit VerificationFailed(taskId, proof.robot, "Verification timeout", block.timestamp);
    }
    
    /**
     * @dev Verify proof hash against stored data (utility function)
     * @param taskId Task to verify hash for
     * @param providedHash Hash to verify
     */
    function verifyProofHash(uint256 taskId, bytes32 providedHash) external view returns (bool) {
        ProofSubmission memory proof = proofSubmissions[taskId];
        return proof.proofBundleHash == providedHash;
    }
    
    /**
     * @dev Get proof submission details
     * @param taskId Task to get proof for
     */
    function getProofSubmission(uint256 taskId) external view returns (
        address robot,
        bytes32 waypointsHash,
        bytes32[] memory imageHashes,
        uint256 submissionTime,
        ProofState state,
        string memory verificationResult
    ) {
        ProofSubmission memory proof = proofSubmissions[taskId];
        require(proof.robot != address(0), "No proof submission found");
        
        return (
            proof.robot,
            proof.waypointsHash,
            proof.imageHashes,
            proof.submissionTime,
            proof.state,
            proof.verificationResult
        );
    }
    
    /**
     * @dev Get verification criteria for task
     * @param taskId Task to get criteria for
     */
    function getVerificationCriteria(uint256 taskId) external view returns (
        uint256[2] memory requiredLocation,
        uint256 locationTolerance,
        uint256 maxCompletionTime,
        uint256 minImageCount,
        bool requiresGPS,
        bool requiresImages
    ) {
        VerificationCriteria memory criteria = taskCriteria[taskId];
        return (
            criteria.requiredLocation,
            criteria.locationTolerance,
            criteria.maxCompletionTime,
            criteria.minImageCount,
            criteria.requiresGPSProof,
            criteria.requiresImageProof
        );
    }
    
    /**
     * @dev Set Rivalz oracle address
     * @param _oracleAddress Address of the Rivalz ADCS oracle
     */
    function setRivalzOracle(address _oracleAddress) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_oracleAddress != address(0), "Invalid oracle address");
        rivalzOracleAddress = _oracleAddress;
        _grantRole(ORACLE_ROLE, _oracleAddress);
    }
    
    /**
     * @dev Update verification timeout
     * @param _timeout New timeout in seconds
     */
    function setVerificationTimeout(uint256 _timeout) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_timeout > 0 && _timeout <= 300, "Invalid timeout"); // Max 5 minutes
        verificationTimeout = _timeout;
    }
    
    /**
     * @dev Manual verification trigger (admin only, for testing)
     * @param taskId Task to verify
     * @param success Verification result
     * @param resultMessage Result message
     */
    function manualVerification(
        uint256 taskId,
        bool success,
        string calldata resultMessage
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        ProofSubmission storage proof = proofSubmissions[taskId];
        require(proof.robot != address(0), "No proof submission found");
        require(proof.state == ProofState.SUBMITTED || proof.state == ProofState.VERIFYING, "Invalid state");
        
        proof.state = ProofState.VERIFYING;
        _completeVerification(taskId, success, resultMessage);
    }
}