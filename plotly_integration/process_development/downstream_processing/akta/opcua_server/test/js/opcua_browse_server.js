const {
    OPCUAClient,
    MessageSecurityMode,
    SecurityPolicy,
    AttributeIds,
    NodeClass,
    TimestampsToReturn
} = require("node-opcua");
const {ReadRawModifiedDetails} = require("node-opcua-service-history");
const fs = require("fs");
const path = require("path");
const express = require("express");
const cors = require("cors");
const {exec} = require('child_process');
const {insertAktaNodeIds, resultIdExists} = require('./db_writer');
const {v5: uuidv5} = require('uuid');
const {createSelfSignedCertificate} = require("node-opcua-crypto");
const os = require("os");
const axios = require("axios");


const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static("public"));

const HOST = "0.0.0.0";
const PORT = 3000;
const SELECTED_VARIABLES_FILE = "variables.json";

// Initialize variables file
fs.writeFileSync(SELECTED_VARIABLES_FILE, JSON.stringify([]));

// Define folders to traverse
const FOLDERS_TO_TRAVERSE = [
    // "ns=2;s=6:Archive/OPCuser/Folders/LegacyData/LegacyData_Fry/PD Results and Project specific methods/SI-50E15",
    // "ns=2;s=6:Archive/OPCuser/Folders/LegacyData/LegacyData_Fry/PD Results and Project specific methods",
    // "ns=2;s=6:Archive/OPCuser/Folders/LegacyData/LegacyData_Fry/PD Results and Project specific methods/SI-50E15",
    // "ns=2;s=6:Archive/OPCuser/Folders/LegacyData/LegacyData_Farnsworth/PD Results  project specific methods",
    "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods",
    // "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/05_CLD and Upstream Screening Results"
    // Add more folders here as needed

];
// 🔧 Platform-safe certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

async function ensureCertificates() {
    if (fs.existsSync(OWN_CERT_PATH) && fs.existsSync(OWN_KEY_PATH)) {
        console.log("✅ Found existing certificate and key.");
        return;
    }

    console.log("🔐 Generating self-signed OPC UA certificate...");
    await createSelfSignedCertificate({
        applicationUri: `urn:${os.hostname()}:MyOpcUaClient`,
        subject: "/CN=MyOpcUaClient",
        privateKey: OWN_KEY_PATH,
        outputFile: OWN_CERT_PATH,
        validity: 365
    });
    console.log("✅ Certificate and key generated.");
}

const endpointUrl = "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer";
const client = OPCUAClient.create({
    applicationName: "OPCUA Browser",
    applicationUri: `urn:SI-CF8MJX3:UnifiedAutomation:UaExpert`,
    securityMode: MessageSecurityMode.SignAndEncrypt,
    securityPolicy: SecurityPolicy.Basic256Sha256,
    certificateFile: OWN_CERT_PATH,
    privateKeyFile: OWN_KEY_PATH,
    endpointMustExist: false,
    connectionStrategy: {
        initialDelay: 2000,
        maxRetry: 5,
        maxDelay: 60000,
        randomisationFactor: 0.5
    },
    // keepSessionAlive: true,
    keepAliveInterval: 5000,
    keepAliveTimeout: 60000,
    defaultSecureTokenLifetime: 3600000,
    transactionTimeout: 60000,
    timeout: 24 * 60 * 60 * 1000
});

client.on("backoff", (retry, delay) =>
    console.log(`Backoff ${retry}: retrying in ${delay}ms`));

client.on("connection_lost", () =>
    console.error("Connection lost to server"));

client.on("connection_reestablished", () =>
    console.log("Connection reestablished"));

class NodeTreeBrowser {
    constructor() {
        this.cache = new Map();
        this.cacheExpiry = 30000;
    }

