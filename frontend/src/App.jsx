import { Routes, Route} from 'react-router-dom'
import TickerResearchPage from './pages/TickerResearchPage'
import AuthPage from './pages/AuthPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<TickerResearchPage />} />
      <Route path="/auth" element={<AuthPage/>} />
    </Routes>
  )
}

export default App