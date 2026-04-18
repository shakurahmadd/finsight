import { Button, Container, TextField, Typography, Box, Card, CardContent, Divider, IconButton } from "@mui/material";
import axios from "axios";
import { useEffect, useState } from "react";

function PortfolioDashboard() {
    const [isLoading, setIsLoading] = useState(false)
    const [portfolios, setPortfolios] = useState(null)
    const [selectedPortfolio, setSelectedPortfolio] = useState(null)
    const [error, setError] = useState('')
    const [newPortfolioName, setNewPortfolioName] = useState('')
    const [holdings, setHoldings] = useState(null)
    const [ticker, setTicker] = useState('')
    const [shares, setShares] = useState('')

    const fetchPortfolios = async () => {
        const token = localStorage.getItem('token')
        try {
            const portfolioResponse = await axios.get("http://localhost:8000/portfolio", { headers: { Authorization: `Bearer ${token}` } })
            setPortfolios(portfolioResponse.data)
        } catch (error) {
            console.error(error)
            setError(error.response?.data?.detail)
        }
    }

    useEffect(() => {
        fetchPortfolios()
    }, [])

    const handleCreatePortfolio = async () => {
        const token = localStorage.getItem('token')
        try {
            await axios.post("http://localhost:8000/portfolio", { name: newPortfolioName }, { headers: { Authorization: `Bearer ${token}` } })
            setNewPortfolioName('')
            fetchPortfolios()
        } catch (error) {
            console.error(error)
            setError(error.response?.data?.detail)
        }
    }

    const handleDeletePortfolio = async (portfolioId) => {
        const token = localStorage.getItem('token')
        try {
            await axios.delete(`http://localhost:8000/portfolio/${portfolioId}`, { headers: { Authorization: `Bearer ${token}` } })
            fetchPortfolios()
        } catch (error) {
            console.log(error)
            setError(error.response?.data?.detail)
        }
    }

    const handleSelectPortfolio = (portfolioId) => {
        setSelectedPortfolio(portfolioId)
    }

    const fetchHoldings = async () => {
        const token = localStorage.getItem('token')
        try {
            const fetchHoldingResponse = await axios.get(`http://localhost:8000/holdings/${selectedPortfolio}`, { headers: { Authorization: `Bearer ${token}` } })
            setHoldings(fetchHoldingResponse.data)
        } catch (error) {
            console.log(error)
            setError(error.response?.data?.detail)
        }
    }

    useEffect(() => {
        if (selectedPortfolio == null) return
        fetchHoldings()
    }, [selectedPortfolio])

    const handleAddHolding = async () => {
        const token = localStorage.getItem('token')
        try {
            await axios.post(`http://localhost:8000/holdings/${selectedPortfolio}`, { ticker, shares }, { headers: { Authorization: `Bearer ${token}` } })
            fetchHoldings()
            setTicker('')
            setShares('')
        } catch (error) {
            console.log(error)
            setError(error.response?.data?.detail)
        }
    }

    const handleDeleteHolding = async (holding_id) => {
        const token = localStorage.getItem('token')
        try {
            await axios.delete(`http://localhost:8000/holdings/${selectedPortfolio}/${holding_id}`, { headers: { Authorization: `Bearer ${token}` } })
            fetchHoldings()
        } catch (error) {
            console.log(error)
            setError(error.response?.data?.detail)
        }
    }

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            {selectedPortfolio === null ? (
                <Box>
                    <Typography variant="h4" sx={{ mb: 3 }}>My Portfolios</Typography>

                    <Card sx={{ mb: 3 }}>
                        <CardContent>
                            <Typography variant="subtitle1" sx={{ mb: 2 }}>Create Portfolio</Typography>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                                <TextField
                                    fullWidth
                                    value={newPortfolioName}
                                    label="Portfolio Name"
                                    onChange={(e) => setNewPortfolioName(e.target.value)}
                                />
                                <Button variant="contained" onClick={handleCreatePortfolio}>
                                    Create
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                        {portfolios && portfolios.map((portfolio) => (
                            <Card key={portfolio.id}>
                                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: '12px !important' }}>
                                    <Typography variant="subtitle1">{portfolio.name}</Typography>
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        <Button size="small" variant="outlined" onClick={() => handleSelectPortfolio(portfolio.id)}>
                                            View Holdings
                                        </Button>
                                        <IconButton size="small" onClick={() => handleDeletePortfolio(portfolio.id)} sx={{ color: '#8b949e', '&:hover': { color: '#f85149' } }}>
                                            ×
                                        </IconButton>
                                    </Box>
                                </CardContent>
                            </Card>
                        ))}
                    </Box>
                </Box>
            ) : (
                <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                        <IconButton onClick={() => setSelectedPortfolio(null)} sx={{ color: '#8b949e', fontSize: 20 }}>
                            ←
                        </IconButton>
                        <Typography variant="h4">Holdings</Typography>
                    </Box>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                        {holdings && holdings.map((holding) => (
                            <Card key={holding.id}>
                                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: '10px !important' }}>
                                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{holding.ticker}</Typography>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <Typography variant="body2" color="text.secondary">{holding.shares} shares</Typography>
                                        <IconButton size="small" onClick={() => handleDeleteHolding(holding.id)} sx={{ color: '#8b949e', fontSize: 16, '&:hover': { color: '#f85149' } }}>
                                            ×
                                        </IconButton>
                                    </Box>
                                </CardContent>
                            </Card>
                        ))}
                    </Box>

                    <Divider sx={{ mb: 3 }} />

                    <Card>
                        <CardContent>
                            <Typography variant="subtitle1" sx={{ mb: 2 }}>Add Holding</Typography>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                                <TextField
                                    value={ticker}
                                    label="Ticker"
                                    onChange={(e) => setTicker(e.target.value)}
                                    sx={{ width: 120 }}
                                />
                                <TextField
                                    value={shares}
                                    label="Shares"
                                    onChange={(e) => setShares(e.target.value)}
                                    sx={{ width: 120 }}
                                />
                                <Button variant="contained" onClick={handleAddHolding}>
                                    Add
                                </Button>
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            )}
        </Container>
    )
}

export default PortfolioDashboard
