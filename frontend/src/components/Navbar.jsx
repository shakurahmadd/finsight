import { AppBar, Toolbar, Button, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";

function Navbar() {
    
    const navigate = useNavigate()
    return (
    <AppBar position='static'>
        <Toolbar>
            <Typography variant='h6' onClick={() => navigate('/')} sx={{ cursor: 'pointer'}}>
                Finsight
                </Typography>
            <Button color="inherit" onClick={() => navigate('/watchlist')}>Watchlist</Button>
            <Button color='inherit' onClick={() => navigate('/portfolio')}>Portfolio</Button>
            <Button color='inherit' onClick={() => {localStorage.removeItem('token'); navigate('/auth')}}>Sign Out</Button>
        </Toolbar>



    </AppBar>
    )
}

export default Navbar