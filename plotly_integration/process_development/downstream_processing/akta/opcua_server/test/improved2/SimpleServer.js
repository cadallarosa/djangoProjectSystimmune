// SimpleServer.js - Simple OPC UA traversal server
const express = require('express');
const cors = require('cors');
const SimpleTraversal = require('./SimpleTraversal');
const { getStatus: getDbStatus } = require('./DatabaseManagerWithTunnel');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 3000;

// Configuration
const config = {
    endpoint: "opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer",
    username: "OPCuser",
    password: "OPCuser_710l",
    startNode: "ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods"
};

let activeTraversal = null;

// Start traversal
app.post('/api/traverse/start', async (req, res) => {
    if (activeTraversal) {
        return res.status(400).json({
            success: false,
            error: 'Traversal already in progress'
        });
    }

    console.log('Starting traversal...');
    activeTraversal = new SimpleTraversal();

    // Start traversal asynchronously
    activeTraversal.connect(config.endpoint, config.username, config.password)
        .then(() => activeTraversal.traverse(config.startNode))
        .then(result => {
            console.log('Traversal completed:', result);
            activeTraversal.disconnect();
            activeTraversal = null;
        })
        .catch(error => {
            console.error('Traversal failed:', error);
            if (activeTraversal) {
                activeTraversal.disconnect();
            }
            activeTraversal = null;
        });

    res.json({
        success: true,
        message: 'Traversal started'
    });
});

// Get status
app.get('/api/status', (req, res) => {
    const dbStatus = getDbStatus();

    res.json({
        traversal: activeTraversal ? 'active' : 'idle',
        database: dbStatus
    });
});

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date() });
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log('');
    console.log('API Endpoints:');
    console.log('  POST /api/traverse/start - Start traversal');
    console.log('  GET  /api/status - Get status');
    console.log('  GET  /api/health - Health check');
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nShutting down...');
    if (activeTraversal) {
        await activeTraversal.disconnect();
    }
    process.exit(0);
});