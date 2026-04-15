import { Routes, Route} from 'react-router-dom'
import TickerResearchPage from './pages/TickerResearchPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<TickerResearchPage />} />
    </Routes>
  )
}

export default App