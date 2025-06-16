const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    NodeClass,
    TimestampsToReturn
} = require("node-opcua");
const fs = require("fs");
const path = require("path");
const express = require("express");
const cors = require("cors");
const {insertAktaNodeIds, resultIdExists} = require('./DatabaseManagerWithTunnel.js');
const {v5: uuidv5} = require('uuid');
const {createSelfSignedCertificate} = require("node-opcua-crypto");
const os = require("os");
const axios = require("axios");

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static("html"));

const HOST = "0.0.0.0";
const PORT = 3000;
const SELECTED_VARIABLES_FILE = "variables.json";

// Initialize variables file
fs.writeFileSync(SELECTED_VARIABLES_FILE, JSON.stringify([]));

const FOLDERS_TO_TRAVERSE = [
    "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods",
];

// Certificate configuration (unchanged)
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

const endpointUrl = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer";

// Optimized connection pool
class OPCConnectionPool {
    constructor(maxConnections = 3) {
        this.maxConnections = maxConnections;
        this.connections = [];
        this.activeConnections = 0;
        this.queue = [];
    }

    createClient() {
        return OPCUAClient.create({
            applicationName: "OPCUA Browser",
            applicationUri: `urn:SI-CF8MJX3:UnifiedAutomation:UaExpert`,
            securityMode: MessageSecurityMode.SignAndEncrypt,
            securityPolicy: SecurityPolicy.Basic256Sha256,
            certificateFile: OWN_CERT_PATH,
            privateKeyFile: OWN_KEY_PATH,
            endpointMustExist: false,
            connectionStrategy: {
                initialDelay: 1000,
                maxRetry: 3,
                maxDelay: 10000,
                randomisationFactor: 0.1
            },
            keepAliveInterval: 10000,
            keepAliveTimeout: 30000,
            defaultSecureTokenLifetime: 3600000,
            transactionTimeout: 30000
        });
    }

    async getConnection() {
        if (this.connections.length > 0) {
            return this.connections.pop();
        }

        if (this.activeConnections < this.maxConnections) {
            this.activeConnections++;
            const client = this.createClient();
            await client.connect(endpointUrl);
            const session = await client.createSession({
                userName: "OPCuser",
                password: "OPCuser_710l"
            });
            return { client, session };
        }

        // Wait for available connection
        return new Promise((resolve) => {
            this.queue.push(resolve);
        });
    }

    async releaseConnection(connection) {
        if (this.queue.length > 0) {
            const resolve = this.queue.shift();
            resolve(connection);
        } else {
            this.connections.push(connection);
        }
    }

    async cleanup() {
        // Close all pooled connections
        for (const conn of this.connections) {
            try {
                await conn.session.close();
                await conn.client.disconnect();
            } catch (err) {
                console.error('Error cleaning up connection:', err);
            }
        }
        this.connections = [];
        this.activeConnections = 0;
    }
}

// Optimized traversal manager with better algorithms
class OptimizedTraversalManager {
    constructor() {
        // Initialize properties first
        this.connectionPool = new OPCConnectionPool(2);
        this.batchSize = 50; // Process nodes in batches
        this.concurrentLimit = 3; // Limit concurrent operations
        this.excludedPatterns = [
            'UV 3_0', 'UV 2_0', '% Cond', 'System linear flow',
            'Cond temp', 'Sample linear flow', 'Conc Q1', 'Conc Q2',
            'Conc Q3', 'Conc Q4', 'Frac temp', 'UV cell path length',
            'Ratio UV2/UV1', 'Sample flow (CV/h)', 'System flow (CV/h)'
        ];
        this.skippedFolders = ["FracPoolTables", "Documentation", "PeakTables"];
        this.endBranchVariable = "UV 1_280";
        this.NAMESPACE = '2f1b9874-5bcd-4f66-a1c0-07f12c0aeb3a';

        // Database batch processing
        this.dbBatchSize = 100;
        this.dbBatch = [];
        this.processedResults = new Set(); // Avoid duplicates

        // Initialize progress after properties are set
        this.resetProgress();
    }

