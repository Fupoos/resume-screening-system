/** 认证上下文 */
import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { message } from 'antd';

interface UserInfo {
  id: string;
  username: string;
  role: string;
  job_categories: string[];
  is_active: boolean;
}

interface AuthContextType {
  user: UserInfo | null;
  token: string | null;
  login: (token: string, user: UserInfo) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasJobCategory: (category: string) => boolean;
  isLoading: boolean;  // 添加loading状态
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);  // 初始为true，表示正在加载

  useEffect(() => {
    // 从localStorage恢复登录状态
    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('userInfo');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (error) {
        localStorage.removeItem('token');
        localStorage.removeItem('userInfo');
      }
    }
    setIsLoading(false);  // 加载完成
  }, []);

  const login = (newToken: string, newUser: UserInfo) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('token', newToken);
    localStorage.setItem('userInfo', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('userInfo');
    message.info('已退出登录');
  };

  const isAuthenticated = !!token && !!user;
  const isAdmin = user?.role === 'admin';

  const hasJobCategory = (category: string): boolean => {
    if (isAdmin) return true;
    return user?.job_categories.includes(category) ?? false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated,
        isAdmin,
        hasJobCategory,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
