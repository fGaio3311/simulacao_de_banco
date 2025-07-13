import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Home from './components/Home'; // seu componente inicial

export default function App() {
  return (
    <BrowserRouter>
      <nav className="p-4 bg-gray-100">
        <Link className="mr-4" to="/">Home</Link>
        <Link to="/dashboard">Dashboard</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