    resetProgress() {
        this.progress = {
            totalNodes: 0,
            processedNodes: 0,
            variablesFound: 0,
            resultsProcessed: 0,
            startTime: Date.now(),
            lastUpdate: Date.now(),
            status: 'idle',
            currentOperation: '',
            errors: []
        };
        this.isRunning = false;
        this.shouldStop = false;
        this.dbBatch = [];

        // Only clear if it exists
        if (this.processedResults) {
            this.processedResults.clear();
        } else {
            this.processedResults = new Set();
        }
    }

    // Breadth-first traversal with batching
    async traverseOptimized(startingPaths) {
        if (this.isRunning) {
            throw new Error('Traversal already in progress');
        }

        this.isRunning = true;
        this.shouldStop = false;
        this.resetProgress();
        this.progress.status = 'running';

        console.log(`🚀 Starting optimized traversal of ${startingPaths.length} paths`);

        try {
            // Use breadth-first search with batching
            let currentQueue = [...startingPaths];
            let nextQueue = [];
            let level = 0;

            while (currentQueue.length > 0 && !this.shouldStop) {
                console.log(`📊 Level ${level}: Processing ${currentQueue.length} nodes`);
                this.progress.currentOperation = `Processing level ${level}`;

                // Process current level in batches
                const batches = this.createBatches(currentQueue, this.batchSize);

                for (const batch of batches) {
                    if (this.shouldStop) break;

                    const childNodes = await this.processBatchConcurrent(batch);
                    nextQueue.push(...childNodes);
                }

                // Flush database batch if needed
                await this.flushDatabaseBatch();

                currentQueue = nextQueue;
                nextQueue = [];
                level++;

                this.updateProgress();
            }

            // Final database flush
            await this.flushDatabaseBatch(true);

            this.progress.status = 'completed';
            console.log(`✅ Traversal completed: ${this.progress.variablesFound} variables, ${this.progress.resultsProcessed} results`);

        } catch (error) {
            this.progress.status = 'error';
            this.progress.errors.push(error.message);
            console.error('❌ Traversal error:', error);
            throw error;
        } finally {
            this.isRunning = false;
            await this.connectionPool.cleanup();
        }
    }

    createBatches(items, batchSize) {
        const batches = [];
        for (let i = 0; i < items.length; i += batchSize) {
            batches.push(items.slice(i, i + batchSize));
        }
        return batches;
    }

    async processBatchConcurrent(batch) {
        const semaphore = new Array(this.concurrentLimit).fill(null);
        const childNodes = [];

        const processBatchItem = async (nodeId, index) => {
            const connection = await this.connectionPool.getConnection();

            try {
                const result = await this.processNode(connection.session, nodeId);
                if (result.childNodes) {
                    childNodes.push(...result.childNodes);
                }
                this.progress.processedNodes++;
            } catch (error) {
                console.error(`Error processing node ${nodeId}:`, error.message);
                this.progress.errors.push(`Node ${nodeId}: ${error.message}`);
            } finally {
                await this.connectionPool.releaseConnection(connection);
                semaphore[index % this.concurrentLimit] = null;
            }
        };

        // Process batch with concurrency limit
        const promises = batch.map((nodeId, index) => {
            return new Promise(async (resolve) => {
                // Wait for semaphore slot
                while (semaphore[index % this.concurrentLimit] !== null) {
                    await new Promise(r => setTimeout(r, 10));
                }
                semaphore[index % this.concurrentLimit] = true;

                await processBatchItem(nodeId, index);
                resolve();
            });
        });

        await Promise.all(promises);
        return childNodes;
    }