    async browseChildren(session, parentNodeId) {
        try {
            const cacheKey = `${session.sessionId}-${parentNodeId}`;
            const cached = this.cache.get(cacheKey);
            if (cached && (Date.now() - cached.timestamp) < this.cacheExpiry) {
                return cached.nodes;
            }

            const nodesToBrowse = [{
                nodeId: parentNodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: "Forward",
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F
            }];

            const results = await session.browse(nodesToBrowse);
            const nodes = [];

            for (const result of results) {
                if (result.statusCode.isGood() && result.references) {
                    for (const ref of result.references) {
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
                                console.warn(`Read failed for ${ref.nodeId}: ${readError.message}`);
                            }
                        }

                        nodes.push(nodeInfo);
                    }
                }
            }

            this.cache.set(cacheKey, {
                nodes,
                timestamp: Date.now()
            });

            return nodes;
        } catch (error) {
            console.error("Browse error:", error);
            throw error;
        }
    }

    clearCache() {
        this.cache.clear();
    }
}


class TraversalManager {
    constructor() {
        this.resetProgress();
        this.shouldPause = false;
        this.isComplete = false;
        this.active = false;
        this.currentSession = null;
        this.timeout = 24 * 60 * 60 * 1000;
        this.maxDepth = 100;
        this.checkpointInterval = 2000;
        this.operationTimeout = 60000;
        this.variableBatchSize = 1000;
        this.variableBatches = [];
        this.currentBatch = [];
        this.healthCheckInterval = setInterval(() => this._healthCheck(), 30000);
        this.endBranchVariable = "UV 1_280";
        this.foundEndBranch = false;
        this.skippedFolders = ["FracPoolTables", "Documentation", "PeakTables"];
        this.maxVariablesToFind = Infinity;
        this.isTraversing = false;
    }

    resetProgress() {
        this.progress = {
            totalFolders: 0,
            completedFolders: 0,
            variablesFound: 0,
            currentPath: '',
            pendingFolders: 0,
            lastCheckpoint: new Date(),
            checkpoints: [],
            allVariables: [],
            startTime: null,
            endTime: null,
            status: 'idle',
            lastOperationDuration: 0,
            branchesSkipped: 0,
            foldersSkipped: 0
        };
        this.variableBatches = [];
        this.currentBatch = [];
        this.foundEndBranch = false;
    }

    async _healthCheck() {
        if (!this.active || !this.currentSession) return;

        try {
            if (this.currentSession.hasBeenClosed()) {
                console.log('Session closed, recreating...');
                this.currentSession = await this._recreateSession();
                return;
            }

            await this.currentSession.read({
                nodeId: "i=2255",
                attributeId: AttributeIds.Value,
                timeoutHint: 10000
            });
        } catch (err) {
            console.warn('Health check failed:', err.message);
            try {
                await client.reconnect();
                this.currentSession = await this._recreateSession();
            } catch (reconnectErr) {
                console.error('Reconnect failed:', reconnectErr);
            }
        }
    }

