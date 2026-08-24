/* =====================================================
   PhysioMind AI - API client
   Thin wrapper over fetch: base URL, bearer token, and
   error messages the UI can show directly.
   ===================================================== */

'use strict';

const API = (() => {
  const BASE = '';                       // same origin: FastAPI serves this page
  const TOKEN_KEY = 'pm_token';

  const getToken = () => localStorage.getItem(TOKEN_KEY);
  const setToken = t => t ? localStorage.setItem(TOKEN_KEY, t)
                          : localStorage.removeItem(TOKEN_KEY);

  /** Pull a human-readable message out of whatever the server returned. */
  function errorMessage(payload, status) {
    const detail = payload && payload.detail;
    if (typeof detail === 'string') return detail;
    // FastAPI validation errors arrive as a list of field problems.
    if (Array.isArray(detail) && detail.length) {
      return detail.map(d => d.msg || 'Invalid input').join('. ');
    }
    return `Request failed (${status})`;
  }

  async function request(path, { method = 'GET', body, isForm = false } = {}) {
    const headers = {};
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (body && !isForm) headers['Content-Type'] = 'application/json';

    let response;
    try {
      response = await fetch(BASE + path, {
        method,
        headers,
        body: isForm ? body : (body ? JSON.stringify(body) : undefined),
      });
    } catch {
      throw new Error('Cannot reach the server. Is the backend running?');
    }

    if (response.status === 204) return null;

    let payload = null;
    try { payload = await response.json(); } catch { /* empty body */ }

    if (!response.ok) {
      // Session expired: clear it so the UI drops back to logged-out state
      // instead of retrying with a token the server keeps rejecting.
      if (response.status === 401 && getToken()) setToken(null);
      const err = new Error(errorMessage(payload, response.status));
      err.status = response.status;
      throw err;
    }
    return payload;
  }

  return {
    getToken,
    setToken,
    isLoggedIn: () => Boolean(getToken()),

    // --- auth ---
    async signup(name, email, password, lang) {
      const data = await request('/api/auth/signup', {
        method: 'POST', body: { name, email, password, lang },
      });
      setToken(data.access_token);
      return data.user;
    },
    async login(email, password) {
      const data = await request('/api/auth/login', {
        method: 'POST', body: { email, password },
      });
      setToken(data.access_token);
      return data.user;
    },
    me: () => request('/api/auth/me'),
    logout: () => setToken(null),

    // --- content ---
    exercises: cat => request(
      `/api/exercises${cat && cat !== 'all' ? `?category=${encodeURIComponent(cat)}` : ''}`
    ),
    poseConfig: slug => request(`/api/exercises/${encodeURIComponent(slug)}/pose-config`),

    // --- clinical ---
    assess: (text, lang) => request('/api/assess', {
      method: 'POST', body: { text, lang },
    }),
    createPlan: lang => request('/api/plans', { method: 'POST', body: { lang } }),
    activePlan: () => request('/api/plans/active'),

    submitSession: payload => request('/api/sessions', {
      method: 'POST', body: payload,
    }),
    sessions: () => request('/api/sessions'),
    analytics: () => request('/api/analytics'),

    uploadReport(file) {
      const form = new FormData();
      form.append('file', file);
      return request('/api/reports', { method: 'POST', body: form, isForm: true });
    },
  };
})();