    async processNode(session, nodeId) {
        try {
            // Check if folder should be skipped
            const nodeName = nodeId.split('/').pop() || nodeId;
            if (this.skippedFolders.some(skipFolder => nodeName.includes(skipFolder))) {
                return { childNodes: [] };
            }

            const browseResult = await session.browse({
                nodeId: nodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: "Forward",
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F
            });

            if (!browseResult.references || browseResult.references.length === 0) {
                return { childNodes: [] };
            }

            const variables = browseResult.references.filter(ref => ref.nodeClass === NodeClass.Variable);
            const folders = browseResult.references.filter(ref => ref.nodeClass === NodeClass.Object);

            // Check for end branch variable
            const hasEndBranch = variables.some(ref =>
                ref.browseName.toString() === this.endBranchVariable
            );

            if (hasEndBranch) {
                console.log(`🛑 Skipping branch at ${nodeName} (found end branch variable)`);
                return { childNodes: [] };
            }

            // Process variables for this node
            await this.processVariablesOptimized(variables, nodeId);

            // Return child folder nodes for next level
            const childNodes = folders
                .filter(ref => !this.skippedFolders.some(skip =>
                    ref.browseName.toString().includes(skip)))
                .map(ref => ref.nodeId.toString());

            return { childNodes };

        } catch (error) {
            console.error(`Error browsing node ${nodeId}:`, error);
            return { childNodes: [] };
        }
    }

    async processVariablesOptimized(variables, parentNodeId) {
        if (variables.length === 0) return;

        const seenNodeIds = new Set();
        const resultGroups = {};

        // Group variables by result path
        for (const ref of variables) {
            const displayName = ref.displayName.text.toString();
            if (this.excludedPatterns.some(p => displayName.includes(p))) continue;

            const nodeId = ref.nodeId.toString();
            if (seenNodeIds.has(nodeId)) continue;

            const lastSlash = nodeId.lastIndexOf('/');
            const resultPath = lastSlash !== -1 ? nodeId.slice(0, lastSlash) : parentNodeId;
            const variableName = nodeId.slice(lastSlash + 1);

            seenNodeIds.add(nodeId);

            if (!resultGroups[resultPath]) {
                resultGroups[resultPath] = [];
            }
            resultGroups[resultPath].push({ nodeId, variableName });
        }

        // Process each result group
        for (const [resultPath, vars] of Object.entries(resultGroups)) {
            await this.createResultRecord(resultPath, vars);
        }

        this.progress.variablesFound += variables.length;
    }

    async createResultRecord(resultPath, variables) {
        const lookup = (vars, keyword) => {
            const match = vars.find(v => v.variableName.toLowerCase().includes(keyword.toLowerCase()));
            return match ? match.nodeId : null;
        };

        const runLog = lookup(variables, "Run Log");
        if (!runLog) return; // Skip if no run log found

        const pathOnly = runLog.split(':').slice(0, -2).join(':');
        const resultId = uuidv5(pathOnly, this.NAMESPACE);

        // Check if already processed
        if (this.processedResults.has(resultId)) return;
        this.processedResults.add(resultId);

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
        this.progress.resultsProcessed++;

        // Flush batch if it's full
        if (this.dbBatch.length >= this.dbBatchSize) {
            await this.flushDatabaseBatch();
        }
    }

    async flushDatabaseBatch(force = false) {
        if (this.dbBatch.length === 0) return;
        if (!force && this.dbBatch.length < this.dbBatchSize) return;

        console.log(`💾 Flushing ${this.dbBatch.length} database records`);

        try {
            // Process database batch
            const promises = this.dbBatch.map(data => insertAktaNodeIds(data));
            await Promise.all(promises);

            console.log(`✅ Successfully processed ${this.dbBatch.length} database records`);
        } catch (error) {
            console.error('❌ Database batch error:', error);
            this.progress.errors.push(`Database batch error: ${error.message}`);
        }

        this.dbBatch = [];
    }

    updateProgress() {
        const now = Date.now();
        if (now - this.progress.lastUpdate > 2000) { // Update every 2 seconds
            const elapsed = (now - this.progress.startTime) / 1000;
            const rate = this.progress.processedNodes / elapsed;

            console.log(`📊 Progress: ${this.progress.processedNodes} nodes processed, ${this.progress.variablesFound} variables, ${rate.toFixed(1)} nodes/sec`);
            this.progress.lastUpdate = now;
        }
    }

    async stop() {
        this.shouldStop = true;
        await this.flushDatabaseBatch(true);
        await this.connectionPool.cleanup();
        this.progress.status = 'stopped';
    }

