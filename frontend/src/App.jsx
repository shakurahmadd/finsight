import { Routes, Route} from 'react-router-dom'
import TickerResearchPage from './pages/TickerResearchPage'
import AuthPage from './pages/AuthPage'
import PortfolioDashboard from './pages/PortfolioDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<TickerResearchPage />} />
      <Route path="/auth" element={<AuthPage/>} />
      <Route path="/portfolio" element={<PortfolioDashboard/>} />
    </Routes>
  )
}

export default App