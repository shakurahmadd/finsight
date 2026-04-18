import { Card, CardContent, Typography, Chip, Box } from "@mui/material";

function NewsFeed({ news }) {
    return (
        <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Latest News</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {news.map((article) => (
                    <Card key={article.title}>
                        <CardContent sx={{ py: '12px !important' }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
                                <Typography variant="body2" sx={{ flex: 1, lineHeight: 1.5 }}>
                                    {article.title}
                                </Typography>
                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5, flexShrink: 0 }}>
                                    <Chip
                                        label={article.sentiment_label}
                                        size="small"
                                        color={
                                            article.sentiment_label === 'Bullish' ? 'success' :
                                            article.sentiment_label === 'Bearish' ? 'error' :
                                            'default'
                                        }
                                        sx={{ fontWeight: 600, minWidth: 65 }}
                                    />
                                    {article.sentiment_confidence && (
                                        <Typography variant="caption" color="text.secondary">
                                            {(article.sentiment_confidence * 100).toFixed(1)}% confidence
                                        </Typography>
                                    )}
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>
                ))}
            </Box>
        </Box>
    )
}

export default NewsFeed
