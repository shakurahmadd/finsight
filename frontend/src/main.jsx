import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material'
import './index.css'
import App from './App.jsx'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#58a6ff' },
    background: {
      default: '#0d1117',
      paper: '#161b22',
    },
    text: {
      primary: '#e6edf3',
      secondary: '#8b949e',
    },
    success: { main: '#3fb950' },
    error: { main: '#f85149' },
    divider: '#30363d',
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", system-ui, sans-serif',
    h4: { fontWeight: 600, letterSpacing: '-0.5px' },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 600 },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid #30363d',
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500 }
      }
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#161b22',
          borderBottom: '1px solid #30363d',
          boxShadow: 'none',
        }
      }
    },
    MuiTextField: {
      defaultProps: { size: 'small' }
    },
    MuiDataGrid: {
      styleOverrides: {
        root: {
          border: '1px solid #30363d',
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: '#0d1117',
            borderBottom: '1px solid #30363d',
          },
          '& .MuiDataGrid-cell': {
            borderBottom: '1px solid #21262d',
          },
        }
      }
    }
  }
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
)
