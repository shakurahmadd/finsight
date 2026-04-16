import { useState } from 'react'
import axios from 'axios'
import { TextField, Button, Typography, Container, Box, Card, CardContent, CircularProgress} from '@mui/material'
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
    const handleSearch = async () => {
        setIsLoading(true)                                                                                                                                    
        try {
            const response = await axios.post('http://localhost:8000/analyse', { ticker: ticker })                                                            
            setAnalysisResult(response.data)                                                                                                                
                                                
            const sentimentResponse = await axios.get(`http://localhost:8000/sentiment/history/${ticker}`)
            setSentimentHistory(sentimentResponse.data)
    

            const newsFeedResponse = await axios.get(`http://localhost:8000/news/${ticker}`)
            setNewsFeed(newsFeedResponse.data)
            
            const earningsTableResponse = await axios.get(`http://localhost:8000/earnings/${ticker}`)
            setEarningsTable(earningsTableResponse.data)

            const secFilingResponse = await axios.get(`http://localhost:8000/filings/${ticker}`)
            setSecFilingCard(secFilingResponse.data)

        } catch (error) {                                                                                                                                     
            console.error(error)                
        } finally {                                                                                                                                           
            setIsLoading(false)                                                                                                                             
        }                                                                                                                                                     
    }
    
    return (
        <Container maxWidth="md">
            <Box sx={{ mt: 4, mb: 4 }}>
                <Typography variant="h4">Ticker Research</Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                <TextField
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value)}
                    label="Enter ticker"
                />
                <Button variant="contained" onClick={handleSearch}>Search</Button>
            </Box>
            {isLoading && <CircularProgress />}
            {analysisResult && (
                <Card sx={{ mb: 2}}>
                    <CardContent>
                        <Typography variant="h6">Reseach Summary</Typography>
                        <Typography variant="body1">{analysisResult.summary}</Typography>
                    </CardContent>
                </Card>                                                                                                                                              
            )}
            {sentimentHistory && <SentimentChart data={sentimentHistory} />} 

            {newsFeed && <NewsFeed news={newsFeed} />}

            {earningsTable && <EarningsTable earnings={earningsTable} />}

            {secFilingCard && <SecFilings filings={secFilingCard} />}


        </Container>                                                                                                                                          
    )
}             

export default TickerResearchPage