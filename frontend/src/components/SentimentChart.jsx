import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import { Card, CardContent, Typography } from '@mui/material'

function SentimentChart({ data }) {
    return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>30-Day Sentiment Trend</Typography>
                <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                        <XAxis
                            dataKey="date"
                            tickFormatter={(date) => new Date(date).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })}
                            tick={{ fill: '#8b949e', fontSize: 12 }}
                            axisLine={{ stroke: '#30363d' }}
                            tickLine={false}
                        />
                        <YAxis
                            domain={[-1, 1]}
                            tick={{ fill: '#8b949e', fontSize: 12 }}
                            axisLine={{ stroke: '#30363d' }}
                            tickLine={false}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#161b22', border: '1px solid #30363d', borderRadius: 8 }}
                            labelStyle={{ color: '#8b949e' }}
                            itemStyle={{ color: '#58a6ff' }}
                        />
                        <ReferenceLine y={0} stroke="#30363d" strokeDasharray="4 4" />
                        <Line
                            type="monotone"
                            dataKey="sentiment_score"
                            stroke="#58a6ff"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4, fill: '#58a6ff' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    )
}

export default SentimentChart
