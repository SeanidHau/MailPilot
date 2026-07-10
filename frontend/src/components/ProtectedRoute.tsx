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
          authNotice: 'Please sign in before opening settings, mailbox data, or AI configuration.',
        }}
        replace
      />
    );
  }

  return <>{children}</>;
}