    async _recreateSession() {
        if (this.currentSession) {
            try {
                await this.currentSession.close();
            } catch (err) {
                console.error('Error closing old session:', err);
            }
        }

        return await client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });
    }

    async startTraversal(session, rootNodeId) {
        if (this.isTraversing) {
            throw new Error('Traversal already in progress');
        }

        this.isTraversing = true;
        this.active = true;
        this.isComplete = false;
        this.currentSession = session;
        this.resetProgress();
        this.progress.startTime = new Date();
        this.progress.status = 'running';

        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Traversal timeout')), this.timeout);
            });

            await Promise.race([
                this._traverseNode(session, rootNodeId),
                timeoutPromise
            ]);

            if (this.currentBatch.length > 0) {
                this.variableBatches.push(this.currentBatch);
                this.currentBatch = [];
            }

            this.progress.status = this.foundEndBranch ? 'complete (end branch found)' : 'complete';
            this.isComplete = true;
            return this.getVariables();
        } catch (error) {
            if (error.message.includes('SecureChannel')) {
                console.log('Reconnecting channel and retrying...');
                await client.reconnect();
                this.currentSession = await this._recreateSession();
                return this.startTraversal(this.currentSession, rootNodeId);
            }

            this.progress.status = 'error: ' + error.message;
            console.error('Traversal error:', error);
            throw error;
        } finally {
            this.progress.endTime = new Date();
            this.progress.foundEndBranch = this.foundEndBranch;
            this.active = false;
            this.isTraversing = false;
            this.resultGroups = {};
        }
    }

    async traverseMultipleFolders(session, folderPaths) {
        if (this.isTraversing) {
            throw new Error('Traversal already in progress');
        }

        this.isTraversing = true;
        this.active = true;
        this.isComplete = false;
        this.currentSession = session;
        this.resetProgress();
        this.progress.startTime = new Date();
        this.progress.status = 'running';

        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Traversal timeout')), this.timeout);
            });

            await Promise.race([
                (async () => {
                    for (const folderPath of folderPaths) {
                        if (!this.active) break;
                        await this._traverseNode(session, folderPath);
                    }
                })(),
                timeoutPromise
            ]);

            if (this.currentBatch.length > 0) {
                this.variableBatches.push(this.currentBatch);
                this.currentBatch = [];
            }

            this.progress.status = 'complete';
            this.isComplete = true;
            return this.getVariables();
        } catch (error) {
            if (error.message.includes('SecureChannel')) {
                console.log('Reconnecting channel and retrying...');
                await client.reconnect();
                this.currentSession = await this._recreateSession();
                return this.traverseMultipleFolders(this.currentSession, folderPaths);
            }

            this.progress.status = 'error: ' + error.message;
            console.error('Traversal error:', error);
            throw error;
        } finally {
            this.progress.endTime = new Date();
            this.active = false;
            this.isTraversing = false;
        }
    }

    async _traverseNode(session, nodeId, depth = 0, parentPath = []) {
        if (this.shouldPause) await this._waitForResume();
        if (!this.active || depth > this.maxDepth) return false;

        const startTime = Date.now();
        const currentPath = [...parentPath, nodeId];
        this.progress.currentPath = currentPath.join(' > ');
        this.progress.pendingFolders++;
        this.progress.status = 'processing: ' + nodeId;

        try {
            if (session.hasBeenClosed()) {
                this.currentSession = await this._recreateSession();
                session = this.currentSession;
            }

            const nodeName = nodeId.split('/').pop() || nodeId;
            if (this.skippedFolders.some(skipFolder => nodeName.includes(skipFolder))) {
                console.log(`Skipping entire branch at ${nodeId} (contains forbidden folder name)`);
                this.progress.foldersSkipped++;
                return false;
            }

            const browseResult = await this._browseWithRetry(session, nodeId);
            if (!browseResult.references) return true;

            const variables = browseResult.references.filter(ref => ref.nodeClass === NodeClass.Variable);
            const endBranchVarFound = variables.some(ref =>
                ref.browseName.toString() === this.endBranchVariable
            );

            if (endBranchVarFound) {
                console.log(`Found end branch variable at ${nodeId} - skipping this branch`);
                this.progress.branchesSkipped++;
                this.progress.status = `Skipped branch at ${nodeId}`;
                return false;
            }

            this._processVariables(variables);

            const folders = browseResult.references.filter(ref => {
                if (ref.nodeClass !== NodeClass.Object) return false;
                const folderName = ref.browseName.toString();
                if (this.skippedFolders.some(skipFolder => folderName.includes(skipFolder))) {
                    console.log(`Skipping folder: ${folderName}`);
                    this.progress.foldersSkipped++;
                    return false;
                }
                return true;
            });

            this.progress.totalFolders += folders.length;
            this._createCheckpoint();

            for (const folder of folders) {
                const shouldContinue = await this._traverseNode(
                    session,
                    folder.nodeId.toString(),
                    depth + 1,
                    currentPath
                );

                if (!shouldContinue) {
                    break;
                }
            }

            return true;
        } catch (error) {
            console.error(`Error traversing node ${nodeId}:`, error);
            return true;
        } finally {
            const duration = Date.now() - startTime;
            this.progress.lastOperationDuration = duration;
            this.progress.completedFolders++;
            this.progress.pendingFolders--;
        }
    }

    _processVariables(variables) {
        const excludedPatterns = [
            'UV 3_0', 'UV 2_0', '% Cond', 'System linear flow',
            'Cond temp', 'Sample linear flow', 'Conc Q1', 'Conc Q2',
            'Conc Q3', 'Conc Q4', 'Frac temp', 'UV cell path length',
            'Ratio UV2/UV1', 'Sample flow (CV/h)', 'System flow (CV/h)'
        ];

        const seenNodeIds = new Set();
        const resultGroups = {};

        for (const ref of variables) {
            const displayName = ref.displayName.text.toString();
            if (excludedPatterns.some(p => displayName.includes(p))) continue;

            const nodeId = ref.nodeId.toString();
            if (seenNodeIds.has(nodeId)) continue;

            const lastSlash = nodeId.lastIndexOf('/');
            const resultPath = lastSlash !== -1 ? nodeId.slice(0, lastSlash) : "unknown";
            const variableName = nodeId.slice(lastSlash + 1);

            const variableInfo = {nodeId, resultPath, variableName};
            seenNodeIds.add(nodeId);

            if (!resultGroups[resultPath]) {
                resultGroups[resultPath] = [];
            }
            resultGroups[resultPath].push(variableInfo);
        }

        const lookup = (vars, keyword) => {
            const match = vars.find(v => v.variableName.toLowerCase().includes(keyword.toLowerCase()));
            return match ? match.nodeId : null;
        };

        const NAMESPACE = '2f1b9874-5bcd-4f66-a1c0-07f12c0aeb3a';

        for (const [resultPath, vars] of Object.entries(resultGroups)) {
            const runLog = lookup(vars, "Run Log");
            if (!runLog) continue;

            const pathOnly = runLog.split(':').slice(0, -2).join(':');
            const resultId = uuidv5(pathOnly, NAMESPACE);

            const data = {
                result_id: resultId,
                run_log: runLog,
                fraction: lookup(vars, "Fraction"),
                uv_1: lookup(vars, "UV 1_280"),
                uv_2: lookup(vars, "UV 2_280"),
                uv_3: lookup(vars, "UV 3_280"),
                cond: lookup(vars, "Cond"),
                conc_b: lookup(vars, "Conc B"),
                ph: lookup(vars, "pH"),
                system_flow: lookup(vars, "System Flow"),
                system_pressure: lookup(vars, "System Pressure"),
                sample_flow: lookup(vars, "Sample Flow"),
                sample_pressure: lookup(vars, "Sample Pressure"),
                prec_pressure: lookup(vars, "PreC Pressure"),
                deltac_pressure: lookup(vars, "DeltaC Pressure"),
                postc_pressure: lookup(vars, "PostC Pressure")
            };

            insertAktaNodeIds(data); // don't await here to speed up traversal
        }
    }


    async _browseWithRetry(session, nodeId, attempt = 1) {
        try {
            const result = await session.browse({
                nodeId: nodeId,
                referenceTypeId: "HierarchicalReferences",
                browseDirection: "Forward",
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 0x3F,
                timeoutHint: 30000
            });
            return result;
        } catch (error) {
            if (attempt >= 3) {
                console.warn(`Browse failed after ${attempt} attempts for ${nodeId}: ${error.message}`);
                return {references: []};
            }

            if (error.message.includes('session') || session.hasBeenClosed()) {
                this.currentSession = await this._recreateSession();
                session = this.currentSession;
            }

            const delay = 2000 * attempt;
            console.log(`Retrying browse for ${nodeId} in ${delay}ms (attempt ${attempt})`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return this._browseWithRetry(session, nodeId, attempt + 1);
        }
    }

    _createCheckpoint() {
        const now = new Date();
        if (now - this.progress.lastCheckpoint >= this.checkpointInterval) {
            this.progress.lastCheckpoint = now;

            const checkpoint = {
                timestamp: now,
                stats: {
                    totalFolders: this.progress.totalFolders,
                    completedFolders: this.progress.completedFolders,
                    variablesFound: this.progress.variablesFound,
                    currentPath: this.progress.currentPath,
                    pendingFolders: this.progress.pendingFolders,
                    status: this.progress.status,
                    lastOperationDuration: this.progress.lastOperationDuration,
                    branchesSkipped: this.progress.branchesSkipped,
                    foldersSkipped: this.progress.foldersSkipped
                }
            };

            this.progress.checkpoints.push(checkpoint);
            console.log('Checkpoint:', checkpoint.stats);
        }
    }

    _extractResultPath(nodeId) {
        const match = nodeId.match(/(ns=\d+;s=\d+:.*\/)([^/:]+:[^:]+)$/);
        return match ? match[1] : nodeId;
    }

    async _waitForResume() {
        await new Promise(resolve => {
            const check = () => {
                if (!this.shouldPause) return resolve();
                setTimeout(check, 100);
            };
            check();
        });
    }

    getVariables() {
        const allVariables = [...this.variableBatches.flat(), ...this.currentBatch];
        return allVariables;
    }

    getProgress() {
        return {
            active: this.active,
            complete: this.isComplete,
            stats: {
                totalFolders: this.progress.totalFolders,
                completedFolders: this.progress.completedFolders,
                variablesFound: this.progress.variablesFound,
                currentPath: this.progress.currentPath,
                pendingFolders: this.progress.pendingFolders,
                status: this.progress.status,
                startTime: this.progress.startTime,
                endTime: this.progress.endTime,
                lastOperationDuration: this.progress.lastOperationDuration,
                branchesSkipped: this.progress.branchesSkipped,
                foldersSkipped: this.progress.foldersSkipped
            },
            checkpoints: this.progress.checkpoints.map(cp => ({
                timestamp: cp.timestamp,
                stats: {...cp.stats}
            }))
        };
    }

    pause() {
        this.shouldPause = true;
    }

    resume() {
        this.shouldPause = false;
    }

    async cancel() {
        this.shouldPause = true;
        this.active = false;
        this.isTraversing = false;

        if (this.currentSession) {
            try {
                await this.currentSession.close();
            } catch (err) {
                console.error('Error closing session:', err);
            }
            this.currentSession = null;
        }

        clearInterval(this.healthCheckInterval);
    }
}