    // Browse method for HTML tree navigation
    async browseNode(session, nodeId) {
        try {
            const browseResult = await session.browse({
                nodeId: nodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: "Forward",
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F
            });

            if (!browseResult.references) return [];

            const nodes = [];
            for (const ref of browseResult.references) {
                const nodeInfo = {
                    nodeId: ref.nodeId.toString(),
                    browseName: ref.browseName.toString(),
                    displayName: ref.displayName.text.toString(),
                    nodeClass: NodeClass[ref.nodeClass],
                    isFolder: ref.nodeClass === NodeClass.Object
                };

                if (ref.nodeClass === NodeClass.Variable) {
                    try {
                        const dataValue = await session.read({
                            nodeId: ref.nodeId,
                            attributeId: AttributeIds.Value,
                            maxAge: 1000,
                            timeoutHint: 20000
                        });
                        nodeInfo.value = dataValue.value.value;
                        nodeInfo.dataType = dataValue.value.dataType.key;
                        nodeInfo.status = dataValue.statusCode.name;
                    } catch (readError) {
                        nodeInfo.value = "N/A";
                        nodeInfo.status = "ReadError";
                    }
                }

                nodes.push(nodeInfo);
            }

            return nodes;
        } catch (error) {
            console.error("Browse error:", error);
            return [];
        }
    }

    getProgress() {
        return {
            ...this.progress,
            isRunning: this.isRunning,
            elapsed: Date.now() - this.progress.startTime,
            rate: this.progress.processedNodes / ((Date.now() - this.progress.startTime) / 1000)
        };
    }
}

// Alternative: Subscription-based approach for real-time updates
class SubscriptionTraversalManager {
    constructor() {
        this.subscriptions = new Map();
        this.client = null;
        this.session = null;
    }

    async startSubscriptionMode(rootPaths) {
        console.log('🔔 Starting subscription-based monitoring...');

        this.client = this.createClient();
        await this.client.connect(endpointUrl);
        this.session = await this.client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });

        // Create subscriptions for each root path
        for (const rootPath of rootPaths) {
            await this.createSubscriptionForPath(rootPath);
        }
    }

    async createSubscriptionForPath(rootPath) {
        const subscription = await this.session.createSubscription2({
            requestedPublishingInterval: 5000,
            requestedMaxKeepAliveCount: 20,
            requestedLifetimeCount: 6000,
            maxNotificationsPerPublish: 1000,
            priority: 10
        });

        subscription.on("keepalive", () => {
            console.log(`🔔 Subscription keepalive for ${rootPath}`);
        });

        subscription.on("terminated", () => {
            console.log(`❌ Subscription terminated for ${rootPath}`);
        });

        // Monitor for new nodes/variables
        const monitoredItem = await subscription.monitor({
            nodeId: rootPath,
            attributeId: AttributeIds.Value
        }, {
            samplingInterval: 1000,
            discardOldest: true,
            queueSize: 100
        });

        monitoredItem.on("changed", (dataValue) => {
            console.log(`🔄 Change detected in ${rootPath}:`, dataValue);
            // Handle new data detection
        });

        this.subscriptions.set(rootPath, subscription);
    }

    createClient() {
        return OPCUAClient.create({
            applicationName: "OPCUA Subscription Monitor",
            applicationUri: `urn:SI-CF8MJX3:UnifiedAutomation:UaExpert`,
            securityMode: MessageSecurityMode.SignAndEncrypt,
            securityPolicy: SecurityPolicy.Basic256Sha256,
            certificateFile: OWN_CERT_PATH,
            privateKeyFile: OWN_KEY_PATH,
            endpointMustExist: false,
            connectionStrategy: {
                initialDelay: 1000,
                maxRetry: 10,
                maxDelay: 30000
            },
            keepAliveInterval: 10000
        });
    }

    async cleanup() {
        for (const subscription of this.subscriptions.values()) {
            await subscription.terminate();
        }
        this.subscriptions.clear();

        if (this.session) {
            await this.session.close();
        }
        if (this.client) {
            await this.client.disconnect();
        }
    }
}

// Initialize managers
const optimizedTraversalManager = new OptimizedTraversalManager();
const subscriptionManager = new SubscriptionTraversalManager();

