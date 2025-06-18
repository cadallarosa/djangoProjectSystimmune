// variable-patterns.js - Complete file with flexible pattern matching

const variablePatterns = {
    // Core variable patterns - now more flexible
    run_log: /run\s*log/i,
    fraction: /fraction(?!.*(?:table|pool))/i,
    uv_1: /^UV\s+1_280$/i,
    uv_2: /uv\s*2[\s_]*(0|nm)?|uv[\s_]*2(?!80)/i,
    uv_3: /uv\s*3[\s_]*(0|nm)?|uv[\s_]*3/i,
    cond: /^cond(?!.*temp)|conductivity(?!.*temp)/i,
    conc_b: /conc[\s_]*b|concentration[\s_]*b/i,
    ph: /^ph$/i,
    system_flow: /system[\s_]*flow(?!.*cv)/i,
    system_pressure: /system[\s_]*pressure/i,
    sample_flow: /sample[\s_]*flow(?!.*cv)/i,
    sample_pressure: /sample[\s_]*pressure/i,
    prec_pressure: /prec[\s_]*pressure/i,
    deltac_pressure: /deltac[\s_]*pressure/i,
    postc_pressure: /postc[\s_]*pressure/i
};

// Endpoint indicator patterns
const endpointIndicators = [
    /uv\s*1[\s_]*(280|nm)?|uv[\s_]*280/i,
    /uv\s*2[\s_]*(0|nm)?/i,
    /uv\s*3[\s_]*(0|nm)?/i,
    /run\s*log/i,
    /system[\s_]*flow/i,
    /system[\s_]*pressure/i,
    /fraction/i,
    /ratio\s*uv/i,
    /cv\/h/i
];

// Match variable name to pattern key
function matchVariable(name, patterns) {
    if (!name) return null;

    // Clean the name - remove extra spaces
    const cleanName = name.trim();

    for (const [key, pattern] of Object.entries(patterns)) {
        if (pattern.test(cleanName)) {
            return key;
        }
    }

    return null;
}

// Check if a name indicates this is an endpoint
function isEndpointIndicator(name) {
    if (!name) return false;

    const cleanName = name.trim();

    return endpointIndicators.some(pattern => pattern.test(cleanName));
}

module.exports = {
    variablePatterns,
    endpointIndicators,
    matchVariable,
    isEndpointIndicator
};