const traversalManager = new TraversalManager();
const browser = new NodeTreeBrowser();

// API Endpoints
app.get("/api/browse", async (req, res) => {
    let session;
    try {
        if (!client._secureChannel) {
            await client.connect(endpointUrl);
        }

        session = await client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });

        const nodes = await browser.browseChildren(
            session,
            req.query.nodeId || "ns=2;s=1:Archive/OPCuser"
        );

        res.json({
            success: true,
            nodes,
            timestamp: new Date().toISOString()
        });
    } catch (err) {
        console.error("API Error:", err);
        res.status(500).json({
            success: false,
            error: err.message,
            code: err.code || "UNKNOWN_ERROR"
        });
    } finally {
        if (session) {
            try {
                await session.close();
            } catch (closeError) {
                console.error("Session close error:", closeError);
            }
        }
    }
});

app.get("/api/health", async (req, res) => {
    try {
        if (client._secureChannel) {
            res.json({status: "connected", timestamp: new Date().toISOString()});
        } else {
            res.status(503).json({status: "disconnected"});
        }
    } catch (err) {
        res.status(500).json({status: "error", error: err.message});
    }
});

app.post("/api/clear-cache", (req, res) => {
    browser.clearCache();
    res.json({success: true});
});

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

app.get("/api/grouped-variables", (req, res) => {
    try {
        const grouped = JSON.parse(fs.readFileSync("grouped_variables.json"));
        res.json({
            success: true,
            groups: Object.keys(grouped).length,
            data: grouped
        });
    } catch (err) {
        res.status(500).json({
            success: false,
            error: "Failed to read grouped variables: " + err.message
        });
    }
});

