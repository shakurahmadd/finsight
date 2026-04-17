import { Box, Container, Typography } from "@mui/material";
import axios from "axios";
import { useEffect, useState } from "react";

function WatchlistPage() {
    const [watchlistData, setWatchListData] = useState(null)
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState('')


    const fetch_watchlist = async () => {
        setIsLoading(true)
        try {
        const getWatchlistResponse = await axios.get(`http://localhost:8000/watchlist`)
        const ticker = getWatchlistResponse.data
        
        const sentimentResponses = await Promise.all(
            ticker.map(row => axios.get(`http://localhost:8000/sentiment/history/${row.ticker}`))
        )

        const combined = ticker.map((row, index) => ({
            ticker: row.ticker,
            sentimentHistory: sentimentResponses[index].data
            
        }))
        setWatchListData(combined)


    } catch (error) {
        console.log(error)
        setError(error.response.data.detail)
    
    }finally {
        setIsLoading(false)
     }}

    useEffect(() => {
        fetch_watchlist()
    }, [])


    return (
        <Container>
            {watchlistData && watchlistData.map((watchlist) => (
                <Box key={watchlist.ticker}>
                    <Typography>{watchlist.ticker}</Typography>
                    <Typography>{watchlist.sentimentHistory.at(-1)?.sentiment_score}</Typography>
                </Box>
            ))}
        </Container>
    )
}

export default WatchlistPage