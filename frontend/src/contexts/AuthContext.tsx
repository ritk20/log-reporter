import { createContext } from 'react';
import type { AuthContextType } from '../types/auth';

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => false,
  logout: () => {},
  isLoading: false,
  refreshAccessToken: async() => null,
});