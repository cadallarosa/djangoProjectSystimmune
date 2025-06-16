const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    NodeClass
} = require("node-opcua");
const fs = require("fs");
const path = require("path");
const express = require("express");
const cors = require("cors");
const {insertAktaNodeIds, resultIdExists, batchInsertAktaNodeIds} = require('./DatabaseManagerWithTunnel.js');
const {v5: uuidv5} = require('uuid');
const {createSelfSignedCertificate} = require("node-opcua-crypto");
const os = require("os");
const axios = require("axios");

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static("html"));

// Enhanced configuration
const config = {
    server: {
        host: "0.0.0.0",
        port: 3000
    },
    opcua: {
        endpointUrl: "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer",
        maxConcurrentConnections: 1, // Server limitation
        connectionPoolSize: 1,
        requestTimeout: 30000,
        sessionTimeout: 300000,
        reconnectDelay: 5000,
        maxRetries: 3
    },
    traversal: {
        batchSize: 25, // Smaller batches for slow server
        maxDepth: 50,
        checkpointInterval: 10, // More frequent checkpoints
        pauseBetweenRequests: 500, // Add delays to prevent overwhelming
        adaptiveDelay: true, // Increase delay on errors
        cacheResults: true,
        persistProgress: true
    },
    database: {
        batchSize: 50,
        flushInterval: 30000, // Flush every 30 seconds
        maxRetries: 3
    }
};

// Certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

// Enhanced Connection Manager with Queue System
class OPCConnectionManager {
    constructor() {
        this.client = null;
        this.session = null;
        this.isConnected = false;
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.consecutiveErrors = 0;
        this.dynamicDelay = config.traversal.pauseBetweenRequests;
        this.lastRequestTime = 0;
        this.healthScore = 100; // 0-100, affects request handling
    }

    createClient() {
        return OPCUAClient.create({
            applicationName: "Enhanced OPCUA Browser",
            applicationUri: `urn:${os.hostname()}:EnhancedOpcUaClient`,
            securityMode: MessageSecurityMode.SignAndEncrypt,
            securityPolicy: SecurityPolicy.Basic256Sha256,
            certificateFile: OWN_CERT_PATH,
            privateKeyFile: OWN_KEY_PATH,
            endpointMustExist: false,
            connectionStrategy: {
                initialDelay: 2000,
                maxRetry: config.opcua.maxRetries,
                maxDelay: 30000,
                randomisationFactor: 0.3
            },
            keepAliveInterval: 10000,
            keepAliveTimeout: 30000,
            defaultSecureTokenLifetime: config.opcua.sessionTimeout,
            transactionTimeout: config.opcua.requestTimeout
        });
    }

    async connect() {
        if (this.isConnected) return true;

        try {
            console.log('🔌 Connecting to OPC UA server...');
            this.client = this.createClient();
            await this.client.connect(config.opcua.endpointUrl);

            this.session = await this.client.createSession({
                userName: "OPCuser",
                password: "OPCuser_710l"
            });

            this.isConnected = true;
            this.consecutiveErrors = 0;
            this.healthScore = Math.min(100, this.healthScore + 10);

            console.log('✅ OPC UA connection established');
            return true;
        } catch (error) {
            console.error('❌ Connection failed:', error.message);
            this.isConnected = false;
            this.consecutiveErrors++;
            this.healthScore = Math.max(0, this.healthScore - 20);
            throw error;
        }
    }

    async disconnect() {
        try {
            if (this.session) {
                await this.session.close();
                this.session = null;
            }
            if (this.client) {
                await this.client.disconnect();
                this.client = null;
            }
            this.isConnected = false;
            console.log('🔌 Disconnected from OPC UA server');
        } catch (error) {
            console.error('⚠️ Disconnect error:', error.message);
        }
    }

