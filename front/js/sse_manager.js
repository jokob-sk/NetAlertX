/**
 * NetAlertX SSE (Server-Sent Events) Manager
 * Replaces polling with real-time updates from backend
 * Falls back to polling if SSE unavailable
 */

class NetAlertXStateManager {
  constructor() {
    this.eventSource = null;
    this.clientId = `client-${Math.random().toString(36).substr(2, 9)}`;
    this.pollInterval = null;
    this.pollBackoffInterval = 1000; // Start at 1s
    this.maxPollInterval = 30000; // Max 30s
    this.useSSE = true;
    this.sseConnectAttempts = 0;
    this.maxSSEAttempts = 3;
    this.initialized = false;
  }

  /**
   * Initialize the state manager
   * Tries SSE first, falls back to polling if unavailable
   */
  init() {
    if (this.initialized) return;

    console.log("[NetAlertX State] Initializing state manager...");
    this.trySSE();
    this.initialized = true;
  }

  /**
   * Attempt SSE connection with fetch streaming
   * Uses Authorization header like all other endpoints
   */
  async trySSE() {
    if (this.sseConnectAttempts >= this.maxSSEAttempts) {
      console.warn("[NetAlertX State] SSE failed after max attempts, switching to polling");
      this.useSSE = false;
      this.startPolling();
      return;
    }

    try {
      const apiToken = getSetting("API_TOKEN");
      const apiBase = getApiBase().replace(/\/$/, '');
      const sseUrl = `${apiBase}/sse/state?client=${encodeURIComponent(this.clientId)}`;

      const response = await fetch(sseUrl, {
        headers: { 'Authorization': `Bearer ${apiToken}` }
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      console.log("[NetAlertX State] Connected to SSE");
      this.sseConnectAttempts = 0;

      // Stream and parse SSE events
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          this.handleSSEError();
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events[events.length - 1];

        events.slice(0, -1).forEach(e => this.processSSEEvent(e));
      }
    } catch (e) {
      console.error("[NetAlertX State] SSE error:", e);
      this.handleSSEError();
    }
  }

  /**
   * Parse and dispatch a single SSE event
   */
  processSSEEvent(eventText) {
    if (!eventText || !eventText.trim()) return;

    const lines = eventText.split('\n');
    let eventType = null, eventData = null;

    for (const line of lines) {
      if (line.startsWith('event:')) eventType = line.substring(6).trim();
      else if (line.startsWith('data:')) eventData = line.substring(5).trim();
    }

    if (!eventType || !eventData) return;

    try {
      switch (eventType) {
        case 'state_update':
          this.handleStateUpdate(JSON.parse(eventData));
          break;
        case 'unread_notifications_count_update':
          this.handleUnreadNotificationsCountUpdate(JSON.parse(eventData));
          break;
      }
    } catch (e) {
      console.error(`[NetAlertX State] Parse error for ${eventType}:`, e, "eventData:", eventData);
    }
  }

  /**
   * Handle SSE connection error with exponential backoff
   */
  handleSSEError() {
    this.sseConnectAttempts++;
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.sseConnectAttempts < this.maxSSEAttempts) {
      console.log(`[NetAlertX State] Retry ${this.sseConnectAttempts}/${this.maxSSEAttempts}...`);
      setTimeout(() => this.trySSE(), 5000);
    } else {
      this.trySSE();
    }
  }

  /**
   * Handle state update from SSE
   */
  handleStateUpdate(appState) {
    try {
      if (document.getElementById("state")) {
        const cleanState = appState["currentState"].replaceAll('"', "");
        document.getElementById("state").innerHTML = cleanState;
      }
    } catch (e) {
      console.error("[NetAlertX State] Failed to update state display:", e);
    }
  }

  /**
   * Handle unread notifications count update
   */
  handleUnreadNotificationsCountUpdate(data) {
    try {
      const count = data.count || 0;
      console.log("[NetAlertX State] Unread notifications count:", count);
      handleUnreadNotifications(count);
    } catch (e) {
      console.error("[NetAlertX State] Failed to handle unread count update:", e);
    }
  }

  /**
   * Start polling fallback (if SSE fails)
   */
  startPolling() {
    console.log("[NetAlertX State] Starting polling fallback...");
    this.poll();
  }

  /**
   * Poll the server for state updates
   */
  poll() {
    $.get(
      "php/server/query_json.php",
      { file: "app_state.json", nocache: Date.now() },
      (appState) => {
        this.handleStateUpdate(appState);
        this.pollBackoffInterval = 1000; // Reset on success
        this.pollInterval = setTimeout(() => this.poll(), this.pollBackoffInterval);
      }
    ).fail(() => {
      // Exponential backoff on failure
      this.pollBackoffInterval = Math.min(
        this.pollBackoffInterval * 1.5,
        this.maxPollInterval
      );
      this.pollInterval = setTimeout(() => this.poll(), this.pollBackoffInterval);
    });
  }

  /**
   * Stop all updates
   */
  stop() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.pollInterval) {
      clearTimeout(this.pollInterval);
      this.pollInterval = null;
    }
    this.initialized = false;
  }

  /**
   * Get stats for debugging
   */
  async getStats() {
    try {
      const apiToken = getSetting("API_TOKEN");
      const apiBase = getApiBase();
      const response = await fetch(`${apiBase}/sse/stats`, {
        headers: {
          Authorization: `Bearer ${apiToken}`,
        },
      });
      return await response.json();
    } catch (e) {
      console.error("[NetAlertX State] Failed to get stats:", e);
      return null;
    }
  }
}

// Global instance
let netAlertXStateManager = new NetAlertXStateManager();
