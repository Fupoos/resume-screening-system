/** App根组件 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import Resumes from './pages/Resumes';
import Screening from './pages/Screening';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="resumes" element={<Resumes />} />
          <Route path="screening" element={<Screening />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
