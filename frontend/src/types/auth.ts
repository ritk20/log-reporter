export interface User {
  id?: string;
  email: string;
  role: 'admin' | 'viewer';
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
  refreshAccessToken: () => Promise<string | null>;
}