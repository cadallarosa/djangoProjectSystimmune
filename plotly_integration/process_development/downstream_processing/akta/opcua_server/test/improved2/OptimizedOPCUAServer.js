// Save as OptimizedOPCUAServer.js
const express = require('express');
const cors = require('cors');
const winston = require('winston');
const path = require('path');
const { runOptimizedTraversal } = require('./OptimizedTraversalManager');

// Setup logging
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.simple()
    ),
    transports: [
        new winston.transports.File({ filename: 'opcua_server.log' }),
        new winston.transports.Console()
    ]
});

// Initialize Express app
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'html')));

const PORT = process.env.PORT || 3000;

// OPC UA Configuration
const opcuaConfig = {
    endpoint: "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer",
    username: "OPCuser",
    password: "OPCuser_710l"
};

// Store active traversal info
let activeTraversal = null;

// API Routes

// Health check
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        activeTraversal: activeTraversal !== null
    });
});

// Start optimized traversal
app.post('/api/traverse/start-optimized', async (req, res) => {
    try {
        if (activeTraversal) {
            return res.status(400).json({
                success: false,
                error: 'Traversal already in progress'
            });
        }

        const {
            startNodeId = "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods",
            parallelTraversals = 1
        } = req.body;

        logger.info(`🚀 Starting optimized traversal with ${parallelTraversals} parallel workers...`);

        // Mark as active
        activeTraversal = {
            startTime: new Date(),
            config: { startNodeId, parallelTraversals }
        };

        // Start traversal asynchronously
        runOptimizedTraversal({
            endpoint: opcuaConfig.endpoint,
            username: opcuaConfig.username,
            password: opcuaConfig.password,
            startNodeId,
            parallelTraversals: Math.max(1, Math.min(10, parallelTraversals))
        })
        .then(result => {
            logger.info('✅ Traversal completed successfully', result);
            activeTraversal = null;
        })
        .catch(error => {
            logger.error('❌ Traversal failed:', error);
            activeTraversal = null;
        });

        res.json({
            success: true,
            message: 'Traversal started',
            config: activeTraversal.config
        });

    } catch (error) {
        logger.error('❌ Failed to start traversal:', error);
        activeTraversal = null;
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get traversal status
app.get('/api/traverse/status', (req, res) => {
    if (activeTraversal) {
        const duration = (new Date() - activeTraversal.startTime) / 1000;
        res.json({
            active: true,
            duration: duration.toFixed(2),
            config: activeTraversal.config
        });
    } else {
        res.json({
            active: false,
            message: 'No active traversal'
        });
    }
});

// Test browse endpoint
app.post('/api/test/browse', async (req, res) => {
    const { nodeId = "ns=2;s=6:Archive/OPCuser" } = req.body;

    try {
        // This would use a simplified browse test
        res.json({
            success: true,
            message: `Would browse: ${nodeId}`
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Database status endpoint
app.get('/api/database/status', async (req, res) => {
    try {
        const { getStatus } = require('./DatabaseManagerWithTunnel');
        const status = getStatus();
        res.json(status);
    } catch (error) {
        res.status(500).json({
            error: 'Failed to get database status',
            message: error.message
        });
    }
});

// Serve index
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'html', 'opc_ua_browser_optimized.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    logger.error('Express error:', err);
    res.status(500).json({
        error: 'Internal server error',
        message: err.message
    });
});

// Start server
async function start() {
    try {
        // Ensure logs directory exists
        const fs = require('fs');
        const logsDir = path.join(__dirname, 'logs');
        if (!fs.existsSync(logsDir)) {
            fs.mkdirSync(logsDir);
        }

        logger.info('🚀 Starting Optimized OPC UA Server...');

        // Check certificate
        const { getCertificatePaths } = require('./CertificateManager');
        const certPaths = await getCertificatePaths();

        if (!fs.existsSync(certPaths.cert)) {
            logger.warn('⚠️ Certificate not found. Please run: node fixCertificate.js');
        } else {
            logger.info('✅ Certificate found');
        }

        app.listen(PORT, () => {
            logger.info(`🌐 Server running on http://localhost:${PORT}`);
            logger.info('📋 Ready to accept requests');
            logger.info('\nAPI Endpoints:');
            logger.info('  POST /api/traverse/start-optimized - Start traversal');
            logger.info('  GET  /api/traverse/status - Get traversal status');
            logger.info('  GET  /api/database/status - Get database status');
            logger.info('  GET  /api/health - Health check');
        });

        // Graceful shutdown
        process.on('SIGINT', async () => {
            logger.info('🛑 Shutting down...');
            process.exit(0);
        });

    } catch (error) {
        logger.error('❌ Startup failed:', error);
        process.exit(1);
    }
}

// Start the server
start();