import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  // Dummy login (no backend)
  const login = async (email, password) => {
    const fakeUser = { email };
    setUser(fakeUser);
    return fakeUser;
  };

  // Dummy register (no backend)
  const register = async (username, email, password) => {
    const fakeUser = { username, email };
    setUser(fakeUser);
    return fakeUser;
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);