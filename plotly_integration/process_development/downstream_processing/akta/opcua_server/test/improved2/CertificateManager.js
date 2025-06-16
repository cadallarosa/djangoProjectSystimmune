// Save as CertificateManager.js
const fs = require('fs').promises;
const path = require('path');
const os = require('os');

async function getCertificatePaths() {
    const isWindows = os.platform() === 'win32';
    const homeDir = os.homedir();

    const CERT_FOLDER = isWindows
        ? path.join(homeDir, 'AppData', 'Roaming', 'node-opcua-default-nodejs', 'Config', 'PKI')
        : path.join(homeDir, '.config', 'node-opcua-default-nodejs', 'Config', 'PKI');

    const certPath = path.join(CERT_FOLDER, 'own', 'certs', 'MyOpcUaClient.pem');
    const keyPath = path.join(CERT_FOLDER, 'own', 'private', 'private_key.pem');

    // Alternative key path (some versions use different naming)
    const altKeyPath = path.join(CERT_FOLDER, 'own', 'private', 'MyOpcUaClient_key.pem');

    // Check which key file exists
    const keyExists = await fs.access(keyPath).then(() => true).catch(() => false);
    const altKeyExists = await fs.access(altKeyPath).then(() => true).catch(() => false);

    return {
        cert: certPath,
        key: keyExists ? keyPath : (altKeyExists ? altKeyPath : keyPath)
    };
}

module.exports = { getCertificatePaths };