    // Queue-based request management
    async queueRequest(operation, ...args) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({
                operation,
                args,
                resolve,
                reject,
                timestamp: Date.now()
            });
            this.processQueue();
        });
    }

    async processQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) return;

        this.isProcessingQueue = true;

        while (this.requestQueue.length > 0) {
            const request = this.requestQueue.shift();

            try {
                // Ensure connection
                if (!this.isConnected) {
                    await this.connect();
                }

                // Adaptive delay based on server health
                await this.waitForNextRequest();

                // Execute request with timeout
                const result = await Promise.race([
                    this[request.operation](...request.args),
                    new Promise((_, reject) =>
                        setTimeout(() => reject(new Error('Request timeout')), config.opcua.requestTimeout)
                    )
                ]);

                request.resolve(result);
                this.consecutiveErrors = 0;
                this.healthScore = Math.min(100, this.healthScore + 1);

            } catch (error) {
                console.error(`❌ Request failed: ${error.message}`);
                this.consecutiveErrors++;
                this.healthScore = Math.max(0, this.healthScore - 5);

                // Implement exponential backoff
                if (this.consecutiveErrors > 2) {
                    this.dynamicDelay = Math.min(5000, this.dynamicDelay * 1.5);
                    console.log(`⏳ Increasing delay to ${this.dynamicDelay}ms due to errors`);
                }

                // Attempt reconnection on session errors
                if (error.message.includes('session') || error.message.includes('connection')) {
                    this.isConnected = false;
                }

                request.reject(error);
            }
        }

        this.isProcessingQueue = false;
    }

    async waitForNextRequest() {
        const timeSinceLastRequest = Date.now() - this.lastRequestTime;
        const requiredDelay = this.dynamicDelay;

        if (timeSinceLastRequest < requiredDelay) {
            const waitTime = requiredDelay - timeSinceLastRequest;
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }

        this.lastRequestTime = Date.now();
    }

    // Core OPC UA operations
    async _browseNode(nodeId) {
        if (!this.session) throw new Error('No active session');

        return await this.session.browse({
            nodeId: nodeId,
            referenceTypeId: "HierarchicalReferences",
            browseDirection: "Forward",
            includeSubtypes: true,
            nodeClassMask: 0,
            resultMask: 0x3F
        });
    }

    // Public interface
    async browseNode(nodeId) {
        return this.queueRequest('_browseNode', nodeId);
    }

    getHealthStatus() {
        return {
            isConnected: this.isConnected,
            healthScore: this.healthScore,
            consecutiveErrors: this.consecutiveErrors,
            queueLength: this.requestQueue.length,
            dynamicDelay: this.dynamicDelay
        };
    }
}

// Enhanced Traversal Manager with Progress Persistence
class EnhancedTraversalManager {
    constructor() {
        this.connectionManager = new OPCConnectionManager();
        this.progressFile = 'traversal_progress.json';
        this.cacheFile = 'node_cache.json';
        this.resetProgress();
        this.loadProgress();
        this.loadCache();
    }

    resetProgress() {
        this.progress = {
            status: 'idle',
            startTime: null,
            endTime: null,
            totalNodes: 0,
            processedNodes: 0,
            discoveredVariables: 0,
            insertedRecords: 0,
            currentPath: '',
            errors: [],
            checkpoints: [],
            lastCheckpoint: Date.now(),
            processedPaths: new Set(),
            skippedPaths: new Set()
        };
        this.isRunning = false;
        this.shouldStop = false;
        this.shouldPause = false;
        this.dbBatch = [];
        this.nodeCache = new Map();
    }

    saveProgress() {
        try {
            const progressData = {
                ...this.progress,
                processedPaths: Array.from(this.progress.processedPaths),
                skippedPaths: Array.from(this.progress.skippedPaths)
            };
            fs.writeFileSync(this.progressFile, JSON.stringify(progressData, null, 2));
        } catch (error) {
            console.error('⚠️ Failed to save progress:', error.message);
        }
    }

    loadProgress() {
        try {
            if (fs.existsSync(this.progressFile)) {
                const data = JSON.parse(fs.readFileSync(this.progressFile, 'utf8'));
                this.progress = {
                    ...data,
                    processedPaths: new Set(data.processedPaths || []),
                    skippedPaths: new Set(data.skippedPaths || [])
                };
                console.log(`📂 Loaded progress: ${this.progress.processedNodes} nodes processed`);
            }
        } catch (error) {
            console.error('⚠️ Failed to load progress:', error.message);
        }
    }

    saveCache() {
        try {
            const cacheData = Array.from(this.nodeCache.entries());
            fs.writeFileSync(this.cacheFile, JSON.stringify(cacheData, null, 2));
        } catch (error) {
            console.error('⚠️ Failed to save cache:', error.message);
        }
    }

    loadCache() {
        try {
            if (fs.existsSync(this.cacheFile)) {
                const data = JSON.parse(fs.readFileSync(this.cacheFile, 'utf8'));
                this.nodeCache = new Map(data);
                console.log(`💾 Loaded cache: ${this.nodeCache.size} nodes`);
            }
        } catch (error) {
            console.error('⚠️ Failed to load cache:', error.message);
        }
    }

