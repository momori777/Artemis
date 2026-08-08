// ============================================================
// store.js - localStorage persistence
// Structure:
//   chats: { [charId]: { [sessionId]: { name, messages[], createdAt } } }
//   activeSession: { [charId]: sessionId }
// ============================================================

var STORE_KEY = 'ai-girlfriend-store-v2';
var STORE_VERSION = 2;

function isStoreValid(data) {
  // Return true if the stored data has all required top-level keys
  // that the rest of the app expects.
  if (!data || typeof data !== 'object') return false;
  if (data._version === undefined || data._version === null) return false;
  if (data.settings === undefined || data.settings === null) return false;
  if (data.chats === undefined || data.chats === null) return false;
  return true;
}

function migrateStore(data) {
  // Ensure backward compatibility: merge old data with default structure,
  // preserving all user values and filling in any missing keys.
  var def = createDefaultStore();
  var result = {};
  // Copy all own properties from data first
  for (var key in data) {
    if (Object.prototype.hasOwnProperty.call(data, key)) {
      result[key] = data[key];
    }
  }
  // Fill in missing keys from defaults
  for (var dk in def) {
    if (!Object.prototype.hasOwnProperty.call(result, dk)) {
      if (dk === 'settings') {
        // Deep merge: keep user settings, fill missing ones
        var merged = {};
        for (var sk in def.settings) {
          if (Object.prototype.hasOwnProperty.call(def.settings, sk)) {
            merged[sk] = (result.settings && result.settings[sk] !== undefined && result.settings[sk] !== null) ? result.settings[sk] : def.settings[sk];
          }
        }
        result.settings = merged;
      } else if (dk === 'chats') {
        result.chats = (result.chats && typeof result.chats === 'object') ? result.chats : {};
      } else if (dk === 'avatars') {
        result.avatars = (result.avatars && typeof result.avatars === 'object') ? result.avatars : {};
      } else {
        result[dk] = def[dk];
      }
    }
  }
  result._version = STORE_VERSION;
  return result;
}

function loadStore() {
  try {
    var raw = localStorage.getItem(STORE_KEY);
    if (!raw) return createDefaultStore();
    var data = JSON.parse(raw);
    // Validate and migrate old store formats
    if (!isStoreValid(data)) {
      // Data has no _version or missing keys — likely an old format.
      // Try to salvage it by merging with defaults.
      if (data && typeof data === 'object') {
        data = migrateStore(data);
      } else {
        data = createDefaultStore();
      }
    }
    return data;
  } catch (e) {
    return createDefaultStore();
  }
}

function createDefaultStore() {
  return {
    _version: STORE_VERSION,
    activeCharId: DEFAULT_CHAR_ID,
    settings: {
      apiBase: '',
      model: 'local-model',
      streamEnabled: true,
      reasoningEnabled: true,
      thinkingMode: 'default',
      mem0Enhanced: true,
      mem0WriteEnabled: true,
      mem0WriteInterval: 10,
      bridgeUrl: 'http://localhost:19250',
      // Tree mode: 'on' = always, 'off' = never, 'auto' = new sessions
      treeMode: 'auto',
    },
    // { [charId]: { [sessionId]: { name, messages[], tree?, createdAt } } }
    chats: {},
    // { [charId]: sessionId }
    activeSession: {},
    // { [charId]: dataUrl } — custom avatar image (base64)
    avatars: {},
  };
}

function saveStore(store) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(store));
  } catch (e) {
    console.warn('Failed to save store:', e.message);
  }
}

// ---- Session management ----

