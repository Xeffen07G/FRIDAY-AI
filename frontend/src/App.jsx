import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AssistantPage from './pages/AssistantPage';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<AssistantPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="*" element={<Navigate to="/assistant" replace />} />
        </Routes>
      </ErrorBoundary>
    </Router>
  );
}