app.get('/api/traverse/start', async (req, res) => {
    if (traversalManager.isTraversing) {
        return res.status(400).json({
            success: false,
            error: 'Traversal already in progress'
        });
    }

    // Set up Server-Sent Events
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    let session;
    try {
        if (!client._secureChannel) {
            await client.connect(endpointUrl);
        }

        session = await client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });

        // Clear previous variables
        fs.writeFileSync(SELECTED_VARIABLES_FILE, JSON.stringify([]));

        traversalManager.currentSession = session;

        // Send progress updates
        const progressInterval = setInterval(() => {
            const progress = traversalManager.getProgress();
            res.write(`data: ${JSON.stringify({
                variablesFound: progress.stats.variablesFound,
                status: progress.stats.status,
                currentPath: progress.stats.currentPath,
                complete: progress.complete
            })}\n\n`);

            if (progress.complete || !traversalManager.active) {
                clearInterval(progressInterval);
                if (progress.complete) {
                    const variables = JSON.parse(fs.readFileSync(SELECTED_VARIABLES_FILE));
                    res.write(`data: ${JSON.stringify({
                        variablesFound: variables.length,
                        status: 'Complete',
                        complete: true,
                        variables: variables.slice(0, 100)
                    })}\n\n`);
                    res.end(); // Explicitly end the response
                }
            }
        }, 1000);

        // Start traversing all folders
        await traversalManager.traverseMultipleFolders(session, FOLDERS_TO_TRAVERSE);

    } catch (err) {
        console.error('Traversal error:', err);
        res.write(`data: ${JSON.stringify({
            error: err.message,
            complete: true
        })}\n\n`);
        res.end(); // End the response on error
    } finally {
        if (session) {
            try {
                await session.close();
            } catch (e) {
                console.error('Session close error:', e);
            }
        }
    }
});

