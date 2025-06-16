// checkCertificate.js - Check what ApplicationURI is in the certificate
const fs = require('fs');
const crypto = require('crypto');
const { Certificate } = require('node-opcua-crypto');
const path = require('path');
const os = require('os');

async function checkCertificate() {
    try {
        // Certificate path
        const homeDir = os.homedir();
        const certPath = path.join(
            homeDir,
            'AppData',
            'Roaming',
            'node-opcua-default-nodejs',
            'Config',
            'PKI',
            'own',
            'certs',
            'MyOpcUaClient.pem'
        );

        console.log('📋 Checking certificate at:', certPath);
        console.log('');

        // Read certificate
        const certPEM = fs.readFileSync(certPath, 'utf8');

        // Parse certificate
        const cert = Certificate.fromPEM(certPEM);

        console.log('Certificate Information:');
        console.log('=======================');
        console.log('Subject:', cert.subject);
        console.log('');

        // Extract ApplicationURI from subjectAltName
        const extensions = cert.tbsCertificate.extensions;
        if (extensions) {
            for (const ext of extensions) {
                if (ext.extnID === '2.5.29.17') { // subjectAltName
                    console.log('SubjectAltName found!');
                    // The ApplicationURI is stored in the subjectAltName
                }
            }
        }

        // Alternative: Just look at the raw certificate text
        console.log('\nSearching for URN in certificate...');
        const urnMatch = certPEM.match(/urn:[^\s,]*/);
        if (urnMatch) {
            console.log('Found ApplicationURI:', urnMatch[0]);
            console.log('\n✅ You should use this ApplicationURI in your code:');
            console.log(`   applicationUri: "${urnMatch[0]}"`);
        }

    } catch (error) {
        console.error('Error reading certificate:', error.message);

        // Fallback: Use openssl if available
        console.log('\nTrying with openssl command...');
        const { exec } = require('child_process');

        const certPath = path.join(
            os.homedir(),
            'AppData/Roaming/node-opcua-default-nodejs/Config/PKI/own/certs/MyOpcUaClient.pem'
        );

        exec(`openssl x509 -in "${certPath}" -text -noout`, (error, stdout, stderr) => {
            if (error) {
                console.error('OpenSSL not available or error:', error.message);
                return;
            }

            // Look for Subject Alternative Name
            const lines = stdout.split('\n');
            let inSAN = false;
            for (const line of lines) {
                if (line.includes('Subject Alternative Name:')) {
                    inSAN = true;
                    continue;
                }
                if (inSAN && line.trim()) {
                    console.log('Subject Alternative Name:', line.trim());
                    const urnMatch = line.match(/URI:([^,\s]+)/);
                    if (urnMatch) {
                        console.log('\n✅ Found ApplicationURI:', urnMatch[1]);
                        console.log('Use this in your client configuration.');
                    }
                    break;
                }
            }
        });
    }
}

checkCertificate();