// Updated API endpoints with HTML compatibility
app.post('/api/traverse/start-optimized', async (req, res) => {
    try {
        console.log("🚀 Starting optimized traversal...");
        await optimizedTraversalManager.traverseOptimized(FOLDERS_TO_TRAVERSE);

        // Trigger Django import
        try {
            const djangoResponse = await axios.get("http://localhost:8000/plotly_integration/api/trigger-opc-import/");
            console.log("✅ Django OPC import triggered");
        } catch (djangoErr) {
            console.error("❌ Django trigger failed:", djangoErr.message);
        }

        res.json({
            success: true,
            message: "Optimized traversal completed",
            stats: optimizedTraversalManager.getProgress()
        });
    } catch (error) {
        console.error("❌ Optimized traversal error:", error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/api/traverse/start-subscription', async (req, res) => {
    try {
        await subscriptionManager.startSubscriptionMode(FOLDERS_TO_TRAVERSE);
        res.json({
            success: true,
            message: "Subscription monitoring started"
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.get('/api/traverse/progress-optimized', (req, res) => {
    res.json(optimizedTraversalManager.getProgress());
});

app.post('/api/traverse/stop-optimized', async (req, res) => {
    try {
        await optimizedTraversalManager.stop();
        res.json({ success: true, message: "Optimized traversal stopped" });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// HTML Compatibility endpoints - map to optimized versions
app.post('/api/traverse/start-auto', async (req, res) => {
    if (optimizedTraversalManager.isRunning) {
        return res.status(400).json({
            success: false,
            error: "Traversal already in progress"
        });
    }

    try {
        console.log("🚀 Starting auto traversal (using optimized version)...");
        console.log("🗂️ Clearing previous variables file...");
        fs.writeFileSync(SELECTED_VARIABLES_FILE, JSON.stringify([]));

        // Start optimized traversal in background
        optimizedTraversalManager.traverseOptimized(FOLDERS_TO_TRAVERSE)
            .then(async () => {
                console.log("📡 Triggering Django OPC import...");
                try {
                    const djangoResponse = await axios.get("http://localhost:8000/plotly_integration/api/trigger-opc-import/");
                    console.log("✅ Django OPC import triggered successfully");
                } catch (djangoErr) {
                    console.error("❌ Failed to contact Django OPC import endpoint:", djangoErr.message);
                }
            })
            .catch(err => {
                console.error("❌ Traversal error:", err);
            });

        res.json({
            success: true,
            message: "Optimized traversal started successfully"
        });

    } catch (err) {
        console.error("❌ Start error:", err);
        res.status(500).json({
            success: false,
            error: err.message
        });
    }
});

app.get("/api/progress", (req, res) => {
    const progress = optimizedTraversalManager.getProgress();

    // Convert to format expected by HTML
    const htmlCompatibleProgress = {
        active: progress.isRunning,
        complete: progress.status === 'completed',
        stats: {
            totalFolders: Math.max(progress.totalNodes, progress.processedNodes),
            completedFolders: progress.processedNodes,
            variablesFound: progress.variablesFound,
            currentPath: progress.currentOperation,
            status: progress.status,
            pendingFolders: Math.max(0, progress.totalNodes - progress.processedNodes),
            startTime: new Date(progress.startTime),
            endTime: progress.status === 'completed' ? new Date() : null,
            resultsProcessed: progress.resultsProcessed
        }
    };

    res.json(htmlCompatibleProgress);
});

app.post("/api/traverse/stop", async (req, res) => {
    try {
        await optimizedTraversalManager.stop();
        console.log("⏹️ Optimized traversal stopped by user request");
        res.json({
            success: true,
            message: 'Traversal stopped'
        });
    } catch (err) {
        console.error('❌ Stop error:', err);
        res.status(500).json({
            success: false,
            error: err.message
        });
    }
});

app.post("/api/traverse/pause", (req, res) => {
    optimizedTraversalManager.shouldStop = true; // Pause by setting stop flag
    console.log("⏸️ Optimized traversal paused by user request");
    res.json({
        success: true,
        message: 'Traversal paused'
    });
});

app.post("/api/traverse/resume", (req, res) => {
    optimizedTraversalManager.shouldStop = false; // Resume by clearing stop flag
    console.log("▶️ Optimized traversal resumed by user request");
    res.json({
        success: true,
        message: 'Traversal resumed'
    });
});

// Server-Sent Events endpoint for real-time progress (HTML compatibility)
app.get("/api/traverse/progress", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const sendProgress = () => {
        const progress = optimizedTraversalManager.getProgress();

        // Convert to HTML-compatible format
        const htmlProgress = {
            active: progress.isRunning,
            complete: progress.status === 'completed',
            stats: {
                totalFolders: Math.max(progress.totalNodes, progress.processedNodes),
                completedFolders: progress.processedNodes,
                variablesFound: progress.variablesFound,
                currentPath: progress.currentOperation,
                status: progress.status,
                pendingFolders: Math.max(0, progress.totalNodes - progress.processedNodes),
                resultsProcessed: progress.resultsProcessed
            }
        };

        res.write(`data: ${JSON.stringify(htmlProgress)}\n\n`);

        if (progress.status === 'completed' || progress.status === 'error' || !progress.isRunning) {
            res.end();
        }
    };

    sendProgress();
    const interval = setInterval(sendProgress, 1000);
    req.on("close", () => clearInterval(interval));
});

// Browse endpoint for tree navigation
app.get("/api/browse", async (req, res) => {
    let session;
    let client;
    try {
        console.log("🔌 Connecting to OPC UA server for browse request...");
        const connection = await optimizedTraversalManager.connectionPool.getConnection();
        session = connection.session;

        const nodes = await optimizedTraversalManager.browseNode(
            session,
            req.query.nodeId || "ns=2;s=1:Archive/OPCuser"
        );

        await optimizedTraversalManager.connectionPool.releaseConnection(connection);

        res.json({
            success: true,
            nodes,
            timestamp: new Date().toISOString()
        });
    } catch (err) {
        console.error("❌ API Error:", err);
        res.status(500).json({
            success: false,
            error: err.message,
            code: err.code || "UNKNOWN_ERROR"
        });
    }
});

// Health check endpoint
app.get("/api/health", async (req, res) => {
    try {
        console.log("🔌 Testing OPC UA server connection...");
        const connection = await optimizedTraversalManager.connectionPool.getConnection();
        await optimizedTraversalManager.connectionPool.releaseConnection(connection);
        console.log("✅ OPC UA server is reachable");

        res.json({status: "connected", timestamp: new Date().toISOString()});
    } catch (err) {
        console.log("❌ OPC UA server is not reachable:", err.message);
        res.status(503).json({status: "disconnected", error: err.message});
    }
});

// Variables endpoint
app.get("/api/variables", (req, res) => {
    try {
        const variables = JSON.parse(fs.readFileSync(SELECTED_VARIABLES_FILE));
        res.json({
            success: true,
            count: variables.length,
            variables: variables
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            error: err.message
        });
    }
});

// Test Python endpoint
app.post("/api/test-python", async (req, res) => {
    console.log("🚀 Testing Django OPC import trigger...");

    try {
        const djangoResponse = await axios.get("http://localhost:8000/plotly_integration/api/trigger-opc-import/");

        console.log("✅ Django OPC import triggered successfully.");
        console.log("📨 Django Response:", djangoResponse.data);

        res.json({
            success: true,
            message: "Successfully triggered Django OPC import.",
            response: djangoResponse.data
        });
    } catch (error) {
        console.error("❌ Failed to trigger Django OPC import:", error.message);

        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Legacy compatibility endpoints
app.post("/api/traverse/trigger", async (req, res) => {
    // Redirect to optimized version
    return app.post('/api/traverse/start-auto')(req, res);
});

app.post("/api/traverse/cancel", async (req, res) => {
    // Redirect to stop
    return app.post('/api/traverse/stop')(req, res);
});
app.listen(PORT, 'localhost', () => {
    console.log(`🌐 Optimized OPC UA Browser running on http://localhost:${PORT}`);
    console.log(`🔧 Available traversal modes:`);
    console.log(`   - Optimized: POST /api/traverse/start-optimized`);
    console.log(`   - Subscription: POST /api/traverse/start-subscription`);
});

// Graceful shutdown
process.on("SIGINT", async () => {
    console.log("🛑 Shutting down...");
    await optimizedTraversalManager.stop();
    await subscriptionManager.cleanup();
    process.exit(0);
});