app.get('/api/traverse/progress', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const sendProgress = () => {
        const progress = traversalManager.getProgress();
        res.write(`data: ${JSON.stringify(progress)}\n\n`);

        // Close connection if traversal is complete
        if (progress.complete) {
            res.end();
        }
    };

    sendProgress();

    const interval = setInterval(sendProgress, 1000);

    req.on('close', () => {
        clearInterval(interval);
    });
});

app.post('/api/traverse/cancel', async (req, res) => {
    try {
        await traversalManager.cancel();
        res.json({
            success: true,
            message: 'Traversal cancelled'
        });
    } catch (err) {
        console.error('Cancel error:', err);
        res.status(500).json({
            success: false,
            error: err.message
        });
    }
});

let autoTraversalInterval = null;

// Start auto traversal (runs ONCE, no internal interval)
app.post('/api/traverse/start-auto', async (req, res) => {
    if (autoTraversalInterval) {
        return res.status(400).json({ success: false, message: "Auto traversal is already running." });
    }

    try {
        if (!client._secureChannel) {
            await client.connect(endpointUrl);
        }

        const session = await client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });

        console.log("🔁 Running one-time traversal...");
        fs.writeFileSync(SELECTED_VARIABLES_FILE, JSON.stringify([]));
        traversalManager.currentSession = session;
        await traversalManager.traverseMultipleFolders(session, FOLDERS_TO_TRAVERSE);
        console.log("✅ Traversal complete.");

        // ✅ Trigger Django OPC import endpoint
        console.log("📡 Triggering Django OPC import...");
        try {
            const djangoResponse = await axios.get("http://localhost:8000/plotly_integration/api/trigger-opc-import/");
            console.log("✅ Django OPC import triggered. Response:", djangoResponse.data);
        } catch (djangoErr) {
            console.error("❌ Failed to contact Django OPC import endpoint:", djangoErr.message);
        }

        res.json({ success: true, message: "Traversal complete and Django OPC import triggered." });

        await session.close();
        if (client._secureChannel) {
            await client.disconnect();
            console.log("🔌 OPC UA client disconnected");
        }

    } catch (err) {
        console.error("Traversal error:", err);
        res.status(500).json({ success: false, error: err.message });
    }
});

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


