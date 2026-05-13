import { AppBar, Toolbar, Button, Typography, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";

function Navbar() {
    const navigate = useNavigate()
    const isLoggedIn = !!localStorage.getItem('token')

    return (
        <AppBar position='sticky'>
            <Toolbar sx={{ gap: 1 }}>
                <Typography
                    variant='h6'
                    onClick={() => navigate('/')}
                    sx={{ cursor: 'pointer', color: '#58a6ff', fontWeight: 700, flexGrow: 1 }}
                >
                    FinSight
                </Typography>
                <Button color="inherit" onClick={() => navigate('/watchlist')} sx={{ color: '#8b949e', '&:hover': { color: '#e6edf3' } }}>
                    Watchlist
                </Button>
                <Button color='inherit' onClick={() => navigate('/portfolio')} sx={{ color: '#8b949e', '&:hover': { color: '#e6edf3' } }}>
                    Portfolio
                </Button>
                {isLoggedIn ? (
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={() => { localStorage.removeItem('token'); navigate('/auth') }}
                        sx={{ borderColor: '#30363d', color: '#8b949e', '&:hover': { borderColor: '#58a6ff', color: '#58a6ff' } }}
                    >
                        Sign Out
                    </Button>
                ) : (
                    <Button
                        variant="outlined"
                        size="small"
                        onClick={() => navigate('/auth')}
                        sx={{ borderColor: '#30363d', color: '#8b949e', '&:hover': { borderColor: '#58a6ff', color: '#58a6ff' } }}
                    >
                        Sign In
                    </Button>
                )}
            </Toolbar>
        </AppBar>
    )
}

export default Navbar