function generateSessionId() {
  return 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

function ensureDefaultSession(charId) {
  var store = loadStore();
  if (!store.chats[charId]) {
    store.chats[charId] = {};
  }
  var sessions = store.chats[charId];
  // Always create a fresh default session if none exists
  var keys = Object.keys(sessions);
  if (keys.length === 0) {
    var sid = generateSessionId();
    var s0 = {
      name: 'Chat 1',
      messages: [],
      createdAt: new Date().toISOString(),
    };
    var treeMode = (store.settings && store.settings.treeMode) || 'auto';
    if (treeMode !== 'off') {
      s0.tree = migrateToTree([]);
    }
    sessions[sid] = s0;
    store.activeSession[charId] = sid;
    saveStore(store);
    return sid;
  }
  // Ensure active session is valid
  if (!store.activeSession[charId] || !sessions[store.activeSession[charId]]) {
    store.activeSession[charId] = keys[0];
    saveStore(store);
  }
  return store.activeSession[charId];
}

function createSession(charId, name) {
  var store = loadStore();
  if (!store.chats[charId]) store.chats[charId] = {};
  var sid = generateSessionId();
  var s = {
    name: name || ('Chat ' + (Object.keys(store.chats[charId]).length + 1)),
    messages: [],
    createdAt: new Date().toISOString(),
  };
  // Initialize tree for new sessions if treeMode is not 'off'
  var treeMode = (store.settings && store.settings.treeMode) || 'auto';
  if (treeMode !== 'off') {
    s.tree = migrateToTree([]);
  }
  store.chats[charId][sid] = s;
  store.activeSession[charId] = sid;
  saveStore(store);
  return sid;
}

function deleteSession(charId, sessionId) {
  var store = loadStore();
  if (!store.chats[charId]) return;
  var sessions = store.chats[charId];
  delete sessions[sessionId];
  // pick new active
  var keys = Object.keys(sessions);
  if (keys.length === 0) {
    delete store.activeSession[charId];
    // create a default
    var sid = generateSessionId();
    var s2 = {
      name: 'Chat 1',
      messages: [],
      createdAt: new Date().toISOString(),
    };
    var treeMode = (store.settings && store.settings.treeMode) || 'auto';
    if (treeMode !== 'off') {
      s2.tree = migrateToTree([]);
    }
    sessions[sid] = s2;
    store.activeSession[charId] = sid;
  } else {
    store.activeSession[charId] = keys[keys.length - 1];
  }
  saveStore(store);
}

function renameSession(charId, sessionId, newName) {
  var store = loadStore();
  if (store.chats[charId] && store.chats[charId][sessionId]) {
    store.chats[charId][sessionId].name = newName;
    saveStore(store);
  }
}

function getSessions(charId) {
  var store = loadStore();
  var sessions = store.chats[charId] || {};
  // sorted newest first
  return Object.keys(sessions).map(function(k) {
    var s = sessions[k];
    return { id: k, name: s.name, createdAt: s.createdAt, count: sessionMessageCount(s) };
  }).sort(function(a, b) {
    return (b.createdAt || '').localeCompare(a.createdAt || '');
  });
}

function getActiveSessionId(charId) {
  var store = loadStore();
  return store.activeSession && store.activeSession[charId];
}

function setActiveSession(charId, sessionId) {
  var store = loadStore();
  store.activeSession[charId] = sessionId;
  saveStore(store);
}

function getChatHistory(charId, sessionId) {
  var store = loadStore();
  var s = (store.chats[charId] || {})[sessionId];
  return s ? s.messages : [];
}

function saveChatHistory(charId, sessionId, messages) {
  var store = loadStore();
  if (!store.chats[charId]) store.chats[charId] = {};
  if (!store.chats[charId][sessionId]) return;
  var s = store.chats[charId][sessionId];
  // If using tree mode, save tree only (messages param is ignored)
  if (s.tree) {
    saveStore(store);
    return;
  }
  var m = messages;
  if (m.length > 500) m = m.slice(m.length - 500);
  s.messages = m;
  saveStore(store);
}

/**
 * Save tree changes back to session.
 */
function saveSessionTree(charId, sessionId, tree) {
  var store = loadStore();
  if (!store.chats[charId]) store.chats[charId] = {};
  var s = store.chats[charId][sessionId];
  if (!s) return;
  s.tree = tree;
  saveStore(store);
}

/**
 * Get message count for session (tree or flat).
 */
function sessionMessageCount(s) {
  if (s.tree) return treeNodeCount(s.tree);
  return (s.messages || []).length;
}

function saveSettings(settings) {
  var store = loadStore();
  store.settings = Object.assign({}, store.settings, settings);
  saveStore(store);
}

function getSettings() {
  return loadStore().settings;
}

function getActiveCharId() {
  return loadStore().activeCharId;
}

function setActiveCharId(charId) {
  var store = loadStore();
  store.activeCharId = charId;
  saveStore(store);
}

// ---- Custom Avatars ----
function getCharAvatar(charId) {
  var store = loadStore();
  return (store.avatars && store.avatars[charId]) || null;
}

function setCharAvatar(charId, dataUrl) {
  var store = loadStore();
  if (!store.avatars) store.avatars = {};
  store.avatars[charId] = dataUrl;
  saveStore(store);
}

function removeCharAvatar(charId) {
  var store = loadStore();
  if (store.avatars && store.avatars[charId]) {
    delete store.avatars[charId];
    saveStore(store);
  }
}
