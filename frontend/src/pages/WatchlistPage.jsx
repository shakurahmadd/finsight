import { Box, Container, Typography, Card, CardContent, Chip, CircularProgress } from "@mui/material";
import axios from "axios";
import { useEffect, useState } from "react";

function getSentimentColor(score) {
    if (score === null || score === undefined) return 'default'
    if (score > 0.1) return 'success'
    if (score < -0.1) return 'error'
    return 'warning'
}

function getSentimentLabel(score) {
    if (score === null || score === undefined) return 'No data'
    if (score > 0.1) return 'Bullish'
    if (score < -0.1) return 'Bearish'
    return 'Neutral'
}

function WatchlistPage() {
    const [watchlistData, setWatchListData] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')

    const fetch_watchlist = async () => {
        setIsLoading(true)
        try {
            const getWatchlistResponse = await axios.get(`${import.meta.env.VITE_API_URL}/api/watchlist`)
            const ticker = getWatchlistResponse.data

            const sentimentResponses = await Promise.all(
                ticker.map(row => axios.get(`${import.meta.env.VITE_API_URL}/api/sentiment/history/${row.ticker}`))
            )

            const combined = ticker.map((row, index) => ({
                ticker: row.ticker,
                sentimentHistory: sentimentResponses[index].data
            }))
            setWatchListData(combined)

        } catch (error) {
            console.log(error)
            setError('Failed to load watchlist')
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetch_watchlist()
    }, [])

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Typography variant="h4" sx={{ mb: 3 }}>Watchlist</Typography>

            {isLoading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
                    <CircularProgress />
                </Box>
            )}

            {error && (
                <Typography color="error">{error}</Typography>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {watchlistData && watchlistData.map((watchlist) => {
                    const latestScore = watchlist.sentimentHistory.at(-1)?.sentiment_score
                    return (
                        <Card key={watchlist.ticker}>
                            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: '12px !important' }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 700, letterSpacing: '0.5px' }}>
                                    {watchlist.ticker}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    {latestScore !== undefined && (
                                        <Typography variant="body2" color="text.secondary">
                                            Score: {latestScore?.toFixed(3)}
                                        </Typography>
                                    )}
                                    <Chip
                                        label={getSentimentLabel(latestScore)}
                                        color={getSentimentColor(latestScore)}
                                        size="small"
                                        sx={{ fontWeight: 600, minWidth: 70 }}
                                    />
                                </Box>
                            </CardContent>
                        </Card>
                    )
                })}
            </Box>
        </Container>
    )
}

export default WatchlistPage
