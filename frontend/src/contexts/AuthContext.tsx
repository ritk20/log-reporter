import { createContext } from 'react';
import type { AuthContextType } from '../types/auth';

export const AuthContext = createContext<AuthContextType>({
  user: null,
  login: async () => {},
  logout: () => {},
  isLoading: false
});