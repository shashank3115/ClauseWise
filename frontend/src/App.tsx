import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Analyze from './pages/Analyze'
import AnalysisResult from './pages/AnalysisResult'
import BulkAnalyze from './pages/BulkAnalyze'
import Compliance from './pages/Compliance'
import Regulations from './pages/Regulations'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Signup from './pages/Signup'

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Dashboard />} />
        <Route path='/analyze' element={<Analyze />} />
        <Route path='/analysis/:analysisId' element={<AnalysisResult />} />
        <Route path='/bulk-analyze' element={<BulkAnalyze />} />
        <Route path='/compliance' element={<Compliance />} />
        <Route path='/regulations' element={<Regulations />} />
        <Route path='/reports' element={<Reports />} />
        <Route path='/settings' element={<Settings />} />
        <Route path='/login' element={<Login/>} />
        <Route path='/signup' element={<Signup />} />
      </Routes>
    </Router>
  )
}