// Stop auto traversal
app.post('/api/traverse/stop-auto', (req, res) => {
    if (autoTraversalInterval) {
        clearInterval(autoTraversalInterval);
        autoTraversalInterval = null;
        return res.json({success: true, message: "Auto traversal stopped."});
    }

    res.status(400).json({success: false, message: "Auto traversal is not running."});
});

app.post("/api/traverse/trigger", async (req, res) => {
    let session;
    try {
        await client.connect(endpointUrl);
        session = await client.createSession({
            userName: "OPCuser",
            password: "OPCuser_710l"
        });

        await traversalManager.traverseMultipleFolders(session, FOLDERS_TO_TRAVERSE);
        res.json({success: true, message: "Traversal complete"});
    } catch (err) {
        console.error("Traversal error:", err);
        res.status(500).json({success: false, error: err.message});
    } finally {
        if (session) {
            try {
                await session.close();
            } catch (e) {
            }
        }
        try {
            if (client._secureChannel) {
                await client.disconnect();
                console.log("🔌 OPC UA client disconnected");
            }
        } catch (e) {
            console.error("Client disconnect failed:", e);
        }
    }
});

app.get("/api/traverse/progress", (req, res) => {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");

    const sendProgress = () => {
        const progress = traversalManager.getProgress();
        res.write(`data: ${JSON.stringify(progress)}\n\n`);
        if (progress.status === "Complete") res.end();
    };

    sendProgress();
    const interval = setInterval(sendProgress, 1000);
    req.on("close", () => clearInterval(interval));
});

app.post("/api/traverse/cancel", (req, res) => {
    traversalManager.isTraversing = false;
    res.json({success: true, message: "Traversal cancelled"});
});

app.get("/api/serverstatus", async (req, res) => {
    try {
        const isConnected = client._secureChannel !== null;
        res.status(isConnected ? 200 : 503).json({
            status: isConnected ? "connected" : "disconnected",
            timestamp: new Date().toISOString()
        });
    } catch (err) {
        res.status(500).json({status: "error", error: err.message});
    }
});

// Check auto traversal status
app.get('/api/traverse/auto-status', (req, res) => {
    res.json({autoRunning: !!autoTraversalInterval});
});

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "public", "index.html"));
});


async function start() {
    try {
        console.log("Initializing OPC UA Browser with certificate security...");

        if (!fs.existsSync(OWN_CERT_PATH)) {
            throw new Error(`Certificate file not found at ${OWN_CERT_PATH}`);
        }
        if (!fs.existsSync(OWN_KEY_PATH)) {
            throw new Error(`Private key file not found at ${OWN_KEY_PATH}`);
        }

        // await client.connect(endpointUrl);
        // console.log("Connected to OPC UA server successfully");

        app.listen(PORT, 'localhost', () => {
            console.log(`OPC UA Browser running on http://localhost:${PORT}`);
            console.log(`Using certificate: ${OWN_CERT_PATH}`);
            console.log(`Variables saved to: ${SELECTED_VARIABLES_FILE}`);
        });

        process.on("SIGINT", async () => {
            console.log("Shutting down...");
            try {
                await traversalManager.cancel();
                await client.disconnect();
            } catch (err) {
                console.error("Disconnect error:", err);
            }
            process.exit(0);
        });
    } catch (err) {
        console.error("Startup failed:", err);
        process.exit(1);
    }
}

start();