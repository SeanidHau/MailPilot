import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../app/AuthContext';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="empty-state" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        加载中...
      </div>
    );
  }

  if (!user) {
    return (
      <Navigate
        to="/login"
        state={{
          from: location,
          authNotice: '请先登录后再访问设置、邮箱数据或 AI 配置。',
        }}
        replace
      />
    );
  }

  return <>{children}</>;
}
