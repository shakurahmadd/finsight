import { Routes, Route} from 'react-router-dom'
import TickerResearchPage from './pages/TickerResearchPage'
import AuthPage from './pages/AuthPage'
import PortfolioDashboard from './pages/PortfolioDashboard'
import WatchlistPage from './pages/WatchlistPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<TickerResearchPage />} />
      <Route path="/auth" element={<AuthPage/>} />
      <Route path="/portfolio" element={<PortfolioDashboard/>} />
      <Route path="/watchlist" element={<WatchlistPage/>} />
    </Routes>

  )
}

export default App