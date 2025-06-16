// certificates/generateCert.js - Generate OPC UA certificates
const {
    OPCUAServer,
    standardSecurityPolicies,
    extractFullyQualifiedDomainName
} = require("node-opcua");
const fs = require('fs');
const path = require('path');
const os = require('os');

async function generateCertificate() {
    const certDir = path.join(__dirname);
    const certFile = path.join(certDir, 'client_cert.pem');
    const keyFile = path.join(certDir, 'client_key.pem');

    // Create directory if it doesn't exist
    if (!fs.existsSync(certDir)) {
        fs.mkdirSync(certDir, { recursive: true });
    }

    console.log('🔐 Generating self-signed certificate...');

    try {
        // Use node-opcua's built-in certificate manager
        const certificateManager = OPCUAServer.defaultCertificateManager;
        await certificateManager.initialize();

        // Create certificate with proper parameters
        const fqdn = await extractFullyQualifiedDomainName();

        const { certificate, privateKey } = await certificateManager.createSelfSignedCertificate({
            applicationUri: "urn:NodeOPCUA-Client",
            dns: [fqdn, "localhost", os.hostname()],
            ip: await getIpAddresses(),
            subject: `/CN=OPCUABrowser/O=NodeOPCUA/L=Local/ST=State/C=US`,
            startDate: new Date(),
            validity: 365 * 10 // 10 years
        });

        // Write certificate and key files
        fs.writeFileSync(certFile, certificate);
        fs.writeFileSync(keyFile, privateKey);

        console.log('✅ Certificate generated successfully!');
        console.log(`   Certificate: ${certFile}`);
        console.log(`   Private Key: ${keyFile}`);

        return { certFile, keyFile };
    } catch (error) {
        console.error('❌ Certificate generation failed:', error);

        // Fallback: Use existing certificates from node-opcua default location
        console.log('🔄 Attempting to use existing certificates...');

        const defaultCertPath = path.join(
            os.homedir(),
            '.config', 'node-opcua-default-nodejs', 'PKI', 'own', 'certs'
        );

        const windowsCertPath = path.join(
            os.homedir(),
            'AppData', 'Roaming', 'node-opcua-default-nodejs', 'Config', 'PKI', 'own', 'certs'
        );

        // Check both possible locations
        const certPath = fs.existsSync(defaultCertPath) ? defaultCertPath : windowsCertPath;

        if (fs.existsSync(certPath)) {
            const files = fs.readdirSync(certPath);
            const pemFile = files.find(f => f.endsWith('.pem'));

            if (pemFile) {
                const sourceCert = path.join(certPath, pemFile);
                const sourceKey = path.join(certPath, '..', 'private', 'private_key.pem');

                // Copy to our location
                fs.copyFileSync(sourceCert, certFile);
                fs.copyFileSync(sourceKey, keyFile);

                console.log('✅ Copied existing certificates');
                return { certFile, keyFile };
            }
        }

        throw new Error('No certificates found and generation failed');
    }
}

async function getIpAddresses() {
    const interfaces = os.networkInterfaces();
    const addresses = [];

    for (const name of Object.keys(interfaces)) {
        for (const iface of interfaces[name]) {
            if (iface.family === 'IPv4' && !iface.internal) {
                addresses.push(iface.address);
            }
        }
    }

    addresses.push("127.0.0.1");
    return addresses;
}

// Alternative simple method if the above fails
async function generateSimpleCertificate() {
    const certDir = path.join(__dirname);
    const certFile = path.join(certDir, 'client_cert.pem');
    const keyFile = path.join(certDir, 'client_key.pem');

    if (!fs.existsSync(certDir)) {
        fs.mkdirSync(certDir, { recursive: true });
    }

    console.log('🔐 Using openssl to generate certificate...');

    const { exec } = require('child_process');
    const util = require('util');
    const execAsync = util.promisify(exec);

    try {
        // Generate private key
        await execAsync(`openssl genrsa -out "${keyFile}" 2048`);

        // Generate certificate
        const subject = '/C=US/ST=State/L=City/O=OPCUABrowser/CN=localhost';
        await execAsync(`openssl req -new -x509 -key "${keyFile}" -out "${certFile}" -days 3650 -subj "${subject}"`);

        console.log('✅ Certificate generated with openssl');
        return { certFile, keyFile };
    } catch (error) {
        console.error('OpenSSL generation failed:', error);
        throw error;
    }
}

// Run if called directly
if (require.main === module) {
    generateCertificate()
        .catch(() => generateSimpleCertificate())
        .catch(console.error);
}

module.exports = { generateCertificate, generateSimpleCertificate };