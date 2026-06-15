/**
 * Yonyou Cloud SSO Proxy for Microsoft Teams
 * 
 * Flow:
 * 1. Frontend calls microsoftTeams.auth.getAuthToken() in Teams
 * 2. Frontend POSTs token to /sso/login
 * 3. Backend validates token with Microsoft Graph API
 * 4. Backend extracts user email and logs into Yonyou Cloud
 * 5. Returns session info to frontend
 */

const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 5001;

// Configuration from Azure AD
const AZURE_TENANT_ID = 'b739eec7-643b-4371-b8d4-12f30da3918b';
const GRAPH_API = 'https://graph.microsoft.com/v1.0/me';

// Yonyou Cloud SSO configuration
const YONYOU_SSO_URL = 'https://euc.yonyoucloud.com/cas/thirdSaml2Login';
const YONYOU_SSO_CODE = 'u10pzze8';
const YONYOU_SERVICE = encodeURIComponent('https://c2.yonyoucloud.com/login?tenantId=w5f0xnbi');
const YONYOU_HOME = 'https://c2.yonyoucloud.com/';
const YONYOU_API_BASE = 'https://c2.yonyoucloud.com';

// In-memory session store (use Redis/DB in production)
const sessions = new Map();

// Logging
function log(level, msg, data = {}) {
  const ts = new Date().toISOString();
  console.log(JSON.stringify({ ts, level, msg, ...data }));
}

// Middleware
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(cors());

// CORS for Teams tab
function cors() {
  return (req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, x-ms-token-aad');
    if (req.method === 'OPTIONS') return res.sendStatus(200);
    next();
  };
}

// ============================================================
// SSO Login endpoint
// Receives Azure AD token from Teams frontend
// ============================================================
app.post('/sso/login', async (req, res) => {
  const { token, ssoCode } = req.body;
  
  if (!token) {
    return res.status(400).json({ error: 'Token is required' });
  }
  
  log('info', 'SSO login attempt', { ssoCode });
  
  try {
    // Step 1: Validate token with Microsoft Graph API
    const graphResponse = await axios.get(GRAPH_API, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      },
      timeout: 15000
    });
    
    const user = graphResponse.data;
    log('info', 'Graph API response', { 
      userId: user.id, 
      email: user.mail || user.userPrincipalName,
      displayName: user.displayName
    });
    
    // Step 2: Generate session ID
    const sessionId = crypto.randomBytes(32).toString('hex');
    const userEmail = user.mail || user.userPrincipalName;
    
    // Step 3: Try to authenticate with Yonyou Cloud
    // Build the SAML redirect URL for Yonyou SSO
    const yonyouRedirectUrl = buildYonyouSSOUrl(userEmail);
    
    // Step 4: Try to get Yonyou session by following the redirect
    const yonyouSession = await attemptYonyouLogin(yonyouRedirectUrl, userEmail);
    
    // Step 5: Store session
    sessions.set(sessionId, {
      userId: user.id,
      email: userEmail,
      displayName: user.displayName,
      yonyouSession: yonyouSession,
      createdAt: Date.now()
    });
    
    log('info', 'SSO login success', { userId: user.id, email: userEmail });
    
    res.json({
      success: true,
      sessionId,
      user: {
        id: user.id,
        email: userEmail,
        displayName: user.displayName
      },
      redirectUrl: yonyouSession ? yonyouSession.url : yonyouRedirectUrl,
      message: 'Login successful'
    });
    
  } catch (error) {
    // Handle specific Graph API errors
    if (error.response) {
      const { status, data } = error.response;
      log('error', 'Graph API error', { status, data });
      
      if (status === 401) {
        return res.status(401).json({ 
          error: 'AADSTS90014', // Missing credential error
          message: 'Token validation failed - may need re-authentication in Teams'
        });
      }
      if (status === 403) {
        return res.status(403).json({ 
          error: 'AADSTS50076',
          message: 'MFA required or insufficient permissions'
        });
      }
    }
    
    log('error', 'SSO login failed', { error: error.message });
    res.status(500).json({ 
      error: 'LOGIN_FAILED',
      message: error.message 
    });
  }
});

// ============================================================
// Session status endpoint
// ============================================================
app.get('/sso/status/:sessionId', (req, res) => {
  const { sessionId } = req.params;
  const session = sessions.get(sessionId);
  
  if (!session) {
    return res.json({ loggedIn: false });
  }
  
  // Check if session expired (1 hour)
  if (Date.now() - session.createdAt > 3600000) {
    sessions.delete(sessionId);
    return res.json({ loggedIn: false, expired: true });
  }
  
  res.json({
    loggedIn: true,
    user: {
      id: session.userId,
      email: session.email,
      displayName: session.displayName
    }
  });
});

// ============================================================
// Logout endpoint
// ============================================================
app.post('/sso/logout', (req, res) => {
  const { sessionId } = req.body;
  if (sessionId && sessions.has(sessionId)) {
    sessions.delete(sessionId);
    log('info', 'User logged out', { sessionId });
  }
  res.json({ success: true });
});

// ============================================================
// Health check
// ============================================================
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', version: '1.0.0', timestamp: new Date().toISOString() });
});

// ============================================================
// Yonyou Cloud Login Helper
// Attempts to login to Yonyou Cloud via SSO
// ============================================================
async function attemptYonyouLogin(redirectUrl, userEmail) {
  try {
    // Try to follow the SSO flow
    const response = await axios.get(redirectUrl, {
      maxRedirects: 5,
      timeout: 15000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
      // Don't validate SSL in dev (remove in production with proper cert)
      validateStatus: (status) => status < 500
    });
    
    // Check if we got a session cookie
    const setCookie = response.headers['set-cookie'];
    return {
      url: response.request?.res?.responseUrl || redirectUrl,
      cookies: setCookie
    };
  } catch (error) {
    log('warn', 'Yonyou direct login failed, returning SSO URL', { error: error.message });
    return { url: redirectUrl, cookies: null };
  }
}

function buildYonyouSSOUrl(userEmail) {
  // Yonyou Cloud SSO URL - user enters SSO code on Yonyou page
  // This redirects to Azure AD for M365 authentication
  const service = encodeURIComponent('https://c2.yonyoucloud.com/login?tenantId=w5f0xnbi');
  return `${YONYOU_SSO_URL}?thirdUCId=${YONYOU_SSO_CODE}&service=${service}`;
}

// ============================================================
// Error handler
// ============================================================
app.use((err, req, res, next) => {
  log('error', 'Unhandled error', { error: err.message, stack: err.stack });
  res.status(500).json({ error: 'INTERNAL_ERROR', message: err.message });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  log('info', `SSO Proxy started on port ${PORT}`);
  console.log(`Yonyou SSO Proxy listening on http://0.0.0.0:${PORT}`);
  console.log('Endpoints:');
  console.log('  POST /sso/login  - SSO login with Azure AD token');
  console.log('  GET  /sso/status/:sessionId - Check session');
  console.log('  POST /sso/logout - Logout');
  console.log('  GET  /health     - Health check');
});