    async start(rootPaths) {
        if (this.isRunning) {
            throw new Error('Traversal already in progress');
        }

        this.isRunning = true;
        this.shouldStop = false;
        this.shouldPause = false;
        this.progress.status = 'starting';
        this.progress.startTime = new Date();

        console.log('🚀 Starting enhanced traversal...');

        try {
            await this.connectionManager.connect();

            // Use breadth-first search with intelligent queuing
            const queue = [...rootPaths];
            let currentLevel = 0;

            while (queue.length > 0 && !this.shouldStop) {
                if (this.shouldPause) {
                    await this.waitForResume();
                }

                const batchSize = Math.min(config.traversal.batchSize, queue.length);
                const currentBatch = queue.splice(0, batchSize);

                console.log(`📊 Level ${currentLevel}: Processing batch of ${currentBatch.length} nodes`);
                this.progress.status = `Processing level ${currentLevel}`;

                const newNodes = await this.processBatch(currentBatch);
                queue.push(...newNodes);

                currentLevel++;
                this.createCheckpoint();

                // Flush database batch periodically
                if (this.dbBatch.length >= config.database.batchSize) {
                    await this.flushDatabaseBatch();
                }
            }

            // Final flush
            await this.flushDatabaseBatch();

            this.progress.status = 'completed';
            this.progress.endTime = new Date();

            console.log(`✅ Traversal completed: ${this.progress.discoveredVariables} variables found`);

        } catch (error) {
            this.progress.status = 'error';
            this.progress.errors.push(error.message);
            console.error('❌ Traversal error:', error);
            throw error;
        } finally {
            this.isRunning = false;
            await this.connectionManager.disconnect();
            this.saveProgress();
            this.saveCache();
        }
    }

    async processBatch(nodes) {
        const newNodes = [];

        for (const nodeId of nodes) {
            if (this.shouldStop) break;

            try {
                this.progress.currentPath = nodeId;
                this.progress.processedNodes++;

                // Check cache first
                if (this.nodeCache.has(nodeId)) {
                    const cachedResult = this.nodeCache.get(nodeId);
                    newNodes.push(...cachedResult.childNodes);
                    continue;
                }

                const result = await this.processNode(nodeId);
                if (result.childNodes.length > 0) {
                    newNodes.push(...result.childNodes);
                }

                // Cache the result
                this.nodeCache.set(nodeId, result);

            } catch (error) {
                console.error(`❌ Error processing ${nodeId}:`, error.message);
                this.progress.errors.push(`${nodeId}: ${error.message}`);
            }
        }

        return newNodes;
    }

    async processNode(nodeId) {
        // Skip if already processed
        if (this.progress.processedPaths.has(nodeId)) {
            return { childNodes: [] };
        }

        const browseResult = await this.connectionManager.browseNode(nodeId);

        if (!browseResult.references || browseResult.references.length === 0) {
            return { childNodes: [] };
        }

        const variables = browseResult.references.filter(ref => ref.nodeClass === NodeClass.Variable);
        const folders = browseResult.references.filter(ref => ref.nodeClass === NodeClass.Object);

        // Process variables if found
        if (variables.length > 0) {
            await this.processVariables(variables, nodeId);
        }

        // Mark as processed
        this.progress.processedPaths.add(nodeId);

        // Return child folders for next level
        return {
            childNodes: folders.map(ref => ref.nodeId.toString())
        };
    }

    async processVariables(variables, parentPath) {
        const excludedPatterns = [
            'UV 3_0', 'UV 2_0', '% Cond', 'System linear flow',
            'Cond temp', 'Sample linear flow', 'Conc Q1', 'Conc Q2',
            'Conc Q3', 'Conc Q4', 'Frac temp', 'UV cell path length',
            'Ratio UV2/UV1', 'Sample flow (CV/h)', 'System flow (CV/h)'
        ];

        const resultGroups = {};

        for (const ref of variables) {
            const displayName = ref.displayName.text.toString();
            if (excludedPatterns.some(p => displayName.includes(p))) continue;

            const nodeId = ref.nodeId.toString();
            const lastSlash = nodeId.lastIndexOf('/');
            const resultPath = lastSlash !== -1 ? nodeId.slice(0, lastSlash) : parentPath;
            const variableName = nodeId.slice(lastSlash + 1);

            if (!resultGroups[resultPath]) {
                resultGroups[resultPath] = [];
            }
            resultGroups[resultPath].push({ nodeId, variableName });
        }

        // Create database records
        for (const [resultPath, vars] of Object.entries(resultGroups)) {
            await this.createDatabaseRecord(resultPath, vars);
        }

        this.progress.discoveredVariables += variables.length;
    }

    async createDatabaseRecord(resultPath, variables) {
        const lookup = (vars, keyword) => {
            const match = vars.find(v => v.variableName.toLowerCase().includes(keyword.toLowerCase()));
            return match ? match.nodeId : null;
        };

        const runLog = lookup(variables, "Run Log");
        if (!runLog) return;

        const NAMESPACE = '2f1b9874-5bcd-4f66-a1c0-07f12c0aeb3a';
        const pathOnly = runLog.split(':').slice(0, -2).join(':');
        const resultId = uuidv5(pathOnly, NAMESPACE);

        const data = {
            result_id: resultId,
            run_log: runLog,
            fraction: lookup(variables, "Fraction"),
            uv_1: lookup(variables, "UV 1_280"),
            uv_2: lookup(variables, "UV 2_280"),
            uv_3: lookup(variables, "UV 3_280"),
            cond: lookup(variables, "Cond"),
            conc_b: lookup(variables, "Conc B"),
            ph: lookup(variables, "pH"),
            system_flow: lookup(variables, "System Flow"),
            system_pressure: lookup(variables, "System Pressure"),
            sample_flow: lookup(variables, "Sample Flow"),
            sample_pressure: lookup(variables, "Sample Pressure"),
            prec_pressure: lookup(variables, "PreC Pressure"),
            deltac_pressure: lookup(variables, "DeltaC Pressure"),
            postc_pressure: lookup(variables, "PostC Pressure")
        };

        this.dbBatch.push(data);
    }

