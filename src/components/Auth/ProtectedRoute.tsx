import React, { ReactNode } from 'react';

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
    // Simple placeholder logic
    const isAuthenticated = true;
    return isAuthenticated ? <>{children}</> : <div>Please log in.</div>;
};

export default ProtectedRoute;