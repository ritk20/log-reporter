type RequestOptions = RequestInit & {
  headers?: HeadersInit;
  _retry?: boolean;
};

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (token: string) => void) => {
  refreshSubscribers.push(cb);
};

const onRefreshed = (token: string) => {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
};

export async function fetchWithAuth(url: string, options: RequestOptions = {}): Promise<Response> {
  const token = localStorage.getItem('authToken');
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers,
  };

  try {
    let response = await fetch(`http://localhost:8000${url}`, {
      ...options,
      headers,
      credentials: 'include', // REQUIRED for cookies
    });

    // Token expired - try to refresh
    if (response.status === 401 && !options._retry) {
      if (!isRefreshing) {
        isRefreshing = true;
        
        try {
          const newToken = await refreshAccessToken();
          isRefreshing = false;
          
          if (newToken) {
            onRefreshed(newToken);
            // Retry original request with new token
            const newHeaders = {
              ...headers,
              'Authorization': `Bearer ${newToken}`
            };
            return fetchWithAuth(url, {
              ...options,
              headers: newHeaders,
              _retry: true
            });
          } else {
            // Refresh failed - force logout
            localStorage.removeItem('authToken');
            window.location.href = '/login';
          }
        } catch (error) {
          isRefreshing = false;
          throw error;
        }
      }

      // Wait for ongoing refresh to complete
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh(async (newToken: string) => {
          try {
            const newHeaders = {
              ...headers,
              'Authorization': `Bearer ${newToken}`
            };
            const response = await fetchWithAuth(url, {
              ...options,
              headers: newHeaders,
              _retry: true
            });
            resolve(response);
          } catch (error) {
            reject(error);
          }
        });
      });
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
}

// Add refresh function
async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await fetch('http://localhost:8000/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('authToken', data.access_token);
      return data.access_token;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  return null;
}

// Helper methods for HTTP methods (unchanged)
export const api = {
  async get<T>(url: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, { 
      ...options, 
      method: 'GET',
    });
    return response.json();
  },

  async post<T, D = unknown>(url: string, data?: D, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async put<T, D = unknown>(url: string, data?: D, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async delete<T>(url: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(url, {
      ...options,
      method: 'DELETE',
    });
    return response.json();
  }
};