    async flushDatabaseBatch() {
        if (this.dbBatch.length === 0) return;

        console.log(`💾 Flushing ${this.dbBatch.length} database records`);

        try {
            await batchInsertAktaNodeIds(this.dbBatch);
            this.progress.insertedRecords += this.dbBatch.length;
            this.dbBatch = [];
            console.log(`✅ Database batch flushed successfully`);
        } catch (error) {
            console.error('❌ Database flush error:', error);
            this.progress.errors.push(`Database error: ${error.message}`);
        }
    }

    createCheckpoint() {
        const now = Date.now();
        if (now - this.progress.lastCheckpoint > config.traversal.checkpointInterval * 1000) {
            this.progress.checkpoints.push({
                timestamp: now,
                processedNodes: this.progress.processedNodes,
                discoveredVariables: this.progress.discoveredVariables,
                insertedRecords: this.progress.insertedRecords
            });
            this.progress.lastCheckpoint = now;
            this.saveProgress();

            const health = this.connectionManager.getHealthStatus();
            console.log(`📊 Checkpoint - Nodes: ${this.progress.processedNodes}, Variables: ${this.progress.discoveredVariables}, Health: ${health.healthScore}%`);
        }
    }

    async waitForResume() {
        console.log('⏸️ Traversal paused, waiting for resume...');
        while (this.shouldPause && !this.shouldStop) {
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        console.log('▶️ Traversal resumed');
    }

    pause() {
        this.shouldPause = true;
        this.progress.status = 'paused';
    }

    resume() {
        this.shouldPause = false;
        this.progress.status = 'running';
    }

    async stop() {
        this.shouldStop = true;
        this.progress.status = 'stopping';

        // Flush any remaining data
        await this.flushDatabaseBatch();

        this.isRunning = false;
        this.progress.status = 'stopped';
        this.progress.endTime = new Date();

        await this.connectionManager.disconnect();
        this.saveProgress();
        this.saveCache();
    }

    getProgress() {
        const health = this.connectionManager.getHealthStatus();

        return {
            ...this.progress,
            isRunning: this.isRunning,
            serverHealth: health,
            processedPaths: undefined, // Don't send large sets over network
            skippedPaths: undefined
        };
    }
}

// Initialize managers
const traversalManager = new EnhancedTraversalManager();

// API Routes
app.get('/api/health', async (req, res) => {
    try {
        const health = traversalManager.connectionManager.getHealthStatus();
        res.json({
            status: health.isConnected ? 'connected' : 'disconnected',
            health: health,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            error: error.message
        });
    }
});

app.post('/api/traverse/start', async (req, res) => {
    if (traversalManager.isRunning) {
        return res.status(400).json({
            success: false,
            error: 'Traversal already in progress'
        });
    }

    try {
        const rootPaths = [
            "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods"
        ];

        // Start traversal in background
        traversalManager.start(rootPaths).catch(error => {
            console.error('Background traversal error:', error);
        });

        res.json({
            success: true,
            message: 'Enhanced traversal started'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/api/traverse/stop', async (req, res) => {
    try {
        await traversalManager.stop();
        res.json({
            success: true,
            message: 'Traversal stopped'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/api/traverse/pause', (req, res) => {
    traversalManager.pause();
    res.json({
        success: true,
        message: 'Traversal paused'
    });
});

app.post('/api/traverse/resume', (req, res) => {
    traversalManager.resume();
    res.json({
        success: true,
        message: 'Traversal resumed'
    });
});

app.get('/api/traverse/progress', (req, res) => {
    const progress = traversalManager.getProgress();
    res.json(progress);
});

// Serve the HTML interface
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Start server
app.listen(config.server.port, config.server.host, () => {
    console.log(`🌐 Enhanced OPC UA Browser running on http://${config.server.host}:${config.server.port}`);
    console.log('🔧 Enhanced features:');
    console.log('   - Intelligent request queuing');
    console.log('   - Progress persistence');
    console.log('   - Node caching');
    console.log('   - Adaptive error handling');
    console.log('   - Health monitoring');
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('🛑 Shutting down gracefully...');
    await traversalManager.stop();
    process.exit(0);
});

module.exports = { traversalManager, app };