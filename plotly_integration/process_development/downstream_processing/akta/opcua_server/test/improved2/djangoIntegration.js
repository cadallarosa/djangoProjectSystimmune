// Save as djangoIntegration.js
const axios = require('axios');
const winston = require('winston');

const logger = winston.createLogger({
    level: 'info',
    format: winston.format.simple(),
    transports: [new winston.transports.Console()]
});

async function triggerDjangoImport() {
    try {
        logger.info('📨 Triggering Django OPC import...');

        const response = await axios.get('http://localhost:8000/plotly_integration/api/trigger-opc-import/', {
            timeout: 30000
        });

        logger.info('✅ Django OPC import triggered successfully');
        logger.info('📨 Django Response:', response.data);

        return response.data;
    } catch (error) {
        logger.error('❌ Failed to trigger Django import:', error.message);
        throw error;
    }
}

module.exports = { triggerDjangoImport };