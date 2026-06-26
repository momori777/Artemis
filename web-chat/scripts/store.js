// ============================================================
// store.js - localStorage persistence
// Structure:
//   chats: { [charId]: { [sessionId]: { name, messages[], createdAt } } }
//   activeSession: { [charId]: sessionId }
// ============================================================

var STORE_KEY = 'ai-girlfriend-store-v2';
var STORE_VERSION = 2;

function loadStore() {
  try {
    var raw = localStorage.getItem(STORE_KEY);
    if (!raw) return createDefaultStore();
    var data = JSON.parse(raw);
    if (data._version !== STORE_VERSION) {
      // future migration
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
      bridgeUrl: 'http://localhost:19250',
    },
    // { [charId]: { [sessionId]: { name, messages[], createdAt } } }
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
    var char = getChar(charId);
    sessions[sid] = {
      name: 'Chat 1',
      messages: [],
      createdAt: new Date().toISOString(),
    };
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
  store.chats[charId][sid] = {
    name: name || ('Chat ' + (Object.keys(store.chats[charId]).length + 1)),
    messages: [],
    createdAt: new Date().toISOString(),
  };
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
    var char = getChar(charId);
    sessions[sid] = {
      name: 'Chat 1',
      messages: [],
      createdAt: new Date().toISOString(),
    };
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
    return { id: k, name: sessions[k].name, createdAt: sessions[k].createdAt, count: sessions[k].messages.length };
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
  var m = messages;
  if (m.length > 500) m = m.slice(m.length - 500);
  store.chats[charId][sessionId].messages = m;
  saveStore(store);
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
