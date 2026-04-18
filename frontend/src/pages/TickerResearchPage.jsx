import { useState } from 'react'
import axios from 'axios'
import { TextField, Button, Typography, Container, Box, Card, CardContent, CircularProgress, Alert } from '@mui/material'
import SentimentChart from '../components/SentimentChart'
import NewsFeed from '../components/NewsFeed'
import EarningsTable from '../components/EarningsTable'
import SecFilings from '../components/SecFilingsCard'

function TickerResearchPage() {
    const [ticker, setTicker] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [analysisResult, setAnalysisResult] = useState(null)
    const [sentimentHistory, setSentimentHistory] = useState(null)
    const [newsFeed, setNewsFeed] = useState(null)
    const [earningsTable, setEarningsTable] = useState(null)
    const [secFilingCard, setSecFilingCard] = useState(null)
    const [error, setError] = useState('')

    const handleSearch = async () => {
        if (!ticker.trim()) return
        setIsLoading(true)
        setError('')
        setAnalysisResult(null)
        setSentimentHistory(null)
        setNewsFeed(null)
        setEarningsTable(null)
        setSecFilingCard(null)
        try {
            const [analysisRes, sentimentRes, newsRes, earningsRes, secRes] = await Promise.allSettled([
                axios.post('http://localhost:8000/analyse', { ticker: ticker.toUpperCase() }),
                axios.get(`http://localhost:8000/sentiment/history/${ticker.toUpperCase()}`),
                axios.get(`http://localhost:8000/news/${ticker.toUpperCase()}`),
                axios.get(`http://localhost:8000/earnings/${ticker.toUpperCase()}`),
                axios.get(`http://localhost:8000/filings/${ticker.toUpperCase()}`),
            ])

            if (analysisRes.status === 'fulfilled') setAnalysisResult(analysisRes.value.data)
            if (sentimentRes.status === 'fulfilled') setSentimentHistory(sentimentRes.value.data)
            if (newsRes.status === 'fulfilled') setNewsFeed(newsRes.value.data)
            if (earningsRes.status === 'fulfilled') setEarningsTable(earningsRes.value.data)
            if (secRes.status === 'fulfilled') setSecFilingCard(secRes.value.data)

            if (analysisRes.status === 'rejected') setError('Analysis failed — ' + (analysisRes.reason?.response?.data?.detail || 'unknown error'))
        } catch (err) {
            setError('Something went wrong')
            console.error(err)
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSearch()
    }

    const hasResults = analysisResult || sentimentHistory || newsFeed || earningsTable || secFilingCard

    return (
        <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>

            {/* Hero search area */}
            <Box sx={{ textAlign: 'center', mb: 6 }}>
                <Typography variant="h4" sx={{ mb: 1, color: '#e6edf3' }}>
                    Research any stock
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                    AI-powered analysis across news, earnings, SEC filings and insider activity
                </Typography>
                <Box sx={{ display: 'flex', gap: 1.5, justifyContent: 'center', maxWidth: 460, mx: 'auto' }}>
                    <TextField
                        fullWidth
                        value={ticker}
                        onChange={(e) => setTicker(e.target.value.toUpperCase())}
                        onKeyDown={handleKeyDown}
                        placeholder="e.g. AAPL, MSFT, NVDA"
                        sx={{ '& .MuiOutlinedInput-root': { backgroundColor: '#161b22' } }}
                    />
                    <Button
                        variant="contained"
                        onClick={handleSearch}
                        disabled={isLoading}
                        sx={{ px: 3, whiteSpace: 'nowrap', flexShrink: 0 }}
                    >
                        {isLoading ? 'Analysing...' : 'Analyse'}
                    </Button>
                </Box>
            </Box>

            {/* Loading state */}
            {isLoading && (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, py: 6 }}>
                    <CircularProgress size={40} sx={{ color: '#58a6ff' }} />
                    <Typography variant="body2" color="text.secondary">
                        Running agent analysis for {ticker}...
                    </Typography>
                </Box>
            )}

            {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

            {/* Results */}
            {hasResults && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

                    {/* Research summary */}
                    {analysisResult && (
                        <Card sx={{ mb: 2 }}>
                            <CardContent>
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    Research Summary — {ticker}
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                                    {analysisResult.summary}
                                </Typography>
                            </CardContent>
                        </Card>
                    )}

                    {sentimentHistory && sentimentHistory.length > 0 && (
                        <SentimentChart data={sentimentHistory} />
                    )}

                    {newsFeed && newsFeed.length > 0 && (
                        <NewsFeed news={newsFeed} />
                    )}

                    {earningsTable && earningsTable.length > 0 && (
                        <EarningsTable earnings={earningsTable} />
                    )}

                    {secFilingCard && (
                        <SecFilings filings={secFilingCard} />
                    )}

                </Box>
            )}

        </Container>
    )
}

export default TickerResearchPage
