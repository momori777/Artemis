// ============================================================
// tree.js - Conversation Branch Tree
//
// Each session stores a tree instead of a flat messages[] array:
//
//   tree: {
//     rootId: "n0",
//     currentNodeId: "n5",
//     nodes: {
//       "n0": { id:"n0", role:"system", content:"Session start", parentId:null, childrenIds:["n1"] },
//       "n1": { id:"n1", role:"user", content:"hello", parentId:"n0", childrenIds:["n2","n4"] },
//       "n2": { id:"n2", role:"assistant", content:"hi~", parentId:"n1", childrenIds:["n3"] },
//       "n3": { id:"n3", role:"user", content:"how are you", parentId:"n2", childrenIds:[] },
//       "n4": { id:"n4", role:"assistant", content:"hey there~", parentId:"n1", childrenIds:[] },
//     }
//   }
//
// Walk from root to currentNodeId to get the current message chain.
// Each regenerate creates a new sibling node under the parent user msg.
//
// Compatibility: existing sessions with flat messages[] are auto-migrated
// on first load.
// ============================================================

var TREE_VERSION = 1;

function _makeNodeId() {
  return 'n' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

/**
 * Migrate a flat messages[] array into a tree.
 */
function migrateToTree(messages) {
  if (!messages || !messages.length) {
    var rootId = _makeNodeId();
    return {
      rootId: rootId,
      currentNodeId: rootId,
      nodes: (function() {
        var m = {};
        m[rootId] = { id: rootId, role: 'system', content: '', parentId: null, childrenIds: [], time: new Date().toISOString() };
        return m;
      }())
    };
  }

  var rootId = _makeNodeId();
  var nodes = {};
  nodes[rootId] = { id: rootId, role: 'system', content: '', parentId: null, childrenIds: [], time: new Date().toISOString() };

  var prevId = rootId;
  messages.forEach(function(msg) {
    var nid = _makeNodeId();
    nodes[nid] = {
      id: nid,
      role: msg.role,
      content: msg.content || '',
      parentId: prevId,
      childrenIds: [],
      time: msg.time || new Date().toISOString(),
      media: msg.media || null,
      // Preserve image/paint metadata across flat -> tree migration.
      mediaType: msg.mediaType || null,
      paint: !!msg.paint,
      paintParams: msg.paintParams || null,
      regenerated: !!msg.regenerated,
    };
    nodes[prevId].childrenIds.push(nid);
    prevId = nid;
  });

  return {
    rootId: rootId,
    currentNodeId: prevId,
    nodes: nodes,
  };
}

/**
 * Get tree from a session. Migrates if needed.
 */
function getSessionTree(charId, sessionId) {
  var store = loadStore();
  var s = (store.chats[charId] || {})[sessionId];
  if (!s) return null;
  if (s.tree) return s.tree;
  // migrate
  var tree = migrateToTree(s.messages || []);
  s.tree = tree;
  s._treeVersion = TREE_VERSION;
  s.messages = []; // clear old format (keep for backward compat until confirmed)
  saveStore(store);
  return tree;
}

/**
 * Get the current message chain (from root to currentNode).
 */
function getCurrentChain(tree) {
  if (!tree) return [];
  var chain = [];
  var nid = tree.currentNodeId;
  while (nid) {
    var node = tree.nodes[nid];
    if (!node) break;
    chain.unshift(node);
    nid = node.parentId;
  }
  return chain;
}

/**
 * Get messages array (for API calls) from the current chain.
 */
function getChainMessages(tree) {
  var chain = getCurrentChain(tree);
  return chain
    .filter(function(n) { return n.role !== 'system'; })
    .map(function(n) {
      // Carry media/paint fields through. The UI reads state.messages to decide
      // how to render (and whether a message is re-rollable), so dropping these
      // turned generated images into blank assistant bubbles.
      var m = { role: n.role, content: n.content };
      if (n.media) m.media = n.media;
      if (n.mediaType) m.mediaType = n.mediaType;
      if (n.paint) m.paint = true;
      if (n.paintParams) m.paintParams = n.paintParams;
      if (n.time) m.time = n.time;
      return m;
    });
}

/**
 * Find a node in tree by its position in the current chain.
 */
function getNodeByChainIndex(tree, index) {
  var chain = getCurrentChain(tree);
  return chain[index] || null;
}

/**
 * Add a new message node as child of currentNode.
 */
function appendTreeNode(tree, msg) {
  var nid = _makeNodeId();
  tree.nodes[nid] = {
    id: nid,
    role: msg.role,
    content: msg.content || '',
    parentId: tree.currentNodeId,
    childrenIds: [],
    time: msg.time || new Date().toISOString(),
    media: msg.media || null,
    // Image/paint metadata must survive the round-trip into the tree,
    // otherwise a generated image loses its paint identity (and its
    // regeneration params) as soon as it is persisted.
    mediaType: msg.mediaType || null,
    paint: !!msg.paint,
    paintParams: msg.paintParams || null,
  };
  tree.nodes[tree.currentNodeId].childrenIds.push(nid);
  tree.currentNodeId = nid;
  return nid;
}

/**
 * Find the user message that triggered the assistant at chainIndex.
 * Returns { userNode, userChainIndex } or null.
 */
function findTriggerUser(tree, assistantChainIndex) {
  var chain = getCurrentChain(tree);
  for (var i = assistantChainIndex - 1; i >= 0; i--) {
    if (chain[i].role === 'user') {
      return { userNode: chain[i], userChainIndex: i };
    }
  }
  return null;
}

/**
 * Regenerate: create a sibling branch from the user message.
 * The old assistant node stays; a new branch is created.
 * Returns the new node id.
 */
function branchRegenerate(tree, assistantChainIndex) {
  var chain = getCurrentChain(tree);
  var assistantNode = chain[assistantChainIndex];
  if (!assistantNode || assistantNode.role !== 'assistant') return null;

  // Mark old assistant as regenerated
  assistantNode.regenerated = true;

  // Find parent user
  var parent = assistantNode.parentId;
  var parentNode = tree.nodes[parent];
  if (!parentNode || parentNode.role !== 'user') return null;

  // Create new child node under parent user
  var newId = _makeNodeId();
  tree.nodes[newId] = {
    id: newId,
    role: 'assistant',
    content: '',
    parentId: parent,
    childrenIds: [],
    time: new Date().toISOString(),
    _pending: true,  // placeholder until stream completes
  };
  parentNode.childrenIds.push(newId);
  tree.currentNodeId = newId;
  return newId;
}

/**
 * Move currentNode to a specific node (user clicks a branch).
 * Returns the chain index to scroll to.
 */
function jumpToNode(tree, nodeId) {
  if (!tree.nodes[nodeId]) return null;
  tree.currentNodeId = nodeId;
  return getCurrentChain(tree);
}

/**
 * Get branch siblings for a node (other children of same parent).
 */
function getSiblings(tree, nodeId) {
  var node = tree.nodes[nodeId];
  if (!node || !node.parentId) return [];
  var parent = tree.nodes[node.parentId];
  if (!parent) return [];
  return parent.childrenIds.map(function(id) { return tree.nodes[id]; });
}

/**
 * Get the full path from root to a given node (as chain).
 */
function getPathToNode(tree, nodeId) {
  var path = [];
  var nid = nodeId;
  while (nid) {
    var node = tree.nodes[nid];
    if (!node) break;
    path.unshift(node);
    nid = node.parentId;
  }
  return path;
}

/**
 * Check if a session uses tree format.
 */
function isTreeSession(charId, sessionId) {
  var store = loadStore();
  var s = (store.chats[charId] || {})[sessionId];
  return !!(s && s.tree);
}

/**
 * Count total nodes in tree.
 */
function treeNodeCount(tree) {
  return Object.keys(tree.nodes).length;
}
