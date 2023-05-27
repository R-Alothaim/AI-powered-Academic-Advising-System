import { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import { auth as authApi } from '../api/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
