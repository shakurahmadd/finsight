import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'
import { Card, CardContent, Typography } from '@mui/material'

function SentimentChart({ data }) {
    return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                <Typography variant="h6">30-Day Sentiment Trend</Typography>
                <LineChart width={600} height={300} data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date"
                            tickFormatter={(date) => new Date(date).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })} />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="sentiment_score" stroke="#1976d2" />
                </LineChart>
            </CardContent>
        </Card>
    )
}

export default SentimentChart